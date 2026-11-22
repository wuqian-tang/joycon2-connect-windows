"""Smoke the real EXEs on a private port; never connect or acquire vJoy."""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
import queue
import re
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from joycon2_assistant.paths import VERSION


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--skip-bluetooth', action='store_true',
                        help='For CI without an adapter: still check EXE startup, HTTP and imports.')
    arguments = parser.parse_args()
    bundle = arguments.bundle.resolve()
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    with tempfile.TemporaryDirectory(prefix='joycon2-portable-check-') as runtime:
        env = dict(os.environ, JOYCON2_RUNTIME_DIR=runtime, PYTHONIOENCODING='utf-8')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        url = f'http://127.0.0.1:{port}'

        def request(path, token=None):
            headers = {'Content-Type': 'application/json', 'X-JC2-Token': token} if token else {}
            message = urllib.request.Request(url + path, data=b'{}' if token else None, headers=headers)
            with urllib.request.urlopen(message, timeout=3) as result:
                return result.read()

        token = None
        worker = None
        server_handle = None
        try:
            # The launching process must exit while its independent server stays up.
            launcher = subprocess.Popen([str(bundle / 'JoyCon2Assistant.exe'), '--port', str(port),
                                         '--no-browser'], env=env, creationflags=flags)
            if launcher.wait(timeout=25) != 0:
                raise AssertionError('Windowed launcher exited with an error')
            health = json.loads(request('/api/health'))
            # Keep the actual process alive as a waitable kernel object. The
            # identity file disappears before Python closes windowed log streams.
            server_handle = kernel.OpenProcess(0x00100000, False, health['pid'])  # SYNCHRONIZE
            if not server_handle:
                raise ctypes.WinError(ctypes.get_last_error())
            assert health['app'] == 'joycon2-local-assistant' and health['version'] == VERSION, health
            assert health['pid'] != launcher.pid
            page = request('/').decode('utf-8')
            # Find the server nonce by the token meta element, independent of layout.
            token_match = re.search(r'<meta\b[^>]*name=["\']request-token["\'][^>]*content=["\']([^"\']+)', page)
            if not token_match:
                token_match = re.search(r'<meta\b[^>]*name=["\']jc2-token["\'][^>]*content=["\']([^"\']+)', page)
            assert token_match, 'Request token meta element not found'
            token = token_match.group(1)
            state = json.loads(request('/api/status'))
            assert state['phase'] == 'idle' and not state['running']
            assert isinstance(state['environment']['driver_ready'], bool)
            for asset in ('/app.js', '/styles.css', '/i18n.js', '/sync-guide.svg', '/favicon.svg'):
                assert request(asset), asset
            check = subprocess.run([str(bundle / 'JoyCon2Worker.exe'), '--self-test'], env=env,
                                   capture_output=True, text=True, encoding='utf-8',
                                   timeout=20, creationflags=flags)
            assert check.returncode == 0, check.stderr + check.stdout
            assert json.loads(check.stdout)['ok'] is True
            if not arguments.skip_bluetooth:
                worker = subprocess.Popen([str(bundle / 'JoyCon2Worker.exe'), '--scan-only'], env=env,
                                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          text=True, encoding='utf-8', creationflags=flags)
                events = queue.Queue()

                def read_events():
                    for line in worker.stdout:
                        events.put(json.loads(line))
                    events.put({'event': 'worker_exit', 'details': worker.stderr.read()})
                threading.Thread(target=read_events, daemon=True).start()
                event = events.get(timeout=20)
                assert event == {'event': 'phase', 'phase': 'scanning_left'}, event
                worker.stdin.write('stop\n')
                worker.stdin.flush()
                event = events.get(timeout=10)
                assert event['event'] == 'stopped', event
                assert worker.wait(timeout=10) == 0
            print(json.dumps({'ok': True, 'version': health['version'], 'launcher_exited': True,
                              'server_survived': True, 'worker_imports': True,
                              'passive_scan_cancel': 'skipped (--skip-bluetooth)' if arguments.skip_bluetooth else True,
                              'driver': state['environment']}, ensure_ascii=False))
        finally:
            if worker is not None and worker.poll() is None:
                worker.terminate()
                worker.wait(timeout=5)
            try:
                if token:
                    request('/api/exit', token)
            finally:
                if server_handle:
                    try:
                        result = kernel.WaitForSingleObject(server_handle, 10000)
                        assert result == 0, f'Test server did not exit within 10 seconds (wait={result})'
                    finally:
                        kernel.CloseHandle(server_handle)
            if token:
                assert not (Path(runtime) / f'server-{port}.json').exists(), 'Test server left its identity file'
            for path in (Path(runtime) / 'launcher.log', Path(runtime) / 'server.log'):
                try:
                    contents = path.read_text(encoding='utf-8', errors='replace')
                except FileNotFoundError:
                    continue
                if contents:
                    print(contents, file=sys.stderr)


if __name__ == '__main__':
    main()
