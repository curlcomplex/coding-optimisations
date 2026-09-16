import importlib.util
import io
import os
from pathlib import Path
import tarfile
import tempfile
import tomllib
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('rtk_fidelity', Path(__file__).parents[1]/'harness/rtk_fidelity.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def result(out=b'', err=b'', code=0, timeout=False):
    return dict(stdout=out,stderr=err,code=code,timeout=timeout,wall_ms=1)


class FidelityTests(unittest.TestCase):
    def test_toml_roundtrip(self):
        obj={'display':{'colors':False,'max_width':80},'hooks':{'exclude_commands':['foo','ü']},'a':7}
        self.assertEqual(tomllib.loads(m.toml(obj)),obj)

    def test_unsafe_value_rejected(self):
        with self.assertRaises(ValueError): m.scalar(None)

    def test_live_config_not_mutated(self):
        cfg={'tee':{'directory':'/private','mode':'always'},'retriever':{'mode':'tee','database_path':'/private'},'limits':{'diff_max_lines':150}}
        normalized=m.isolated_config(cfg)
        self.assertEqual(cfg['retriever']['database_path'],'/private')
        self.assertNotIn('database_path',normalized['retriever'])
        self.assertNotIn('directory',normalized['tee'])
        self.assertEqual(normalized['retriever']['mode'],'tee')
        self.assertEqual(normalized['limits'],cfg['limits'])
        self.assertFalse(normalized['tracking']['enabled'])
        self.assertFalse(normalized['telemetry']['enabled'])

    def test_no_new_recovery_mode(self):
        cfg=m.isolated_config({'tee':{'mode':'always'}})
        self.assertNotIn('retriever',cfg)

    def test_environment_no_credentials(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'OPENAI_API_KEY':'fake','GH_TOKEN':'fake'}):
            env=m.environment(Path(d))
        self.assertNotIn('OPENAI_API_KEY',env)
        self.assertNotIn('GH_TOKEN',env)
        self.assertEqual(env['RTK_TELEMETRY_DISABLED'],'1')

    def test_archive_digest_enforced(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): m.extract_binary(b'invalid',Path(d))

    def test_archive_member_never_extracts_path(self):
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode='w:gz') as t:
            x=tarfile.TarInfo('../../rtk'); x.size=3; t.addfile(x,io.BytesIO(b'bin'))
        with tempfile.TemporaryDirectory() as d, patch.object(m,'DIGEST',m.sha(stream.getvalue())):
            binary=m.extract_binary(stream.getvalue(),Path(d))
            self.assertEqual(binary,Path(d)/'rtk')
            self.assertEqual(binary.read_bytes(),b'bin')

    def test_archive_symlink_rejected(self):
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode='w:gz') as t:
            x=tarfile.TarInfo('rtk'); x.type=tarfile.SYMTYPE; x.linkname='/etc/passwd'; t.addfile(x)
        with tempfile.TemporaryDirectory() as d, patch.object(m,'DIGEST',m.sha(stream.getvalue())):
            with self.assertRaises(ValueError):m.extract_binary(stream.getvalue(),Path(d))

    def evaluate(self, outputs):
        case={'name':'test','wrapper':'err','exit':17,'text':'error SENTINEL\n','facts':['SENTINEL']}
        with tempfile.TemporaryDirectory() as d,patch.object(m,'run',side_effect=outputs):
            return m.check_case(Path('/fake-rtk'),case,Path(d),{},Path(d))

    def test_exact_exit_and_facts_pass(self):
        self.assertTrue(self.evaluate([result(code=17),result(b'error SENTINEL\n',code=17)])['pass'])

    def test_collapsed_exit_fails(self):
        self.assertFalse(self.evaluate([result(code=17),result(b'SENTINEL',code=1)])['pass'])

    def test_missing_fact_fails(self):
        self.assertFalse(self.evaluate([result(code=17),result(b'error',code=17)])['pass'])

    def test_timeout_never_passes(self):
        self.assertFalse(self.evaluate([result(code=17),result(b'SENTINEL',code=17,timeout=True)])['pass'])

    def test_exact_recall_passes_but_marks_hidden_fact(self):
        row=self.evaluate([result(code=17),result(b'rtk recall abcdef123456',code=17),result(b'error SENTINEL\n')])
        self.assertTrue(row['pass']);self.assertEqual(row['missing_inline'],['SENTINEL'])

    def test_partial_recall_fails(self):
        self.assertFalse(self.evaluate([result(code=17),result(b'rtk recall abcdef123456',code=17),result(b'SENTINEL')])['pass'])

    def test_nonzero_recall_fails(self):
        self.assertFalse(self.evaluate([result(code=17),result(b'rtk recall abcdef123456',code=17),result(b'error SENTINEL\n',code=1)])['pass'])

    def test_owned_timeout(self):
        import sys
        with tempfile.TemporaryDirectory() as d:
            row=m.run([sys.executable,'-c','import time;time.sleep(5)'],Path(d),m.environment(Path(d)),timeout=.05)
        self.assertTrue(row['timeout']); self.assertNotEqual(row['code'],0)

    def test_fixture_count(self):
        self.assertEqual(len(m.fixture_cases()),6)


if __name__=='__main__': unittest.main()
