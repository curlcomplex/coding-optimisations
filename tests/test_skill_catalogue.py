import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'harness'))
import skill_catalogue as s


def trace(records, identity='thread'):
    rows=[{'type':'session_meta','payload':{'id':identity}},
          {'type':'turn_context','payload':{'model':s.MODEL}}]
    for last,total in records:
        rows.append({'type':'event_msg','payload':{'type':'token_count','info':{'last_token_usage':last,'total_token_usage':total}}})
    return ('\n'.join(map(json.dumps,rows))+'\n').encode()


def u(i,o,c=0):
    return {'input_tokens':i,'output_tokens':o,'cached_input_tokens':c}


class CatalogueTests(unittest.TestCase):
    def test_cached_is_subset(self):
        self.assertEqual(s.counters(u(100,5,90))['input_tokens'],100)

    def test_invalid_counters(self):
        for value in (u(True,5),u(-1,5),u(2,3,4),u(1,2.5),None,{}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                s.counters(value)

    def test_two_requests_and_quota_duplicate(self):
        first,second,total=u(100,5),u(110,6,90),u(210,11,90)
        result=s.rollout_usage(trace([(first,first),(first,first),(second,total)]),'thread')
        self.assertEqual(result['requests'],[first,second])
        self.assertEqual(result['total'],total)

    def test_reject_wrong_identity(self):
        with self.assertRaises(ValueError):
            s.rollout_usage(trace([(u(1,2),u(1,2))]),'other')

    def test_reject_cumulative_as_increment(self):
        with self.assertRaises(ValueError):
            s.rollout_usage(trace([(u(100,5),u(100,5)),(u(210,11),u(210,11))]),'thread')

    def test_reject_malformed(self):
        with self.assertRaises(ValueError):
            s.rollout_usage(b'{broken','thread')

    def test_unknown_is_not_zero(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertFalse(s.inspect_rollout(Path(t),'a'*36)['verified'])

    def test_canary_in_body_not_description(self):
        with tempfile.TemporaryDirectory() as t:
            name,marker=s.make_skill_workspace(Path(t)/'workspace')
            text=(Path(t)/'workspace/.agents/skills'/name/'SKILL.md').read_text()
            self.assertNotIn(marker,text.split('---')[1])
            self.assertIn(marker,text.split('---')[2])
            self.assertNotIn(marker,s.SMOKE)

    def test_each_canary_unpredictable_and_distinct(self):
        with tempfile.TemporaryDirectory() as t:
            _,a=s.make_skill_workspace(Path(t)/'a')
            _,b=s.make_skill_workspace(Path(t)/'b')
            self.assertNotEqual(a,b)

    def test_incomplete_or_failed_matrix_rejected(self):
        self.assertFalse(s.comparison([])['valid'])
        self.assertFalse(s.comparison([{'passed':False}]*5)['valid'])

    def test_first_and_turn_metrics_are_separate(self):
        rows=[]
        for include in (True,False,True,False,True):
            x=100 if include else 60
            rows.append({'passed':True,'include_instructions':include,
                         'turn_usage':{'input_tokens':x*2+10},'request_accounting_verified':True,
                         'request_usage':[{'input_tokens':x}]})
        result=s.comparison(rows)
        self.assertEqual(result['first_request_input']['reduction_percent'],40)
        self.assertNotEqual(result['turn_input']['reduction_percent'],40)
        self.assertEqual(result['first_request_input']['catalogue_on']['n'],3)
        rows[0]['request_accounting_verified']=False
        self.assertIsNone(s.comparison(rows)['first_request_input'])


if __name__=='__main__':
    unittest.main()
