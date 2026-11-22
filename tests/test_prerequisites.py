import tempfile
import threading
import unittest
import ctypes
from pathlib import Path


class PrerequisiteTests(unittest.TestCase):
    def test_declined_windows_uac_is_reported_as_cancelled_and_can_retry(self):
        from joycon2_assistant.prerequisites import PrerequisiteSetup
        with tempfile.TemporaryDirectory() as directory:
            def declined(*_args):
                raise ctypes.WinError(1223)

            setup = PrerequisiteSetup(environment_probe=lambda: {'driver_ready': False},
                                      runtime_dir=Path(directory),
                                      downloader=lambda path, progress: path.write_bytes(b'fixture'),
                                      verifier=lambda _path: None, launch=declined)
            setup.start('install')
            setup.thread.join(3)
            self.assertEqual(setup.status()['error_key'], 'setup_cancelled')
            self.assertFalse(setup.status()['busy'])

    def test_already_ready_driver_is_not_downloaded_or_reinstalled(self):
        from joycon2_assistant.prerequisites import PrerequisiteSetup
        setup = PrerequisiteSetup(environment_probe=lambda: {'driver_ready': True, 'device_ready': True},
                                  launch=lambda *_args: self.fail('Ready driver must not launch installer'))
        setup.start('install')
        self.assertEqual(setup.status()['state'], 'ready')

    def test_configuration_is_blocked_while_any_feeder_is_active(self):
        from joycon2_assistant.prerequisites import PrerequisiteSetup
        setup = PrerequisiteSetup(environment_probe=lambda: {'driver_ready': True, 'device_ready': False,
                                                             'busy_devices': [3]},
                                  launch=lambda *_args: self.fail('Active feeder must not be interrupted'))
        setup.start('configure')
        self.assertEqual(setup.status()['error_key'], 'setup_busy')
        self.assertFalse(setup.status()['busy'])

    def test_driver_download_hash_failure_never_launches_the_file(self):
        from joycon2_assistant.prerequisites import PrerequisiteSetup
        with tempfile.TemporaryDirectory() as directory:
            finished = threading.Event()

            def bad_download(destination, progress):
                destination.write_bytes(b'Not the official signed driver installer')

            setup = PrerequisiteSetup(environment_probe=lambda: {'driver_ready': False},
                                      runtime_dir=Path(directory), downloader=bad_download,
                                      launch=lambda *_args: self.fail('Unverified download must never run'))
            setup.start('install')
            setup.thread.join(5)
            self.assertEqual(setup.status()['state'], 'error')
            self.assertEqual(setup.status()['error_key'], 'setup_download_failed')
            self.assertFalse(setup.status()['busy'])

    def test_open_installer_is_single_job_and_cancelled_wizard_allows_retry(self):
        from joycon2_assistant.prerequisites import PrerequisiteSetup
        entered, closed = threading.Event(), threading.Event()
        downloads = []

        class Wizard:
            def wait(self):
                entered.set()
                closed.wait(5)
                return 2  # Official Inno Setup cancellation exit code.

        with tempfile.TemporaryDirectory() as directory:
            def download(destination, progress):
                destination.write_bytes(b'controlled external installer fixture')
                downloads.append(destination)

            setup = PrerequisiteSetup(environment_probe=lambda: {'driver_ready': False},
                                      runtime_dir=Path(directory), downloader=download,
                                      verifier=lambda _path: None, launch=lambda *_args: Wizard())
            setup.start('install')
            self.assertTrue(entered.wait(2))
            self.assertTrue(setup.status()['busy'])
            setup.start('install')
            self.assertEqual(len(downloads), 1)
            closed.set()
            setup.thread.join(3)
            self.assertEqual(setup.status()['error_key'], 'setup_cancelled')
            self.assertFalse(setup.status()['busy'])
            setup.start('install')
            setup.thread.join(3)
            self.assertEqual(len(downloads), 2)


if __name__ == '__main__':
    unittest.main()
