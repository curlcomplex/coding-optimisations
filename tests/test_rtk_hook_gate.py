import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('hook_gate',Path(__file__).parents[1]/'harness/rtk_hook_gate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class HookGateTests(unittest.TestCase):
    def test_modes_and_passthrough_cases(self):
        cases=m.wire_cases()
        self.assertEqual(len(cases),14)
        self.assertEqual(len(set(n for n,_,_ in cases)),14)
        self.assertEqual({o.get('permission_mode') for _,o,_ in cases},
                         {'default','acceptEdits','plan','dontAsk','bypassPermissions','future-mode',None})
    def test_preserves_noncommand_fields(self):
        def fake(argv,cwd,env,payload=b'',timeout=20):
            if payload==b'{bad json':return 0,b'',b'bad input'
            obj=json.loads(payload);match=next((e for _,o,e in m.wire_cases() if o==obj),None)
            if not match:return 0,b'',b''
            replacement=dict(obj['tool_input']);replacement['command']=match
            return 0,json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse',
                'permissionDecision':'allow','updatedInput':replacement}}).encode(),b''
        with tempfile.TemporaryDirectory() as d,patch.object(m,'execute',side_effect=fake):
            rows=m.check_wire(Path('/fake'),Path(d),{},Path(d))
        self.assertEqual(len(rows),15);self.assertTrue(all(r['pass'] for r in rows))
    def test_missing_rewrite_does_not_pass(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'execute',return_value=(0,b'',b'')):
            rows=m.check_wire(Path('/fake'),Path(d),{},Path(d))
        self.assertFalse(next(r for r in rows if r['case']=='status')['pass'])
    def test_owned_deadline(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(TimeoutError):
                m.execute([sys.executable,'-c','import time;time.sleep(10)'],d,os.environ.copy(),timeout=.05)
    def test_rpc_buffers_multiple_messages_and_errors(self):
        program='import sys,json\nfor line in sys.stdin:\n o=json.loads(line)\n if "id" in o:\n  print(json.dumps({"method":"notice"}));print(json.dumps({"id":o["id"],"result":{"ok":True}}));sys.stdout.flush()\n'
        with tempfile.TemporaryDirectory() as d:
            rpc=m.Rpc([sys.executable,'-u','-c',program],d,os.environ.copy(),Path(d)/'rpc.jsonl')
            try:
                rpc.start();self.assertEqual(rpc.call('test',{}),{'ok':True})
            finally:rpc.close()
        self.assertIsNotNone(rpc.proc.returncode)

if __name__=='__main__':unittest.main()
