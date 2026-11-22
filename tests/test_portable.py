"""Portable layout, dependency readiness, and localized bridge contracts."""
import tempfile
import unittest
import subprocess
import sys
import os
from pathlib import Path

from joycon2_assistant import paths
from joycon2_assistant.bridge import BridgeManager


class PortableTests(unittest.TestCase):
    def test_packaged_source_worker_entrypoint_is_runnable(self):
        result = subprocess.run([sys.executable, '-m', 'joycon2_assistant.worker', '--self-test'],
                                capture_output=True, text=True, encoding='utf-8', timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn('"ok": true', result.stdout)

    def test_frozen_processes_use_separate_console_worker_and_bundled_resources(self):
        self.assertTrue(hasattr(paths, 'resolve_layout'), 'Portable layout is not implemented')
        layout = paths.resolve_layout(Path('C:/portable'), Path('C:/portable/_internal'),
                                      frozen=True, executable=Path('C:/portable/Assistant.exe'))
        self.assertEqual(layout['source'], Path('C:/portable/_internal/vendor/joy2win'))
        self.assertEqual(layout['worker_command'], ['C:\\portable\\JoyCon2Worker.exe'])
        self.assertEqual(layout['server_command'], ['C:\\portable\\Assistant.exe', '--server'])

    def test_source_execution_uses_current_python_when_no_venv_is_installed(self):
        self.assertTrue(hasattr(paths, 'resolve_layout'), 'Portable layout is not implemented')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            layout = paths.resolve_layout(folder, folder, executable=Path('C:/Python/python.exe'))
            self.assertEqual(layout['python'], Path('C:/Python/python.exe'))
            self.assertEqual(layout['source'], folder / 'vendor' / 'joy2win')

    def test_unwritable_portable_runtime_falls_back_to_local_appdata(self):
        self.assertTrue(hasattr(paths, 'choose_runtime_dir'), 'Writable runtime fallback is missing')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = root / 'portable'
            app.mkdir()
            (app / 'runtime').write_text('A file prevents directory creation')
            actual = paths.choose_runtime_dir(app, root / 'localdata')
            self.assertEqual(actual, root / 'localdata' / 'JoyCon2Assistant' / 'runtime')
            self.assertTrue(actual.is_dir())

    def test_missing_driver_is_visible_and_connect_does_not_spawn_a_worker(self):
        self.assertIn('environment_probe', __import__('inspect').signature(BridgeManager).parameters,
                      'Driver readiness is not checked')
        manager = BridgeManager(command=['must-not-exist'], external_probe=lambda: [],
                                environment_probe=lambda: {'driver_ready': False,
                                    'code': 'missing_driver', 'details': 'Install signed vJoy 2.2.2.0'})
        state = manager.start()
        self.assertFalse(state['running'])
        self.assertEqual(state['environment']['code'], 'missing_driver')
        self.assertEqual(state['error_key'], 'missing_driver')
        self.assertEqual(state['logs'][-1]['key'], 'missing_driver')

    def test_idle_state_and_logs_have_translation_keys(self):
        manager = BridgeManager(external_probe=lambda: [])
        self.assertEqual(manager.status().get('message_key'), 'phase_idle')
        self.assertIn('environment', manager.status())

    def test_busy_virtual_device_is_blocked_without_starting_ble_or_losing_driver_readiness(self):
        manager = BridgeManager(command=['must-not-start'], external_probe=lambda: [],
                                environment_probe=lambda: {'driver_ready': True, 'device_ready': False,
                                    'code': 'virtual_device_busy', 'details': 'Another feeder owns device 1'})
        state = manager.start()
        self.assertFalse(state['running'])
        self.assertTrue(state['environment']['driver_ready'])
        self.assertEqual(state['error_key'], 'virtual_device_busy')


class DriverTests(unittest.TestCase):
    def test_source_pyvjoy_uses_bundled_sdk_even_when_its_original_dll_is_missing(self):
        import shutil
        import importlib.util
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / 'pyvjoy'
            package.mkdir()
            original = Path(importlib.util.find_spec('pyvjoy').origin).parent
            for file in original.glob('*.py'):
                shutil.copyfile(file, package / file.name)
            script = ('import sys; sys.path.insert(0, sys.argv[1]); '
                      'from joycon2_assistant.driver import bind_pyvjoy_sdk, sdk_path; '
                      'p=bind_pyvjoy_sdk(); '
                      'assert p._sdk.dll_path == str(sdk_path()); '
                      'assert p._sdk._vj is not None; print("bound bundled SDK")')
            result = subprocess.run([sys.executable, '-c', script, temporary], capture_output=True,
                                    text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn('bound bundled SDK', result.stdout)

    def test_missing_sdk_is_reported_without_importing_pyvjoy(self):
        from joycon2_assistant import driver
        state = driver.driver_environment(dll_path=Path('not-a-real-sdk.dll'))
        self.assertFalse(state['driver_ready'])
        self.assertEqual(state['code'], 'missing_driver')
        self.assertEqual(state['download_url'],
                         'https://github.com/BrunnerInnovation/vJoy/releases/tag/v2.2.2.0')

    def test_different_installed_driver_version_is_rejected(self):
        from joycon2_assistant import driver

        class Function:
            def __init__(self, result):
                self.result = result

            def __call__(self, *args):
                if args:
                    args[0]._obj.value = 0x222
                    args[1]._obj.value = 0x219
                return self.result

        class SDK:
            vJoyEnabled = Function(True)
            DriverMatch = Function(False)

        state = driver.driver_environment(loader=lambda _: SDK())
        self.assertFalse(state['driver_ready'])
        self.assertEqual(state['code'], 'version_mismatch')
        self.assertEqual(state['driver_version'], '2.1.9')

    def test_missing_axis_requires_configuring_device_before_ble_connection(self):
        from joycon2_assistant import driver

        class Function:
            def __init__(self, callback):
                self.callback = callback

            def __call__(self, *args):
                return self.callback(*args)

        def match(sdk, installed):
            sdk._obj.value = installed._obj.value = 0x222
            return True

        class SDK:
            vJoyEnabled = Function(lambda: True)
            DriverMatch = Function(match)
            GetVJDStatus = Function(lambda device: 1)
            GetVJDButtonNumber = Function(lambda device: 24)
            GetVJDAxisExist = Function(lambda device, axis: axis != 0x33)

        state = driver.driver_environment(loader=lambda _: SDK())
        self.assertTrue(state['driver_ready'])
        self.assertFalse(state.get('device_ready', True))
        self.assertEqual(state['code'], 'configure_virtual_device')


class WorkerErrorTests(unittest.TestCase):
    def test_scan_diagnostic_validates_callback_signature_and_can_stop_without_hardware(self):
        with tempfile.TemporaryDirectory() as temporary:
            Path(temporary, 'bleak.py').write_text('''
import inspect
class BleakScanner:
    def __init__(self, callback):
        if len(inspect.signature(callback).parameters) != 2:
            raise TypeError('callback must be callable with 2 parameters')
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
''', encoding='utf-8')
            result = subprocess.run([sys.executable, '-u', '-m', 'joycon2_assistant.worker', '--scan-only'],
                                    input='stop\n', capture_output=True, text=True, encoding='utf-8',
                                    timeout=10, env=dict(os.environ, PYTHONPATH=temporary,
                                                         PYTHONIOENCODING='cp950'))
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn('"event": "stopped"', result.stdout)

    def test_worker_errors_keep_actionable_translation_keys(self):
        from joycon2_assistant import worker
        self.assertTrue(hasattr(worker, 'describe_error'), 'Worker errors have no translation keys')
        cases = [(TimeoutError(), 'connection_timeout'),
                 (RuntimeError('Bluetooth Unreachable'), 'gatt_unreachable'),
                 (RuntimeError('vjoy failed to acquire'), 'virtual_device_unavailable'),
                 (ValueError('failure'), 'unknown_error')]
        for error, expected in cases:
            with self.subTest(expected=expected):
                key, message = worker.describe_error(error)
                self.assertEqual(key, expected)
                self.assertTrue(message)


if __name__ == '__main__':
    unittest.main()
