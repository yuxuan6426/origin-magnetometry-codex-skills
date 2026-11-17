"""Run the fixed upstream server against an owned external Origin instance."""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


def session_snapshot():
    """Read only PID/window-title identity; titles remain private runtime data."""
    pids = origin_pids()
    if os.name != 'nt':
        return {'pids': sorted(pids), 'windows': []}
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    windows = []
    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.EnumWindows.argtypes = [callback, wintypes.LPARAM]
    def visit(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids:
            length = user32.GetWindowTextLengthW(hwnd)
            if length:
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                windows.append([pid.value, buffer.value])
        return True
    user32.EnumWindows(callback(visit), 0)
    return {'pids': sorted(pids), 'windows': sorted(windows)}


def origin_pids():
    result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True, check=True)
    return {int(row[1]) for row in csv.reader(result.stdout.splitlines()) if row and row[0].lower().startswith('origin')}


def verified_endpoint(runtime):
    """Return a proven per-run endpoint without consulting shared defaults."""
    runtime = Path(runtime)
    handshake = json.loads((runtime / 'bridge.json').read_text(encoding='utf-8'))
    ownership = json.loads((runtime / 'ownership.json').read_text(encoding='utf-8'))
    if (ownership.get('ownership_verified') is not True
            or handshake.get('origin_pid') != ownership.get('owned_origin_pid')
            or handshake.get('host') != '127.0.0.1'
            or not handshake.get('token') or not handshake.get('generation')
            or not 0 < handshake.get('port', 0) < 65536):
        raise RuntimeError('Refusing cleanup through an unverified Origin endpoint.')
    return handshake


def shutdown_owned(runtime):
    """Use only an explicit, proven endpoint; never resolve shared defaults."""
    handshake = verified_endpoint(runtime)
    from origin_mcp.bridge_client import OriginBridgeClient, OriginBridgeConfig
    config = OriginBridgeConfig(host=handshake['host'], port=handshake['port'], token=handshake['token'],
                                generation=handshake['generation'], lease_id=handshake['lease_id'],
                                origin_pid=handshake['origin_pid'], handshake_managed=False, timeout=10)
    return OriginBridgeClient(config).request('shutdown', {'release_origin':True,'close_origin':True})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo / 'third_party/origin-mcp/src'))
    for key in list(os.environ):
        if key.startswith('ORIGIN_MCP_BRIDGE_'):
            os.environ.pop(key)
    os.environ['ORIGIN_MCP_BRIDGE_HANDSHAKE'] = str(runtime / 'bridge.json')
    os.environ['ORIGIN_MCP_BRIDGE_STATUS'] = str(runtime / 'status.json')
    from origin_mcp.origin_client import OriginClient
    from origin_mcp.bridge import OriginEmbeddedBridgeServer
    from origin_mcp.bridge_handshake import generate_token, generate_generation, write_handshake, clear_handshake
    before = origin_pids()
    client = OriginClient()
    op = client.op
    import originpro.config
    if not originpro.config.oext:
        raise RuntimeError('The owned adapter requires external OriginPro mode.')
    nonce = uuid.uuid4().hex
    probe = runtime / 'ownership-probe.json'
    code = runtime / 'ownership_probe.py'
    code.write_text('import os,json\nfrom pathlib import Path\nPath(' + repr(str(probe)) + ').write_text(json.dumps({"origin_pid":os.getpid(),"nonce":' + repr(nonce) + '}))\n', encoding='utf-8')
    if op.lt_exec('run -pyf "' + code.as_posix() + '";') is False:
        raise RuntimeError('Origin ownership probe did not execute.')
    observed = json.loads(probe.read_text(encoding='utf-8'))
    pid = observed['origin_pid']
    if observed['nonce'] != nonce or pid in before or pid not in origin_pids():
        # Do not close, clear or attach to an unowned instance.
        raise RuntimeError('Origin ownership could not be proven; no project operation was performed.')
    generation, token = generate_generation(), generate_token()
    server = OriginEmbeddedBridgeServer(('127.0.0.1', 0), token=token, client=client,
                                         generation=generation, lease_id=generation, origin_pid=pid)
    path = write_handshake('127.0.0.1', server.server_address[1], token,
                           path=runtime / 'bridge.json', generation=generation, lease_id=generation, origin_pid=pid)
    (runtime / 'ownership.json').write_text(json.dumps({'owned_origin_pid': pid, 'existing_origin_pids': sorted(before),
                                                     'adapter_pid': os.getpid(), 'ownership_verified': True}), encoding='utf-8')
    op.set_show(False)
    print(json.dumps({'ready': True, 'owned_origin_pid': pid}), flush=True)
    try:
        server.serve_forever(0.05)
    finally:
        server.server_close()
        clear_handshake(path=path)
        # This reference belongs only to the PID verified above.
        if pid in origin_pids():
            op.exit()


if __name__ == '__main__':
    main()
