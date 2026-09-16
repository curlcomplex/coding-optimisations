#!/usr/bin/env python3
"""Read-only audit of owned hook trials. No model calls; raw tool items stay private."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re

ARMS=('standalone-off','standalone-on','desktop-chatgpt-off','desktop-chatgpt-on')

def thread_id(events):
    ids=[]
    for event in events:
        if event.get('type')=='thread.started':ids.append(event.get('thread_id'))
        if event.get('method')=='thread/started':ids.append(event['params']['thread']['id'])
        result=event.get('result')
        if isinstance(result,dict) and isinstance(result.get('thread'),dict):ids.append(result['thread'].get('id'))
    ids=list(dict.fromkeys(ids))
    if len(ids)!=1 or not isinstance(ids[0],str) or not re.fullmatch(r'[a-f0-9-]{36}',ids[0]):
        raise ValueError('trial thread identity not unique')
    return ids[0]

def audit(prior,output,home):
    prior=prior.resolve();output.mkdir(parents=True,exist_ok=False)
    previous=json.loads((prior/'safe.json').read_text())
    if previous.get('invocation_attempts')!=4:raise ValueError('expected four completed attempts')
    report={'stage':'rtk-hook-owned-trace-audit','model_calls':0,'arms':[]}
    today=dt.datetime.now(dt.timezone.utc).date()
    for name in ARMS:
        data=(prior/(name+'.jsonl')).read_bytes()
        original=next(r for r in previous['arms'] if r['label']==name)
        if hashlib.sha256(data).hexdigest()!=original['trace_sha256']:raise ValueError('trial trace changed')
        ident=thread_id([json.loads(x) for x in data.splitlines() if x.strip()])
        paths=[]
        for day in (today,today-dt.timedelta(days=1),today+dt.timedelta(days=1)):
            paths.extend((home/'sessions'/day.strftime('%Y/%m/%d')).glob('*'+ident+'*.jsonl'))
        if len(paths)!=1 or paths[0].is_symlink() or paths[0].stat().st_size>20_000_000:
            raise ValueError('owned rollout not safely/uniquely available')
        raw=paths[0].read_bytes();rows=[json.loads(x) for x in raw.splitlines() if x.strip()]
        if [x.get('payload',{}).get('id') for x in rows if x.get('type')=='session_meta']!=[ident]:
            raise ValueError('rollout identity mismatch')
        selected=[];contexts=[];catalogue_mentions=0
        for event in rows:
            p=event.get('payload',{})
            if event.get('type')=='response_item':
                if p.get('type') in ('function_call','function_call_output','custom_tool_call','custom_tool_call_output'):
                    selected.append(event)
                if p.get('type')=='message' and p.get('role')=='developer':
                    catalogue_mentions+=json.dumps(p).count('Available skills')
            if event.get('type')=='turn_context':
                contexts.append({k:p.get(k) for k in ('model','effort','approval_policy','sandbox_policy') if k in p})
        (output/(name+'-tools.private.json')).write_text(json.dumps(selected,indent=2)+'\n')
        # Context can contain private paths: this file is retained only privately.
        (output/(name+'-context.private.json')).write_text(json.dumps(contexts,indent=2)+'\n')
        report['arms'].append({'label':name,'rollout_sha256':hashlib.sha256(raw).hexdigest(),
                               'tool_items':len(selected),'developer_available_skills_mentions':catalogue_mentions})
    (output/'safe.json').write_text(json.dumps(report,indent=2)+'\n');return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prior',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if 'PUEUE_WORKER_ID' not in os.environ:raise SystemExit('Use established private queue')
    os.umask(0o077)
    report=audit(args.prior,args.output,Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex'))))
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
