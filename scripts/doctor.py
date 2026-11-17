"""Read-only environment and bundled-source checks. Does not connect to Origin."""
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = json.loads((ROOT / 'third_party/origin-mcp.provenance.json').read_text(encoding='utf-8'))
    failures = []
    for item in source['files']:
        path = ROOT / 'third_party/origin-mcp' / item['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            failures.append(item['path'])
    modules = {name: importlib.util.find_spec(name) is not None for name in ('openpyxl','PIL','pypdf','mcp','originpro','OriginExt')}
    packages = {}
    for name in ('openpyxl','Pillow','pypdf','mcp','originpro','OriginExt','pywin32'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    report = {'python':platform.python_version(),'platform':sys.platform,'packages':packages,
              'modules':modules,'upstream_commit':source['commit'],'source_integrity':'passed' if not failures else 'failed',
              'changed_source_files':failures,'origin_connection':'not_attempted'}
    print(json.dumps(report, indent=2))
    return 0 if not failures and all(modules.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
