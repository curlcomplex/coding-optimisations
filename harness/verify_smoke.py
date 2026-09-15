#!/usr/bin/env python3
"""Require successful process, valid accounting and an exact deterministic answer."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('summary', type=Path)
    parser.add_argument('expected', type=Path)
    args = parser.parse_args()
    try:
        summary = json.loads(args.summary.read_text())
        expected = args.expected.read_text().strip()
    except (OSError, json.JSONDecodeError):
        print('Unreadable smoke evidence or expected answer.', file=sys.stderr)
        return 2
    if not isinstance(summary, dict) or summary.get('schema') != 2:
        print('Unqualified summary schema.', file=sys.stderr)
        return 1
    if summary.get('invocation_verified') is not True or summary.get('validation_errors'):
        print('Invocation or usage evidence not verified.', file=sys.stderr)
        return 1
    if summary.get('answer') != expected:
        print('Final answer did not match the deterministic fixture.', file=sys.stderr)
        return 1
    print('PASS: successful invocation, valid accounting and exact fixture answer.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
