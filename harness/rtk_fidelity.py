#!/usr/bin/env python3
"""Bounded, zero-model-call RTK binary fidelity gate. Issue #11 owns decisions.

Run only through the trusted private controller. Raw files remain in --output.
This is NOT a whole-task token benchmark or a production RTK installation.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import tarfile
import time
import tomllib
import urllib.request

VERSION = '0.49.0'
SOURCE = 'b1c0dc00649c50fbe8930f849c800d4d6ca12091'
ASSET = 'https://github.com/rtk-ai/rtk/releases/download/v0.49.0/rtk-aarch64-apple-darwin.tar.gz'
DIGEST = 'bbbfebabb22686993a80da731aa4d5d35116fb8ae24abb00608efa028e13ae01'
REF = re.compile(rb'rtk recall\s+([a-f0-9]{12})\b')
DEADLINE = 0.0


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv: list[str], cwd: Path, env: dict[str, str], timeout: float = 15) -> dict:
    remaining = DEADLINE - time.monotonic() if DEADLINE else timeout
    if remaining <= 0:
        raise TimeoutError('total fidelity deadline reached')
    start = time.monotonic()
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True)
    timed_out = False
    try:
        out, err = proc.communicate(timeout=min(timeout, remaining))
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate(timeout=5)
    return {'code': proc.returncode, 'stdout': out, 'stderr': err,
            'timeout': timed_out, 'wall_ms': round((time.monotonic()-start)*1000)}


def require(result: dict) -> bytes:
    if result['timeout'] or result['code'] != 0:
        raise RuntimeError('bounded setup command failed; inspect private evidence')
    return result['stdout']


def scalar(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return '[' + ', '.join(scalar(x) for x in value) + ']'
    raise ValueError('unsupported config value; do not silently drop it')


def toml(config: dict) -> str:
    lines = []
    def table(obj, prefix):
        if prefix:
            lines.append('[' + '.'.join(json.dumps(p) for p in prefix) + ']')
        for key, value in obj.items():
            if not isinstance(value, dict):
                lines.append(json.dumps(key) + ' = ' + scalar(value))
        for key, value in obj.items():
            if isinstance(value, dict):
                table(value, prefix + [key])
    table(config, [])
    return '\n'.join(lines) + '\n'


def isolated_config(config: dict) -> dict:
    """Preserve filtering/recovery choices; redirect all known writable stores."""
    result = json.loads(json.dumps(config))
    result.setdefault('tracking', {}).update(enabled=False, history_days=1)
    result['tracking'].pop('database_path', None)
    result.setdefault('telemetry', {}).update(enabled=False, consent_given=False)
    for section, keys in {'retriever': ('database_path', 'tee_directory'),
                          'tee': ('directory',)}.items():
        for key in keys:
            result.get(section, {}).pop(key, None)
    return result


def environment(home: Path) -> dict[str, str]:
    home.mkdir(parents=True, exist_ok=True)
    return {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(home),
            'XDG_CONFIG_HOME': str(home/'.config'), 'XDG_DATA_HOME': str(home/'.local/share'),
            'XDG_CACHE_HOME': str(home/'.cache'), 'TMPDIR': str(home),
            'LANG': 'en_US.UTF-8', 'LC_ALL': 'en_US.UTF-8', 'NO_COLOR': '1',
            'TERM': 'dumb', 'CI': '1', 'RTK_TELEMETRY_DISABLED': '1',
            'RTK_RECALL_DB': str(home/'recall.db'),
            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
            'GIT_TERMINAL_PROMPT': '0'}


def write_config(home: Path, source: str):
    for directory in (home/'.config/rtk', home/'Library/Application Support/rtk'):
        directory.mkdir(parents=True, exist_ok=True)
        (directory/'config.toml').write_text(source)


def extract_binary(data: bytes, dest: Path) -> Path:
    if sha(data) != DIGEST:
        raise ValueError('release archive digest mismatch')
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        matches = [m for m in archive.getmembers() if Path(m.name).name == 'rtk']
        if len(matches) != 1 or not matches[0].isfile() or matches[0].size > 50_000_000:
            raise ValueError('unexpected release archive binary')
        # Read one regular member, never extract paths/symlinks from an archive.
        file = archive.extractfile(matches[0])
        if file is None:
            raise ValueError('unreadable release member')
        binary = dest/'rtk'
        binary.write_bytes(file.read())
        binary.chmod(0o700)
        return binary


def evidence(result: dict, directory: Path, name: str) -> dict:
    for stream in ('stdout', 'stderr'):
        (directory/(name+'.'+stream)).write_bytes(result[stream])
    return {'exit_code': result['code'], 'timed_out': result['timeout'],
            'wall_ms': result['wall_ms'],
            **{k: {'bytes': len(result[k]), 'sha256': sha(result[k])}
               for k in ('stdout', 'stderr')}}


def fixture_cases() -> list[dict]:
    progress = ''.join(f'[build {i:03d}/100] Compiling unrelated translation unit\n' for i in range(100))
    return [
        {'name': 'clang-stderr', 'wrapper': 'err', 'exit': 1, 'stderr': True,
         'text': progress + "src/voice.cpp:47:19: error: no member named 'releaseLevel' in 'Voice'\n"
                 "note: expected release coefficient 0.000125; actual 0.125000\n1 error generated.\n",
         'facts': ['src/voice.cpp:47:19', 'releaseLevel', '0.000125', '0.125000']},
        {'name': 'ctest-failure', 'wrapper': 'test', 'exit': 8,
         'text': progress + '2/2 Test #2: ReleaseModulation ... ***Failed\n'
                 'tests/release.cpp:83: CHECK failed: actual=0.125000 expected=0.000125 tolerance=0.000001\n'
                 '50% tests passed, 1 tests failed out of 2\nThe following tests FAILED:\n2 - ReleaseModulation (Failed)\n',
         'facts': ['ReleaseModulation', 'tests/release.cpp:83', '0.125000', '0.000125', '0.000001']},
        {'name': 'typescript-failure', 'wrapper': 'err', 'exit': 2,
         'text': progress + "src/transport.ts(41,7): error TS2322: Type 'string' is not assignable to type 'number'.\n"
                 'Found 1 error in src/transport.ts:41\n',
         'facts': ['src/transport.ts', '41', 'TS2322', "'string'", "'number'"]},
        {'name': 'ui-assertion', 'wrapper': 'test', 'exit': 1,
         'text': progress + 'FAIL tests/transport.test.ts > BPM updates while dragging\n'
                 'AssertionError: expected 120 to equal 147.5\n'
                 'at tests/transport.test.ts:63:12\nTest Files 1 failed (1)\nTests 1 failed | 19 passed (20)\n',
         'facts': ['BPM updates while dragging', '120', '147.5', 'tests/transport.test.ts:63:12']},
        {'name': 'custom-exit', 'wrapper': 'err', 'exit': 17,
         'text': progress + 'ERROR AUDIO_ACCEPTANCE_FAILED peak=-1.250dBFS rms=-18.375dBFS\n',
         'facts': ['AUDIO_ACCEPTANCE_FAILED', '-1.250', '-18.375']},
        {'name': 'success', 'wrapper': 'test', 'exit': 0,
         'text': 'Test Files 2 passed (2)\nTests 20 passed (20)\n', 'facts': ['20']},
    ]


def check_case(binary: Path, case: dict, cwd: Path, env: dict, raw: Path) -> dict:
    (cwd/'emit.py').write_text('import sys\n'
        + ('sys.stderr' if case.get('stderr') else 'sys.stdout')
        + '.buffer.write(' + repr(case['text'].encode()) + ')\n'
        + 'raise SystemExit(' + str(case['exit']) + ')\n')
    command = [sys.executable, 'emit.py']
    baseline = run(command, cwd, env)
    filtered = run([str(binary), case['wrapper'], *command], cwd, env)
    name = case['name']
    result = {'name': name, 'raw': evidence(baseline, raw, name+'-raw'),
              'filtered': evidence(filtered, raw, name+'-filtered')}
    view = filtered['stdout'] + filtered['stderr']
    missing = [x for x in case['facts'] if x.encode() not in view]
    recovered = b''
    refs = list(dict.fromkeys(REF.findall(view)))
    result['recall_refs'] = [r.decode() for r in refs]
    result['recall'] = []
    for index, ref in enumerate(refs[:3]):
        rec = run([str(binary), 'recall', ref.decode()], cwd, env)
        result['recall'].append(evidence(rec, raw, name+f'-recall-{index}'))
        if rec['code'] == 0 and not rec['timeout']:
            recovered += rec['stdout']
    result['missing_inline'] = missing
    result['missing_after_recall'] = [x for x in missing if x.encode() not in recovered]
    result['recall_byte_exact'] = recovered == case['text'].encode() if refs else None
    result['exit_preserved'] = filtered['code'] == baseline['code'] == case['exit']
    result['pass'] = (not baseline['timeout'] and not filtered['timeout']
                      and result['exit_preserved'] and not result['missing_after_recall']
                      and (not refs or result['recall_byte_exact']))
    return result


def git_cases(binary: Path, cwd: Path, env: dict, raw: Path) -> list[dict]:
    require(run(['git','init','-q'], cwd, env))
    for key, value in [('user.name','Fixture'), ('user.email','fixture@example.invalid'), ('core.quotepath','false')]:
        require(run(['git','config',key,value], cwd, env))
    source = cwd/'voice.cpp'
    source.write_text('double releaseLevel = 0.125000;\n')
    require(run(['git','add','voice.cpp'], cwd, env))
    require(run(['git','commit','-qm','fixture'], cwd, env))
    result = []
    for number, value in enumerate(('0.000125','0.000250')):
        source.write_text('double releaseLevel = '+value+';\n')
        base = run(['git','diff','--no-ext-diff'], cwd, env)
        filtered = run([str(binary),'git','diff'], cwd, env)
        text = filtered['stdout']+filtered['stderr']
        result.append({'name':'git-diff-'+str(number),
            'raw':evidence(base,raw,'diff-'+str(number)+'-raw'),
            'filtered':evidence(filtered,raw,'diff-'+str(number)+'-filtered'),
            'pass':not filtered['timeout'] and filtered['code']==0
                and all(x.encode() in text for x in ('voice.cpp','0.125000',value))})
    (cwd/'tracker-ü.ts').write_text('export const bpm = 147.5;\n')
    filtered = run([str(binary),'git','status'],cwd,env)
    text = filtered['stdout']+filtered['stderr']
    result.append({'name':'git-status-unicode','filtered':evidence(filtered,raw,'status'),
        'pass':not filtered['timeout'] and filtered['code']==0
            and b'voice.cpp' in text and 'tracker-ü.ts'.encode() in text})
    return result


def main() -> int:
    global DEADLINE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--installed-rtk', type=Path, required=True)
    args = parser.parse_args()
    DEADLINE = time.monotonic()+300
    os.umask(0o077)
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    report = {'schema':1, 'stage':'rtk-offline-fidelity', 'model_calls':0,
              'whole_task_tokens':None, 'subscription_savings':None,
              'release_version':VERSION, 'candidate_source':SOURCE, 'archive_sha256':DIGEST,
              'cases':{}, 'desktop_qualified':False, 'full_workflow_baseline_qualified':False}
    try:
        if platform.system()!='Darwin' or platform.machine()!='arm64':
            raise RuntimeError('this pinned artifact requires macOS arm64')
        installed = args.installed_rtk.resolve(strict=True)
        original_hash = sha(installed.read_bytes())
        report['installed_binary_sha256'] = original_hash
        home = Path.home()
        cfg_path = home/'Library/Application Support/rtk/config.toml'
        if cfg_path.is_symlink():
            raise RuntimeError('live RTK config symlink: inspect rather than guessing')
        cfg_bytes = cfg_path.read_bytes() if cfg_path.exists() else b''
        live = tomllib.loads(cfg_bytes.decode())
        report['live_config_present'] = bool(cfg_bytes)
        report['live_config_sha256'] = sha(cfg_bytes)
        normalized = toml(isolated_config(live))
        report['isolated_config_sha256'] = sha(normalized.encode())
        report['recovery_config'] = {k:live.get(k,{}).get('mode') for k in ('tee','retriever')}
        config_file = Path(__file__).resolve().parents[1]/'.codex/config.toml'
        report['repo_skills_include_instructions'] = tomllib.loads(config_file.read_text())['skills']['include_instructions']
        binary_dir = root/'candidate'; binary_dir.mkdir()
        with urllib.request.urlopen(ASSET, timeout=40) as response:
            archive = response.read(10_000_001)
        if len(archive)>10_000_000:
            raise RuntimeError('unexpected archive size')
        candidate = extract_binary(archive,binary_dir)
        report['candidate_binary_sha256'] = sha(candidate.read_bytes())
        for arm, binary in [('installed', installed),('candidate',candidate)]:
            private = root/arm; private.mkdir()
            env = environment(private/'home'); write_config(Path(env['HOME']),normalized)
            cwd = Path(env['HOME'])/'work'; cwd.mkdir()
            version = require(run([str(binary),'--version'],cwd,env)).decode().strip()
            if not re.fullmatch(r'rtk \d+\.\d+\.\d+(?:[-+][\w.-]+)?',version):
                raise RuntimeError('unexpected RTK identity')
            report[arm+'_version'] = version
            if arm=='candidate' and version!='rtk '+VERSION:
                raise RuntimeError('candidate version mismatch')
            probe = run([str(binary),'config'],cwd,env)
            evidence(probe,private,'effective-config')
            if probe['timeout'] or probe['code']!=0:
                raise RuntimeError('config isolation not established')
            # The isolated HOME is allowed to be beneath real HOME; use exact Config header.
            header = probe['stdout'].decode(errors='replace').splitlines()[0]
            if not header.startswith('Config: '+str(Path(env['HOME']))):
                raise RuntimeError('RTK config directory escaped its isolated HOME')
            report['cases'][arm] = [check_case(binary,c,cwd,env,private) for c in fixture_cases()]
            report['cases'][arm] += git_cases(binary,cwd,env,private)
        report['same_version'] = report['installed_version']=='rtk '+VERSION
        report['installed_binary_unchanged'] = sha(installed.read_bytes()) == original_hash
        report['live_config_unchanged'] = (cfg_path.read_bytes() if cfg_path.exists() else b'') == cfg_bytes
        report['pass'] = report['installed_binary_unchanged'] and report['live_config_unchanged'] and all(c['pass'] for c in report['cases']['candidate'])
        report['status'] = 'fidelity-pass' if report['pass'] else 'fidelity-failed'
        return 0 if report['pass'] else 1
    except Exception as error:
        # Never publish arbitrary exception strings containing private URLs/paths.
        (root/'error.private.txt').write_text(repr(error)+'\n')
        report.update(status='infrastructure-failed', error_type=type(error).__name__, passed=False)
        return 2
    finally:
        (root/'safe.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
