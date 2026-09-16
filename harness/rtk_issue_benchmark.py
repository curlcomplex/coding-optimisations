#!/usr/bin/env python3
"""Issue #11: matched coding implementations AND fresh independent reviews.

Reuse the lab's installed first-party Codex app-server transport and strict rollout
accounting. Private evidence only; no production installer or credentials copied.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
from issue_fixtures import materialize, files
from rtk_hook_gate import Rpc, execute, digest, fetch_binary
from rtk_hook_live import hook_list, trusted_flags
from rtk_fidelity import environment, isolated_config, toml, write_config
from skill_catalogue import inspect_rollout

STABLE_SHA='055ef1cd1aa0afb96c854bddf43d24af10dcac5a6288ed44519cb1cc10b093a9'
HOOK_SHA='5a7ffea710be19b8a6a5dac5f5a8be88b23441f21c1fdb2750f6d8ce20b63585'
WORKER='gpt-5.6-terra'; REVIEWER='gpt-5.6-luna'; EFFORT='medium'
MAX_TOKENS=3_000_000; MAX_INVOCATIONS=16; TOTAL_SECONDS=3000
TASK_PROMPT='Implement ISSUE.md using the repository RTK/Serena workflow. Run the unchanged tests and finish with changes and test evidence.'
REVIEW_PROMPT='''Independently review the current patch against ISSUE.md. Inspect the actual source and git diff; run python3 run_tests.py. Do not change any source, tests, instructions or configuration. Assess all specified edge cases, API compatibility and maintainability, not only whether tests pass. Do not read other trial directories. Return a JSON object only: {"accepted": true or false, "findings": [specific blocking defects if any]}. Do not accept if any requirement is unfulfilled.'''


def snapshot(paths):
    return {str(p):digest(p.read_bytes()) if p.is_file() and not p.is_symlink() else None for p in paths}


def protected_ok(cwd, expected):
    for name,want in expected.items():
        if name.startswith('src/'):continue
        path=cwd/name
        if path.is_symlink() or not path.is_file() or digest(path.read_bytes())!=want:return False
    return True


def source_snapshot(cwd):
    return {str(p.relative_to(cwd)):digest(p.read_bytes()) for p in sorted((cwd/'src').rglob('*')) if p.is_file()}


def allow_inspection(command):
    """Conservative local-read scope; never rewrite Git mutations or compounds."""
    if any(c in command for c in (';', '|', '&', '>', '<', '$', '`', '\n')):return False
    try:argv=shlex.split(command)
    except ValueError:return False
    if not argv:return False
    if argv[0]=='git':
        return len(argv)>1 and argv[1] in ('status','diff','log','show') and not any(a.startswith(('--ext-diff','--textconv','--output','--exec-path','--config-env')) for a in argv)
    if argv[0] in ('ls','cat','head','tail'):return True
    if argv[0] in ('rg','grep'):
        return not any(a.startswith(('--pre','--hostname-bin','--hyperlink-format')) for a in argv)
    return False


def hook_delegate(config_path):
    cfg=json.loads(Path(config_path).read_text())
    data=sys.stdin.buffer.read(1_000_001)
    if len(data)>1_000_000:return 1
    try:obj=json.loads(data);command=obj.get('tool_input',{}).get('command','')
    except (ValueError,AttributeError):return 0
    response=b'';err=b'';code=0
    if isinstance(command,str) and allow_inspection(command):
        code,response,err=execute([cfg['hook_binary'],'hook','codex'],Path(cfg['cwd']),cfg['hook_env'],data,5)
    record={'command':command,'response':response.decode(errors='replace'),'exit':code}
    with Path(cfg['audit']).open('a') as f:f.write(json.dumps(record)+'\n')
    sys.stdout.buffer.write(response);sys.stderr.buffer.write(err)
    return code


def setup_trial(parent,kind,stable,hook_binary,live_rtk_config):
    cwd=parent/'fixture';expected=materialize(cwd,kind)
    rtkhome=cwd/'.rtk-state';rtkenv=environment(rtkhome)
    write_config(rtkhome,toml(isolated_config(live_rtk_config)))
    # Same executable, argument path and isolated stores for both arms.
    shim=parent/'shim';shim.mkdir()
    (shim/'rtk').write_text('#!'+sys.executable+'\nimport os,sys\n'
        +'from pathlib import Path\nimport json\nwith Path('+repr(str(rtkhome/'executions.jsonl'))+').open("a") as f:f.write(json.dumps(sys.argv[1:])+chr(10))\n'
        +'os.execve('+repr(str(stable))+',['+repr(str(stable))+',*sys.argv[1:]],'+repr(rtkenv)+')\n')
    (shim/'rtk').chmod(0o700)
    # Avoid counting writable tool caches as task changes.
    (cwd/'.gitignore').write_text((cwd/'.gitignore').read_text()+'.rtk-state/\n')
    expected['.gitignore']=digest((cwd/'.gitignore').read_bytes())
    genv=dict(rtkenv,GIT_AUTHOR_DATE='2026-09-16T00:00:00Z',GIT_COMMITTER_DATE='2026-09-16T00:00:00Z')
    for args in (['git','init','-q'],['git','config','user.name','Fixture'],['git','config','user.email','fixture@example.invalid'],
                 ['git','add','.'],['git','commit','-qm','Frozen issue fixture']):
        code,_,_=execute(args,cwd,genv)
        if code:raise RuntimeError('fixture Git setup failed')
    code,out,_=execute(['git','rev-parse','HEAD'],cwd,genv)
    if code:raise RuntimeError('fixture commit missing')
    baseline=out.decode().strip()
    hookenv=environment(parent/'hook-home')
    write_config(Path(hookenv['HOME']),toml(isolated_config(live_rtk_config)))
    config=parent/'delegate.private.json';audit=parent/'hook-audit.private.jsonl'
    config.write_text(json.dumps({'hook_binary':str(hook_binary),'cwd':str(cwd),'hook_env':hookenv,'audit':str(audit)}))
    command=shlex.join([sys.executable,str(Path(__file__).resolve()),'--delegate',str(config)])
    return cwd,shim,expected,baseline,command,audit


def inline(value):
    if isinstance(value,dict):return '{'+','.join(json.dumps(k)+'='+inline(v) for k,v in value.items())+'}'
    if isinstance(value,list):return '['+','.join(inline(v) for v in value)+']'
    if isinstance(value,bool):return str(value).lower()
    if isinstance(value,(str,int,float)):return json.dumps(value)
    raise ValueError('unsupported existing hook config')


def base_flags(cwd,path,command,existing_pretool=None):
    # Do not overwrite global hooks, MCP, model policy, instructions or auth.
    return ['-c','forced_login_method="chatgpt"','-c','skills.include_instructions=false',
      '-c','features.hooks=true','-c','projects={'+json.dumps(str(cwd))+'={trust_level="trusted"}}',
      '-c','shell_environment_policy.set.PATH='+json.dumps(path),
      '-c','shell_environment_policy.set.RTK_TELEMETRY_DISABLED="1"',
      '-c','sandbox_workspace_write.network_access=false',
      '-c','hooks.PreToolUse='+inline(list(existing_pretool or [])+[{'matcher':'^Bash$','hooks':[{'type':'command','command':command,'timeout':8}]}])]


def parse_review(answer):
    text=answer.strip()
    if text.startswith('```'):
        text=re.sub(r'^```(?:json)?\s*|\s*```$','',text)
    value=json.loads(text)
    if not isinstance(value,dict) or type(value.get('accepted')) is not bool or not isinstance(value.get('findings'),list):
        raise ValueError('invalid independent review')
    return value['accepted'] and not value['findings'],value


def run_agent(codex,flags,cwd,env,raw,model,prompt,timeout,home):
    row={'model':model,'reasoning':EFFORT,'passed':False,'usage':None,'timed_out':False}
    rpc=None;thread=None;turn_id=None;started=time.monotonic();end=started+timeout
    try:
        rpc=Rpc([str(codex),*flags,'app-server'],cwd,env,raw);rpc.start()
        t=rpc.call('thread/start',{'model':model,'cwd':str(cwd),'approvalPolicy':'never','sandbox':'workspace-write'},timeout=20)
        sandbox=t.get('sandbox')
        if not isinstance(sandbox,dict) or sandbox.get('type')!='workspaceWrite' or sandbox.get('networkAccess') is True:
            raise RuntimeError('unexpected sandbox')
        thread=t['thread']['id'];row['thread_id']=thread
        turn=rpc.call('turn/start',{'threadId':thread,'input':[{'type':'text','text':prompt}],'effort':EFFORT},timeout=20)
        turn_id=turn.get('turn',{}).get('id')
        while True:
            e=rpc.read(end)
            if 'method' in e and 'id' in e:
                rpc.send({'id':e['id'],'error':{'code':-32601,'message':'Benchmark never escalates approvals'}})
            if e.get('method')=='turn/completed' and e.get('params',{}).get('threadId')==thread:
                row['passed']=e['params'].get('turn',{}).get('status')=='completed';break
    except TimeoutError:
        row['timed_out']=True
        if rpc and thread and turn_id:
            try:rpc.call('turn/interrupt',{'threadId':thread,'turnId':turn_id},timeout=5)
            except Exception:pass
    except Exception as error:
        row['error_type']=type(error).__name__;raw.with_suffix('.error.private.txt').write_text(repr(error))
    finally:
        if rpc:rpc.close()
        row['wall_seconds']=round(time.monotonic()-started,3)
        events=[json.loads(x) for x in raw.read_text().splitlines() if x.strip()] if raw.exists() else []
        answers=[]
        for e in events:
            if e.get('method')=='item/completed':
                item=e.get('params',{}).get('item',{})
                if item.get('type')=='agentMessage':answers.append(item.get('text',''))
        answer=answers[-1] if answers else ''
        raw.with_suffix('.answer.txt').write_text(answer)
        row['answer_present']=bool(answer)
        accounting=inspect_rollout(home,thread) if thread else {'verified':False}
        row['accounting_verified']=accounting.get('verified',False)
        if row['accounting_verified']:
            row['usage']=accounting['total'];row['provider_requests']=len(accounting['requests']);row['observed_models']=accounting['models']
            raw.with_suffix('.usage.json').write_text(json.dumps(accounting,indent=2))
        row['trace_sha256']=digest(raw.read_bytes()) if raw.exists() else None
    return row,answer


def check_tests(cwd,env,raw,expected):
    if not protected_ok(cwd,expected):
        raw.write_text("Protected test/input file changed; verification refused")
        return {"passed":False,"exit":97,"wall_seconds":0,"sha256":digest(raw.read_bytes())}
    start=time.monotonic()
    try:
        code,out,err=execute([sys.executable,'run_tests.py'],cwd,env,timeout=30)
    except TimeoutError:
        code,out,err=124,b'',b'owned deterministic test timeout'
    raw.write_bytes(out+err)
    return {'passed':code==0,'exit':code,'wall_seconds':round(time.monotonic()-start,3),'sha256':digest(out+err)}


def aggregate(rows):
    result={}
    for arm in ('off','on'):
        rs=[r for r in rows if r['arm']==arm]
        calls=[r[k] for r in rs for k in ('worker','review') if k in r]
        known=all(c.get('accounting_verified') and c.get('usage') is not None for c in calls)
        totals={key:(sum(c['usage'][key] for c in calls) if all(key in c['usage'] for c in calls) else None) for key in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')} if known else None
        accepted=sum(r.get('accepted',False) for r in rs)
        total=totals['input_tokens']+totals['output_tokens'] if totals else None
        result[arm]={'attempts':len(rs),'accepted':accepted,'failures':len(rs)-accepted,'model_invocations':len(calls),
          'usage':totals,'total_tokens':total,'tokens_per_accepted':total/accepted if accepted and total is not None else None,
          'output_per_accepted':totals['output_tokens']/accepted if accepted and totals else None,
          'wall_seconds':sum(c['wall_seconds'] for c in calls),'accounting_complete':known}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--codex',type=Path,required=True);p.add_argument('--stable-rtk',type=Path,required=True)
    args=p.parse_args()
    if 'PUEUE_WORKER_ID' not in os.environ:raise SystemExit('Established private queue required')
    os.umask(0o077);root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    env={k:v for k,v in os.environ.items() if not k.startswith(('GITHUB_','ACTIONS_'))}
    for k in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL'):
        if env.get(k):raise SystemExit('API override present')
    env['RTK_TELEMETRY_DISABLED']='1';env['PYTHONDONTWRITEBYTECODE']='1'
    home=Path(env.get('CODEX_HOME',str(Path.home()/'.codex')))
    config=home/'config.toml';rtkconfig=Path.home()/'Library/Application Support/rtk/config.toml'
    protected=[config,home/'hooks.json',home/'AGENTS.md',home/'AGENTS.override.md',rtkconfig]
    before=snapshot(protected)
    report={'schema':2,'stage':'rtk-reviewed-issue-ab','scope':'synthetic multi-case C++ and TypeScript issue fixtures; bundled engine app-server, not GUI interaction',
      'worker_model':WORKER,'review_model':REVIEWER,'reasoning':EFFORT,'rows':[],'invocations':0,
      'status':'running','whole_programme_usage_known':False,'prior_unaccounted_attempts':1,
      'budget':{'invocations':MAX_INVOCATIONS,'worker_seconds':180,'review_seconds':120,'batch_seconds':TOTAL_SECONDS,'stop_after_observed_tokens':MAX_TOKENS},
      'production_adoption':False,'subscription_allowance_savings':None}
    def save():
        report['aggregate']=aggregate(report['rows']);(root/'safe.json').write_text(json.dumps(report,indent=2)+'\n')
    save();end=time.monotonic()+TOTAL_SECONDS
    try:
        import tomllib
        liveconfig=tomllib.loads(config.read_text());live_rtk=tomllib.loads(rtkconfig.read_text()) if rtkconfig.exists() else {}
        if 'serena' not in liveconfig.get('mcp_servers',{}):raise RuntimeError('baseline Serena configuration missing')
        report['serena_configured']=True
        stable=args.stable_rtk.resolve(strict=True);codex=args.codex.resolve(strict=True)
        if digest(stable.read_bytes())!=STABLE_SHA:raise RuntimeError('stable baseline binary drift')
        report['codex_binary_sha256']=digest(codex.read_bytes());report['stable_binary_sha256']=STABLE_SHA
        report['common_config_sha256']=digest(config.read_bytes())
        report['instruction_hashes']={p.name:before[str(p)] for p in protected if p.name.startswith('AGENTS')}
        report['common_rtk_config_sha256']=digest(toml(isolated_config(live_rtk)).encode())
        hook_binary=fetch_binary(root)
        if digest(hook_binary.read_bytes())!=HOOK_SHA:raise RuntimeError('hook processor drift')
        report['hook_processor_sha256']=HOOK_SHA
        code,out,err=execute([str(codex),'-c','forced_login_method="chatgpt"','login','status'],root,env)
        if code or b'chatgpt' not in (out+err).lower():raise RuntimeError('subscription login not verified')
        report['subscription_login_verified']=True
        code,out,_=execute([str(codex),'--version'],root,env);report['codex_version']=out.decode().strip()
        rpc=Rpc([str(codex),'app-server'],root,env,root/'models.private.jsonl')
        try:
            rpc.start();models=rpc.call('model/list',{})
            available={m['id']:m for m in models.get('data',[])}
            for model in (WORKER,REVIEWER):
                if model not in available or EFFORT not in [e['reasoningEffort'] for e in available[model]['supportedReasoningEfforts']]:raise RuntimeError('requested model/effort unavailable')
        finally:rpc.close()
        bases={}
        for kind in ('cpp','ui'):
            for repetition in (1,2):
                for enabled in ((False,True) if repetition==1 else (True,False)):
                    observed=sum((c.get('usage') or {}).get('input_tokens',0)+(c.get('usage') or {}).get('output_tokens',0) for r in report['rows'] for c in (r.get('worker',{}),r.get('review',{})))
                    if report['invocations']+2>MAX_INVOCATIONS or time.monotonic()+320>end or observed>=MAX_TOKENS:
                        report['status']='budget-stopped';save();return 2
                    label=f'{kind}-{repetition}-'+('on' if enabled else 'off');parent=root/('trial-%02d' % (len(report['rows'])+1));parent.mkdir()
                    cwd,shim,expected,base,command,audit=setup_trial(parent,kind,stable,hook_binary,live_rtk)
                    if kind in bases and bases[kind]!=base:raise RuntimeError('starting commits not identical')
                    bases[kind]=base
                    row={'fixture':kind,'repetition':repetition,'arm':'on' if enabled else 'off','baseline_commit':base,'accepted':False};report['rows'].append(row)
                    trial_env=dict(env,PATH=str(shim)+os.pathsep+env.get('PATH','/usr/bin:/bin'))
                    flags=base_flags(cwd,trial_env['PATH'],command,liveconfig.get('hooks',{}).get('PreToolUse',[]))
                    hooks=hook_list(codex,flags,cwd,trial_env,parent/'discovery.jsonl')
                    flags+=trusted_flags(hooks,command,enabled)
                    verified=hook_list(codex,flags,cwd,trial_env,parent/'trust.jsonl')
                    trial=[h for h in verified if h.get('command')==command]
                    if len(trial)!=1 or trial[0].get('enabled')!=enabled or enabled and trial[0].get('trustStatus')!='trusted':raise RuntimeError('trial hook state not effective')
                    others=lambda hs:[(h['key'],h.get('enabled'),h.get('trustStatus')) for h in hs if h.get('command')!=command]
                    if others(hooks)!=others(verified):raise RuntimeError('unrelated hook changed')
                    row['initial_tests']=check_tests(cwd,trial_env,parent/'initial-tests.txt',expected)
                    if row['initial_tests']['passed']:raise RuntimeError('broken fixture unexpectedly passes')
                    audit.write_text('');report['invocations']+=1;save()
                    row['worker'],_=run_agent(codex,flags,cwd,trial_env,parent/'worker.jsonl',WORKER,TASK_PROMPT,180,home)
                    row['worker_tests']=check_tests(cwd,trial_env,parent/'worker-tests.txt',expected)
                    row['protected_after_worker']=protected_ok(cwd,expected)
                    src=source_snapshot(cwd)
                    shutil.copytree(cwd/'src',parent/'implementation-src')
                    code,patch,err=execute(['git','diff','--no-ext-diff','--','src'],cwd,trial_env)
                    (parent/'implementation.patch').write_bytes(patch)
                    row['patch_sha256']=digest(patch);row['changed_source']=bool(patch)
                    save();report['invocations']+=1;save()
                    row['review'],answer=run_agent(codex,flags,cwd,trial_env,parent/'review.jsonl',REVIEWER,REVIEW_PROMPT,120,home)
                    try:accepted,review=parse_review(answer);(parent/'review-verdict.json').write_text(json.dumps(review,indent=2))
                    except (ValueError,TypeError):accepted=False
                    row['independent_review_accepted']=accepted
                    row['reviewer_source_unchanged']=src==source_snapshot(cwd)
                    row['final_tests']=check_tests(cwd,trial_env,parent/'final-tests.txt',expected)
                    row['protected_after_review']=protected_ok(cwd,expected)
                    code,_,_=execute(['git','diff','--check'],cwd,trial_env);row['diff_check']=code==0
                    hookrows=[json.loads(x) for x in audit.read_text().splitlines() if x.strip()]
                    execution_log=cwd/'.rtk-state/executions.jsonl'
                    row['stable_wrapper_executions']=len(execution_log.read_text().splitlines()) if execution_log.exists() else 0
                    row['hook_calls']=len(hookrows);row['automatic_rewrites']=sum(bool(x['response'].strip()) for x in hookrows)
                    row['accepted']=all((row['worker'].get('passed'),row['review'].get('passed'),accepted,row['worker_tests']['passed'],row['final_tests']['passed'],row['protected_after_worker'],row['protected_after_review'],row['reviewer_source_unchanged'],row['changed_source'],row['diff_check']))
                    row['global_unchanged']=snapshot(protected)==before
                    save();print('TRIAL_RESULT '+json.dumps(row),flush=True)
                    if not row['global_unchanged']:raise RuntimeError('protected global config drift')
                    if not row['worker'].get('accounting_verified') or not row['review'].get('accounting_verified'):
                        report['status']='accounting-incomplete';save();return 2
        report['status']='completed';return 0
    except Exception as error:
        (root/'error.private.txt').write_text(repr(error));report.update(status='infrastructure-failed',error_type=type(error).__name__);return 2
    finally:
        report['protected_global_unchanged']=snapshot(protected)==before
        save();print('BENCHMARK_RESULT '+json.dumps(report),flush=True)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--delegate':raise SystemExit(hook_delegate(sys.argv[2]))
    raise SystemExit(main())
