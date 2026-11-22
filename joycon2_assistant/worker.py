"""BLE/vJoy worker. Structured stdout is the only interface to the web service."""
from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sys
import threading
import time

from .driver import bind_pyvjoy_sdk, driver_environment
from .paths import RUNTIME_DIR, SOURCE
from .protocol import identify_advertisement


def emit(kind, **fields):
    print(json.dumps({'event': kind, **fields}, ensure_ascii=False), flush=True)


class StopRequested(Exception):
    pass


class UserFacingError(RuntimeError):
    def __init__(self, key, message):
        super().__init__(message)
        self.key = key


def describe_error(exc):
    raw = str(exc)
    if isinstance(exc, UserFacingError):
        return exc.key, raw
    if 'unreachable' in raw.lower():
        return 'gatt_unreachable', '蓝牙链路未建立。请让 Switch 2 睡眠，并长按正确的小圆同步键后重试。'
    if isinstance(exc, TimeoutError):
        return 'connection_timeout', '连接响应超时。请把手柄靠近电脑，重新进入配对模式后重试。'
    if 'vjoy' in (raw + type(exc).__name__).lower():
        return 'virtual_device_unavailable', '虚拟手柄当前不可用，可能被其他连接程序占用。请关闭旧版 Joy2Win 后重试。'
    return 'unknown_error', f'连接未完成（{type(exc).__name__}）。请断开后重试，详情见连接日志。'


def watch_stdin(loop, stop):
    def reader():
        try:
            for line in sys.stdin:
                if line.strip() == 'stop':
                    loop.call_soon_threadsafe(stop.set)
                    return
        finally:
            loop.call_soon_threadsafe(stop.set)
    threading.Thread(target=reader, daemon=True).start()


def load_upstream():
    # Bundled files remain read-only; never read a personal config.ini or save MACs.
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SOURCE))
    from config import Config
    settings = Config(str(SOURCE / 'config-example.ini'))
    for key, value in {'controller': 0, 'orientation': 0, 'mouse_mode': 0,
                       'enable_dsu': False, 'save_mac_address': False}.items():
        setattr(settings, key, value)
    import main as upstream
    upstream.config = settings.getConfig()
    return upstream


async def scan_only():
    """Diagnostic passive scan; does not connect to BLE devices or acquire vJoy."""
    from bleak import BleakScanner
    stop = asyncio.Event()
    watch_stdin(asyncio.get_running_loop(), stop)
    async with BleakScanner(lambda _device, _advertisement: None):
        emit('phase', phase='scanning_left')
        await stop.wait()
    emit('stopped')


async def interruptible(operation, stop, timeout=None):
    task = asyncio.ensure_future(operation)
    stop_task = asyncio.create_task(stop.wait())
    try:
        done, _ = await asyncio.wait({task, stop_task}, timeout=timeout,
                                     return_when=asyncio.FIRST_COMPLETED)
        if stop_task in done:
            raise StopRequested()
        if task not in done:
            raise TimeoutError()
        return await task
    finally:
        for item in (task, stop_task):
            if not item.done():
                item.cancel()
        await asyncio.gather(task, stop_task, return_exceptions=True)


async def run():
    from bleak import BleakClient, BleakScanner

    readiness = driver_environment()
    if not readiness['driver_ready'] or not readiness.get('device_ready', True):
        raise UserFacingError(readiness['code'], readiness['details'])
    os.chdir(RUNTIME_DIR)
    with contextlib.redirect_stdout(sys.stderr):
        bind_pyvjoy_sdk()
        upstream = load_upstream()
        import control_type.duo_joycon as duo

    loop = asyncio.get_running_loop()
    stop = asyncio.Event()
    clients = []
    cleaning = False
    disconnect_reason = None
    packets = {'Left': 0, 'Right': 0}
    emitted = {'Left': 0., 'Right': 0.}
    original_notify = duo.notify_duo_joycons

    async def observed_notify(client, side, data):
        nonlocal disconnect_reason
        try:
            await original_notify(client, side, data)
            packets[side] += 1
            now = time.monotonic()
            if now - emitted[side] >= 0.05:
                emitted[side] = now
                model = duo.joyconLeft if side == 'Left' else duo.joyconRight
                axes = [round(max(-1, min(1, (model.analog_stick[k] - 16384) / 16384)), 3)
                        for k in ('X', 'Y')]
                emit('input', side=side.lower(), packets=packets[side], axes=axes,
                     buttons=[k for k, pressed in model.buttons.items() if pressed])
        except Exception as exc:
            disconnect_reason = UserFacingError('input_interrupted',
                f'手柄输入中断：{type(exc).__name__}。请断开后重新连接。')
            stop.set()

    duo.notify_duo_joycons = observed_notify

    watch_stdin(loop, stop)

    def disconnected(side):
        def callback(_client):
            nonlocal disconnect_reason
            if not cleaning:
                disconnect_reason = UserFacingError('disconnected_' + side,
                    f'{"左手" if side == "left" else "右手"}连接已中断，请重新连接。')
                emit('side', side=side, connected=False)
                stop.set()
        return callback

    try:
        for side in ('left', 'right'):
            emit('phase', phase='scanning_' + side)
            found = asyncio.Event()
            target = None
            warned = False

            def advertisement(device, adv):
                nonlocal target, warned
                info = identify_advertisement(adv.manufacturer_data.get(0x0553, b''))
                if not info or info[0] != side:
                    return
                if not info[1]:
                    if not warned:
                        warned = True
                        emit('hint', key='reconnect_mode', params={},
                             message='检测到手柄正在回连原主机。请长按图中小圆同步键，进入新的配对模式。')
                    return
                if target is None:
                    target = device
                    found.set()

            async with BleakScanner(advertisement):
                await interruptible(found.wait(), stop)
            emit('phase', phase='connecting_' + side)
            client = BleakClient(target, timeout=20, disconnected_callback=disconnected(side))
            clients.append(client)
            await interruptible(client.connect(), stop, timeout=25)
            # Initialization and forwarding are exactly the already verified Joy2Win path.
            with contextlib.redirect_stdout(sys.stderr):
                await interruptible(upstream.handle_duo_joycons(client, side.capitalize()), stop, timeout=18)
            if not client.is_connected:
                raise UserFacingError('disconnected_' + side, '手柄在初始化时断开，请重新配对。')
            emit('side', side=side, connected=True)
        emit('phase', phase='connected')
        await stop.wait()
        if disconnect_reason:
            raise disconnect_reason
    except StopRequested:
        if disconnect_reason:
            raise disconnect_reason
    finally:
        cleaning = True
        for client in clients:
            if client.is_connected:
                try:
                    await asyncio.wait_for(client.disconnect(), timeout=3)
                except Exception:
                    pass
        try:
            duo.vjoy.reset()
        except Exception:
            pass
        emit('stopped')


def main():
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')
    try:
        if '--self-test' in sys.argv:
            # Imports only: no virtual-device acquisition or BLE connection.
            with contextlib.redirect_stdout(sys.stderr):
                load_upstream()
                bind_pyvjoy_sdk()
                import pynput.mouse
                import controllers.JoyconL
                import controllers.JoyconR
                import bleak
            emit('self_test', ok=True, environment=driver_environment())
            return 0
        asyncio.run(scan_only() if '--scan-only' in sys.argv else run())
        return 0
    except Exception as exc:
        raw = str(exc)
        key, message = describe_error(exc)
        emit('error', key=key, params={}, message=message)
        print(type(exc).__name__ + ': ' + raw, file=sys.stderr, flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
