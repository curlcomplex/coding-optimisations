#!/usr/bin/env python3
"""Bounded, reversible skill-catalogue qualification. Raw traces stay private."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import statistics
import subprocess
import sys
import time
import uuid

MODEL = 'gpt-5.6-luna'
SMOKE = ('Use the shell exactly once to read input.txt. Add the two integers in '
         'that file. Return only the decimal sum and nothing else.')
TOKEN_KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens',
              'reasoning_output_tokens', 'total_tokens')


def counters(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError('missing_usage')
    result = {k: value[k] for k in TOKEN_KEYS if k in value}
    if any(type(v) is not int or v < 0 for v in result.values()):
        raise ValueError('invalid_counter')
    if not all(k in result for k in ('input_tokens', 'output_tokens')):
        raise ValueError('missing_required_counter')
    if result.get('cached_input_tokens', 0) > result['input_tokens']:
        raise ValueError('cached_exceeds_input')
    return result


def rollout_usage(data: bytes, thread_id: str) -> dict:
    """Deduplicate quota-only repeats; never count cumulative usage twice."""
    rows = [json.loads(line) for line in data.decode('utf-8').splitlines() if line.strip()]
    identities = [r.get('payload', {}).get('id') for r in rows if r.get('type') == 'session_meta']
    if identities != [thread_id]:
        raise ValueError('rollout_identity_mismatch')
    requests, previous, models = [], None, set()
    for row in rows:
        p = row.get('payload', {})
        if row.get('type') == 'turn_context' and p.get('model'):
            models.add(p['model'])
        if row.get('type') != 'event_msg' or p.get('type') != 'token_count':
            continue
        info = p.get('info')
        if info is None:
            continue
        total = counters(info.get('total_token_usage'))
        if total == previous:
            continue
        last = counters(info.get('last_token_usage'))
        for key in ('input_tokens', 'output_tokens'):
            if total[key] - (previous or {}).get(key, 0) != last[key]:
                raise ValueError('non_reconciling_request_usage')
        requests.append(last)
        previous = total
    if not requests:
        raise ValueError('no_request_usage')
    return {'requests': requests, 'total': previous, 'models': sorted(models)}


def inspect_rollout(home: Path, thread_id: str) -> dict:
    if not re.fullmatch(r'[0-9a-f-]{36}', thread_id):
        return {'verified': False, 'error': 'invalid_thread_id'}
    # Read only this invocation's transcript, never unrelated conversation bodies.
    today = dt.datetime.now(dt.timezone.utc).date()
    candidates = []
    for day in (today, today-dt.timedelta(days=1), today+dt.timedelta(days=1)):
        directory = home / 'sessions' / day.strftime('%Y/%m/%d')
        candidates.extend(directory.glob(f'*{thread_id}*.jsonl'))
    if len(candidates) != 1:
        return {'verified': False, 'error': 'rollout_not_uniquely_available'}
    try:
        return {'verified': True, **rollout_usage(candidates[0].read_bytes(), thread_id)}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return {'verified': False, 'error': 'invalid_rollout_accounting'}


def run_bounded(command: list[str], cwd: Path, env: dict, raw: Path,
                stderr: Path, timeout: int) -> tuple[int, bool]:
    with raw.open('wb') as out, stderr.open('wb') as err:
        proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=out, stderr=err,
                                start_new_session=True)
        try:
            return proc.wait(timeout=timeout), False
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            # Terminate only this invocation's process group, not the queue or other agents.
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            return 124, True


def run_arm(codex: str, home: Path, env: dict, out: Path, cwd: Path,
            label: str, include: bool, prompt: str, expected: str,
            *, smoke: bool = False) -> dict:
    from collect_smoke import collect
    raw, err = out / f'{label}.jsonl', out / f'{label}.stderr'
    command = [codex, '-a', 'never', '-c', 'forced_login_method="chatgpt"',
               'exec', '--json', '--skip-git-repo-check', '-s', 'read-only',
               '-m', MODEL, '-c', 'model_reasoning_effort="low"',
               '-c', f'skills.include_instructions={str(include).lower()}', prompt]
    started = time.monotonic()
    rc, timed_out = run_bounded(command, cwd, env, raw, err, 120)
    data = raw.read_bytes()
    summary = collect(data, rc)
    # Private trace inspection; do not publish raw answers, commands, paths or errors.
    events = []
    for line in data.splitlines():
        try:
            event = json.loads(line)
            if isinstance(event, dict):
                events.append(event)
        except (ValueError, UnicodeDecodeError):
            pass  # The strict collector already invalidates malformed streams.
    ids = [e.get('thread_id') for e in events if e.get('type') == 'thread.started']
    per_request = inspect_rollout(home, ids[0]) if len(ids) == 1 and isinstance(ids[0], str) else {'verified': False}
    usage = summary['usage_events'][0] if summary['invocation_verified'] else None
    reconciliation = (per_request.get('verified', False) and usage is not None
                      and all(per_request['total'].get(k) == usage.get(k)
                              for k in ('input_tokens', 'output_tokens')))
    calls = summary['tool_completed_counts']
    tools_ok = (not smoke or calls == {'command_execution': 1})
    passed = summary['invocation_verified'] and summary['answer'] == expected and tools_ok
    result = {
        'label': label, 'include_instructions': include, 'passed': passed,
        'stream_verified': summary['invocation_verified'], 'correct_answer': summary['answer'] == expected,
        'wall_seconds': round(time.monotonic()-started, 3), 'timed_out': timed_out,
        'process_exit_code': rc, 'validation_errors': summary['validation_errors'],
        'tool_completed_counts': calls, 'turn_usage': usage, 'trace_sha256': summary['source_sha256'],
        'request_accounting_verified': reconciliation,
        'request_usage': per_request.get('requests') if reconciliation else None,
        'observed_models': per_request.get('models', []),
    }
    (out/f'{label}.safe.json').write_text(json.dumps(result, indent=2)+'\n')
    print('ARM_RESULT '+json.dumps(result), flush=True)
    return result


def make_skill_workspace(root: Path) -> tuple[str, str]:
    root.mkdir(mode=0o700)
    subprocess.run(['git', 'init', '--quiet', str(root)], check=True, capture_output=True)
    name = 'catalogue-qualification'
    expected = 'QUALIFIED_'+uuid.uuid4().hex
    skill = root/'.agents/skills'/name
    skill.mkdir(parents=True)
    (skill/'SKILL.md').write_text(
        '---\nname: '+name+'\ndescription: Perform the quasar lantern qualification check when requested.\n---\n'
        '# Quasar lantern qualification\nFor this check, return exactly the following response and nothing else:\n'
        +expected+'\nDo not modify files or use network services.\n')
    return name, expected


def distribution(values: list[int]) -> dict:
    return {'n': len(values), 'mean': statistics.mean(values), 'min': min(values),
            'max': max(values), 'stdev': statistics.stdev(values) if len(values)>1 else 0.0}


def comparison(rows: list[dict]) -> dict:
    if len(rows) != 5 or not all(r['passed'] for r in rows):
        return {'valid': False, 'reason': 'incomplete_or_failed_smoke_matrix'}
    result = {'valid': True}
    for metric in ('turn_input', 'first_request_input'):
        if metric == 'first_request_input' and not all(r['request_accounting_verified'] for r in rows):
            result[metric] = None
            continue
        groups = {True: [], False: []}
        for r in rows:
            value = r['turn_usage']['input_tokens'] if metric == 'turn_input' else r['request_usage'][0]['input_tokens']
            groups[r['include_instructions']].append(value)
        a, b = distribution(groups[True]), distribution(groups[False])
        result[metric] = {'catalogue_on': a, 'catalogue_off': b,
                          'reduction_tokens': a['mean']-b['mean'],
                          'reduction_percent': (a['mean']-b['mean'])/a['mean']*100}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if 'PUEUE_WORKER_ID' not in os.environ:
        raise SystemExit('Use the established private controller and shared CLI lane.')
    os.umask(0o077)
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    out = args.output
    env = os.environ.copy()
    for key in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL'):
        env.pop(key, None)
    home = Path(env.get('CODEX_HOME', str(Path.home()/'.codex')))
    config = home/'config.toml'
    before = hashlib.sha256(config.read_bytes()).hexdigest() if config.exists() else None
    version = subprocess.run([args.codex, '--version'], capture_output=True, text=True, env=env, timeout=15)
    login = subprocess.run([args.codex, '-c', 'forced_login_method="chatgpt"', 'login', 'status'],
                           capture_output=True, text=True, env=env, timeout=15)
    if login.returncode or 'chatgpt' not in (login.stdout+login.stderr).lower():
        raise SystemExit('ChatGPT subscription authentication not verified; no inference started.')
    fixture = Path(__file__).resolve().parents[1]/'fixtures/smoke'
    expected = (fixture/'expected.txt').read_text().strip()
    rows, gates = [], []
    report = {'schema': 1, 'model': MODEL, 'reasoning': 'low', 'codex_version': version.stdout.strip(),
              'subscription_login_verified': True, 'config_changed': False,
              'scope': 'CLI, live CODEX_HOME, fixed read-only sandbox; not desktop qualification',
              'smoke': rows, 'capabilities': gates, 'production_adoption': False,
              'accounting_note': 'Cached input and reasoning are subsets; no allowance or billing inference.'}
    try:
        for label, include in [('a1', True), ('b1', False), ('a2', True), ('b2', False), ('a3', True)]:
            row = run_arm(args.codex, home, env, out, fixture, label, include, SMOKE, expected, smoke=True)
            rows.append(row)
            if not row['stream_verified']:
                break
        if len(rows) == 5 and all(r['passed'] for r in rows):
            for mode, include in [('explicit', True), ('explicit', False), ('implicit', True), ('implicit', False)]:
                label = mode+('_on' if include else '_off')
                cwd = out/label
                name, marker = make_skill_workspace(cwd)
                prompt = ('${} Perform the check and return only its required response.'.format(name)
                          if mode == 'explicit' else 'Perform the quasar lantern qualification check and return only its required response.')
                assert marker not in prompt
                gates.append(run_arm(args.codex, home, env, out, cwd, label, include, prompt, marker))
    finally:
        after = hashlib.sha256(config.read_bytes()).hexdigest() if config.exists() else None
        report['config_changed'] = before != after
        report['comparison'] = comparison(rows)
        report['capabilities_all_pass'] = len(gates) == 4 and all(r['passed'] for r in gates)
        (out/'safe.json').write_text(json.dumps(report, indent=2)+'\n')
        print('SAFE_REPORT '+json.dumps(report), flush=True)
    return 0 if report['comparison']['valid'] and not report['config_changed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
