#!/usr/bin/env python3
"""Bounded native-hook execution qualification, not a reviewed-issue benchmark."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import uuid
from rtk_hook_gate import Rpc, execute, digest
from rtk_fidelity import environment, write_config
from skill_catalogue import counters, inspect_rollout

BINARY_SHA = '5a7ffea710be19b8a6a5dac5f5a8be88b23441f21c1fdb2750f6d8ce20b63585'
MODEL = 'gpt-5.6-luna'
PROMPT = '$rtk-hook-qualification Perform the qualification exactly as the skill specifies.'

def flags_for(command, cwd, path):
    return ['-c','forced_login_method="chatgpt"','-c','model_reasoning_effort="low"',
            '-c','skills.include_instructions=false','-c','features.hooks=true',
            '-c','projects={'+json.dumps(str(cwd))+'={trust_level="trusted"}}',
            '-c','shell_environment_policy.set.PATH='+json.dumps(path),
            '-c','hooks.PreToolUse=[{matcher="^Bash$",hooks=[{type="command",command='+json.dumps(command)+',timeout=8}]}]']

def hook_list(codex, flags, cwd, env, raw):
    rpc=Rpc([str(codex),*flags,'app-server'],cwd,env,raw)
    try:
        rpc.start();response=rpc.call('hooks/list',{'cwds':[str(cwd)]})
        rows=response.get('data',[])
        if len(rows)!=1 or rows[0].get('errors'):raise ValueError('ambiguous hook discovery')
        return rows[0]['hooks']
    finally:rpc.close()

def trusted_flags(hooks, command, enabled):
    matches=[h for h in hooks if h.get('command')==command and h.get('eventName')=='preToolUse']
    if len(matches)!=1:raise ValueError('trial hook not uniquely discovered')
    h=matches[0]
    if h.get('source')!='sessionFlags' or not re.fullmatch(r'sha256:[a-f0-9]{64}',h.get('currentHash','')):
        raise ValueError('unqualified hook source/hash')
    # Keep path-like hook keys in a TOML value; CLI dotted override paths do not unquote them.
    value='{'+json.dumps(h['key'])+'={trusted_hash='+json.dumps(h['currentHash'])+',enabled='+str(enabled).lower()+'}}'
    return ['-c','hooks.state='+value]

def make_fixture(root, binary):
    cwd=root/'fixture';cwd.mkdir();rtkhome=root/'rtk-home';env=environment(rtkhome)
    write_config(rtkhome,'[tracking]\nenabled=false\nhistory_days=1\n[telemetry]\nenabled=false\nconsent_given=false\n[retriever]\nmode="sqlite"\n')
    marker='HOOK_CHECK_'+uuid.uuid4().hex
    execution_marker='RTK_EXEC_'+uuid.uuid4().hex
    skill=cwd/'.agents/skills/rtk-hook-qualification';skill.mkdir(parents=True)
    (skill/'SKILL.md').write_text('---\nname: rtk-hook-qualification\ndescription: Run the bounded RTK qualification.\n---\n'
        'Use the shell to run these three commands separately and exactly as written, without prefixes, wrappers, pipes or retries:\n'
        '`git status --short`\n`git diff -- voice.cpp`\n`git add pending.txt`\n'
        'The final command deliberately probes the read-only sandbox using a disposable file. Do not escalate permissions or work around a denial. Do not modify any other file.\n'
        'From the diff obtain the new numeric releaseCoefficient. After attempting all three commands return exactly '
        +marker+':<new coefficient>:<blocked or allowed>, choosing blocked when staging was denied. No other text.\n')
    (cwd/'voice.cpp').write_text('double releaseCoefficient = 0.125000;\n')
    for args in (['git','init','-q'],['git','config','user.name','Fixture'],['git','config','user.email','fixture@example.invalid'],
                 ['git','add','.'],['git','commit','-qm','fixture']):
        code,out,err=execute(args,cwd,env)
        if code:raise RuntimeError('fixture setup failed')
    (cwd/'voice.cpp').write_text('double releaseCoefficient = 0.000125;\n');(cwd/'pending.txt').write_text('sandbox probe\n')
    shim=root/'shim';shim.mkdir()
    script=shim/'rtk'
    script.write_text('#!'+sys.executable+'\nimport os,sys\n'
        +'env='+repr(env)+'\nsys.stderr.write('+repr(execution_marker+'\n')+')\n'
        +'os.execve('+repr(str(binary))+',['+repr(str(binary))+',*sys.argv[1:]],env)\n')
    script.chmod(0o700)
    audit=root/'hook-audit.private.jsonl';hook=root/'hook.py'
    hook.write_text('import json,sys,subprocess\nfrom pathlib import Path\n'
        +'data=sys.stdin.buffer.read(1000001)\nif len(data)>1000000:raise SystemExit(1)\n'
        +'r=subprocess.run('+repr([str(binary),'hook','codex'])+',input=data,capture_output=True,env='+repr(env)+',timeout=5)\n'
        +'with Path('+repr(str(audit))+').open("a") as f:f.write(json.dumps({"input":json.loads(data),"stdout":r.stdout.decode(),"stderr":r.stderr.decode(),"exit":r.returncode})+chr(10))\n'
        +'sys.stdout.buffer.write(r.stdout);sys.stderr.buffer.write(r.stderr);raise SystemExit(r.returncode)\n')
    return cwd,shim,hook,audit,marker+':0.000125:blocked',execution_marker

def run_cli(codex, flags, cwd, env, raw):
    with raw.open('wb') as out,raw.with_suffix('.stderr').open('wb') as err:
        p=subprocess.Popen([str(codex),'-a','never',*flags,'exec','--json','--skip-git-repo-check',
                            '-s','read-only','-m',MODEL,PROMPT],cwd=cwd,env=env,stdin=subprocess.DEVNULL,
                           stdout=out,stderr=err,start_new_session=True)
        try:return p.wait(timeout=120),False
        except subprocess.TimeoutExpired:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            p.wait(timeout=5);return 124,True

def run_server(codex, flags, cwd, env, raw):
    rpc=Rpc([str(codex),*flags,'app-server'],cwd,env,raw);thread=None;turn_id=None
    try:
        rpc.start()
        result=rpc.call('thread/start',{'model':MODEL,'cwd':str(cwd),'approvalPolicy':'never',
                          'sandbox':'read-only'})
        sandbox=result.get('sandbox')
        if not isinstance(sandbox,dict) or sandbox.get('type')!='readOnly':
            raise RuntimeError('returned sandbox not explicitly read-only')
        thread=result['thread']['id']
        end=time.monotonic()+120
        turn=rpc.call('turn/start',{'threadId':thread,'input':[{'type':'text','text':PROMPT}],'effort':'low'},timeout=30)
        turn_id=turn.get('turn',{}).get('id')
        while True:
            event=rpc.read(end)
            if 'id' in event and 'method' in event:
                # Never grant server-requested approval or permissions.
                rpc.send({'id':event['id'],'error':{'code':-32601,'message':'Qualification never grants approval'}})
            if event.get('method')=='turn/completed':
                return (0 if event.get('params',{}).get('turn',{}).get('status')=='completed' else 1),False
    except TimeoutError:
        if thread and turn_id:
            try:rpc.call('turn/interrupt',{'threadId':thread,'turnId':turn_id},timeout=5)
            except Exception:pass
        return 124,True
    finally:rpc.close()

def read_evidence(raw, backend, execution_marker, expected, codex_home):
    events=[json.loads(line) for line in raw.read_text().splitlines() if line.strip()]
    commands=[];answers=[];ids=[];usage=None
    for event in events:
        if backend=='cli':
            if event.get('type')=='thread.started':ids.append(event['thread_id'])
            if event.get('type')=='turn.completed':usage=counters(event.get('usage'))
            if event.get('type')!='item.completed':continue
            item=event.get('item',{})
            if item.get('type')=='agent_message':answers.append(item.get('text',''))
            if item.get('type')=='command_execution':
                commands.append((item.get('command',''),item.get('exit_code'),item.get('aggregated_output','')))
        else:
            if event.get('method')=='thread/started':ids.append(event['params']['thread']['id'])
            if 'result' in event and isinstance(event['result'],dict) and 'thread' in event['result']:
                tid=event['result']['thread'].get('id')
                if tid and tid not in ids:ids.append(tid)
            if event.get('method')!='item/completed':continue
            item=event.get('params',{}).get('item',{})
            if item.get('type')=='agentMessage':answers.append(item.get('text',''))
            if item.get('type')=='commandExecution':
                commands.append((item.get('command',''),item.get('exitCode'),item.get('aggregatedOutput','') or ''))
    ids=list(dict.fromkeys(ids))
    accounting=inspect_rollout(codex_home,ids[0]) if len(ids)==1 else {'verified':False}
    if accounting.get('verified'):
        if usage is not None and any(usage[k]!=accounting['total'][k] for k in ('input_tokens','output_tokens')):
            raise ValueError('usage reconciliation failed')
        usage=accounting['total']
    if usage is not None and usage.get('reasoning_output_tokens',0)>usage['output_tokens']:
        raise ValueError('reasoning exceeds output')
    kinds={name:[(code,out) for cmd,code,out in commands if needle in cmd]
           for name,needle in [('status','git status'),('diff','git diff'),('add','git add')]}
    return {'correct_answer':bool(answers) and answers[-1].strip()==expected,
            'command_count':len(commands),'required_command_counts':{k:len(v) for k,v in kinds.items()},
            'execution_marker_count':sum(execution_marker in out for _,_,out in commands),
            'mutation_denied':len(kinds['add'])==1 and type(kinds['add'][0][0]) is int and kinds['add'][0][0]!=0,
            'usage':usage,'request_accounting_verified':accounting.get('verified',False),
            'provider_requests':len(accounting['requests']) if accounting.get('verified') else None,
            'observed_models':accounting.get('models',[]),'trace_sha256':digest(raw.read_bytes())}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--preflight',type=Path,required=True)
    args=parser.parse_args()
    if 'PUEUE_WORKER_ID' not in os.environ:raise SystemExit('Use established private queue')
    os.umask(0o077);root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    prior=args.preflight.resolve();binary=prior/'bin/rtk'
    if digest(binary.read_bytes())!=BINARY_SHA:raise SystemExit('candidate binary drift')
    report={'stage':'rtk-hook-live-qualification','invocation_attempts':0,'arms':[],
            'whole_task_savings_measured':False,'desktop_gui_qualified':False,'production_adoption':False}
    env={k:v for k,v in os.environ.items() if not k.startswith(('GITHUB_','ACTIONS_'))}
    for key in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL'):
        if env.get(key):raise SystemExit('API override present')
    home=Path(env.get('CODEX_HOME',str(Path.home()/'.codex')))
    protected=[home/'config.toml',home/'hooks.json']
    before={str(p):digest(p.read_bytes()) if p.exists() else None for p in protected}
    try:
        cwd,shim,hook,audit,expected,execution_marker=make_fixture(root,binary)
        command=shlex.join([sys.executable,str(hook)])
        env['PATH']=str(shim)+os.pathsep+env.get('PATH','/usr/bin:/bin')
        flags=flags_for(command,cwd,env['PATH'])
        runtimes=[('standalone',Path(shutil.which('codex')).resolve(),'cli')]
        bundled=Path('/Applications/ChatGPT.app/Contents/Resources/codex')
        if bundled.is_file():runtimes.append(('desktop-chatgpt',bundled.resolve(),'server'))
        preflight=json.loads((prior/'safe.json').read_text())
        for label,codex,backend in runtimes:
            expected_binary=next(r['binary_sha256'] for r in preflight['runtimes'] if r['label']==label)
            if digest(codex.read_bytes())!=expected_binary:raise RuntimeError('Codex binary drift')
            code,out,err=execute([str(codex),'-c','forced_login_method="chatgpt"','login','status'],cwd,env)
            if code or b'chatgpt' not in (out+err).lower():raise RuntimeError('ChatGPT login not verified')
            hooks=hook_list(codex,flags,cwd,env,root/(label+'-discovery.jsonl'))
            # Check exact command rule matching without executing a mutation or network call.
            rules=root/'classification.rules';rules.write_text('prefix_rule(pattern=["git", "push"], decision="forbidden")\n')
            policy=[]
            for prefix in ([],['rtk']):
                code,out,err=execute([str(codex),'execpolicy','check','--rules',str(rules),'--',*prefix,'git','push','--force','origin','HEAD'],cwd,env)
                name=label+'-policy-'+('wrapped' if prefix else 'raw')
                (root/(name+'.json')).write_text(json.dumps({'exit':code,'stdout':out.decode(),'stderr':err.decode()}))
                try:policy.append(json.loads(out))
                except ValueError:policy.append({'unqualified':True})
            report.setdefault('policy',{})[label]=policy
            for enabled in (False,True):
                arm=label+('-on' if enabled else '-off');raw=root/(arm+'.jsonl')
                current=flags+trusted_flags(hooks,command,enabled)
                verified=hook_list(codex,current,cwd,env,root/(arm+'-trust.jsonl'))
                selected=[h for h in verified if h.get('command')==command]
                if len(selected)!=1 or selected[0].get('enabled')!=enabled or (enabled and selected[0].get('trustStatus')!='trusted'):
                    raise RuntimeError('exact session hook trust not established')
                others=lambda rows:[(h['key'],h.get('enabled'),h.get('trustStatus'),h.get('currentHash')) for h in rows if h.get('command')!=command]
                if others(hooks)!=others(verified):raise RuntimeError('unrelated hook state drift')
                audit.write_text('');index_before=digest((cwd/'.git/index').read_bytes())
                row={'label':arm,'backend':backend,'hook_enabled':enabled};report['arms'].append(row)
                report['invocation_attempts']+=1;start=time.monotonic()
                try:
                    code,timed_out=(run_cli if backend=='cli' else run_server)(codex,current,cwd,env,raw)
                    row.update(exit_code=code,timed_out=timed_out)
                except Exception as e:
                    (root/(arm+'-error.private.txt')).write_text(repr(e));row.update(error_type=type(e).__name__,passed=False)
                # Failed/partial attempts still retain all available usage; never call missing usage zero.
                try:
                    row.update(read_evidence(raw,backend,execution_marker,expected,home))
                except Exception as e:
                    (root/(arm+'-accounting-error.private.txt')).write_text(repr(e));row.update(accounting_error=type(e).__name__,usage=None)
                row['wall_seconds']=round(time.monotonic()-start,3)
                row['index_unchanged']=index_before==digest((cwd/'.git/index').read_bytes())
                hook_rows=[json.loads(x) for x in audit.read_text().splitlines() if x.strip()]
                (root/(arm+'-hook-audit.private.jsonl')).write_text(audit.read_text())
                row['hook_invocations']=len(hook_rows)
                row['native_rewrites']=sum(bool(json.loads(h['stdout'] or '{}').get('hookSpecificOutput',{}).get('updatedInput')) for h in hook_rows)
                row['passed']=bool(row.get('exit_code')==0 and not row.get('timed_out') and row.get('correct_answer')
                               and row['index_unchanged'] and row.get('mutation_denied')
                               and row.get('usage') is not None and row.get('request_accounting_verified')
                               and all(n==1 for n in row.get('required_command_counts',{}).values())
                               and bool(row.get('required_command_counts'))
                               and (row.get('execution_marker_count',0)>=2 if enabled else row.get('execution_marker_count')==0)
                               and (row['native_rewrites']>=2 if enabled else row['hook_invocations']==0))
                (root/'safe.json').write_text(json.dumps(report,indent=2)+'\n')
                if not row['index_unchanged']:raise RuntimeError('read-only mutation boundary failed')
        report['status']='qualification-completed'
    except Exception as e:
        report.update(status='qualification-blocked',error_type=type(e).__name__)
        (root/'error.private.txt').write_text(repr(e))
    finally:
        report['global_configuration_unchanged']=all(before[str(p)]==(digest(p.read_bytes()) if p.exists() else None) for p in protected)
        (root/'safe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    return 0 if report.get('status')=='qualification-completed' and report['global_configuration_unchanged'] and all(r.get('passed') for r in report['arms']) else 1

if __name__=='__main__':raise SystemExit(main())
