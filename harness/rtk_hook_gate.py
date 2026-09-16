#!/usr/bin/env python3
"""Issue #11: isolated native RTK hook wire/runtime preflight (zero inference)."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import selectors
import shlex
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import urllib.request

TAG = 'dev-0.50.0-rc.431'
SOURCE = '5626e94a63a34d2792cdaa63a0613eda1d4abb1b'
DIGEST = '003057bcede4e1b519c957f22edae29782cf80382a0e03191ed3f7a277b75e83'
ASSET = f'https://github.com/rtk-ai/rtk/releases/download/{TAG}/rtk-aarch64-apple-darwin.tar.gz'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def execute(argv, cwd, env, payload=b'', timeout=20):
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = proc.communicate(payload, timeout=timeout)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        try: os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        proc.communicate(timeout=5)
        raise TimeoutError('owned child exceeded deadline')

def fetch_binary(root):
    with urllib.request.urlopen(ASSET, timeout=40) as r:
        data = r.read(10_000_001)
    if len(data)>10_000_000 or digest(data)!=DIGEST:
        raise ValueError('candidate checksum/size mismatch')
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = [m for m in archive.getmembers() if Path(m.name).name=='rtk']
        if len(members)!=1 or not members[0].isfile() or members[0].size>50_000_000:
            raise ValueError('unexpected executable archive')
        content=archive.extractfile(members[0]).read()
    binary=root/'bin/rtk';binary.parent.mkdir();binary.write_bytes(content);binary.chmod(0o700)
    return binary

class Rpc:
    """Small bounded first-party JSON-RPC probe, not a replacement agent loop."""
    def __init__(self, command, cwd, env, raw):
        self.err=raw.with_suffix('.stderr').open('wb')
        self.log=raw.open('w');self.buffer=b'';self.messages=[];self.counter=0
        self.proc=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,stderr=self.err,start_new_session=True)
        self.sel=selectors.DefaultSelector();self.sel.register(self.proc.stdout,selectors.EVENT_READ)
    def send(self, obj):
        self.proc.stdin.write((json.dumps(obj)+'\n').encode());self.proc.stdin.flush()
    def read(self, deadline):
        while b'\n' not in self.buffer:
            remaining=deadline-time.monotonic()
            if remaining<=0 or not self.sel.select(remaining):raise TimeoutError('RPC read deadline')
            chunk=os.read(self.proc.stdout.fileno(),65536)
            if not chunk:raise RuntimeError('RPC closed before response')
            self.buffer+=chunk
            if len(self.buffer)>20_000_000:raise ValueError('oversized RPC line')
        line,self.buffer=self.buffer.split(b'\n',1)
        obj=json.loads(line);self.log.write(json.dumps(obj)+'\n');self.log.flush()
        self.messages.append(obj);return obj
    def call(self, method, params, timeout=30):
        self.counter+=1;ident=self.counter
        self.send({'id':ident,'method':method,'params':params})
        end=time.monotonic()+timeout
        while True:
            obj=self.read(end)
            if obj.get('id')==ident:
                if 'error' in obj:raise RuntimeError('RPC '+method+': '+json.dumps(obj['error']))
                return obj['result']
            if 'id' in obj and 'method' in obj:
                # No approval or permission grants in a discovery probe.
                self.send({'id':obj['id'],'error':{'code':-32601,'message':'Probe does not accept server requests'}})
    def start(self):
        self.call('initialize',{'clientInfo':{'name':'coding_optimisations_hook_gate','version':'1'},
                               'capabilities':{'experimentalApi':True}})
        self.send({'method':'initialized','params':{}})
    def close(self):
        try:
            self.proc.stdin.close();self.proc.wait(timeout=5)
        except (subprocess.TimeoutExpired,BrokenPipeError):
            try:os.killpg(self.proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            self.proc.wait(timeout=5)
        finally:self.sel.close();self.proc.stdout.close();self.err.close();self.log.close()

def payload(command, mode='default', **extra):
    return {'hook_event_name':'PreToolUse','tool_name':'Bash','permission_mode':mode,
            'tool_input':{'command':command,'timeout_ms':1234,'description':'fixture',**extra}}

def wire_cases():
    cases=[('status',payload('git status'),'rtk git status'),
           ('diff',payload('git diff'),'rtk git diff'),
           ('list',payload('ls -la'),'rtk ls -la'),
           ('already-wrapped',payload('rtk git status'),None),
           ('unknown-mode',payload('git status','future-mode'),None),
           ('redirect',payload('git status > status.txt'),None),
           ('substitution',payload('git diff $(printf HEAD)'),None),
           ('unsupported',payload('printf hello'),None)]
    missing=payload('git status');missing.pop('permission_mode');cases.append(('missing-mode',missing,None))
    wrong=payload('git status');wrong['tool_name']='apply_patch';cases.append(('wrong-tool',wrong,None))
    for mode in ('acceptEdits','plan','dontAsk','bypassPermissions'):
        cases.append(('mode-'+mode,payload('git status',mode),'rtk git status'))
    return cases

def check_wire(binary, cwd, env, raw):
    rows=[]
    for name,obj,expected in wire_cases():
        code,out,err=execute([str(binary),'hook','codex'],cwd,env,json.dumps(obj).encode())
        (raw/(name+'.json')).write_text(json.dumps({'input':obj,'exit':code,'out':out.decode(),'err':err.decode()}))
        response=json.loads(out) if out.strip() else None
        updated=(response or {}).get('hookSpecificOutput',{})
        if expected is None:valid=not out.strip()
        else:
            want=dict(obj['tool_input']);want['command']=expected
            valid=(updated.get('updatedInput')==want and updated.get('permissionDecision')=='allow'
                   and updated.get('hookEventName')=='PreToolUse')
        rows.append({'case':name,'pass':code==0 and valid})
    code,out,err=execute([str(binary),'hook','codex'],cwd,env,b'{bad json')
    rows.append({'case':'malformed','pass':code==0 and not out.strip()})
    # Classification risk is observed only. Never execute a push or access a network remote.
    code,out,err=execute([str(binary),'hook','codex'],cwd,env,json.dumps(payload('git push --force origin HEAD')).encode())
    (raw/'mutating-command.json').write_text(json.dumps({'exit':code,'output':out.decode(),'stderr':err.decode()}))
    return rows

def runtime_probe(codex, cwd, env, root, label, hook_command):
    flags=['-c','skills.include_instructions=false', '-c',
           'hooks.PreToolUse=[{matcher="^Bash$",hooks=[{type="command",command='+json.dumps(hook_command)+',timeout=5}]}]']
    code,out,err=execute([str(codex),'--version'],cwd,env)
    version=out.decode().strip()
    result={'label':label,'version':version,'binary_sha256':digest(codex.read_bytes())}
    for name,args in [('exec-help',['exec','--help']),('server-help',['app-server','--help'])]:
        rc,text,error=execute([str(codex),*args],cwd,env)
        (root/(label+'-'+name+'.txt')).write_bytes(text+error)
    rpc=Rpc([str(codex),*flags,'app-server'],cwd,env,root/(label+'-rpc.jsonl'))
    try:
        rpc.start()
        hooks=rpc.call('hooks/list',{'cwds':[str(cwd)]})
        (root/(label+'-hooks.private.json')).write_text(json.dumps(hooks,indent=2))
        result['hooks_list_success']=True
        models=rpc.call('model/list',{})
        result['models']=[{'id':m.get('id'),'model':m.get('model'),'reasoning':m.get('supportedReasoningEfforts')} for m in models.get('data',[])]
    except Exception as e:
        (root/(label+'-error.private.txt')).write_text(repr(e))
        result.update(hooks_list_success=False,error_type=type(e).__name__)
    finally:rpc.close()
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if 'PUEUE_WORKER_ID' not in os.environ:raise SystemExit('Use existing private queue')
    if platform.system()!='Darwin' or platform.machine()!='arm64':raise SystemExit('Requires macOS arm64')
    os.umask(0o077);root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
    report={'stage':'rtk-native-hook-preflight','model_calls':0,'source':SOURCE,'tag':TAG,'archive_sha256':DIGEST}
    home=Path.home();config=home/'.codex/config.toml';before=digest(config.read_bytes()) if config.exists() else None
    try:
        from rtk_fidelity import environment,write_config
        binary=fetch_binary(root);report['binary_sha256']=digest(binary.read_bytes())
        testhome=root/'rtk-home';env=environment(testhome)
        write_config(testhome,'[tracking]\nenabled=false\nhistory_days=1\n[telemetry]\nenabled=false\nconsent_given=false\n[retriever]\nmode="sqlite"\n')
        cwd=root/'fixture';cwd.mkdir();raw=root/'wire';raw.mkdir()
        code,out,err=execute([str(binary),'--version'],cwd,env);report['rtk_version']=out.decode().strip()
        report['wire']=check_wire(binary,cwd,env,raw)
        # Every model-facing invocation keeps the actual Codex home/auth untouched.
        live={k:v for k,v in os.environ.items() if not k.startswith(('GITHUB_','ACTIONS_'))}
        for name in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL'):
            if live.get(name):raise RuntimeError('API override present; no Codex launch')
        candidates=[];standalone=shutil.which('codex')
        if standalone:candidates.append(('standalone',Path(standalone).resolve()))
        for app in ('Codex','ChatGPT'):
            p=Path('/Applications')/(app+'.app')/'Contents/Resources/codex'
            if p.is_file():candidates.append(('desktop-'+app.lower(),p.resolve()))
        report['runtimes']=[]
        hook_command=shlex.join([str(binary),'hook','codex'])
        for label,codex in candidates[:3]:
            report['runtimes'].append(runtime_probe(codex,cwd,live,root,label,hook_command))
        report['status']='preflight-completed'
    except Exception as e:
        report.update(status='preflight-failed',error_type=type(e).__name__)
        (root/'error.private.txt').write_text(repr(e))
    finally:
        report['global_config_unchanged']=before==(digest(config.read_bytes()) if config.exists() else None)
        (root/'safe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    return 0 if report['status']=='preflight-completed' and report['global_config_unchanged'] else 1

if __name__=='__main__':raise SystemExit(main())
