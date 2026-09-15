#!/usr/bin/env python3
"""Validate one Codex exec JSONL stream; preserve accounting instead of guessing it."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


def collect(data: bytes, exit_code: int | None = None) -> dict[str, Any]:
    errors: list[str] = []
    counts: Counter[str] = Counter()
    tools: Counter[str] = Counter()
    usage_events: list[dict[str, Any]] = []
    answer: str | None = None
    completed_ids: set[str] = set()
    terminal = False
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        text = ''
        errors.append('invalid_utf8')
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            errors.append(f'malformed_json_line:{number}')
            continue
        if not isinstance(event, dict) or not isinstance(event.get('type'), str):
            errors.append(f'invalid_event_line:{number}')
            continue
        kind = event['type']
        counts[kind] += 1
        if terminal:
            errors.append(f'event_after_terminal:{number}')
        if kind in ('error', 'turn.failed'):
            errors.append(kind)
        if kind == 'turn.started' and counts['thread.started'] != 1:
            errors.append('turn_without_single_thread')
        if kind.startswith('item.'):
            if counts['turn.started'] != 1:
                errors.append('item_outside_single_turn')
            item = event.get('item')
            if not isinstance(item, dict) or not isinstance(item.get('type'), str):
                errors.append(f'invalid_item_line:{number}')
                continue
            if kind == 'item.completed':
                identifier = item.get('id')
                if not isinstance(identifier, str) or not identifier:
                    errors.append('missing_completed_item_id')
                elif identifier in completed_ids:
                    errors.append('duplicate_completed_item')
                else:
                    completed_ids.add(identifier)
                item_type = item['type']
                if item_type == 'agent_message':
                    if not isinstance(item.get('text'), str):
                        errors.append('invalid_agent_message')
                    else:
                        answer = item['text'].strip()
                elif item_type in ('command_execution', 'mcp_tool_call', 'web_search', 'file_change'):
                    tools[item_type] += 1
                    if item.get('status') == 'failed':
                        errors.append('failed_smoke_tool')
                    if item_type == 'command_execution' and item.get('exit_code') not in (None, 0):
                        errors.append('nonzero_smoke_command')
        if kind == 'turn.completed':
            terminal = True
            value = event.get('usage')
            if isinstance(value, dict):
                usage_events.append(value)
            else:
                errors.append('missing_usage')
        elif kind == 'turn.failed':
            terminal = True
    for kind in ('thread.started', 'turn.started', 'turn.completed'):
        if counts[kind] != 1:
            errors.append(f'expected_one:{kind}')
    if not answer:
        errors.append('missing_final_answer')
    usage = usage_events[0] if len(usage_events) == 1 else None
    if usage is None:
        errors.append('expected_one_usage_record')
    else:
        for key in ('input_tokens', 'output_tokens'):
            value = usage.get(key)
            if type(value) is not int or value < 0:
                errors.append(f'invalid_counter:{key}')
        for key, value in usage.items():
            if key.endswith('_tokens') and (type(value) is not int or value < 0):
                errors.append(f'invalid_counter:{key}')
        if type(usage.get('input_tokens')) is int and usage['input_tokens'] == 0:
            errors.append('zero_input_tokens')
        cached, inputs = usage.get('cached_input_tokens'), usage.get('input_tokens')
        if type(cached) is int and type(inputs) is int and cached > inputs:
            errors.append('cached_exceeds_input')
    if exit_code is not None and (type(exit_code) is not int or exit_code != 0):
        errors.append('nonzero_process_exit')
    valid = not errors
    total = None
    if usage is not None and all(type(usage.get(k)) is int and usage[k] >= 0
                                 for k in ('input_tokens', 'output_tokens')):
        total = usage['input_tokens'] + usage['output_tokens']
    return {
        'schema': 2, 'answer': answer, 'usage_events': usage_events,
        'event_types': dict(counts), 'tool_completed_counts': dict(tools),
        'source_event_count': sum(counts.values()), 'source_bytes': len(data),
        'source_sha256': hashlib.sha256(data).hexdigest(), 'process_exit_code': exit_code,
        'stream_valid': valid,
        'invocation_verified': valid and exit_code == 0,
        'validation_errors': sorted(set(errors)),
        'input_plus_output_tokens': total,
        'accounting_note': 'Cached input is a subset, not added. Reasoning is retained as reported, not added again. Subscription allowance is not inferred.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--exit-code', type=int, required=True)
    args = parser.parse_args()
    try:
        summary = collect(args.source.read_bytes(), args.exit_code)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    except OSError:
        print('Cannot read source or write summary; no valid evidence produced.', file=sys.stderr)
        return 2
    if not summary['invocation_verified']:
        print('Invalid smoke evidence: ' + ', '.join(summary['validation_errors']), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
