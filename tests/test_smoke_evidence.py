"""Offline tests: these exercise accounting validation, not model inference."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'harness'))
from collect_smoke import collect


def events():
    return [
        {'type': 'thread.started', 'thread_id': 'test'},
        {'type': 'turn.started'},
        {'type': 'item.started', 'item': {'id': 'cmd', 'type': 'command_execution', 'status': 'in_progress'}},
        {'type': 'item.completed', 'item': {'id': 'cmd', 'type': 'command_execution', 'status': 'completed', 'exit_code': 0}},
        {'type': 'item.completed', 'item': {'id': 'msg', 'type': 'agent_message', 'text': '442'}},
        {'type': 'turn.completed', 'usage': {'input_tokens': 100, 'cached_input_tokens': 80, 'output_tokens': 10}},
    ]


def raw(items):
    return ('\n'.join(json.dumps(e) for e in items) + '\n').encode()


class EvidenceTests(unittest.TestCase):
    def test_success(self):
        r = collect(raw(events()), 0)
        self.assertTrue(r['invocation_verified'])
        self.assertEqual(r['answer'], '442')
        self.assertEqual(r['input_plus_output_tokens'], 110)
        self.assertEqual(r['tool_completed_counts'], {'command_execution': 1})

    def test_missing_exit_is_not_verified(self):
        r = collect(raw(events()))
        self.assertTrue(r['stream_valid'])
        self.assertFalse(r['invocation_verified'])

    def test_nonzero_exit(self):
        self.assertFalse(collect(raw(events()), 1)['invocation_verified'])

    def test_malformed_line(self):
        self.assertFalse(collect(raw(events()) + b'garbage\n', 0)['invocation_verified'])

    def test_invalid_utf8(self):
        self.assertFalse(collect(b'\xff', 0)['stream_valid'])

    def test_empty(self):
        self.assertFalse(collect(b'', 0)['stream_valid'])

    def test_nonobject(self):
        self.assertFalse(collect(b'[]\n' + raw(events()), 0)['stream_valid'])

    def test_missing_usage(self):
        data = events(); data[-1].pop('usage')
        self.assertFalse(collect(raw(data), 0)['stream_valid'])

    def test_incomplete(self):
        self.assertFalse(collect(raw(events()[:-1]), 0)['stream_valid'])

    def test_failure_and_error(self):
        for kind in ('turn.failed', 'error'):
            data = events(); data.insert(-1, {'type': kind})
            self.assertFalse(collect(raw(data), 0)['stream_valid'])

    def test_duplicate_terminal(self):
        data = events(); data.append(copy.deepcopy(data[-1]))
        self.assertFalse(collect(raw(data), 0)['stream_valid'])

    def test_bad_usage_values(self):
        for value in (-1, True, '100', None, 0):
            data = events(); data[-1]['usage']['input_tokens'] = value
            self.assertFalse(collect(raw(data), 0)['stream_valid'], value)

    def test_cached_is_subset(self):
        data = events(); data[-1]['usage']['cached_input_tokens'] = 101
        self.assertFalse(collect(raw(data), 0)['stream_valid'])

    def test_reasoning_not_added_again(self):
        data = events(); data[-1]['usage']['reasoning_output_tokens'] = 5
        result = collect(raw(data), 0)
        self.assertTrue(result['stream_valid'])
        self.assertEqual(result['input_plus_output_tokens'], 110)
        self.assertEqual(result['usage_events'][0]['reasoning_output_tokens'], 5)

    def test_duplicate_completed_tool(self):
        data = events(); data.insert(4, copy.deepcopy(data[3]))
        self.assertFalse(collect(raw(data), 0)['stream_valid'])

    def test_started_answer_not_final(self):
        data = events(); data[4]['type'] = 'item.started'
        self.assertFalse(collect(raw(data), 0)['stream_valid'])

    def test_failed_command(self):
        data = events(); data[3]['item']['exit_code'] = 1
        self.assertFalse(collect(raw(data), 0)['stream_valid'])

    def test_event_order(self):
        data = events(); data[0], data[1] = data[1], data[0]
        self.assertFalse(collect(raw(data), 0)['stream_valid'])

    def test_cli_and_wrong_answer_gate(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); source = d/'events.jsonl'; summary = d/'summary.json'; expected = d/'expected.txt'
            source.write_bytes(raw(events())); expected.write_text('442\n')
            args = [sys.executable, str(ROOT/'harness/collect_smoke.py'), str(source), str(summary), '--exit-code', '0']
            self.assertEqual(subprocess.run(args, capture_output=True).returncode, 0)
            verify = [sys.executable, str(ROOT/'harness/verify_smoke.py'), str(summary), str(expected)]
            self.assertEqual(subprocess.run(verify, capture_output=True).returncode, 0)
            expected.write_text('443\n')
            self.assertEqual(subprocess.run(verify, capture_output=True).returncode, 1)

    def test_cli_failure_preserves_summary(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); source = d/'events.jsonl'; summary = d/'summary.json'
            source.write_bytes(raw(events()) + b'not-json\n')
            args = [sys.executable, str(ROOT/'harness/collect_smoke.py'), str(source), str(summary), '--exit-code', '0']
            self.assertEqual(subprocess.run(args, capture_output=True).returncode, 1)
            self.assertFalse(json.loads(summary.read_text())['invocation_verified'])

    def test_old_schema_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); summary = d/'summary.json'; expected = d/'expected.txt'
            summary.write_text(json.dumps({'answer': '442'})); expected.write_text('442')
            result = subprocess.run([sys.executable, str(ROOT/'harness/verify_smoke.py'), str(summary), str(expected)], capture_output=True)
            self.assertEqual(result.returncode, 1)


if __name__ == '__main__':
    unittest.main()
