#!/usr/bin/env python3
"""Issue #11 corrected A/B: identical model-visible setup, only RTK hook state differs."""
from __future__ import annotations
import argparse,json,os,sys,time
from pathlib import Path
import rtk_issue_benchmark as b
from rtk_hook_gate import execute,digest,fetch_binary
from rtk_hook_live import hook_list,trusted_flags
from rtk_fidelity import environment,isolated_config,toml,write_config
from issue_fixtures import materialize
WORKER='gpt-5.6-terra';REVIEWER='gpt-5.6-luna';EFFORT='medium'
TASK='Implement ISSUE.md. Run the unchanged tests, inspect the final diff, and report changes with exact test evidence.'
REVIEW='''Independently review the current patch against ISSUE.md. Inspect the actual source and git diff; run python3 run_tests.py. Do not change any source, tests, instructions or configuration. Assess all specified edge cases, API compatibility and maintainability, not only whether tests pass. Do not read other trial directories. Return a JSON object only: {"accepted": true or false, "findings": [specific blocking defects if any]}. Do not accept if any requirement is unfulfilled.'''
AGENTS='''# Fixture worker contract\nGitHub issue #11 owns this frozen benchmark; ISSUE.md is the task.\nUse available repository navigation and shell tools as appropriate.\nImplement only under src/. Keep public APIs and useful comments. Tests, ISSUE.md, AGENTS.md, run_tests.py and configuration are protected.\nRun python3 run_tests.py, fix failures within this task, and inspect the final diff.\nNo network, installs, commits, pushes, other agents, permission escalation or other trial directories.\n'''
EXTREME='''\n    { ParameterSmoother z; const double m=std::numeric_limits<double>::max(); z.setTimeMs(0); z.reset(m); z.setTarget(-m); near(z.process(),-m,"zero time opposite max finite"); }\n'''
def snap(ps):return {str(p):digest(p.read_bytes()) if p.is_file() and not p.is_symlink() else None for p in ps}
def prot(c,e):return all((c/n).is_file() and digest((c/n).read_bytes())==v for n,v in e.items() if not n.startswith('src/'))
def src(c):return {str(p.relative_to(c)):digest(p.read_bytes()) for p in sorted((c/'src').rglob('*')) if p.is_file()}
def test(c,e,path,expected):
 t=time.monotonic();code,out,err=execute([sys.executable,'run_tests.py'],c,e,30);path.write_bytes(out+err);return {'passed':code==0 and prot(c,expected),'exit':code,'wall_seconds':round(time.monotonic()-t,3),'sha256':digest(out+err)}
def setup(parent,kind,stable,hookbin,rtkcfg,env):
 c=parent/'fixture';expected=materialize(c,kind);(c/'AGENTS.md').write_text(AGENTS);expected['AGENTS.md']=digest((c/'AGENTS.md').read_bytes())
 if kind=='cpp':
  p=c/'tests/test.cpp';s=p.read_text();needle='    std::cout << checks << " checks; " << failures << " failures\\n";';assert s.count(needle)==1;p.write_text(s.replace(needle,EXTREME+needle));expected['tests/test.cpp']=digest(p.read_bytes())
 ge=dict(env,GIT_AUTHOR_DATE='2026-09-16T00:00:00Z',GIT_COMMITTER_DATE='2026-09-16T00:00:00Z')
 for x in (['git','init','-q'],['git','config','user.name','Fixture'],['git','config','user.email','fixture@example.invalid'],['git','add','.'],['git','commit','-qm','Frozen corrected RTK fixture']):
  if execute(x,c,ge)[0]:raise RuntimeError('git setup')
 base=execute(['git','rev-parse','HEAD'],c,ge)[1].decode().strip();rh=parent/'rtk-home';re=environment(rh);write_config(rh,toml(isolated_config(rtkcfg)));shim=parent/'shim';shim.mkdir();r=shim/'rtk';r.write_text('#!'+sys.executable+'\nimport os,sys\nos.execve('+repr(str(stable))+',['+repr(str(stable))+',*sys.argv[1:]],'+repr(re)+')\n');r.chmod(0o700)
 hh=parent/'hook-home';he=environment(hh);write_config(hh,toml(isolated_config(rtkcfg)));cfg=parent/'delegate.json';audit=parent/'audit.jsonl';cfg.write_text(json.dumps({'hook_binary':str(hookbin),'cwd':str(c),'hook_env':he,'audit':str(audit)}));audit.write_text('');import shlex;command=shlex.join([sys.executable,str(Path(b.__file__).resolve()),'--delegate',str(cfg)]);return c,expected,base,shim,command,audit
def flags(c,p,cmd,old):return ['-c','forced_login_method="chatgpt"','-c','skills.include_instructions=false','-c','features.hooks=true','-c','projects={'+json.dumps(str(c))+'={trust_level="trusted"}}','-c','shell_environment_policy.set.PATH='+json.dumps(p),'-c','sandbox_workspace_write.network_access=false','-c','hooks.PreToolUse='+b.inline(list(old or [])+[{'matcher':'^Bash$','hooks':[{'type':'command','command':cmd,'timeout':8}]}])]
def agg(rows):
 z={}
 for arm in ('off','on'):
  rs=[r for r in rows if r['arm']==arm];calls=[r[k] for r in rs for k in ('worker','review')];u={k:sum(x['usage'][k] for x in calls) for k in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')};a=sum(r['accepted'] for r in rs);t=u['input_tokens']+u['output_tokens'];z[arm]={'attempts':len(rs),'accepted':a,'usage':u,'total_tokens':t,'tokens_per_accepted':t/a if a else None,'provider_requests':sum(x['provider_requests'] for x in calls),'wall_seconds':sum(x['wall_seconds'] for x in calls)}
 return z
def main():
 q=argparse.ArgumentParser();q.add_argument('--output',type=Path,required=True);q.add_argument('--codex',type=Path,required=True);q.add_argument('--stable-rtk',type=Path,required=True);a=q.parse_args();assert 'PUEUE_WORKER_ID' in os.environ;os.umask(0o077);root=a.output.resolve();root.mkdir(parents=True,exist_ok=False);env={k:v for k,v in os.environ.items() if not k.startswith(('GITHUB_','ACTIONS_'))};[env.pop(k,None) for k in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL')];env['RTK_TELEMETRY_DISABLED']='1';env['PYTHONDONTWRITEBYTECODE']='1'
 import tomllib;home=Path(env.get('CODEX_HOME',str(Path.home()/'.codex')));cp=home/'config.toml';live=tomllib.loads(cp.read_text());rp=Path.home()/'Library/Application Support/rtk/config.toml';rc=tomllib.loads(rp.read_text()) if rp.exists() else {};stable=a.stable_rtk.resolve(strict=True);codex=a.codex.resolve(strict=True);assert 'serena' in live.get('mcp_servers',{});assert digest(stable.read_bytes())==b.STABLE_SHA;pg=[cp,home/'hooks.json',home/'AGENTS.md',home/'AGENTS.override.md',rp];before=snap(pg);hb=fetch_binary(root);report={'stage':'corrected-blinded-rtk-ab','rows':[],'status':'running','prompt_sha256':digest(TASK.encode()),'review_prompt_sha256':digest(REVIEW.encode()),'agents_sha256':digest(AGENTS.encode())}
 def save():report['aggregate']=agg(report['rows']) if report['rows'] and all('review' in r and r['review'].get('usage') for r in report['rows']) else {};(root/'safe.json').write_text(json.dumps(report,indent=2)+'\n')
 save();bases={};vis={}
 for kind in ('cpp','ui'):
  for rep in (1,2):
   for enabled in ((False,True) if rep==1 else (True,False)):
    parent=root/f'trial-{len(report["rows"])+1:02d}';parent.mkdir();c,expected,base,shim,cmd,audit=setup(parent,kind,stable,hb,rc,env);bases.setdefault(kind,base);assert bases[kind]==base;p=str(shim)+os.pathsep+env.get('PATH','/usr/bin:/bin');te=dict(env,PATH=p);f=flags(c,p,cmd,live.get('hooks',{}).get('PreToolUse',[]));hs=hook_list(codex,f,c,te,parent/'discover.jsonl');f+=trusted_flags(hs,cmd,enabled);v={'base':base,'task':digest(TASK.encode()),'review':digest(REVIEW.encode()),'agents':digest((c/'AGENTS.md').read_bytes()),'issue':digest((c/'ISSUE.md').read_bytes()),'config':digest(cp.read_bytes())};key=(kind,rep);vis.setdefault(key,v);assert vis[key]==v
    row={'fixture':kind,'repetition':rep,'arm':'on' if enabled else 'off','baseline_commit':base,'visible_hash':digest(json.dumps(v,sort_keys=True).encode()),'accepted':False};report['rows'].append(row);row['initial_tests']=test(c,te,parent/'initial.txt',expected);assert not row['initial_tests']['passed'];row['worker'],_=b.run_agent(codex,f,c,te,parent/'worker.jsonl',WORKER,TASK,180,home);row['worker_tests']=test(c,te,parent/'worker-tests.txt',expected);row['protected_after_worker']=prot(c,expected);s=src(c);_,patch,_=execute(['git','diff','--no-ext-diff','--','src'],c,te);row['changed_source']=bool(patch);row['review'],ans=b.run_agent(codex,f,c,te,parent/'review.jsonl',REVIEWER,REVIEW,120,home)
    try:ok,_=b.parse_review(ans)
    except Exception:ok=False
    row['independent_review_accepted']=ok;row['reviewer_source_unchanged']=s==src(c);row['final_tests']=test(c,te,parent/'final.txt',expected);row['protected_after_review']=prot(c,expected);ar=[json.loads(x) for x in audit.read_text().splitlines() if x.strip()];row['hook_calls']=len(ar);row['automatic_rewrites']=sum(bool(x.get('response','').strip()) for x in ar);row['accepted']=all((row['worker']['passed'],row['review']['passed'],ok,row['worker_tests']['passed'],row['final_tests']['passed'],row['protected_after_worker'],row['protected_after_review'],row['reviewer_source_unchanged'],row['changed_source']));row['global_unchanged']=snap(pg)==before;save();print('TRIAL_RESULT '+json.dumps(row),flush=True);assert row['global_unchanged'] and row['worker']['accounting_verified'] and row['review']['accounting_verified']
 report['status']='completed';report['protected_global_unchanged']=snap(pg)==before;save();print('BENCHMARK_RESULT '+json.dumps(report),flush=True)
if __name__=='__main__':raise SystemExit(main())
