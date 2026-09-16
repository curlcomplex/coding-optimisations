import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('sqz_layer', Path(__file__).parents[1]/'harness/sqz_layer.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
DATA = b'coefficient 0.000125 expected actual edge case\n'*60


class LayerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rollout = self.root/'rollout.jsonl'
        self.cfg = dict(enabled=True, sqz='/fake/sqz', sqz_home=str(self.root/'home'),
                        rollout=str(self.rollout), audit=str(self.root/'audit.jsonl'))

    def write_output(self, output, suffix=None):
        rows = [{'type':'response_item','payload':{'type':'function_call_output','output':output}}]
        if suffix:
            rows += suffix
        self.rollout.write_text(''.join(json.dumps(e)+'\n' for e in rows))

    def apply(self, output, code=0):
        fake = subprocess.CompletedProcess([], code, output, b'')
        with patch.object(m.subprocess,'run',return_value=fake) as call:
            result = m.filter_stdout(DATA,self.cfg)
        return result,call

    def test_disabled_never_calls_candidate(self):
        self.cfg['enabled']=False
        (out,row),call=self.apply(b'ignored')
        self.assertEqual(out,DATA);call.assert_not_called()

    def test_first_result_always_exact_not_lossy(self):
        (out,row),_=self.apply(b'omitted coefficient')
        self.assertEqual(out,DATA);self.assertFalse(row['dedup_hit'])

    def test_ref_without_delivery_rejected(self):
        (out,row),_=self.apply(('§ref:'+m.digest(DATA)[:16]+'§').encode())
        self.assertEqual(out,DATA);self.assertFalse(row['dedup_hit'])

    def test_real_ref_requires_matching_content_hash(self):
        self.write_output(DATA.decode())
        (out,row),_=self.apply('§ref:0000000000000000§'.encode())
        self.assertEqual(out,DATA)

    def test_verified_repeat_compressed_and_recoverable(self):
        self.write_output(DATA.decode())
        (out,row),call=self.apply(('§ref:'+m.digest(DATA)[:16]+'§').encode())
        self.assertIn(b'sqz expand ',out);self.assertTrue(row['dedup_hit'])
        self.assertLess(len(out),len(DATA))
        self.assertEqual(call.call_args.kwargs['input'],DATA)
        self.assertNotIn('--no-cache',call.call_args.args[0])

    def test_truncated_initial_delivery_rejected(self):
        self.write_output(DATA[:200].decode())
        (out,row),_=self.apply(('§ref:'+m.digest(DATA)[:16]+'§').encode())
        self.assertEqual(out,DATA)

    def test_code_mode_nested_result_counted(self):
        self.write_output(json.dumps({'content':[{'text':DATA.decode()}]}))
        self.assertTrue(m.delivered(DATA,self.rollout))

    def test_user_prompt_not_tool_delivery(self):
        self.rollout.write_text(json.dumps({'type':'response_item','payload':{'type':'message','output':DATA.decode()}})+'\n')
        self.assertFalse(m.delivered(DATA,self.rollout))

    def test_compaction_invalidates_previous_delivery(self):
        self.write_output(DATA.decode(),[{'type':'compacted','payload':{}}])
        self.assertFalse(m.delivered(DATA,self.rollout))

    def test_role_has_no_cross_session_delivery(self):
        self.write_output(DATA.decode())
        self.assertFalse(m.delivered(DATA,self.root/'fresh-review.jsonl'))

    def test_invalid_utf8_passthrough(self):
        with patch.object(m.subprocess,'run') as call:
            out,row=m.filter_stdout(b'\xff'*1500,self.cfg)
        self.assertEqual(out,b'\xff'*1500);call.assert_not_called()

    def test_small_passthrough(self):
        with patch.object(m.subprocess,'run') as call:
            out,row=m.filter_stdout(b'ok\n',self.cfg)
        self.assertEqual(out,b'ok\n');call.assert_not_called()

    def test_compressor_failure_returns_original(self):
        (out,row),_=self.apply(b'bad',code=2)
        self.assertEqual(out,DATA)

    def test_timeout_returns_original(self):
        with patch.object(m.subprocess,'run',side_effect=subprocess.TimeoutExpired('sqz',8)):
            out,row=m.filter_stdout(DATA,self.cfg)
        self.assertEqual(out,DATA);self.assertEqual(row['reason'],'sqz-fallback')

    def test_partial_rollout_line_is_not_evidence(self):
        self.rollout.write_text('{"partial":')
        self.assertFalse(m.delivered(DATA,self.rollout))

    def test_subprocess_has_no_api_credentials(self):
        with patch.dict(m.os.environ,{'OPENAI_API_KEY':'not-real','GH_TOKEN':'not-real'}):
            env=m.sqz_environment(self.cfg)
        self.assertNotIn('OPENAI_API_KEY',env);self.assertNotIn('GH_TOKEN',env)
        self.assertEqual(env['SQZ_DB_PATH'],str(self.root/'home/sessions.db'))

    def test_metadata_stderr_is_not_returned_as_model_output(self):
        fake=subprocess.CompletedProcess([],0,b'compressed',b'sqz analytics metadata')
        with patch.object(m.subprocess,'run',return_value=fake):out,row=m.filter_stdout(DATA,self.cfg)
        self.assertEqual(out,DATA);self.assertNotIn(b'metadata',out)

if __name__=='__main__':unittest.main()
