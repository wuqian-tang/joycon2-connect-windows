"""Read-only vJoy readiness checks; never acquire or reset a virtual device."""
from __future__ import annotations

import ctypes
import importlib.util
from functools import lru_cache
from pathlib import Path

from .paths import RESOURCE_DIR

DOWNLOAD_URL = 'https://github.com/BrunnerInnovation/vJoy/releases/tag/v2.2.2.0'
REQUIRED_VERSION = '2.2.2.0'


def sdk_path():
    bundled = RESOURCE_DIR / 'vendor' / 'vjoy' / 'vJoyInterface.dll'
    if bundled.is_file():
        return bundled
    spec = importlib.util.find_spec('pyvjoy')
    return (Path(spec.origin).parent / 'utils' / 'x64' / 'vJoyInterface.dll'
            if spec and spec.origin else bundled)


def _version(value):
    return '.'.join(str((value >> shift) & 15) for shift in (8, 4, 0))


@lru_cache(maxsize=4)
def _load_sdk(path):
    return ctypes.CDLL(path)


def bind_pyvjoy_sdk():
    """Point pinned pyvjoy 1.0.1 at our SDK without editing site-packages.

    pyvjoy hardcodes its wheel's obsolete DLL and exits during import if that
    file is absent. Redirect only that one library load during startup, then
    restore ctypes immediately. No controller has been acquired at this point.
    """
    target = str(sdk_path())
    original = ctypes.cdll.LoadLibrary

    def load(library):
        return original(target if Path(str(library)).name.lower() == 'vjoyinterface.dll' else library)

    try:
        ctypes.cdll.LoadLibrary = load
        import pyvjoy
    finally:
        ctypes.cdll.LoadLibrary = original
    pyvjoy._sdk.dll_path = target
    pyvjoy._sdk._vj = _load_sdk(target)
    return pyvjoy


def driver_environment(*, dll_path=None, loader=_load_sdk):
    state = {'driver_ready': False, 'code': 'missing_driver',
             'details': 'Install and enable signed vJoy 2.2.2.0, then configure device 1.',
             'required_version': REQUIRED_VERSION, 'download_url': DOWNLOAD_URL}
    try:
        sdk = loader(str(dll_path or sdk_path()))
        sdk.vJoyEnabled.argtypes = []
        sdk.vJoyEnabled.restype = ctypes.c_bool
        sdk.DriverMatch.argtypes = [ctypes.POINTER(ctypes.c_ushort),
                                    ctypes.POINTER(ctypes.c_ushort)]
        sdk.DriverMatch.restype = ctypes.c_bool
        if not sdk.vJoyEnabled():
            return state
        dll_version, driver_version = ctypes.c_ushort(), ctypes.c_ushort()
        matches = sdk.DriverMatch(ctypes.byref(dll_version), ctypes.byref(driver_version))
        state.update(sdk_version=_version(dll_version.value),
                     driver_version=_version(driver_version.value))
        if not matches or dll_version.value != 0x222 or driver_version.value != 0x222:
            state.update(code='version_mismatch',
                         details='The installed driver must match the bundled vJoy 2.2.2.0 SDK.')
            return state
        state.update(driver_ready=True, code='ready', details='vJoy 2.2.2.0 driver and SDK match.')
        sdk.GetVJDStatus.argtypes = [ctypes.c_uint]
        sdk.GetVJDStatus.restype = ctypes.c_int
        sdk.GetVJDButtonNumber.argtypes = [ctypes.c_uint]
        sdk.GetVJDButtonNumber.restype = ctypes.c_int
        sdk.GetVJDAxisExist.argtypes = [ctypes.c_uint, ctypes.c_uint]
        sdk.GetVJDAxisExist.restype = ctypes.c_bool
        device_status = sdk.GetVJDStatus(1)
        buttons = sdk.GetVJDButtonNumber(1)
        axes_ready = all(sdk.GetVJDAxisExist(1, axis) for axis in (0x30, 0x31, 0x33, 0x34))
        state.update(device_ready=True, device_status=device_status, buttons=buttons,
                     busy_devices=[device for device in range(1, 17) if sdk.GetVJDStatus(device) == 2])
        if device_status in (3, 4) or buttons < 24 or not axes_ready:
            state.update(device_ready=False, code='configure_virtual_device',
                         details='Configure vJoy device 1 with at least 24 buttons and X, Y, Rx, Ry axes.')
        elif device_status == 2:
            state.update(device_ready=False, code='virtual_device_busy',
                         details='Another feeder owns vJoy device 1. Close it and retry.')
    except (OSError, AttributeError, ImportError, ValueError):
        pass
    return state
