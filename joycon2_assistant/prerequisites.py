"""Explicit, fixed-purpose setup actions for the official vJoy prerequisite."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

from .driver import driver_environment
from .paths import RUNTIME_DIR

DRIVER_URL = ('https://github.com/BrunnerInnovation/vJoy/releases/download/v2.2.2.0/'
              'vJoySetup_v2.2.2.0_Win10_Win11.exe')
DRIVER_SHA256 = 'ef569a3105cd301b89580f18f60c66b339e95296acf2c0dfcaf4b4bbf8ab68fe'
# Keep all original axes so the documented Steam DirectInput indices stay stable.
CONFIG_ARGUMENTS = ['1', '-f', '-a', 'x', 'y', 'z', 'rx', 'ry', 'rz', 'sl0', 'sl1', '-b', '24']


def download_driver(destination, progress):
    partial = destination.with_suffix('.part')
    request = urllib.request.Request(DRIVER_URL, headers={'User-Agent': 'JoyCon2Connect/1.1'})
    try:
        with urllib.request.urlopen(request, timeout=30) as source, partial.open('wb') as output:
            total = int(source.headers.get('Content-Length', 5302312))
            received = 0
            while chunk := source.read(65536):
                received += len(chunk)
                if received > 16 * 1024 * 1024:
                    raise ValueError('Driver download exceeds the expected size')
                output.write(chunk)
                progress(min(95, int(received * 95 / max(1, total))))
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)


def verify_signature(path):
    literal = str(path).replace("'", "''")
    command = ("$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new(); "
               "Import-Module (Join-Path $PSHOME 'Modules\\Microsoft.PowerShell.Security\\Microsoft.PowerShell.Security.psd1'); "
               f"$s=Get-AuthenticodeSignature -LiteralPath '{literal}'; "
               "@{status=$s.Status.ToString();publisher=$s.SignerCertificate.Subject}|ConvertTo-Json -Compress")
    environment = os.environ.copy()
    # PowerShell 7's module path cannot be used by Windows PowerShell 5.1.
    environment['PSModulePath'] = str(Path(os.environ.get('SystemRoot', r'C:\Windows')) /
                                      'System32' / 'WindowsPowerShell' / 'v1.0' / 'Modules')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                            capture_output=True, text=True, encoding='utf-8', errors='replace',
                            timeout=20, env=environment,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    data = json.loads(result.stdout)
    if result.returncode or data.get('status') != 'Valid':
        raise ValueError('Official driver signature validation failed')


class LaunchedProcess:
    def __init__(self, handle):
        self.handle = handle

    def wait(self):
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        try:
            if kernel.WaitForSingleObject(self.handle, 0xFFFFFFFF) != 0:
                raise ctypes.WinError(ctypes.get_last_error())
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(self.handle, ctypes.byref(code)):
                raise ctypes.WinError(ctypes.get_last_error())
            return code.value
        finally:
            kernel.CloseHandle(self.handle)


def launch_elevated(executable, arguments):
    # The executable and all arguments are selected by this module, never HTTP.
    shell = ctypes.WinDLL('shell32', use_last_error=True)
    class ExecuteInfo(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD), ('fMask', wintypes.ULONG), ('hwnd', wintypes.HWND),
                    ('lpVerb', wintypes.LPCWSTR), ('lpFile', wintypes.LPCWSTR),
                    ('lpParameters', wintypes.LPCWSTR), ('lpDirectory', wintypes.LPCWSTR),
                    ('nShow', ctypes.c_int), ('hInstApp', wintypes.HINSTANCE),
                    ('lpIDList', ctypes.c_void_p), ('lpClass', wintypes.LPCWSTR),
                    ('hkeyClass', wintypes.HKEY), ('dwHotKey', wintypes.DWORD),
                    ('hIcon', wintypes.HANDLE), ('hProcess', wintypes.HANDLE)]
    info = ExecuteInfo()
    info.cbSize, info.fMask = ctypes.sizeof(info), 0x40 | 0x400  # NOCLOSEPROCESS | FLAG_NO_UI
    info.lpVerb, info.lpFile = 'runas', str(executable)
    info.lpParameters, info.lpDirectory = subprocess.list2cmdline(arguments), str(executable.parent)
    info.nShow = 1 if arguments == ['/NORESTART'] else 0
    shell.ShellExecuteExW.argtypes = [ctypes.POINTER(ExecuteInfo)]
    shell.ShellExecuteExW.restype = wintypes.BOOL
    if not shell.ShellExecuteExW(ctypes.byref(info)) or not info.hProcess:
        raise ctypes.WinError(ctypes.get_last_error())
    return LaunchedProcess(info.hProcess)


def verify_installer(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != DRIVER_SHA256:
        path.unlink(missing_ok=True)
        raise ValueError('Official driver hash does not match')
    verify_signature(path)


def find_config_tool():
    import winreg
    key_name = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{8E31F76F-74C3-47F1-9550-E041EEDC5FBB}_is1'
    candidates = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_name, 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            candidates.append(Path(winreg.QueryValueEx(key, 'InstallLocation')[0]) / 'x64' / 'vJoyConfig.exe')
    except OSError:
        pass
    for variable in ('ProgramFiles', 'ProgramFiles(x86)'):
        if os.environ.get(variable):
            candidates.append(Path(os.environ[variable]) / 'vJoy' / 'x64' / 'vJoyConfig.exe')
    return next((path for path in candidates if path.is_file()), None)


class PrerequisiteSetup:
    def __init__(self, environment_probe=driver_environment, runtime_dir=RUNTIME_DIR,
                 downloader=download_driver, launch=launch_elevated, config_probe=find_config_tool,
                 verifier=verify_installer, environment_listener=lambda _environment: None):
        self.environment_probe = environment_probe
        self.runtime_dir = Path(runtime_dir)
        self.downloader, self.launch, self.config_probe = downloader, launch, config_probe
        self.verifier, self.environment_listener = verifier, environment_listener
        self._lock = threading.RLock()
        self.thread = None
        self._state = {'state': 'idle', 'busy': False, 'message_key': 'setup_idle',
                       'error_key': None, 'progress': 0}

    def status(self):
        with self._lock:
            return dict(self._state)

    def _update(self, state, *, busy=False, error=None, progress=0, message=None):
        with self._lock:
            self._state.update(state=state, busy=busy, message_key=message or error or 'setup_' + state,
                               error_key=error, progress=progress)

    def start(self, action, *, worker_running=False):
        with self._lock:
            environment = self.environment_probe()
            if self._state['busy']:
                return  # Reuse an existing setup job; never start a duplicate.
            if worker_running or environment.get('busy_devices'):
                self._update('error', error='setup_busy')
                return
            if action == 'install' and environment.get('driver_ready'):
                self._update('ready', progress=100)
                return
            if action == 'configure' and environment.get('device_ready'):
                self._update('ready', progress=100)
                return
            if action == 'configure' and not environment.get('driver_ready'):
                self._update('error', error='missing_driver')
                return
            self._update('downloading' if action == 'install' else 'configuring', busy=True)
            self.thread = threading.Thread(target=self._run, args=(action,), daemon=True)
            self.thread.start()

    def _run(self, action):
        try:
            if action == 'install':
                self.runtime_dir.mkdir(parents=True, exist_ok=True)
                installer = self.runtime_dir / 'vJoySetup_v2.2.2.0_Win10_Win11.exe'
                self.downloader(installer, lambda percent: self._update('downloading', busy=True, progress=percent))
                self.verifier(installer)
                process = self.launch(installer, ['/NORESTART'])
                self._update('installer_opened', busy=True, progress=100)
                exit_code = process.wait()
                environment = self.environment_probe()
                self.environment_listener(environment)
                if environment.get('driver_ready') and environment.get('device_ready'):
                    self._update('ready', progress=100)
                elif environment.get('driver_ready'):
                    self._update('idle', progress=100, message='configure_virtual_device')
                else:
                    self._update('error', error='setup_cancelled' if exit_code in (1, 2, 5) else 'setup_failed')
            else:
                executable = self.config_probe()
                if executable is None:
                    self._update('error', error='setup_config_tool_missing')
                    return
                environment = self.environment_probe()
                if environment.get('busy_devices'):
                    self._update('error', error='setup_busy')
                    return
                if environment.get('device_ready'):
                    self._update('ready', progress=100)
                    return
                process = self.launch(executable, CONFIG_ARGUMENTS)
                process.wait()
                for _ in range(45):
                    environment = self.environment_probe()
                    self.environment_listener(environment)
                    if environment.get('device_ready'):
                        self._update('ready', progress=100)
                        return
                    time.sleep(1)
                self._update('error', error='setup_failed')
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            key = ('setup_cancelled' if isinstance(exc, OSError) and
                   (exc.errno in (5, 1223) or getattr(exc, 'winerror', None) == 1223) else
                   'setup_download_failed' if action == 'install' else 'setup_failed')
            self._update('error', error=key)
