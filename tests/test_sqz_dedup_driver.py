import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parents[1]/'harness'))
import sqz_dedup_benchmark as m

class DriverTests(unittest.TestCase):
    def test_fixed_flags_have_no_arm_parameter(self):
        a=m.flags(Path('/fixture'),'/shim:/usr/bin:/bin')
        self.assertEqual(a,m.flags(Path('/fixture'),'/shim:/usr/bin:/bin'))
        self.assertIn('features.hooks=false',a)
        self.assertNotIn('allow',str(a))

    def test_missing_accounting_not_zero(self):
        result=m.totals([{'arm':'off','accepted':False,'worker':{'accounting_verified':False,'usage':None}}])['off']
        self.assertIsNone(result['total_tokens'])
        self.assertFalse(result['accounting_complete'])

    def test_failed_attempts_stay_in_numerator(self):
        call={'accounting_verified':True,'usage':dict(input_tokens=100,cached_input_tokens=60,output_tokens=20,reasoning_output_tokens=10),'provider_requests':1,'wall_seconds':1}
        result=m.totals([{'arm':'on','accepted':True,'worker':call,'review':call},
                         {'arm':'on','accepted':False,'worker':call,'review':call}])['on']
        self.assertEqual(result['total_tokens'],480)
        self.assertEqual(result['tokens_per_accepted'],480)
        self.assertEqual(result['usage']['output_tokens'],80)

    def test_partial_row_can_be_saved(self):
        r=m.totals([{'arm':'off','accepted':False}])['off']
        self.assertEqual(r['attempts'],1)
        self.assertIsNone(r['total_tokens'])

    def test_fixture_commits_identical_and_extreme_case_frozen(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);env=m.environment(root/'home')
            for kind in ('cpp','ui'):
                a,sa=m.make_fixture(root/(kind+'-a'),kind,env)
                bb,sb=m.make_fixture(root/(kind+'-b'),kind,env)
                self.assertEqual(sa,sb)
                self.assertEqual(a,bb)
                self.assertEqual((root/(kind+'-a')/'AGENTS.md').read_text(),m.AGENTS)
                if kind=='cpp':self.assertIn('zero time opposite max finite',(root/(kind+'-a')/'tests/test.cpp').read_text())

if __name__=='__main__':unittest.main()
