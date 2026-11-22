"""Own exactly one worker; never stop an unrelated or legacy process."""
from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import threading
import time
from collections import deque
from pathlib import Path

from .driver import driver_environment
from .prerequisites import PrerequisiteSetup
from .paths import APP_DIR, FROZEN, PYTHON, RUNTIME_DIR, WORKER_COMMAND

PHASE_MESSAGES = {
    'idle': '准备好连接你的 Joy-Con 2',
    'starting': '正在准备连接…',
    'scanning_left': '请长按左手内侧的小圆同步键，直到四灯循环闪烁',
    'connecting_left': '正在连接左手，请稍候…',
    'scanning_right': '左手已就绪。现在长按右手的小圆同步键',
    'connecting_right': '正在连接右手，请稍候…',
    'connected': '两只手柄已连接，可以打开 Steam 了',
    'stopping': '正在安全断开手柄…',
    'error': '连接未完成，请查看提示后重试',
    'external': '旧版连接程序正在运行，请先关闭旧版窗口，再重新检测',
}


def clean_message(value):
    return re.sub(r'(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b', '[蓝牙设备]', str(value))[:700]


def find_external_bridge():
    legacy_python = PYTHON
    if FROZEN:
        # Only identify a legacy process tied to a known adjacent checkout.
        # A portable bundle has no authority to label arbitrary python main.py.
        legacy_python = next((candidate for candidate in
                              (APP_DIR / '.venv' / 'Scripts' / 'python.exe',
                               APP_DIR.parent / '.venv' / 'Scripts' / 'python.exe')
                              if candidate.is_file()), None)
        if legacy_python is None:
            return []  # vJoy device readiness still detects another feeder.
    executable = str(legacy_python).replace("'", "''")
    command = (
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); "
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        f"Where-Object {{$_.ExecutablePath -eq '{executable}' -and "
        "$_.CommandLine -match '(?:^|\\s)main\\.py(?:\\s|$)'} | "
        'Select-Object -ExpandProperty ProcessId | ConvertTo-Json -Compress'
    )
    try:
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
            capture_output=True, text=True, encoding='utf-8', timeout=8,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        data = json.loads(result.stdout) if result.stdout.strip() else []
        return data if isinstance(data, list) else [data]
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []


def empty_sides():
    return {side: {'connected': False, 'packets': 0, 'axes': [0, 0], 'buttons': []}
            for side in ('left', 'right')}


class BridgeManager:
    def __init__(self, command=None, runtime_dir=RUNTIME_DIR, external_probe=find_external_bridge,
                 environment_probe=driver_environment):
        self.command = list(command or WORKER_COMMAND)
        self.runtime_dir = Path(runtime_dir)
        self.external_probe = external_probe
        self.environment_probe = environment_probe
        self._environment = environment_probe()
        self._environment_checked = time.monotonic()
        self.setup = PrerequisiteSetup(environment_probe=environment_probe, runtime_dir=runtime_dir,
                                      environment_listener=self._cache_environment)
        self._lock = threading.RLock()
        self._process = None
        self._stop_requested = False
        self._logs = deque(maxlen=120)
        self._sequence = 0
        self._state = {'phase': 'idle', 'message': PHASE_MESSAGES['idle'], 'message_key': 'phase_idle',
                       'error': None, 'error_key': None,
                       'sides': empty_sides(), 'started_at': None}

    def _log(self, message, level='info', key=None, params=None):
        self._sequence += 1
        self._logs.append({'id': self._sequence, 'time': time.strftime('%H:%M:%S'),
                           'message': clean_message(message), 'level': level,
                           'key': key, 'params': params or {}})

    def status(self):
        with self._lock:
            if time.monotonic() - self._environment_checked >= 3:
                self._environment = self.environment_probe()
                self._environment_checked = time.monotonic()
            state = copy.deepcopy(self._state)
            running = self._process is not None and self._process.poll() is None
            environment = copy.deepcopy(self._environment)
            if running and environment['code'] == 'virtual_device_busy':
                environment.update(device_ready=True, code='ready',
                                   details='vJoy device 1 is in use by this connection session.')
            state.update(running=running, worker_pid=self._process.pid if running else None,
                         logs=list(self._logs), environment=environment, setup=self.setup.status())
            return state

    def refresh_environment(self):
        with self._lock:
            self._environment = self.environment_probe()
            self._environment_checked = time.monotonic()
            return self.status()

    def _cache_environment(self, environment):
        with self._lock:
            self._environment = environment
            self._environment_checked = time.monotonic()

    def setup_action(self, action):
        with self._lock:
            self.setup.start(action, worker_running=self._process is not None and self._process.poll() is None)
            return self.status()

    def start(self):
        with self._lock:
            if self.setup.status()['busy']:
                return self.status()
            if self._process is not None and self._process.poll() is None:
                return self.status()
            if self.external_probe():
                self._state.update(phase='external', message=PHASE_MESSAGES['external'],
                                   message_key='phase_external', error=None, error_key=None)
                self._log(PHASE_MESSAGES['external'], 'warning', 'legacy_bridge')
                return self.status()
            self._environment = self.environment_probe()
            self._environment_checked = time.monotonic()
            if not self._environment['driver_ready'] or not self._environment.get('device_ready', True):
                code = self._environment['code']
                message = {
                    'version_mismatch': 'vJoy 驱动版本不匹配，请安装 2.2.2.0 后重试。',
                    'configure_virtual_device': '请在 vJoy 设置中启用设备 1，至少 24 个按钮和 X、Y、Rx、Ry 轴。',
                    'virtual_device_busy': 'vJoy 设备 1 正被其他连接程序使用。请关闭该程序后重试。',
                }.get(code, '请先安装并启用 vJoy 2.2.2.0 驱动，再重新连接。')
                self._state.update(phase='error', message=message, message_key=code,
                                   error=message, error_key=code, sides=empty_sides())
                self._log(message, 'error', code)
                return self.status()
            self.runtime_dir.mkdir(parents=True, exist_ok=True)
            self._stop_requested = False
            self._state.update(phase='starting', message=PHASE_MESSAGES['starting'], error=None,
                               message_key='phase_starting', error_key=None,
                               sides=empty_sides(), started_at=time.time())
            self._log('开始连接，先左手，再右手', key='start_session')
            try:
                environment = os.environ.copy()
                environment.update(PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1')
                process = subprocess.Popen(
                    self.command, cwd=APP_DIR, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
                    bufsize=1, env=environment,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                )
            except OSError as exc:
                self._state.update(phase='error', message='连接程序无法启动', error=clean_message(exc),
                                   message_key='bridge_start_failed', error_key='bridge_start_failed')
                self._log(exc, 'error', 'bridge_start_failed')
                return self.status()
            self._process = process
            threading.Thread(target=self._read_worker, args=(process,), daemon=True).start()
            return self.status()

    def _read_worker(self, process):
        try:
            for line in process.stdout:
                try:
                    event = json.loads(line)
                except ValueError:
                    with self._lock:
                        if line.strip():
                            self._log(line.strip(), 'warning')
                    continue
                with self._lock:
                    if self._process is not process:
                        continue
                    kind = event.get('event')
                    if kind == 'phase' and event.get('phase') in PHASE_MESSAGES:
                        phase = event['phase']
                        self._state.update(phase=phase, message=PHASE_MESSAGES[phase],
                                           message_key='phase_' + phase)
                        self._log(self._state['message'], key='phase_' + phase)
                    elif kind == 'side' and event.get('side') in self._state['sides']:
                        self._state['sides'][event['side']]['connected'] = bool(event.get('connected'))
                    elif kind == 'input' and event.get('side') in self._state['sides']:
                        self._state['sides'][event['side']].update(
                            packets=int(event.get('packets', 0)), axes=event.get('axes', [0, 0]),
                            buttons=event.get('buttons', []))
                    elif kind == 'hint':
                        message = clean_message(event.get('message', ''))
                        self._state['message'] = message
                        self._state['message_key'] = event.get('key')
                        self._log(message, 'warning', event.get('key'), event.get('params'))
                    elif kind == 'error':
                        message = clean_message(event.get('message', '连接中断'))
                        key = event.get('key') or 'unknown_error'
                        self._state.update(phase='error', message=message, error=message,
                                           message_key=key, error_key=key)
                        self._log(message, 'error', key, event.get('params'))
            exit_code = process.wait()
            with self._lock:
                if self._process is not process:
                    return
                self._state['sides'] = empty_sides()
                # A cached BUSY reading belonged to this worker. Refresh after
                # process exit so idle never briefly looks like another feeder.
                self._environment = self.environment_probe()
                self._environment_checked = time.monotonic()
                if self._stop_requested or exit_code == 0:
                    self._state.update(phase='idle', message=PHASE_MESSAGES['idle'], error=None,
                                       message_key='phase_idle', error_key=None)
                    self._log('手柄已断开', key='stopped')
                else:
                    error = self._state['error'] or f'连接程序已退出（{exit_code}），请重新连接'
                    key = self._state['error_key'] or 'bridge_exited'
                    self._state.update(phase='error', message=error, error=error,
                                       message_key=key, error_key=key)
                    self._log(error, 'error', key, {'code': exit_code})
        finally:
            if process.stdout:
                process.stdout.close()
            if process.stdin:
                process.stdin.close()

    def stop(self, wait=False):
        with self._lock:
            process = self._process
            if process is None or process.poll() is not None:
                if self._state['phase'] != 'external':
                    self._state.update(phase='idle', message=PHASE_MESSAGES['idle'], error=None,
                                       message_key='phase_idle', error_key=None,
                                       sides=empty_sides())
                return self.status()
            if not self._stop_requested:
                self._stop_requested = True
                self._state.update(phase='stopping', message=PHASE_MESSAGES['stopping'],
                                   message_key='phase_stopping')
                try:
                    process.stdin.write('stop\n')
                    process.stdin.flush()
                except (OSError, ValueError):
                    pass
            threading.Thread(target=self._finish_stop, args=(process,), daemon=True).start()
        if wait:
            self._finish_stop(process)
            deadline = time.monotonic() + 2
            while self.status()['phase'] == 'stopping' and time.monotonic() < deadline:
                time.sleep(0.02)
        return self.status()

    @staticmethod
    def _finish_stop(process):
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            try:
                process.terminate()
                process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                if process.poll() is None:
                    process.kill()
