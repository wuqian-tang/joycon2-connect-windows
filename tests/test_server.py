import http.client
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from joycon2_assistant.bridge import BridgeManager
try:
    from joycon2_assistant.server import create_server
except ImportError:
    create_server = None


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(create_server, 'The local API is not implemented')
        self.temp = tempfile.TemporaryDirectory()
        command = [sys.executable, '-u', str(Path(__file__).with_name('fixture_worker.py'))]
        self.manager = BridgeManager(command=command, runtime_dir=Path(self.temp.name),
                                     external_probe=lambda: [],
                                     environment_probe=lambda: {'driver_ready': True, 'code': 'ready', 'details': ''})
        self.server = create_server(port=0, manager=self.manager)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        if getattr(self, 'server', None):
            self.manager.stop(wait=True)
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(2)
        if getattr(self, 'temp', None):
            self.temp.cleanup()

    def request(self, path, method='GET', headers=None, body=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        status, data = response.status, response.read()
        connection.close()
        return status, data

    def test_health_and_status_do_not_start_a_bridge(self):
        status, data = self.request('/api/health')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)['app'], 'joycon2-local-assistant')
        self.assertEqual(json.loads(data)['version'], '1.1.2')
        status, data = self.request('/api/status')
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(data)['phase'], 'idle')
        self.assertFalse(self.manager.status()['running'])

    def test_connect_without_request_token_is_rejected(self):
        status, _ = self.request('/api/connect', 'POST', {'Content-Type': 'application/json'}, '{}')
        self.assertEqual(status, 403)
        self.assertFalse(self.manager.status()['running'])

    def test_cross_origin_request_cannot_control_the_worker(self):
        headers = {'Content-Type': 'application/json', 'Origin': 'https://another-site.example',
                   'X-JC2-Token': self.server.token}
        status, _ = self.request('/api/connect', 'POST', headers, '{}')
        self.assertEqual(status, 403)
        self.assertFalse(self.manager.status()['running'])

    def test_rejected_post_with_delayed_body_returns_403_without_resetting_socket(self):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            connection.putrequest('POST', '/api/connect')
            connection.putheader('Content-Type', 'application/json')
            connection.putheader('Content-Length', '2')
            connection.putheader('Origin', 'https://another-site.example')
            connection.endheaders()
            time.sleep(0.03)
            connection.send(b'{}')
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            self.assertTrue(response.read())
            self.assertFalse(self.manager.status()['running'])
        finally:
            connection.close()

    def test_non_loopback_host_is_rejected(self):
        status, _ = self.request('/api/status', headers={'Host': 'attacker.example'})
        self.assertEqual(status, 403)

    def test_only_known_static_assets_can_be_read(self):
        status, _ = self.request('/../installation-info.txt')
        self.assertEqual(status, 404)
        status, _ = self.request('/runtime/server.json')
        self.assertEqual(status, 404)

    def test_authorized_connect_and_disconnect_work_over_http(self):
        headers = {'Content-Type': 'application/json', 'X-JC2-Token': self.server.token}
        status, data = self.request('/api/connect', 'POST', headers, '{}')
        self.assertEqual(status, 200)
        pid = json.loads(data)['worker_pid']
        self.assertTrue(pid)
        _, data = self.request('/api/connect', 'POST', headers, '{}')
        self.assertEqual(json.loads(data)['worker_pid'], pid)
        status, _ = self.request('/api/disconnect', 'POST', headers, '{}')
        self.assertEqual(status, 200)
        deadline = time.monotonic() + 5
        while self.manager.status()['running'] and time.monotonic() < deadline:
            time.sleep(0.03)
        self.assertFalse(self.manager.status()['running'])

    def test_setup_actions_keep_csrf_protection_and_ready_actions_are_noops(self):
        for path in ('/api/install-driver', '/api/configure-vjoy', '/api/recheck-environment'):
            with self.subTest(path=path):
                code, _ = self.request(path, 'POST', {'Content-Type': 'application/json'}, '{}')
                self.assertEqual(code, 403)
                headers = {'Content-Type': 'application/json', 'X-JC2-Token': self.server.token}
                self.manager.setup.environment_probe = lambda: {'driver_ready': True, 'device_ready': True}
                code, data = self.request(path, 'POST', headers, '{}')
                self.assertEqual(code, 200)
                self.assertIn('setup', json.loads(data))
                self.assertFalse(self.manager.status()['running'])


if __name__ == '__main__':
    unittest.main()
