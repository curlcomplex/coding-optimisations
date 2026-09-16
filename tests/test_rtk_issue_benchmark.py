import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import tomllib
import types
import unittest
from unittest.mock import patch
H=Path(__file__).parents[1]/'harness'
sys.path.insert(0,str(H))
# Mechanics tests need no agent process; stubs are temporary during import only.
stubs={
 'rtk_hook_gate':types.SimpleNamespace(Rpc=None,execute=None,digest=lambda x:__import__('hashlib').sha256(x).hexdigest(),fetch_binary=None),
 'rtk_hook_live':types.SimpleNamespace(hook_list=None,trusted_flags=None),
 'rtk_fidelity':types.SimpleNamespace(environment=None,isolated_config=None,toml=None,write_config=None),
 'skill_catalogue':types.SimpleNamespace(inspect_rollout=None)}
spec=importlib.util.spec_from_file_location('issue_benchmark_tested',H/'rtk_issue_benchmark.py')
m=importlib.util.module_from_spec(spec)
with patch.dict(sys.modules,stubs):spec.loader.exec_module(m)

class BenchmarkTests(unittest.TestCase):
 def test_safety_scope(self):
  for c in ('git status --short','git diff -- src','rg pattern src','ls -la'):self.assertTrue(m.allow_inspection(c),c)
  for c in ('git push origin HEAD','git add x','git reset --hard','git -c alias.foo=x foo','git diff > file','cat $(secret)','find . -exec x ;','rg --pre=prog x','git diff --output=x'):
   self.assertFalse(m.allow_inspection(c),c)
 def test_review_gate(self):
  self.assertTrue(m.parse_review('{"accepted":true,"findings":[]}')[0])
  self.assertFalse(m.parse_review('{"accepted":true,"findings":["bug"]}')[0])
  for x in ('ok','{}','{"accepted":"true","findings":[]}'):
   with self.assertRaises((ValueError,TypeError)):m.parse_review(x)
 def test_preserve_existing_hook_config(self):
  old=[{'matcher':'Bash','hooks':[{'type':'command','command':'existing'}]}]
  flags=m.base_flags(Path('/fixture'),'/safe','python hook',old)
  value=flags[flags.index('-c',len(flags)-2)+1].split('=',1)[1]
  parsed=tomllib.loads('x='+value)['x']
  self.assertEqual(parsed[0],old[0]);self.assertEqual(len(parsed),2)
 def test_all_attempts_and_reviews_count_without_subsets_twice(self):
  c={'accounting_verified':True,'usage':{'input_tokens':100,'cached_input_tokens':50,'output_tokens':10,'reasoning_output_tokens':4},'wall_seconds':2}
  rows=[{'arm':'off','accepted':True,'worker':c,'review':c},{'arm':'off','accepted':False,'worker':c,'review':c}]
  r=m.aggregate(rows)['off'];self.assertEqual(r['total_tokens'],440);self.assertEqual(r['tokens_per_accepted'],440)
  self.assertEqual(r['usage']['reasoning_output_tokens'],16);self.assertEqual(r['failures'],1)
 def test_unknown_counters_are_not_zero(self):
  c={'accounting_verified':False,'usage':None,'wall_seconds':1}
  r=m.aggregate([{'arm':'on','accepted':False,'worker':c}])['on']
  self.assertIsNone(r['total_tokens']);self.assertFalse(r['accounting_complete'])
  c={'accounting_verified':True,'usage':{'input_tokens':100,'output_tokens':10},'wall_seconds':1}
  r=m.aggregate([{'arm':'off','accepted':True,'worker':c}])['off']
  self.assertIsNone(r['usage']['reasoning_output_tokens']);self.assertEqual(r['total_tokens'],110)
 def test_protected_file_integrity(self):
  with tempfile.TemporaryDirectory() as d:
   cwd=Path(d)/'fixture';expected=m.materialize(cwd,'ui');self.assertTrue(m.protected_ok(cwd,expected))
   (cwd/'src/automation.ts').write_text('edited');self.assertTrue(m.protected_ok(cwd,expected))
   (cwd/'run_tests.py').write_text('tampered');self.assertFalse(m.protected_ok(cwd,expected))
   self.assertEqual(m.check_tests(cwd,{},Path(d)/'result',expected)['exit'],97)
if __name__=='__main__':unittest.main()
