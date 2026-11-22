import importlib.util
import threading
import time
import unittest
from pathlib import Path


class VerificationCleanupTests(unittest.TestCase):
    def test_exited_server_cleanup_waits_for_brief_windows_log_sharing_lock(self):
        spec = importlib.util.spec_from_file_location('verify_portable',
                    Path(__file__).resolve().parents[1] / 'scripts' / 'verify-portable.py')
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        self.assertTrue(hasattr(helper, 'PortableRuntime'), 'Bounded cleanup retry is missing')
        runtime = helper.PortableRuntime(prefix='jc2-log-lock-test-')
        stream = (Path(runtime.name) / 'server.log').open('w', encoding='utf-8')
        closer = threading.Timer(0.15, stream.close)
        closer.start()
        try:
            runtime.server_exited = True
            runtime.cleanup()
            self.assertFalse(Path(runtime.name).exists())
        finally:
            closer.join()
            stream.close()
            runtime.cleanup()
