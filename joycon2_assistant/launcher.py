"""Desktop entry point: reuse an existing server and open the default browser."""
import ctypes
import json
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
import webbrowser

from .paths import APP_DIR, APP_ID, PORT, RUNTIME_DIR, SERVER_COMMAND, VERSION

URL = f'http://127.0.0.1:{PORT}'


def healthy(url=URL):
    try:
        with urllib.request.urlopen(url + '/api/health', timeout=0.8) as response:
            state = json.load(response)
            return state.get('app') == APP_ID and state.get('version') == VERSION
    except (OSError, ValueError, urllib.error.URLError):
        return False


def main(port=PORT, open_browser=True):
    url = f'http://127.0.0.1:{port}'
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    kernel.ReleaseMutex.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    mutex = kernel.CreateMutexW(None, False, f'Local\\JoyCon2WebLauncher-{port}')
    if not mutex:
        raise OSError('无法初始化启动锁')
    acquired = False
    try:
        result = kernel.WaitForSingleObject(mutex, 15000)
        if result not in (0, 0x80):
            raise TimeoutError('另一次启动仍在进行，请稍后再试')
        acquired = True
        if not healthy(url):
            with (RUNTIME_DIR / 'server.log').open('a', encoding='utf-8') as log:
                process = subprocess.Popen(
                    [*SERVER_COMMAND, '--port', str(port)], cwd=APP_DIR,
                    stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
                    close_fds=True,
                )
            for _ in range(60):
                if healthy(url):
                    break
                if process.poll() is not None:
                    raise RuntimeError(f'连接服务未能启动，端口可能已被其他程序占用。详情在 {RUNTIME_DIR / "server.log"}')
                time.sleep(0.15)
            else:
                raise TimeoutError('连接服务启动超时，请稍后重试')
    finally:
        if acquired:
            kernel.ReleaseMutex(mutex)
        kernel.CloseHandle(mutex)
    if open_browser:
        webbrowser.open(url + '/', new=2)


def cli():
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--port', type=int, default=PORT)
        parser.add_argument('--no-browser', action='store_true')
        arguments = parser.parse_args()
        main(arguments.port, not arguments.no_browser)
    except Exception as exc:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        with (RUNTIME_DIR / 'launcher.log').open('a', encoding='utf-8') as log:
            traceback.print_exc(file=log)
        ctypes.windll.user32.MessageBoxW(None, str(exc), 'Joy-Con 2 连接助手', 0x10)
        sys.exit(1)


if __name__ == '__main__':
    cli()
