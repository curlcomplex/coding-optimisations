#!/usr/bin/env python3
"""Issue #11 corrected A/B: identical model-visible setup, only RTK hook state differs."""
from __future__ import annotations
import argparse,json,os,shutil,sys,time
from pathlib import Path
import rtk_issue_benchmark as b
from rtk_hook_gate import Rpc,execute,digest,fetch_binary
from rtk_hook_live import hook_list,trusted_flags
from rtk_fidelity import environment,isolated_config,toml,write_config
from issue_fixtures import materialize

WORKER='gpt-5.6-terra';REVIEWER='gpt-5.6-luna';EFFORT='medium'
TASK='Implement ISSUE.md. Run the unchanged tests, inspect the final diff, and report changes with exact test evidence.'
REVIEW='''Independently review the current patch against ISSUE.md. Inspect the actual source and git diff; run python3 run_tests.py. Do not change any source, tests, instructions or configuration. Assess all specified edge cases, API compatibility and maintainability, not only whether tests pass. Do not read other trial directories. Return a JSON object only: {"accepted": true or false, "findings": [specific blocking defects if any]}. Do not accept if any requirement is unfulfilled.'''
AGENTS='''# Fixture worker contract\nGitHub issue #11 owns this frozen benchmark; ISSUE.md is the task.\nUse available repository navigation and shell tools as appropriate.\nImplement only under src/. Keep public APIs and useful comments. Tests, ISSUE.md, AGENTS.md, run_tests.py and configuration are protected.\nRun python3 run_tests.py, fix failures within this task, and inspect the final diff.\nNo network, installs, commits, pushes, other agents, permission escalation or other trial directories.\n'''
EXTREME='''\n    { ParameterSmoother z; const double m=std::numeric_limits<double>::max(); z.setTimeMs(0); z.reset(m); z.setTarget(-m); near(z.process(),-m,"zero time opposite max finite"); }\n'''

def snap(paths):return {str(p):digest(p.read_bytes()) if p.is_file() and not p.is_symlink() else None for p in paths}
def protected(cwd,expected):return all((cwd/n).is_file() and not (cwd/n).is_symlink() and digest((cwd/n).read_bytes())==v for n,v in expected.items() if not n.startswith('src/'))
def source(cwd):return {str(p.relative_to(cwd)):digest(p.read_bytes()) for p in sorted((cwd/'src').rglob('*')) if p.is_file()}
def check(cwd,env,path,expected):
    if not protected(cwd,expected):return {'passed':False,'exit':97}
    t=time.monotonic();code,out,err=execute([sys.executable,'run_tests.py'],cwd,env,30);path.write_bytes(out+err);return {'passed':code==0,'exit':code,'wall_seconds':round(time.monotonic()-t,3),'sha256':digest(out+err)}
def setup(parent,kind,stable,hookbin,rtkcfg,env):
    cwd=parent/'fixture';expected=materialize(cwd,kind);(cwd/'AGENTS.md').write_text(AGENTS);expected['AGENTS.md']=digest((cwd/'AGENTS.md').read_bytes())
    if kind=='cpp':
        p=cwd/'tests/test.cpp';s=p.read_text();needle='    std::cout << checks << " checks; " << failures << " failures\\n";';p.write_text(s.replace(needle,EXTREME+needle));expected['tests/test.cpp']=digest(p.read_bytes())
    genv=dict(env,GIT_AUTHOR_DATE='2026-09-16T00:00:00Z',GIT_COMMITTER_DATE='2026-09-16T00:00:00Z')
    for c in (['git','init','-q'],['git','config','user.name','Fixture'],['git','config','user.email','fixture@example.invalid'],['git','add','.'],['git','commit','-qm','Frozen corrected RTK fixture']):
        if execute(c,cwd,genv)[0]:raise RuntimeError('fixture git setup')
    base=execute(['git','rev-parse','HEAD'],cwd,genv)[1].decode().strip()
    # External shim and hook state are not inside the task workspace.
    rtkhome=parent/'rtk-home';rtkenv=environment(rtkhome);write_config(rtkhome,toml(isolated_config(rtkcfg)))
    shim=parent/'shim';shim.mkdir();r=shim/'rtk';r.write_text('#!'+sys.executable+'\nimport os,sys\nos.execve('+repr(str(stable))+',['+repr(str(stable))+',*sys.argv[1:]],'+repr(rtkenv)+')\n');r.chmod(0o700)
    hookhome=parent/'hook-home';henv=environment(hookhome);write_config(hookhome,toml(isolated_config(rtkcfg)))
    cfg=parent/'delegate.json';audit=parent/'audit.jsonl';cfg.write_text(json.dumps({'hook_binary':str(hookbin),'cwd':str(cwd),'hook_env':henv,'audit':str(audit)}));audit.write_text('')
    command=__import__('shlex').join([sys.executable,str(Path(b.__file__).resolve()),'--delegate',str(cfg)])
    return cwd,expected,base,shim,command,audit

def flags(cwd,path,command,existing):return ['-c','forced_login_method="chatgpt"','-c','skills.include_instructions=false','-c','features.hooks=true','-c','projects={'+json.dumps(str(cwd))+'={trust_level="trusted"}}','-c','shell_environment_policy.set.PATH='+json.dumps(path),'-c','sandbox_workspace_write.network_access=false','-c','hooks.PreToolUse='+b.inline(list(existing or [])+[{'matcher':'^Bash$','hooks':[{'type':'command','command':command,'timeout':8}]}])]
def aggregate(rows):
    z={}
    for arm in ('off','on'):
        rs=[r for r in rows if r['arm']==arm];calls=[r[k] for r in rs for k in ('worker','review')];u={k:sum(c['usage'][k] for c in calls) for k in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')};acc=sum(r['accepted'] for r in rs);total=u['input_tokens']+u['output_tokens'];z[arm]={'attempts':len(rs),'accepted':acc,'usage':u,'total_tokens':total,'tokens_per_accepted':total/acc if acc else None,'output_per_accepted':u['output_tokens']/acc if acc else None,'provider_requests':sum(c['provider_requests'] for c in calls),'wall_seconds':sum(c['wall_seconds'] for c in calls)}
    return z
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--codex',type=Path,required=True);p.add_argument('--stable-rtk',type=Path,required=True);a=p.parse_args()
    if 'PUEUE_WORKER_ID' not in os.environ:raise SystemExit('queue required')
    os.umask(0o077);root=a.output.resolve();root.mkdir(parents=True,exist_ok=False);env={k:v for k,v in os.environ.items() if not k.startswith(('GITHUB_','ACTIONS_'))};[env.pop(k,None) for k in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL')];env['RTK_TELEMETRY_DISABLED']='1';env['PYTHONDONTWRITEBYTECODE']='1'
    import tomllib;home=Path(env.get('CODEX_HOME',str(Path.home()/'.codex')));config=home/'config.toml';live=tomllib.loads(config.read_text());rtkp=Path.home()/'Library/Application Support/rtk/config.toml';rtkcfg=tomllib.loads(rtkp.read_text()) if rtkp.exists() else {};stable=a.stable_rtk.resolve(strict=True);codex=a.codex.resolve(strict=True)
    if 'serena' not in live.get('mcp_servers',{}):raise RuntimeError('Serena missing')
    if digest(stable.read_bytes())!=b.STABLE_SHA:raise RuntimeError('RTK drift')
    protected_global=[config,home/'hooks.json',home/'AGENTS.md',home/'AGENTS.override.md',rtkp];before=snap(protected_global);hookbin=fetch_binary(root)
    report={'schema':1,'stage':'corrected-blinded-rtk-ab','rows':[],'worker_model':WORKER,'review_model':REVIEWER,'reasoning':EFFORT,'status':'running','prompt_sha256':digest(TASK.encode()),'review_prompt_sha256':digest(REVIEW.encode()),'agents_sha256':digest(AGENTS.encode())}
    def save():report['aggregate']=aggregate(report['rows']) if report['rows'] and all('review' in r and r['review'].get('usage') for r in report['rows']) else {}; (root/'safe.json').write_text(json.dumps(report,indent=2)+'\n')
    save();bases={}
    for kind in ('cpp','ui'):
      for rep in (1,2):
       for enabled in ((False,True) if rep==1 else (True,False)):
        parent=root/f'trial-{len(report["rows"])+1:02d}';parent.mkdir();cwd,expected,base,shim,command,audit=setup(parent,kind,stable,hookbin,rtkcfg,env)
        if kind in bases and bases[kind]!=base:raise RuntimeError('starting commit differs');bases[kind]=base
        bases.setdefault(kind,base);path=str(shim)+os.pathsep+env.get('PATH','/usr/bin:/bin');tenv=dict(env,PATH=path);f=flags(cwd,path,command,live.get('hooks',{}).get('PreToolUse',[]));hs=hook_list(codex,f,cwd,tenv,parent/'discover.jsonl');f+=trusted_flags(hs,command,enabled)
        # Critical invariant: arm state is external; task-visible tree/prompt/config hashes are identical.
        visible={'base':base,'task':digest(TASK.encode()),'review':digest(REVIEW.encode()),'agents':digest((cwd/'AGENTS.md').read_bytes()),'issue':digest((cwd/'ISSUE.md').read_bytes()),'config':digest(config.read_bytes())};key=kind+'-'+str(rep);report.setdefault('visible_hashes',{}).setdefault(key,visible)
        if report['visible_hashes'][key]!=visible:raise RuntimeError('model-visible arm drift')
        row={'fixture':kind,'repetition':rep,'arm':'on' if enabled else 'off','baseline_commit':base,'accepted':False,'visible_hash':digest(json.dumps(visible,sort_keys=True).encode())};report['rows'].append(row);row['initial_tests']=check(cwd,tenv,parent/'initial.txt',expected)
        row['worker'],_=b.run_agent(codex,f,cwd,tenv,parent/'worker.jsonl',WORKER,TASK,180,home);row['worker_tests']=check(cwd,tenv,parent/'worker-tests.txt',expected);row['protected_after_worker']=protected(cwd,expected);src=source(cwd);_,patch,_=execute(['git','diff','--no-ext-diff','--','src'],cwd,tenv);row['patch_sha256']=digest(patch);row['changed_source']=bool(patch)
        row['review'],ans=b.run_agent(codex,f,cwd,tenv,parent/'review.jsonl',REVIEWER,REVIEW,120,home)
        try:ok,_=b.parse_review(ans)
        except Exception:ok=False
        row['independent_review_accepted']=ok;row['reviewer_source_unchanged']=src==source(cwd);row['final_tests']=check(cwd,tenv,parent/'final.txt',expected);row['protected_after_review']=protected(cwd,expected);row['hook_calls']=len(audit.read_text().splitlines());row['automatic_rewrites']=sum(bool(json.loads(x).get('response','').strip()) for x in audit.read_text().splitlines() if x.strip());row['accepted']=all((row['worker']['passed'],row['review']['passed'],ok,row['worker_tests']['passed'],row['final_tests']['passed'],row['protected_after_worker'],row['protected_after_review'],row['reviewer_source_unchanged'],row['changed_source']));row['global_unchanged']=snap(protected_global)==before;save();print('TRIAL_RESULT '+json.dumps(row),flush=True)
        if not row['global_unchanged'] or not row['worker'].get('accounting_verified') or not row['review'].get('accounting_verified'):raise RuntimeError('integrity/accounting failure')
    report['status']='completed';report['protected_global_unchanged']=snap(protected_global)==before;save();print('BENCHMARK_RESULT '+json.dumps(report),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
