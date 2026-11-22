"""Offline local UI. No shell commands or user-supplied paths are exposed by HTTP."""
from __future__ import annotations

import hmac
import json
import mimetypes
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from .bridge import BridgeManager
from .paths import APP_ID, PORT, RUNTIME_DIR, STATIC_DIR, VERSION


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, port, manager):
        self.manager = manager
        self.token = secrets.token_urlsafe(32)
        self.started_at = time.time()
        super().__init__(('127.0.0.1', port), Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = 'JoyCon2Local/1.0'

    def log_message(self, *_args):
        pass

    def send_data(self, data, content_type, status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' data:; "
                         "script-src 'self'; style-src 'self'; connect-src 'self'; "
                         "object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, value, status=200):
        self.send_data(json.dumps(value, ensure_ascii=False).encode('utf-8'),
                       'application/json; charset=utf-8', status)

    def local_request(self):
        port = self.server.server_port
        hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
        if self.headers.get('Host', '') not in hosts:
            self.send_json({'error': '仅接受本机请求'}, 403)
            return False
        origin = self.headers.get('Origin')
        if origin and origin not in {f'http://{host}' for host in hosts}:
            self.send_json({'error': '不接受其他网站的请求'}, 403)
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        path = urlsplit(self.path).path
        if path == '/api/health':
            self.send_json({'app': APP_ID, 'version': VERSION, 'pid': os.getpid()})
            return
        if path == '/api/status':
            self.send_json(self.server.manager.status())
            return
        assets = {'/': STATIC_DIR / 'index.html', '/styles.css': STATIC_DIR / 'styles.css',
                  '/app.js': STATIC_DIR / 'app.js', '/favicon.svg': STATIC_DIR / 'favicon.svg',
                  '/i18n.js': STATIC_DIR / 'i18n.js', '/sync-guide.svg': STATIC_DIR / 'sync-guide.svg',
                  '/static/i18n.js': STATIC_DIR / 'i18n.js',
                  '/static/sync-guide.svg': STATIC_DIR / 'sync-guide.svg'}
        asset = assets.get(path)
        if asset is None:
            self.send_json({'error': '页面不存在'}, 404)
            return
        try:
            data = asset.read_bytes()
            if path == '/':
                data = data.replace(b'__REQUEST_TOKEN__', self.server.token.encode('ascii'))
            content_type = mimetypes.guess_type(str(asset))[0] or 'application/octet-stream'
            if content_type.startswith('text/') or path.endswith('.js'):
                content_type += '; charset=utf-8'
            self.send_data(data, content_type)
        except OSError:
            self.send_json({'error': '页面文件不完整，请从桌面快捷方式重新打开'}, 500)

    def do_POST(self):
        # Consume bounded bodies before an early 403. On Windows, closing a
        # socket with an unread body can reset it and discard the rejection.
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 <= length <= 1024:
                self.send_json({'error': '请求过大'}, 413)
                self.close_connection = True
                return
            self.connection.settimeout(5)
            raw_body = self.rfile.read(length)
        except ValueError:
            self.send_json({'error': '请求格式不正确'}, 400)
            return
        except (TimeoutError, OSError):
            self.send_json({'error': '请求超时'}, 408)
            return
        if not self.local_request():
            return
        supplied = self.headers.get('X-JC2-Token', '')
        if not hmac.compare_digest(supplied, self.server.token):
            self.send_json({'error': '请刷新本机页面后重试'}, 403)
            return
        if self.headers.get_content_type() != 'application/json':
            self.send_json({'error': '请求格式不正确'}, 415)
            return
        try:
            body = json.loads(raw_body or b'{}')
            if not isinstance(body, dict):
                raise ValueError()
        except (ValueError, UnicodeError):
            self.send_json({'error': '请求格式不正确'}, 400)
            return
        path = urlsplit(self.path).path
        if path == '/api/connect':
            self.send_json(self.server.manager.start())
        elif path == '/api/disconnect':
            self.send_json(self.server.manager.stop())
        elif path == '/api/recheck-environment':
            self.send_json(self.server.manager.refresh_environment())
        elif path in ('/api/install-driver', '/api/configure-vjoy'):
            state = self.server.manager.setup_action('install' if path.endswith('install-driver') else 'configure')
            self.send_json(state, 409 if state['setup']['error_key'] else 200)
        elif path == '/api/open-steam':
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as key:
                    executable = winreg.QueryValueEx(key, 'SteamExe')[0]
                if not executable.lower().endswith('steam.exe') or not os.path.isfile(executable):
                    raise OSError('Steam 路径不可用')
                os.startfile(executable)
                self.send_json({'ok': True})
            except OSError:
                self.send_json({'error': '没有找到 Steam，请从桌面手动打开'}, 409)
        elif path == '/api/exit':
            self.send_json({'ok': True})
            threading.Thread(target=self.exit_assistant, daemon=True).start()
        else:
            self.send_json({'error': '操作不存在'}, 404)

    def exit_assistant(self):
        self.server.manager.stop(wait=True)
        self.server.shutdown()


def create_server(port=PORT, manager=None):
    return LocalServer(port, manager or BridgeManager())


def main(port=PORT):
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    server = create_server(port=port)
    identity = RUNTIME_DIR / ('server.json' if port == PORT else f'server-{port}.json')
    identity.write_text(json.dumps({'app': APP_ID, 'version': VERSION, 'pid': os.getpid(),
                                    'port': server.server_port}), encoding='utf-8')
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.manager.stop(wait=True)
        server.server_close()
        try:
            if json.loads(identity.read_text(encoding='utf-8')).get('pid') == os.getpid():
                identity.unlink()
        except (OSError, ValueError):
            pass


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=PORT)
    main(parser.parse_args().port)
