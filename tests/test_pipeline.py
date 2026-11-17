import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/origin-mpms-import/scripts'))
sys.path.insert(0, str(ROOT / 'scripts'))
from mpms_core import parse_dat, segment, DataError, curve_values
from mpms_export import export_dataset
from audit_package import audit
from owned_origin_bridge import verified_endpoint


class PipelineTests(unittest.TestCase):
    def test_unowned_endpoint_is_rejected_before_any_connection(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp)
            (runtime / 'bridge.json').write_text(json.dumps({'host':'127.0.0.1','port':47631,'token':'example','generation':'example','origin_pid':2}))
            (runtime / 'ownership.json').write_text(json.dumps({'ownership_verified':True,'owned_origin_pid':1}))
            with self.assertRaises(RuntimeError):
                verified_endpoint(runtime)

    def test_all_case_exports_independent_audit(self):
        for job in json.loads((ROOT / 'cases/catalog.json').read_text()):
            with self.subTest(case=job['id']), tempfile.TemporaryDirectory() as temp:
                source = ROOT / job['input']
                data = parse_dat(source)
                curves = segment(data)
                output = Path(temp) / '中文 output'
                export_dataset(data, curves, job['mass_mg'], job['dc_source'], output)
                report = audit(source, output)
                for key, expected in job['expected'].items():
                    self.assertEqual(report[key], expected)
                with self.assertRaises(DataError):
                    export_dataset(data, curves, job['mass_mg'], job['dc_source'], output)

    def test_raw_mass_and_explicit_coverage(self):
        source = ROOT / 'cases/synthetic/input/measurement.dat'
        data = parse_dat(source)
        curves = segment(data)
        self.assertTrue(all(row[3] is None for row in curve_values(curves[0], None, 'fixed')))
        for mass in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(DataError):
                curve_values(curves[0],mass,'fixed')
        specs = [{'first_record':c.records[0].number,'last_record':c.records[-1].number,'category':c.category,'direction':c.direction} for c in curves]
        self.assertEqual(len(segment(data, overrides=specs)), len(curves))
        with self.assertRaises(DataError):
            segment(data, overrides=specs[:-1])

    def test_missing_mass_and_existing_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'new'
            command = [sys.executable,str(ROOT / 'scripts/reproduce.py'),'--input',str(ROOT / 'cases/synthetic/input/measurement.dat'),'--output',str(output),'--conversion-only']
            self.assertEqual(subprocess.run(command,capture_output=True).returncode,2)
            self.assertFalse(output.exists())
            output.mkdir()
            self.assertEqual(subprocess.run(command + ['--raw'],capture_output=True).returncode,2)

    def test_header_encoding_and_invalid_records(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / '编码 sample.dat'
            source.write_text('[Header]\nINFO,教学,SAMPLE\n[Data]\nMoment (emu),Magnetic Field (Oe),Temperature (K)\n0,1000,2\n1.2D-3,1000,3\n', encoding='gb18030')
            parsed = parse_dat(source)
            self.assertEqual(parsed.encoding, 'gb18030')
            self.assertEqual(parsed.records[0].moments['Moment (emu)'], 0)
            self.assertAlmostEqual(parsed.records[1].moments['Moment (emu)'], .0012)
            invalid = [
                '[Data]\nTemperature (K),Moment (emu)\n2,1\n',
                '[Data]\nTemperature (K),Temperature (K),Magnetic Field (Oe),Moment (emu)\n2,2,1,1\n',
                '[Data]\nTemperature (K),Magnetic Field (Oe),Moment (emu)\n2,1,\n',
                '[Data]\nTemperature (K),Magnetic Field (Oe),Moment (emu)\n2,1\n',
                '[Data]\nTemperature (K),Magnetic Field (Oe),Moment (emu)\nnan,1,2\n',
            ]
            for content in invalid:
                source.write_text(content, encoding='utf-8')
                with self.assertRaises(DataError):
                    parse_dat(source)


if __name__ == '__main__':
    unittest.main()
