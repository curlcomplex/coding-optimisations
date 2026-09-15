#!/usr/bin/env python3
import json
import sys
from pathlib import Path

summary = json.loads(Path(sys.argv[1]).read_text())
expected = Path(sys.argv[2]).read_text().strip()
actual = (summary.get('answer') or '').strip()
if actual != expected:
    print(f'FAIL: expected {expected!r}, got {actual!r}', file=sys.stderr)
    raise SystemExit(1)
print(f'PASS: answer={actual}')
print(f"events={summary.get('source_event_count', 0)} usage_events={len(summary.get('usage_events', []))}")
