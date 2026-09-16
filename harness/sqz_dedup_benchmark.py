#!/usr/bin/env python3
"""Issue #11: fixed reviewed coding cohort, RTK+Serena +/- sqz exact dedup.

Reuses the lab's first-party app-server transport, fixture generators and strict
provider accounting. This is an isolated experiment, never an installer.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import time
import tomllib

import rtk_issue_benchmark as b
from rtk_hook_gate import Rpc, execute, digest
from rtk_fidelity import environment, isolated_config, toml, write_config
from issue_fixtures import materialize
from sqz_layer import filter_stdout, sqz_environment

WORKER = 'gpt-5.6-terra'
REVIEWER = 'gpt-5.6-luna'
TASK = 'Implement ISSUE.md. Run the unchanged tests, inspect the final diff, and report changes with exact test evidence.'
REVIEW = b.REVIEW_PROMPT
AGENTS = '''# Fixture worker contract
GitHub issue #11 owns this frozen benchmark; ISSUE.md is the task.
Use RTK for supported shell commands and Serena for relevant symbol navigation.
Recover original diagnostics when a tool result omits details needed by the task.
Implement only under src/. Preserve public APIs and useful comments. Tests,
ISSUE.md, AGENTS.md, run_tests.py and configuration are protected.
Run python3 run_tests.py, fix failures within this task, and inspect the final diff.
No network, installs, commits, pushes, other agents, permission escalation or
other trial directories. Report changes and exact test evidence when done.
'''
EXTREME = '''
    { ParameterSmoother z; const double m=std::numeric_limits<double>::max(); z.setTimeMs(0); z.reset(m); z.setTarget(-m); near(z.process(),-m,"zero time opposite max finite"); }
'''
KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens')
MAX_SECONDS = 4200
MAX_TOKENS = 6_000_000


def write_json(path, value):
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, indent=2)+'\n')
    temp.replace(path)


def make_fixture(cwd, kind, env):
    expected = materialize(cwd, kind)
    (cwd/'AGENTS.md').write_text(AGENTS)
    (cwd/'.gitignore').write_text((cwd/'.gitignore').read_text()+'\n.bench-state/\n')
    for name in ('AGENTS.md', '.gitignore'):
        expected[name] = digest((cwd/name).read_bytes())
    if kind == 'cpp':
        path = cwd/'tests/test.cpp'
        text = path.read_text()
        needle = '    std::cout << checks << " checks; " << failures << " failures\\n";'
        if text.count(needle) != 1:
            raise RuntimeError('extreme regression insertion drift')
        path.write_text(text.replace(needle, EXTREME+needle))
        expected['tests/test.cpp'] = digest(path.read_bytes())
    git_env = dict(env, GIT_AUTHOR_DATE='2026-09-16T00:00:00Z',
                   GIT_COMMITTER_DATE='2026-09-16T00:00:00Z')
    for cmd in (['git', 'init', '-q'], ['git', 'config', 'user.name', 'Fixture'],
                ['git', 'config', 'user.email', 'fixture@example.invalid'],
                ['git', 'add', '.'], ['git', 'commit', '-qm', 'Frozen sqz dedup fixture']):
        if execute(cmd, cwd, git_env)[0]:
            raise RuntimeError('fixture git setup failed')
    code, out, _ = execute(['git', 'rev-parse', 'HEAD'], cwd, git_env)
    if code:
        raise RuntimeError('fixture identity unavailable')
    return expected, out.decode().strip()


def flags(cwd, path):
    # Identical in BOTH arms; interception experiments are deliberately disabled.
    return ['-c', 'forced_login_method="chatgpt"', '-c', 'skills.include_instructions=false',
            '-c', 'features.hooks=false',
            '-c', 'projects={'+json.dumps(str(cwd))+'={trust_level="trusted"}}',
            '-c', 'shell_environment_policy.set.PATH='+json.dumps(path),
            '-c', 'sandbox_workspace_write.network_access=false']


def totals(rows):
    out = {}
    for arm in ('off', 'on'):
        selected = [r for r in rows if r['arm'] == arm]
        calls = [r[role] for r in selected for role in ('worker','review') if role in r]
        complete = bool(calls) and all(c.get('accounting_verified') and isinstance(c.get('usage'),dict) and
                                      all(isinstance(c['usage'].get(k),int) for k in KEYS) for c in calls)
        usage = {k:sum(c['usage'][k] for c in calls) for k in KEYS} if complete else None
        accepted = sum(r.get('accepted',False) for r in selected)
        total = usage['input_tokens']+usage['output_tokens'] if usage else None
        out[arm] = dict(attempts=len(selected), accepted=accepted, model_calls=len(calls),
                        usage=usage, total_tokens=total, accounting_complete=complete,
                        tokens_per_accepted=total/accepted if total is not None and accepted else None,
                        provider_requests=sum(c.get('provider_requests',0) for c in calls),
                        wall_seconds=sum(c.get('wall_seconds',0) for c in calls))
    return out


def fidelity(root, sqz):
    """Actual candidate execution, zero inference, no fake provider-token claims."""
    import subprocess
    gate = root/'fidelity'
    gate.mkdir()
    data = ''.join(f'src/unit_{i:03d}.cpp:{i+1}:17 symbol=parameter_{i} expected=0.000125 actual=0.125000\n' for i in range(100)).encode()
    changed = data.replace(b'actual=0.125000', b'actual=0.250000')
    trace = gate/'delivered.jsonl'
    cfg = dict(enabled=True, sqz=str(sqz), sqz_home=str(gate/'home'), rollout=str(trace))
    first, a = filter_stdout(data, cfg)
    if first != data or not a['sqz_called']:
        raise RuntimeError('sqz first-result fidelity failed')
    trace.write_text(json.dumps({'type':'response_item','payload':{'type':'function_call_output','output':data.decode()}})+'\n')
    second, bb = filter_stdout(data, cfg)
    if not bb['dedup_hit'] or len(second) >= len(data):
        raise RuntimeError('sqz actual repeat dedup did not activate')
    ref = __import__('sqz_layer').REF.search(second.decode()).group(1)
    p = subprocess.run([str(sqz),'expand',ref],env=sqz_environment(cfg),cwd=cfg['sqz_home'],capture_output=True,timeout=8)
    if p.returncode or p.stdout != data:
        raise RuntimeError('sqz recovery not byte exact')
    third, c = filter_stdout(changed, cfg)
    if third != changed or c['dedup_hit']:
        raise RuntimeError('sqz stale-content substitution')
    fresh = dict(cfg, sqz_home=str(gate/'new-role'), rollout=str(gate/'absent.jsonl'))
    fourth, d = filter_stdout(data, fresh)
    if fourth != data or d['dedup_hit']:
        raise RuntimeError('cross-role reference leak')
    result = dict(passed=True, model_calls=0, first_exact=True, repeat_dedup=True,
                  expand_exact=True, changed_exact=True, fresh_role_exact=True,
                  raw_bytes=len(data), repeat_bytes=len(second), recovery_bytes=len(p.stdout))
    write_json(gate/'safe.json', result)
    return result


def run_role(codex, common_flags, cwd, env, raw, model, prompt, limit, home, cfgpath, cfg):
    # Capture the actual rollout path before turn/start. The adapter consults
    # only prior function_call_output items of this exact role/thread.
    original = b.Rpc
    class ScopedRpc(original):
        def call(self, method, params, *args, **kwargs):
            response = super().call(method, params, *args, **kwargs)
            if method == 'thread/start':
                path = response.get('thread',{}).get('path')
                if not path:
                    raise RuntimeError('role rollout path unavailable')
                cfg['rollout'] = path
                write_json(cfgpath, cfg)
                status = super().call('mcpServerStatus/list', {'threadId':response['thread']['id']}, timeout=30)
                write_json(raw.with_suffix('.mcp.private.json'),status)
                ready = [s for s in status.get('data',[]) if s.get('name')=='serena' and s.get('tools')]
                if not ready:
                    raise RuntimeError('Serena tools unavailable in isolated baseline')
            return response
    b.Rpc = ScopedRpc
    try:
        result, answer = b.run_agent(codex, common_flags, cwd, env, raw, model, prompt, limit, home)
    finally:
        b.Rpc = original
    if cfg.get('rollout') and Path(cfg['rollout']).is_file():
        shutil.copyfile(cfg['rollout'], raw.with_suffix('.rollout.private.jsonl'))
    return result, answer


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--codex',type=Path,required=True)
    p.add_argument('--rtk',type=Path,required=True)
    p.add_argument('--sqz',type=Path,required=True)
    p.add_argument('--sqz-sha256',required=True)
    args = p.parse_args()
    if 'PUEUE_WORKER_ID' not in os.environ:
        raise SystemExit('Established shared queue required')
    os.umask(0o077)
    root = args.output.resolve()
    root.mkdir(parents=True,exist_ok=False)
    env = {k:v for k,v in os.environ.items() if not k.startswith(('GITHUB_','ACTIONS_'))}
    for key in ('OPENAI_API_KEY','CODEX_API_KEY','OPENAI_BASE_URL'):
        if env.get(key):
            raise SystemExit('API override present; not a subscription-only run')
    env.update(RTK_TELEMETRY_DISABLED='1', PYTHONDONTWRITEBYTECODE='1')
    home = Path(env.get('CODEX_HOME',str(Path.home()/'.codex')))
    cp = home/'config.toml'
    rp = Path.home()/'Library/Application Support/rtk/config.toml'
    config = tomllib.loads(cp.read_text())
    if 'serena' not in config.get('mcp_servers',{}):
        raise SystemExit('Serena configuration missing')
    rtkconfig = tomllib.loads(rp.read_text()) if rp.exists() else {}
    codex,rtk,sqz = (p.resolve(strict=True) for p in (args.codex,args.rtk,args.sqz))
    if digest(rtk.read_bytes()) != b.STABLE_SHA or digest(sqz.read_bytes()) != args.sqz_sha256:
        raise SystemExit('pinned binary mismatch')
    globals_ = [cp,rp,home/'hooks.json',home/'AGENTS.md',home/'AGENTS.override.md']
    before = b.snapshot(globals_)
    report = dict(schema=1, stage='sqz-exact-dedup-reviewed-ab', status='running', rows=[],
                  planned_attempts=8, max_invocations=16, max_seconds=MAX_SECONDS,
                  max_observed_tokens=MAX_TOKENS, worker_model=WORKER, review_model=REVIEWER,
                  reasoning='medium', common_config_sha256=digest(cp.read_bytes()),
                  rtk_sha256=b.STABLE_SHA, sqz_sha256=args.sqz_sha256,
                  prompt_sha256=digest(TASK.encode()), review_prompt_sha256=digest(REVIEW.encode()),
                  agents_sha256=digest(AGENTS.encode()), subscription_allowance=None)
    def save():
        report['aggregate']=totals(report['rows'])
        write_json(root/'safe.json',report)
    start = time.monotonic()
    save()
    try:
        code,out,err = execute([str(codex),'-c','forced_login_method="chatgpt"','login','status'],root,env)
        if code or b'chatgpt' not in (out+err).lower():
            raise RuntimeError('ChatGPT login not established')
        report['fidelity'] = fidelity(root,sqz)
        cwd = root/'fixture'
        shim = root/'shim';shim.mkdir()
        cfgpath = root/'bridge.private.json'
        bridge = Path(__file__).with_name('sqz_layer.py').resolve()
        for name in ('rtk','sqz'):
            (shim/name).write_text('#!'+sys.executable+'\nimport os,sys\nos.execv('+repr(sys.executable)+', '+repr([sys.executable,str(bridge),'--config',str(cfgpath),'--tool',name,'--'])+'+sys.argv[1:])\n')
            (shim/name).chmod(0o700)
        path = str(shim)+os.pathsep+env.get('PATH','/usr/bin:/bin')
        agent_env = dict(env,PATH=path)
        common_flags = flags(cwd,path)
        common_id = digest(json.dumps([common_flags,TASK,REVIEW,WORKER,REVIEWER],sort_keys=True).encode())
        report['common_session_setup_sha256'] = common_id
        bases = {}
        for kind in ('cpp','ui'):
            for rep in (1,2):
                for enabled in ((False,True) if rep==1 else (True,False)):
                    observed = sum(sum((r.get(role,{}).get('usage') or {}).get(k,0) for k in ('input_tokens','output_tokens')) for r in report['rows'] for role in ('worker','review'))
                    if observed >= MAX_TOKENS or time.monotonic()-start > MAX_SECONDS-450:
                        raise RuntimeError('fixed safety budget exhausted')
                    if cwd.exists():
                        if cwd.is_symlink() or cwd.parent != root or cwd.name != 'fixture':
                            raise RuntimeError('refusing non-owned fixture cleanup')
                        shutil.rmtree(cwd)
                    expected,base = make_fixture(cwd,kind,env)
                    if kind in bases and bases[kind] != base:
                        raise RuntimeError('A/B initial source or instruction drift')
                    bases[kind] = base
                    trial = root/f'trial-{len(report["rows"])+1:02d}';trial.mkdir()
                    row = dict(fixture=kind,repetition=rep,arm='on' if enabled else 'off',
                               baseline_commit=base,common_session_setup_sha256=common_id,accepted=False)
                    report['rows'].append(row)
                    row['initial_tests'] = b.check_tests(cwd,env,trial/'initial-tests.txt',expected)
                    if row['initial_tests']['passed']:
                        raise RuntimeError('broken fixture unexpectedly passes')
                    for role,model,prompt,limit in (('worker',WORKER,TASK,240),('review',REVIEWER,REVIEW,180)):
                        state = cwd/'.bench-state'
                        if state.exists():shutil.rmtree(state)
                        state.mkdir()
                        re = environment(state/'rtk')
                        write_config(Path(re['HOME']),toml(isolated_config(rtkconfig)))
                        cfg = dict(enabled=enabled,rtk=str(rtk),sqz=str(sqz),rtk_env=re,
                                   sqz_home=str(state/'sqz'),audit=str(state/'audit.jsonl'),rollout=None)
                        write_json(cfgpath,cfg)
                        if role == 'review':prior_source=b.source_snapshot(cwd)
                        save()
                        row[role],answer=run_role(codex,common_flags,cwd,agent_env,trial/(role+'.jsonl'),
                                                 model,prompt,limit,home,cfgpath,cfg)
                        audit=Path(cfg['audit'])
                        records=[json.loads(x) for x in audit.read_text().splitlines() if x.strip()] if audit.exists() else []
                        write_json(trial/(role+'.adapter.private.json'),records)
                        row[role+'_adapter']=dict(rtk_calls=sum(x['tool']=='rtk' for x in records),
                             sqz_calls=sum(x.get('sqz_called',False) for x in records),
                             dedup_hits=sum(x.get('dedup_hit',False) for x in records),
                             expansions=sum(x.get('recovered',False) for x in records),
                             stdout_bytes_before=sum(x.get('input_bytes',0) for x in records),
                             stdout_bytes_returned=sum(x.get('returned_bytes',0) for x in records),
                             fallbacks=sum(x.get('reason')=='sqz-fallback' for x in records))
                        if role == 'worker':
                            row['worker_tests']=b.check_tests(cwd,env,trial/'worker-tests.txt',expected)
                            row['protected_after_worker']=b.protected_ok(cwd,expected)
                            code,patch,_=execute(['git','diff','--no-ext-diff','--','src'],cwd,env)
                            (trial/'implementation.patch').write_bytes(patch)
                            shutil.copytree(cwd/'src',trial/'implementation-src')
                            row.update(patch_sha256=digest(patch),changed_source=bool(patch),patch_exit=code)
                        else:
                            try:ok,verdict=b.parse_review(answer)
                            except (ValueError,TypeError):ok=False;verdict={'accepted':False,'findings':['invalid or missing review response']}
                            write_json(trial/'review-verdict.json',verdict)
                            row['independent_review_accepted']=ok
                            row['reviewer_source_unchanged']=prior_source==b.source_snapshot(cwd)
                        save()
                        if not row[role].get('accounting_verified'):
                            raise RuntimeError('provider accounting incomplete; preserve failed invocation')
                    row['final_tests']=b.check_tests(cwd,env,trial/'final-tests.txt',expected)
                    row['protected_after_review']=b.protected_ok(cwd,expected)
                    row['diff_check']=execute(['git','diff','--check'],cwd,env)[0]==0
                    row['accepted']=all((row['worker']['passed'],row['review']['passed'],row['independent_review_accepted'],
                        row['worker_tests']['passed'],row['final_tests']['passed'],row['protected_after_worker'],
                        row['protected_after_review'],row['reviewer_source_unchanged'],row['changed_source'],row['diff_check']))
                    row['global_unchanged']=b.snapshot(globals_)==before
                    save();print('SQZ_TRIAL '+json.dumps(row),flush=True)
                    if not row['global_unchanged']:raise RuntimeError('protected global state changed')
        report['status']='completed'
        return 0
    except Exception as error:
        (root/'error.private.txt').write_text(repr(error)+'\n')
        report.update(status='failed',error_type=type(error).__name__)
        return 2
    finally:
        report['protected_global_unchanged']=b.snapshot(globals_)==before
        report['wall_seconds']=time.monotonic()-start
        save();print('SQZ_RESULT '+json.dumps(report),flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
