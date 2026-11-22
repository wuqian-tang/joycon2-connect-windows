"""Resource and writable paths for a checkout or an extracted Windows bundle."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

APP_ID = 'joycon2-local-assistant'
VERSION = '1.1.1'
PORT = 19862


def resolve_layout(app_dir, resource_dir, *, frozen=False, executable=None):
    app_dir, resource_dir = Path(app_dir), Path(resource_dir)
    executable = Path(executable or sys.executable)
    python = executable
    if not frozen:
        for candidate in (app_dir / '.venv' / 'Scripts' / 'python.exe',
                          app_dir.parent / '.venv' / 'Scripts' / 'python.exe'):
            if candidate.is_file():
                python = candidate
                break
    pythonw = python.with_name('pythonw.exe')
    if not pythonw.is_file():
        pythonw = python
    return {
        'python': python,
        'pythonw': pythonw,
        'source': resource_dir / 'vendor' / 'joy2win',
        'worker_command': ([str(app_dir / 'JoyCon2Worker.exe')] if frozen else
                           [str(python), '-u', '-m', 'joycon2_assistant.worker']),
        'server_command': ([str(executable), '--server'] if frozen else
                           [str(pythonw), '-u', '-m', 'joycon2_assistant.server']),
    }


def choose_runtime_dir(app_dir, local_app_data=None):
    fallback = Path(local_app_data or os.environ.get('LOCALAPPDATA') or
                    Path.home() / 'AppData' / 'Local') / 'JoyCon2Assistant' / 'runtime'
    candidates = [Path(app_dir) / 'runtime', fallback]
    override = os.environ.get('JOYCON2_RUNTIME_DIR')
    if override:
        candidates.insert(0, Path(override).expanduser().resolve())
    for directory in candidates:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryFile(dir=directory):
                pass
            return directory
        except OSError:
            continue
    raise OSError('Cannot create a writable JoyCon2Assistant runtime directory')


FROZEN = bool(getattr(sys, 'frozen', False))
RESOURCE_DIR = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent.parent
TOOL_DIR = APP_DIR.parent
_layout = resolve_layout(APP_DIR, RESOURCE_DIR, frozen=FROZEN)
PYTHON, PYTHONW, SOURCE = _layout['python'], _layout['pythonw'], _layout['source']
WORKER_COMMAND, SERVER_COMMAND = _layout['worker_command'], _layout['server_command']
RUNTIME_DIR = choose_runtime_dir(APP_DIR)
STATIC_DIR = RESOURCE_DIR / 'joycon2_assistant' / 'static'
