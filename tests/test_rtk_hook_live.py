import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

harness=Path(__file__).parents[1]/'harness'
sys.path.insert(0,str(harness))
# Pure launcher tests deliberately isolate imported dependencies; Mac full-suite tests
# and actual runtime traces remain the integration evidence.
fidelity=types.ModuleType('rtk_fidelity');fidelity.environment=lambda h: dict(os.environ,HOME=str(h))
fidelity.write_config=lambda h,s:h.mkdir(parents=True,exist_ok=True)
catalogue=types.ModuleType('skill_catalogue');catalogue.counters=lambda x:x
catalogue.inspect_rollout=lambda h,i:{'verified':False}
with patch.dict(sys.modules,rtk_fidelity=fidelity,skill_catalogue=catalogue):
    spec=importlib.util.spec_from_file_location('hook_live',harness/'rtk_hook_live.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class LiveHookTests(unittest.TestCase):
    def hook(self):
        return {'command':'python hook.py','eventName':'preToolUse','source':'sessionFlags',
                'key':'/<session-flags>/config.toml:pre_tool_use:0:0','currentHash':'sha256:'+'a'*64}
    def test_trust_only_exact_reviewed_hook(self):
        flags=m.trusted_flags([self.hook()],'python hook.py',True)
        self.assertEqual(len(flags),4)
        self.assertIn('trusted_hash',flags[1]);self.assertTrue(flags[-1].endswith('enabled=true'))
        self.assertNotIn('bypass',' '.join(flags))
    def test_refuse_other_source_or_ambiguous_hook(self):
        h=self.hook();h['source']='user'
        with self.assertRaises(ValueError):m.trusted_flags([h],'python hook.py',True)
        with self.assertRaises(ValueError):m.trusted_flags([self.hook(),self.hook()],'python hook.py',True)
    def test_refuse_malformed_hash(self):
        h=self.hook();h['currentHash']='trusted'
        with self.assertRaises(ValueError):m.trusted_flags([h],'python hook.py',True)
    def test_fixed_scope_no_auth_or_blanket_trust_override(self):
        flags=' '.join(m.flags_for('python hook.py',Path('/fixture'),'/bin'))
        self.assertIn('skills.include_instructions=false',flags)
        self.assertIn('forced_login_method="chatgpt"',flags)
        self.assertNotIn('bypass',flags);self.assertNotIn('CODEX_HOME',flags)
    def test_generated_fixture_scripts_compile_and_marker_hidden(self):
        with tempfile.TemporaryDirectory() as d:
            cwd,shim,hook,audit,expected,marker=m.make_fixture(Path(d),Path('/fake-binary'))
            compile(hook.read_text(),'hook','exec');compile((shim/'rtk').read_text(),'shim','exec')
            self.assertNotIn(expected.split(':')[0],m.PROMPT)
            self.assertIn(expected.split(':')[0],(cwd/'.agents/skills/rtk-hook-qualification/SKILL.md').read_text())
            self.assertTrue((cwd/'.git/index').exists())
    def test_denial_and_usage_are_distinct(self):
        events=[{'type':'thread.started','thread_id':'test-id'},{'type':'item.completed','item':{
            'type':'command_execution','command':'git add pending.txt','exit_code':1,'aggregated_output':'denied'}},
            {'type':'item.completed','item':{'type':'agent_message','text':'expected'}},
            {'type':'turn.completed','usage':{'input_tokens':5,'output_tokens':2}}]
        with tempfile.TemporaryDirectory() as d:
            raw=Path(d)/'events';raw.write_text('\n'.join(map(json.dumps,events)))
            row=m.read_evidence(raw,'cli','unseen','expected',Path(d))
        self.assertTrue(row['mutation_denied']);self.assertTrue(row['correct_answer'])
        self.assertFalse(row['request_accounting_verified']);self.assertEqual(row['usage']['input_tokens'],5)

if __name__=='__main__':unittest.main()
