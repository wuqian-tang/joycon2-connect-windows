"""Windowed portable entry point; the console worker is a separate executable."""
from __future__ import annotations

import argparse
import ctypes
import sys
import traceback

from joycon2_assistant.paths import PORT, RUNTIME_DIR


def main():
    parser = argparse.ArgumentParser(description='Joy-Con 2 local assistant')
    parser.add_argument('--server', action='store_true')
    parser.add_argument('--port', type=int, default=PORT)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    # Windowed PyInstaller intentionally sets these to None. The worker has a
    # console bootloader so redirected stdin/stdout remain real JSON pipes.
    if sys.stdout is None:
        sys.stdout = (RUNTIME_DIR / 'server.log').open('a', encoding='utf-8')
    if sys.stderr is None:
        sys.stderr = sys.stdout
    if args.server:
        from joycon2_assistant import server
        server.main(args.port)
    else:
        from joycon2_assistant import launcher
        launcher.main(args.port, not args.no_browser)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        with (RUNTIME_DIR / 'launcher.log').open('a', encoding='utf-8') as log:
            traceback.print_exc(file=log)
        if '--server' not in sys.argv and '--no-browser' not in sys.argv:
            ctypes.windll.user32.MessageBoxW(None, str(exc), 'Joy-Con 2 连接助手', 0x10)
        raise SystemExit(1)
