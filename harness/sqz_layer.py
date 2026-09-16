#!/usr/bin/env python3
"""Experimental exact-repeat-only sqz adapter; not an installer or an agent.

Both arms execute the same RTK binary. The enabled arm may replace an already
DELIVERED identical stdout with a real upstream sqz reference. All first results,
non-text, stderr, exit values and sqz expansion outputs remain unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

REF = re.compile(r'§ref:([a-f0-9]{16,64})§')
MIN_BYTES = 1024
MAX_BYTES = 262144
MAX_ROLLOUT = 16_000_000


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_values(value):
    if isinstance(value, str):
        yield value
        # Code Mode can encode the underlying tool's text inside a JSON result.
        if value.lstrip().startswith(('{', '[')):
            try:
                parsed = json.loads(value)
            except ValueError:
                return
            yield from text_values(parsed)
    elif isinstance(value, list):
        for part in value:
            yield from text_values(part)
    elif isinstance(value, dict):
        for part in value.values():
            yield from text_values(part)


def delivered(data: bytes, rollout: Path | None) -> bool:
    """Fail closed unless the exact text is in this role's prior model tool input.

    A wrapper execution or a cache entry is not evidence of delivery. In
    particular, pipes/truncation and earlier workers must not seed references.
    Compaction invalidates prior sightings. No credential files are read.
    """
    try:
        if rollout is None or not rollout.is_file() or rollout.stat().st_size > MAX_ROLLOUT:
            return False
        text = data.decode('utf-8')
        seen = False
        for line in rollout.read_text(encoding='utf-8').splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            payload = event.get('payload', {})
            kind = event.get('type')
            pkind = payload.get('type') if isinstance(payload, dict) else None
            if kind in ('compacted', 'compaction') or pkind in ('context_compacted', 'compacted'):
                seen = False
            if kind == 'response_item' and pkind in ('function_call_output', 'custom_tool_call_output'):
                if any(text in part for part in text_values(payload.get('output'))):
                    seen = True
        return seen
    except (OSError, UnicodeError, TypeError):
        return False


def sqz_environment(cfg: dict) -> dict[str, str]:
    # No credentials, proxy keys, plugins or global sqz persistence inherited.
    home = Path(cfg['sqz_home'])
    home.mkdir(parents=True, exist_ok=True)
    return {'HOME': str(home), 'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
            'SQZ_DB_PATH': str(home/'sessions.db'), 'SQZ_NO_ABBREV': '1',
            'NO_COLOR': '1', 'LANG': 'en_US.UTF-8', 'LC_ALL': 'en_US.UTF-8',
            'TMPDIR': str(home)}


def filter_stdout(data: bytes, cfg: dict) -> tuple[bytes, dict]:
    record = {'input_bytes': len(data), 'input_sha256': digest(data),
              'sqz_called': False, 'dedup_hit': False, 'recovered': False}
    if not cfg.get('enabled'):
        return data, dict(record, reason='disabled')
    if not MIN_BYTES <= len(data) <= MAX_BYTES:
        return data, dict(record, reason='size-pass')
    try:
        data.decode('utf-8')
    except UnicodeError:
        return data, dict(record, reason='non-text-pass')
    start = time.monotonic()
    record['sqz_called'] = True
    try:
        proc = subprocess.run([cfg['sqz'], 'compress', '--cmd', 'stdin', '--no-abbrev'],
                              input=data, capture_output=True, env=sqz_environment(cfg),
                              cwd=cfg['sqz_home'], timeout=8)
        record['sqz_exit'] = proc.returncode
        record['sqz_stderr_sha256'] = digest(proc.stderr)
        ref = REF.fullmatch(proc.stdout.decode('utf-8').strip()) if proc.returncode == 0 else None
        path = Path(cfg['rollout']) if cfg.get('rollout') else None
        if ref and digest(data).startswith(ref.group(1)) and delivered(data, path):
            value = (ref.group(0) + '\n[Identical output already received in this session; '
                     'full output: sqz expand ' + ref.group(1) + ']\n').encode()
            if len(value) < len(data):
                record.update(dedup_hit=True, reason='verified-repeat')
                return value, record
        # All lossy/default formatter output is deliberately discarded. This is
        # an experiment of sqz's exact-repeat path, not its lossy compression.
        record.update(reason='original-preserved')
        return data, record
    except (subprocess.TimeoutExpired, OSError, UnicodeError) as error:
        record.update(reason='sqz-fallback', error_type=type(error).__name__)
        return data, record
    finally:
        record['filter_seconds'] = round(time.monotonic()-start, 6)


def append_audit(cfg: dict, record: dict) -> None:
    with Path(cfg['audit']).open('a', encoding='utf-8') as out:
        out.write(json.dumps(record, sort_keys=True)+'\n')


def invoke(cfg: dict, tool: str, args: list[str]) -> int:
    start = time.monotonic()
    if tool == 'sqz':
        if len(args) != 2 or args[0] != 'expand' or not re.fullmatch(r'[a-f0-9]{16,64}', args[1]):
            sys.stderr.write('Usage: sqz expand HASH\n')
            return 2
        cmd = [cfg['sqz'], *args]
        env = sqz_environment(cfg)
    else:
        cmd = [cfg['rtk'], *args]
        env = dict(cfg['rtk_env'])
    record = {'tool': tool, 'args': args}
    try:
        proc = subprocess.run(cmd, env=env, stdin=None, capture_output=True, timeout=60)
        out = proc.stdout
        if tool == 'rtk' and args and args[0] not in ('recall', 'gain', 'config', '--help', '--version'):
            out, meta = filter_stdout(out, cfg)
            record.update(meta)
        record.setdefault('input_bytes',len(proc.stdout))
        record.setdefault('input_sha256',digest(proc.stdout))
        record.update(exit_code=proc.returncode, stderr_bytes=len(proc.stderr),
                      returned_bytes=len(out), returned_sha256=digest(out),
                      recovered=tool == 'sqz' and proc.returncode == 0,
                      wall_seconds=round(time.monotonic()-start, 6))
        sys.stdout.buffer.write(out)
        sys.stderr.buffer.write(proc.stderr)
        append_audit(cfg, record)
        return proc.returncode if proc.returncode >= 0 else 128-proc.returncode
    except subprocess.TimeoutExpired as error:
        sys.stdout.buffer.write(error.stdout or b'')
        sys.stderr.buffer.write(error.stderr or b'')
        sys.stderr.write('\n[benchmark wrapper timeout]\n')
        append_audit(cfg, dict(record, timeout=True, exit_code=124))
        return 124


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--tool', choices=('rtk', 'sqz'), required=True)
    parser.add_argument('args', nargs=argparse.REMAINDER)
    ns = parser.parse_args()
    args = ns.args[1:] if ns.args[:1] == ['--'] else ns.args
    return invoke(json.loads(ns.config.read_text()), ns.tool, args)


if __name__ == '__main__':
    raise SystemExit(main())
