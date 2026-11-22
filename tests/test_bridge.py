import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

try:
    from joycon2_assistant.bridge import BridgeManager
except ImportError:
    BridgeManager = None


def wait_until(predicate, timeout=5):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if predicate():
            return
        time.sleep(0.03)
    raise AssertionError('Timed out waiting for worker state')


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(BridgeManager, 'Bridge supervision is not implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.command = [sys.executable, '-u', str(Path(__file__).with_name('fixture_worker.py'))]
        self.manager = BridgeManager(command=self.command, runtime_dir=Path(self.temp.name),
                                     external_probe=lambda: [],
                                     environment_probe=lambda: {'driver_ready': True, 'code': 'ready', 'details': ''})

    def tearDown(self):
        if getattr(self, 'manager', None):
            self.manager.stop(wait=True)
        if getattr(self, 'temp', None):
            self.temp.cleanup()

    def test_repeated_connect_reuses_worker_and_stop_clears_state(self):
        self.manager.start()
        wait_until(lambda: self.manager.status()['phase'] == 'scanning_left')
        pid = self.manager.status()['worker_pid']
        self.manager.start()
        self.assertEqual(self.manager.status()['worker_pid'], pid)
        self.manager.stop(wait=True)
        state = self.manager.status()
        self.assertFalse(state['running'])
        self.assertEqual(state['phase'], 'idle')
        self.assertFalse(state['sides']['left']['connected'])
        self.assertFalse(state['sides']['right']['connected'])

    def test_crashed_worker_does_not_leave_connected_badges(self):
        self.manager.command.append('--crash')
        self.manager.start()
        wait_until(lambda: self.manager.status()['phase'] == 'error')
        state = self.manager.status()
        self.assertFalse(state['running'])
        self.assertFalse(state['sides']['left']['connected'])
        self.assertTrue(state['error'])

    def test_external_bridge_is_reported_without_being_killed(self):
        self.manager.external_probe = lambda: [12345]
        self.manager.start()
        state = self.manager.status()
        self.assertFalse(state['running'])
        self.assertEqual(state['phase'], 'external')
        self.assertIn('旧版', state['message'])

    def test_worker_hint_and_error_keys_reach_state_and_logs(self):
        self.manager.command.append('--localized-error')
        self.manager.start()
        wait_until(lambda: self.manager.status()['phase'] == 'error')
        state = self.manager.status()
        self.assertEqual(state['error_key'], 'gatt_unreachable')
        self.assertEqual(state['message_key'], 'gatt_unreachable')
        hints = [item for item in state['logs'] if item['key'] == 'reconnect_mode']
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0]['params'], {'side': 'left'})
        self.assertNotIn('11:22:33:44:55:66', json.dumps(state))

    def test_worker_exit_refreshes_its_cached_busy_device_before_publishing_idle(self):
        environment = {'driver_ready': True, 'device_ready': True, 'code': 'ready', 'details': ''}
        self.manager.environment_probe = lambda: dict(environment)
        self.manager.start()
        wait_until(lambda: self.manager.status()['phase'] == 'scanning_left')
        environment.update(device_ready=False, code='virtual_device_busy')
        self.assertEqual(self.manager.refresh_environment()['environment']['code'], 'ready')
        environment.update(device_ready=True, code='ready')
        self.manager.stop(wait=True)
        self.assertEqual(self.manager.status()['phase'], 'idle')
        self.assertEqual(self.manager.status()['environment']['code'], 'ready')


if __name__ == '__main__':
    unittest.main()
