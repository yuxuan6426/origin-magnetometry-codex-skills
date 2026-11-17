"""Reproduce MPMS conversion and Origin plots from a fresh, owned session."""
import argparse
import asyncio
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import platform
from datetime import timedelta
from audit_package import audit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/origin-mpms-import/scripts'))
from mpms_core import parse_dat, segment
from mpms_export import export_dataset


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def payload(result):
    data = result.structuredContent
    if not isinstance(data, dict):
        data = json.loads('\n'.join(c.text for c in result.content if c.type == 'text'))
    if result.isError or data.get('ok') is False:
        raise RuntimeError(data)
    return data.get('data', data)


async def origin_phase(package, runtime, existing=False):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from owned_origin_bridge import verified_endpoint
    endpoint = verified_endpoint(runtime)
    env = {k: v for k, v in os.environ.items() if not k.startswith('ORIGIN_MCP_BRIDGE_')}
    env.update(PYTHONUTF8='1', ORIGIN_MCP_TOOL_PROFILE='full',
               ORIGIN_MCP_BRIDGE_HANDSHAKE=str(runtime / 'bridge.json'),
               ORIGIN_MCP_BRIDGE_HOST=endpoint['host'], ORIGIN_MCP_BRIDGE_PORT=str(endpoint['port']),
               ORIGIN_MCP_BRIDGE_TOKEN=endpoint['token'],
               PYTHONPATH=str(ROOT / 'third_party/origin-mcp/src'))
    manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
    report = {'status': 'running', 'curves': [], 'graphs': [], 'exports': []}
    with (runtime / 'mcp.stderr.log').open('w', encoding='utf-8') as err:
        async with stdio_client(StdioServerParameters(command=sys.executable, args=['-m', 'origin_mcp'], env=env), errlog=err) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=180)) as client:
                await client.initialize()
                async def call(name, args):
                    return payload(await client.call_tool(name, args))
                connection = await call('origin_ping', {'show':False})
                report['runtime'] = {'origin_version':connection.get('origin_version'), 'python':platform.python_version(), 'platform':sys.platform}
                await call('origin_new_project', {'show': False})
                ogs = str(package / 'import_and_plot.ogs').replace('/', '\\')
                if existing:
                    await call('origin_run_labtalk', {'script':f'string mpmsRoot$="{package.as_posix()}";'})
                else:
                    result = await call('origin_run_labtalk', {'script':f'string mpmsRoot$="{package.as_posix()}"; run.section("{ogs}", Import);', 'capture_log': True})
                    assert result['result'] and any('plotting complete' in line for line in result['message_log']['lines']), result
                groups = {}
                for curve in manifest['curves']:
                    groups.setdefault((curve['category'], curve['mode']), []).append(curve)
                # Position long legends after Origin has instantiated every graph.
                for i, curves in enumerate(groups.values(), 1):
                    if not existing and len(curves) > 6:
                        limits = [c['temperature_range_K'] if c['category'] == 'MT' else c['field_range_Oe'] for c in curves]
                        span = max(pair[1] for pair in limits) - min(pair[0] for pair in limits)
                        if span > 0:
                            desired = span / 4
                            scale = 10 ** math.floor(math.log10(desired))
                            step = next(value * scale for value in (1,2,5,10) if value * scale >= desired)
                            await call('origin_set_axis', {'graph_name':f'G{i:03d}', 'axis':'x', 'step':step})
                        await call('origin_run_labtalk', {'script':f'win -a G{i:03d}; legend.attach=2; legend.x=layer.x.to+(layer.x.to-layer.x.from)*0.25; legend.y=(layer.y.from+layer.y.to)/2;', 'capture_log':True})
                project = package / 'origin_result.opju'
                if not existing:
                    await call('origin_save_project', {'path':str(project)})
                await call('origin_new_project', {'show':False})
                await call('origin_open_project', {'path':str(project), 'asksave':False})
                import csv
                for curve in manifest['curves']:
                    with (package / curve['csv']).open(encoding='utf-8-sig') as stream:
                        reader = csv.reader(stream)
                        next(reader)
                        expected = [[float(v) if v else None for v in row] for row in reader]
                    columns = [0,1,2,3] if manifest['sample_mass_mg'] is not None else [0,1,2]
                    # Raw packages deliberately leave the normalization column empty.
                    # OriginExt omits a wholly empty trailing column from its data block.
                    if manifest['sample_mass_mg'] is None:
                        expected = [row[:3] for row in expected]
                    data = await call('origin_read_worksheet', {'book_name':'MPMSData', 'sheet_name':curve['id'], 'max_rows':max(10000, len(expected)), 'columns':columns})
                    actual = [[row[k] for k in data['columns']] for row in data['rows']]
                    assert len(actual) == len(expected) == data['total_rows']
                    max_error = 0
                    for a, b in zip(actual, expected):
                        for value, wanted in zip(a, b):
                            if wanted is None:
                                assert value is None
                            else:
                                assert isinstance(value, (int,float)) and math.isclose(value, wanted, rel_tol=2e-11, abs_tol=1e-11), (curve['id'], value, wanted)
                                max_error = max(max_error, abs(value-wanted))
                    report['curves'].append({'id':curve['id'], 'rows':len(expected), 'columns':columns, 'max_absolute_error':max_error})
                specs = [(f'P{i:03d}', c['category'], 1) for i,c in enumerate(manifest['curves'],1)]
                specs += [(f'G{i:03d}', category, len(curves)) for i,((category,mode),curves) in enumerate(groups.items(),1)]
                ylabel = 'Magnetization (emu/g)' if manifest['sample_mass_mg'] is not None else 'Moment (emu)'
                for name, category, count in specs:
                    data = await call('origin_get_graph_info', {'graph_name':name})
                    assert data['layers_count'] == 1 and data['layers'][0]['plots_count'] == count
                    axes = data['layers'][0]['axes']
                    assert axes['x']['title'] == ('Temperature (K)' if category == 'MT' else 'Magnetic Field (Oe)')
                    assert axes['y']['title'] == ylabel
                    report['graphs'].append({'name':name,'plots':count,'category':category})
                export = package / 'exports'
                for ext in ('png','pdf'):
                    if existing:
                        count = len(list(export.glob('*.' + ext)))
                    else:
                        result = await call('origin_export_all_graphs', {'output_dir':str(export), 'file_type':ext, 'overwrite':False, 'width':1600 if ext == 'png' else 0})
                        count = result['count']
                    assert count == len(specs)
                    report['exports'].append({'format':ext, 'count':count})
                from PIL import Image
                from pypdf import PdfReader
                for name, _, _ in specs:
                    with Image.open(export / (name + '.png')) as image:
                        image.load()
                        assert image.width == 1600 and image.convert('L').getextrema()[1] - image.convert('L').getextrema()[0] > 50
                    assert len(PdfReader(export / (name + '.pdf')).pages) == 1
                stamp = project.stat().st_mtime_ns
                result = await call('origin_run_labtalk', {'script':f'run.section("{ogs}", Import);', 'capture_log':True})
                assert any('empty Origin project' in line for line in result['message_log']['lines'])
                await call('origin_new_project', {'show':False})
                result = await call('origin_run_labtalk', {'script':f'run.section("{ogs}", Import);', 'capture_log':True})
                assert any('already exists' in line for line in result['message_log']['lines'])
                assert project.stat().st_mtime_ns == stamp
                report.update(status='passed', project_saved_reopened=not existing, protection_guards='passed', project_bytes=project.stat().st_size)
                if existing:
                    report['relocated_project_opened_without_saving'] = True
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['all','synthetic','real-0p5mg','real-24mg'])
    parser.add_argument('--input', type=Path)
    mass = parser.add_mutually_exclusive_group()
    mass.add_argument('--mass-mg', type=float)
    mass.add_argument('--raw', action='store_true')
    parser.add_argument('--dc-source', choices=['fixed','free'], default='fixed')
    parser.add_argument('--segments', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--conversion-only', action='store_true')
    args = parser.parse_args()
    if bool(args.case) == bool(args.input):
        parser.error('Choose --case or --input.')
    if args.case and (args.mass_mg is not None or args.raw or args.dc_source != 'fixed' or args.segments):
        parser.error('Named cases use their catalog settings. Use --input to supply custom conditions.')
    if args.input and not args.raw and args.mass_mg is None:
        parser.error('Provide --mass-mg or --raw for a custom input.')
    if args.mass_mg is not None and (not math.isfinite(args.mass_mg) or args.mass_mg <= 0):
        parser.error('Sample mass must be finite and positive.')
    output = args.output.resolve()
    if output.exists():
        parser.error('Choose a new output directory.')
    if args.case:
        catalog = json.loads((ROOT / 'cases/catalog.json').read_text(encoding='utf-8'))
        jobs = catalog if args.case == 'all' else [job for job in catalog if job['id'] == args.case]
    else:
        jobs = [{'id':'custom', 'input':str(args.input.resolve()), 'mass_mg':args.mass_mg, 'raw':args.raw, 'dc_source':args.dc_source}]
    if any(not (ROOT / job['input']).is_file() for job in jobs):
        parser.error('An input file is missing.')
    output.mkdir(parents=True)
    reports, bridge, existing_sessions = [], None, None
    runtime = output / '.runtime'
    try:
        if not args.conversion_only:
            from owned_origin_bridge import session_snapshot
            existing_sessions = session_snapshot()
            runtime.mkdir()
            save(runtime / 'existing-sessions-before.json', existing_sessions)
            log = (runtime / 'adapter.log').open('w', encoding='utf-8')
            bridge = subprocess.Popen([sys.executable,str(ROOT / 'scripts/owned_origin_bridge.py'),'--runtime',str(runtime)], stdout=log, stderr=log,
                                      creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            deadline = time.monotonic() + 120
            while not ((runtime / 'bridge.json').exists() and (runtime / 'ownership.json').exists()):
                if bridge.poll() is not None:
                    raise RuntimeError('Owned Origin adapter stopped. See the private .runtime/adapter.log.')
                if time.monotonic() > deadline:
                    raise TimeoutError('Owned Origin startup timed out.')
                time.sleep(0.25)
        for job in jobs:
            source = ROOT / job['input']
            data = parse_dat(source)
            overrides = json.loads(args.segments.read_text(encoding='utf-8-sig')) if args.segments else None
            curves = segment(data, overrides=overrides)
            package = output / job['id']
            export_dataset(data, curves, None if job.get('raw') else job.get('mass_mg'), job.get('dc_source','fixed'), package)
            report = {'case':job['id'], 'conversion':audit(source,package)}
            for key, expected in job.get('expected',{}).items():
                assert report['conversion'][key] == expected
            save(package / 'independent-audit.json', report['conversion'])
            if args.conversion_only:
                report['origin'] = {'status':'not_run'}
            else:
                report['origin'] = asyncio.run(origin_phase(package,runtime))
                save(package / 'origin-validation.json', report['origin'])
            reports.append(report)
            save(output / 'run-report.json', {'status':'running','cases':reports})
            print(json.dumps({'case':job['id'],'conversion':'passed','origin':report['origin']['status']}), flush=True)
        save(output / 'run-report.json', {'status':'passed','mode':'conversion' if args.conversion_only else 'end_to_end',
                                        'runtime':{'python':platform.python_version(),'platform':sys.platform}, 'cases':reports})
        return 0
    except Exception as exc:
        import traceback
        runtime.mkdir(exist_ok=True)
        (runtime / 'failure.log').write_text(traceback.format_exc(), encoding='utf-8')
        def describe(error):
            nested = getattr(error, 'exceptions', None)
            return '; '.join(describe(item) for item in nested) if nested else f'{type(error).__name__}: {error}'
        message = describe(exc)
        save(output / 'run-report.json', {'status':'failed','error':message,'cases':reports})
        print(message, file=sys.stderr)
        return 1
    finally:
        if bridge is not None and bridge.poll() is None:
            try:
                from owned_origin_bridge import shutdown_owned
                shutdown_owned(runtime)
                bridge.wait(timeout=30)
            except Exception:
                # Terminate this owned adapter only; never kill Origin by image name.
                bridge.terminate()
                bridge.wait(timeout=10)
        if bridge is not None:
            log.close()
        if existing_sessions is not None:
            after = session_snapshot()
            existing_ids = set(existing_sessions['pids'])
            protection = {'preexisting_processes_preserved': existing_ids.issubset(after['pids']),
                          'preexisting_window_titles_unchanged': existing_sessions['windows'] == [w for w in after['windows'] if w[0] in existing_ids],
                          'preexisting_windows_observed':len(existing_sessions['windows']),
                          'owned_adapter_exited': bridge is not None and bridge.poll() is not None}
            report_path = output / 'run-report.json'
            current = json.loads(report_path.read_text(encoding='utf-8'))
            current['session_protection'] = protection
            save(report_path, current)


if __name__ == '__main__':
    raise SystemExit(main())
