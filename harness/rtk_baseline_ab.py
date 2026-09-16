#!/usr/bin/env python3
"""Issue #11: plain Codex+Serena versus normal RTK+Serena, reviewed coding A/B."""
from __future__ import annotations
import argparse,json,os,shutil,sys,time
from pathlib import Path
import rtk_issue_benchmark as b
from rtk_hook_gate import Rpc,execute,digest

ARMS=('plain','rtk')
WORKER='gpt-5.6-terra'; REVIEWER='gpt-5.6-luna'; EFFORT='medium'
TASK='Implement ISSUE.md. Use Serena for relevant symbol navigation and the configured shell workflow for this arm. Run the unchanged tests, inspect the final diff, and report changes with exact test evidence.'
PLAIN='''# Fixture worker contract\nGitHub issue #11 owns this frozen benchmark. ISSUE.md is the task.\nUse Serena for relevant symbol navigation. Use ordinary shell commands directly; RTK is deliberately disabled in this control arm.\nImplement only under src/. Keep public APIs and useful comments. Tests, ISSUE.md, AGENTS.md, run_tests.py and configuration are protected.\nRun python3 run_tests.py, fix failures within this task, and inspect the final diff.\nNo network, installs, commits, pushes, other agents, permission escalation or other trial directories.\n'''
RTK='''# Fixture worker contract\nGitHub issue #11 owns this frozen benchmark. ISSUE.md is the task.\nUse Serena for relevant symbol navigation. Use the existing RTK wrapper for supported shell commands and recover original diagnostics when compressed output omits needed facts.\nImplement only under src/. Keep public APIs and useful comments. Tests, ISSUE.md, AGENTS.md, run_tests.py and configuration are protected.\nRun python3 run_tests.py, fix failures within this task, and inspect the final diff.\nNo network, installs, commits, pushes, other agents, permission escalation or other trial directories.\n'''
EXTREME='''\n    { ParameterSmoother z; const double m=std::numeric_limits<double>::max(); z.setTimeMs(0); z.reset(m); z.setTarget(-m); near(z.process(),-m,"zero time opposite max finite"); }\n'''

def amend_fixture(cwd,expected,arm,env):
    agents=cwd/'AGENTS.md';agents.write_text(RTK if arm=='rtk' else PLAIN);expected['AGENTS.md']=digest(agents.read_bytes())
    if (cwd/'tests/test.cpp').exists():
        p=cwd/'tests/test.cpp';s=p.read_text();needle='    std::cout << checks << " checks; " << failures << " failures\\n";'
        if needle not in s:raise RuntimeError('C++ regression insertion point drift')
        p.write_text(s.replace(needle,EXTREME+needle));expected['tests/test.cpp']=digest(p.read_bytes())
    genv=dict(env,GIT_AUTHOR_DATE='2026-09-16T00:00:00Z',GIT_COMMITTER_DATE='2026-09-16T00:00:00Z')
    for c in (['git','add','AGENTS.md','tests'],['git','commit','--amend','-qm','Frozen plain-vs-RTK fixture']):
        code,_,_=execute(c,cwd,genv)
        if code:raise RuntimeError('fixture amend failed')
    code,out,_=execute(['git','rev-parse','HEAD'],cwd,genv)
    return out.decode().strip()

def neutral_flags(cwd,path,existing):
    # Preserve existing hooks identically. No automatic RTK hook in either arm.
    return ['-c','forced_login_method="chatgpt"','-c','skills.include_instructions=false','-c','features.hooks=true',
      '-c','projects={'+json.dumps(str(cwd))+'={trust_level="trusted"}}','-c','shell_environment_policy.set.PATH='+json.dumps(path),
      '-c','sandbox_workspace_write.network_access=false','-c','hooks.PreToolUse='+b.inline(list(existing or []))]

def command_stats(raw):
    rows=[json.loads(x) for x in raw.read_text().splitlines() if x.strip()] if raw.exists() else []
    cmds=[]
    for e in rows:
        if e.get('method')=='item/completed':
            item=e.get('params',{}).get('item',{})
            if item.get('type')=='commandExecution':cmds.append(item.get('command',''))
    return {'commands':len(cmds),'rtk_commands':sum('rtk ' in c or c.strip().startswith('rtk') for c in cmds)}

def aggregate(rows):
    out={}
    for arm in ARMS:
        rs=[r for r in rows if r['arm']==arm];calls=[r[k] for r in rs for k in ('worker','review')]
        known=all(c.get('accounting_verified') and c.get('usage') for c in calls)
        u={k:sum(c['usage'][k] for c in calls) for k in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens')} if known else None
        accepted=sum(r.get('accepted',False) for r in rs);total=u['input_tokens']+u['output_tokens'] if u else None
        out[arm]={'attempts':len(rs),'accepted':accepted,'failures':len(rs)-accepted,'model_invocations':len(calls),'usage':u,'total_tokens':total,
          'tokens_per_accepted':total/accepted if total is not None and accepted else None,'output_per_accepted':u['output_tokens']/accepted if u and accepted else None,
          'provider_requests':sum(c.get('provider_requests',0) for c in calls),'wall_seconds':sum(c.get('wall_seconds',0) for c in calls),'accounting_complete':known}
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--codex',type=Path,required=True);p.add_argument('--stable-rtk',type=Path,required=True);a=p.parse_args()
    if 'PUEUE_WORKER_ID' not in os.environ:raise SystemExit('existing queue required')
    os.umask(0o077);root=a.output.resolve();root.mkdir(parents=True,exist_ok=False)
    env={k:v for k,v in os.environ.items() if not k.startswith(('GITHUB_','ACTIONS_'))};[env.pop(k,None) for k in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL')]
    env['RTK_TELEMETRY_DISABLED']='1';env['PYTHONDONTWRITEBYTECODE']='1';home=Path(env.get('CODEX_HOME',str(Path.home()/'.codex')))
    import tomllib
    config=home/'config.toml';rtkcfg=Path.home()/'Library/Application Support/rtk/config.toml';live=tomllib.loads(config.read_text());live_rtk=tomllib.loads(rtkcfg.read_text()) if rtkcfg.exists() else {}
    if 'serena' not in live.get('mcp_servers',{}):raise RuntimeError('Serena baseline missing')
    stable=a.stable_rtk.resolve(strict=True);codex=a.codex.resolve(strict=True)
    if digest(stable.read_bytes())!=b.STABLE_SHA:raise RuntimeError('RTK binary drift')
    protected=[config,home/'hooks.json',home/'AGENTS.md',home/'AGENTS.override.md',rtkcfg];before=b.snapshot(protected)
    report={'schema':1,'stage':'plain-vs-normal-rtk-reviewed-ab','rows':[],'status':'running','worker_model':WORKER,'review_model':REVIEWER,'reasoning':EFFORT,
      'planned_attempts':8,'planned_model_invocations':16,'subscription_allowance_savings':None,'production_adoption':False,'serena_configured':True,
      'codex_sha256':digest(codex.read_bytes()),'rtk_sha256':digest(stable.read_bytes()),'common_config_sha256':digest(config.read_bytes())}
    def save():report['aggregate']=aggregate(report['rows']);(root/'safe.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    code,out,err=execute([str(codex),'-c','forced_login_method="chatgpt"','login','status'],root,env)
    if code or b'chatgpt' not in (out+err).lower():raise RuntimeError('subscription login unavailable')
    # Verify model/effort once.
    rpc=Rpc([str(codex),'app-server'],root,env,root/'models.private.jsonl')
    try:
        rpc.start();models=rpc.call('model/list',{});avail={m['id']:m for m in models.get('data',[])}
        for m in (WORKER,REVIEWER):
            if m not in avail or EFFORT not in [x['reasoningEffort'] for x in avail[m]['supportedReasoningEfforts']]:raise RuntimeError('model/effort unavailable')
    finally:rpc.close()
    bases={}
    try:
      for kind in ('cpp','ui'):
       for rep in (1,2):
        order=ARMS if rep==1 else tuple(reversed(ARMS))
        for arm in order:
            parent=root/f'trial-{len(report["rows"])+1:02d}';parent.mkdir()
            cwd,shim,expected,_,_,_=b.setup_trial(parent,kind,stable,stable,live_rtk)
            # Remove treatment's private RTK state from task-visible changes and freeze stronger quality test.
            base=amend_fixture(cwd,expected,arm,env)
            if kind in bases and bases[kind][arm]!=base:raise RuntimeError('same-arm starting commit drift')
            bases.setdefault(kind,{})[arm]=base
            # Plain arm removes the installed RTK directory from PATH. RTK arm puts the audited shim first.
            rawpath=env.get('PATH','/usr/bin:/bin').split(os.pathsep);stable_parent=str(stable.parent)
            plainpath=os.pathsep.join(x for x in rawpath if x!=stable_parent)
            path=(str(shim)+os.pathsep+plainpath) if arm=='rtk' else plainpath
            trial_env=dict(env,PATH=path)
            flags=neutral_flags(cwd,path,live.get('hooks',{}).get('PreToolUse',[]))
            row={'fixture':kind,'repetition':rep,'arm':arm,'baseline_commit':base,'accepted':False};report['rows'].append(row);save()
            row['initial_tests']=b.check_tests(cwd,trial_env,parent/'initial-tests.txt',expected)
            if row['initial_tests']['passed']:raise RuntimeError('fixture unexpectedly green')
            row['worker'],_=b.run_agent(codex,flags,cwd,trial_env,parent/'worker.jsonl',WORKER,TASK,180,home)
            row['worker_commands']=command_stats(parent/'worker.jsonl')
            row['worker_tests']=b.check_tests(cwd,trial_env,parent/'worker-tests.txt',expected);row['protected_after_worker']=b.protected_ok(cwd,expected)
            src=b.source_snapshot(cwd);shutil.copytree(cwd/'src',parent/'implementation-src')
            _,patch,_=execute(['git','diff','--no-ext-diff','--','src'],cwd,trial_env);(parent/'implementation.patch').write_bytes(patch);row['patch_sha256']=digest(patch);row['changed_source']=bool(patch)
            row['review'],answer=b.run_agent(codex,flags,cwd,trial_env,parent/'review.jsonl',REVIEWER,b.REVIEW_PROMPT,120,home);row['review_commands']=command_stats(parent/'review.jsonl')
            try:accepted,verdict=b.parse_review(answer);(parent/'review-verdict.json').write_text(json.dumps(verdict,indent=2))
            except Exception:accepted=False
            row['independent_review_accepted']=accepted;row['reviewer_source_unchanged']=src==b.source_snapshot(cwd)
            row['final_tests']=b.check_tests(cwd,trial_env,parent/'final-tests.txt',expected);row['protected_after_review']=b.protected_ok(cwd,expected)
            rc,_,_=execute(['git','diff','--check'],cwd,trial_env);row['diff_check']=rc==0
            ex=cwd/'.rtk-state/executions.jsonl';row['rtk_wrapper_executions']=len(ex.read_text().splitlines()) if ex.exists() else 0
            # Control must not accidentally execute RTK; treatment must actually exercise it.
            if arm=='plain' and row['rtk_wrapper_executions']!=0:raise RuntimeError('plain arm executed RTK')
            if arm=='rtk' and row['rtk_wrapper_executions']==0:raise RuntimeError('RTK arm did not execute RTK')
            row['accepted']=all((row['worker'].get('passed'),row['review'].get('passed'),accepted,row['worker_tests']['passed'],row['final_tests']['passed'],row['protected_after_worker'],row['protected_after_review'],row['reviewer_source_unchanged'],row['changed_source'],row['diff_check']))
            row['global_unchanged']=b.snapshot(protected)==before
            save();print('TRIAL_RESULT '+json.dumps(row),flush=True)
            if not row['global_unchanged']:raise RuntimeError('global config drift')
            if not row['worker'].get('accounting_verified') or not row['review'].get('accounting_verified'):raise RuntimeError('accounting incomplete')
      report['status']='completed'
      return 0
    except Exception as e:
      (root/'error.private.txt').write_text(repr(e));report['status']='failed';report['error_type']=type(e).__name__;return 2
    finally:
      report['protected_global_unchanged']=b.snapshot(protected)==before;save();print('BENCHMARK_RESULT '+json.dumps(report),flush=True)
if __name__=='__main__':raise SystemExit(main())
