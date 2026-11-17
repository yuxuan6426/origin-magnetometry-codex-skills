"""Check saved projects and embedded data at a different package location."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from reproduce import ROOT, origin_phase, save
from owned_origin_bridge import session_snapshot, shutdown_owned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packages', nargs='+', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error('Choose a new output directory.')
    output.mkdir(parents=True)
    runtime = output / '.runtime'
    runtime.mkdir()
    before = session_snapshot()
    report = {'status':'running','mode':'relocated_saved_project_readback','cases':[]}
    with (runtime / 'adapter.log').open('w', encoding='utf-8') as log:
        process = subprocess.Popen([sys.executable,str(ROOT / 'scripts/owned_origin_bridge.py'),'--runtime',str(runtime)],
                                   stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
            deadline = time.monotonic() + 120
            while not ((runtime / 'bridge.json').is_file() and (runtime / 'ownership.json').is_file()):
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError('Owned relocation-check adapter did not become ready.')
                time.sleep(.25)
            for package in args.packages:
                result = asyncio.run(origin_phase(package.resolve(),runtime,existing=True))
                report['cases'].append({'case':package.name,'origin':result})
                save(output / 'relocation-report.json',report)
            report['status'] = 'passed'
        finally:
            if process.poll() is None:
                try:
                    shutdown_owned(runtime)
                    process.wait(timeout=30)
                except Exception:
                    process.terminate()
                    process.wait(timeout=10)
            after = session_snapshot()
            ids = set(before['pids'])
            report['session_protection'] = {'preexisting_processes_preserved':ids.issubset(after['pids']),
                                            'preexisting_window_titles_unchanged':before['windows']==[w for w in after['windows'] if w[0] in ids],
                                            'preexisting_windows_observed':len(before['windows']),
                                            'owned_adapter_exited':process.poll() is not None}
            save(output / 'relocation-report.json',report)
    print(json.dumps({'status':report['status'],'projects':len(report['cases'])}))


if __name__ == '__main__':
    main()
