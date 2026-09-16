import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('rtk_driver', Path(__file__).parents[1]/'harness/rtk_fidelity.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def result(out=b''):
    return dict(stdout=out, stderr=b'', code=0, timeout=False, wall_ms=1)


class DriverTests(unittest.TestCase):
    def test_complete_driver_keeps_binary_and_arm_storage_separate(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d); live=base/'live';live.mkdir()
            lab=base/'lab';(lab/'.codex').mkdir(parents=True)
            (lab/'.codex/config.toml').write_text('[skills]\ninclude_instructions=false\n')
            installed=base/'installed';installed.write_bytes(b'installed')
            def extract(data,dest):
                p=dest/'rtk';p.write_bytes(b'candidate');return p
            def fake_run(argv,cwd,env,timeout=15):
                if argv[-1]=='--version':
                    return result(('rtk 0.1.0\n' if argv[0]==str(installed) else 'rtk 0.49.0\n').encode())
                return result(('Config: '+env['HOME']+'/Library/Application Support/rtk/config.toml\n').encode())
            with patch.object(sys,'argv',['rtk_fidelity','--output',str(base/'out'),'--installed-rtk',str(installed)]), patch.object(m.platform,'system',return_value='Darwin'), patch.object(m.platform,'machine',return_value='arm64'), patch.object(m.Path,'home',return_value=live), patch.object(m,'__file__',str(lab/'harness/rtk_fidelity.py')), patch.object(m.urllib.request,'urlopen',return_value=io.BytesIO(b'archive')), patch.object(m,'extract_binary',side_effect=extract), patch.object(m,'run',side_effect=fake_run), patch.object(m,'check_case',return_value={'pass':True}), patch.object(m,'git_cases',return_value=[]), patch('builtins.print'):
                try:self.assertEqual(m.main(),0)
                finally:m.DEADLINE=0
            self.assertTrue((base/'out/candidate-bin/rtk').is_file())
            self.assertTrue((base/'out/candidate/home').is_dir())


if __name__=='__main__':unittest.main()
