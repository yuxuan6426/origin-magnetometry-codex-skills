"""Independent audit of saved files, using only the DAT and package manifest."""
import csv
import hashlib
import json
import math
from pathlib import Path
from openpyxl import load_workbook


def audit(source, package):
    source, package = Path(source), Path(package)
    raw = source.read_bytes()
    for encoding in ('utf-8-sig', 'gb18030'):
        try:
            lines = raw.decode(encoding).splitlines()
            break
        except UnicodeDecodeError:
            continue
    start = next(i for i, line in enumerate(lines) if line.strip().lower() == '[data]')
    reader = csv.reader(lines[start + 1:])
    headers = next(reader)
    rows, physical_lines = [], []
    for values in reader:
        if any(value.strip() for value in values):
            rows.append(dict(zip(headers, values)))
            physical_lines.append(start + 1 + reader.line_num)
    manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['source_sha256'] == hashlib.sha256(raw).hexdigest()
    assert len(rows) == manifest['record_count']
    mass = manifest['sample_mass_mg']
    def number(value):
        return float(value.replace('D', 'E').replace('d', 'e'))
    covered, expected_by_id = [], {}
    maxima = {'csv': 0.0, 'per_curve.xlsx': 0.0, 'wide.xlsx': 0.0}
    for curve in manifest['curves']:
        first, last = curve['first_record'], curve['last_record']
        covered.extend(range(first, last + 1))
        expected = []
        for row in rows[first - 1:last]:
            moment = number(row[curve['moment_source']])
            expected.append([number(row['Temperature (K)']), number(row['Magnetic Field (Oe)']), moment,
                             moment / mass * 1000 if mass is not None else None])
        expected_by_id[curve['id']] = expected
        with (package / curve['csv']).open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.reader(stream)
            next(reader)
            actual = [[float(v) if v else None for v in row] for row in reader]
        assert actual == expected, curve['id']
        assert len(expected) == curve['points']
    assert covered == list(range(1, len(rows) + 1))
    def check(actual, expected, kind):
        assert len(actual) == len(expected)
        for a, b in zip(actual, expected):
            if b is None:
                assert a is None
            else:
                assert isinstance(a, (float, int)) and math.isclose(a, b, rel_tol=2e-12, abs_tol=1e-12), (kind, a, b)
                maxima[kind] = max(maxima[kind], abs(a - b))
    per = load_workbook(package / 'per_curve.xlsx', data_only=True, read_only=True)
    wide = load_workbook(package / 'wide.xlsx', data_only=True, read_only=True)
    for curve in manifest['curves']:
        actual = list(per[curve['id']].iter_rows(min_row=4, values_only=True))
        expected = expected_by_id[curve['id']]
        assert len(actual) == len(expected)
        for a, b in zip(actual, expected):
            check(a, b, 'per_curve.xlsx')
    for category in {c['category'] for c in manifest['curves']}:
        curves = [c for c in manifest['curves'] if c['category'] == category]
        for i, row in enumerate(wide[category].iter_rows(min_row=4, values_only=True)):
            for j, curve in enumerate(curves):
                values = expected_by_id[curve['id']]
                expected = [values[i][0 if category == 'MT' else 1], values[i][2], values[i][3]] if i < len(values) else [None] * 3
                check(row[j * 3:j * 3 + 3], expected, 'wide.xlsx')
    per.close()
    wide.close()
    with (package / 'source_rows.csv').open(encoding='utf-8-sig') as stream:
        trace = list(csv.DictReader(stream))
    assert [int(r['source_record']) for r in trace] == covered
    for row in trace:
        assert int(row['source_physical_line']) == physical_lines[int(row['source_record']) - 1]
    return {'status': 'passed', 'records': len(rows), 'curves': len(manifest['curves']),
            'max_absolute_error': maxima, 'source_sha256': manifest['source_sha256']}
