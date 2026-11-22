# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH)
datas = [(str(root / 'joycon2_assistant' / 'static'), 'joycon2_assistant/static'),
         (str(root / 'vendor' / 'joy2win'), 'vendor/joy2win'),
         (str(root / 'vendor' / 'vjoy'), 'vendor/vjoy'),
         (str(root / 'licenses'), 'licenses')]
binaries = []
hidden = ['main', 'config', 'controller_command', 'dsu_server',
          'control_type.duo_joycon', 'controllers.JoyconL', 'controllers.JoyconR',
          'pynput.mouse._win32', 'pynput.keyboard._win32']
for package in ('bleak', 'pyvjoy', 'pynput', 'winrt'):
    package_data, package_binaries, package_hidden = collect_all(package)
    datas += package_data
    binaries += package_binaries
    hidden += package_hidden

# pyvjoy's wheel can contain obsolete x86 DLLs and local backup files.
datas = [entry for entry in datas if not entry[1].replace('\\', '/').startswith('pyvjoy/utils')]
binaries = [entry for entry in binaries if not entry[1].replace('\\', '/').startswith('pyvjoy/utils')]
binaries.append((str(root / 'vendor' / 'vjoy' / 'vJoyInterface.dll'), 'pyvjoy/utils/x64'))

a = Analysis([str(root / 'app.py'), str(root / 'worker_entry.py')],
             pathex=[str(root), str(root / 'vendor' / 'joy2win')],
             binaries=binaries, datas=datas, hiddenimports=hidden,
             excludes=['tkinter', 'unittest', 'pynput.keyboard._darwin',
                       'pynput.keyboard._xorg', 'pynput.mouse._darwin', 'pynput.mouse._xorg'])
# The upstream hook also discovers both SDK architectures; retain our exact x64.
a.binaries = [entry for entry in a.binaries if
              not entry[0].replace('\\', '/').startswith('pyvjoy/utils/') or
              entry[0].replace('\\', '/') == 'pyvjoy/utils/x64/vJoyInterface.dll']
# LGPL pynput remains ordinary replaceable source files in _internal/pynput.
# collect_all includes the source tree; exclude its bytecode from the archive.
a.pure = [entry for entry in a.pure if entry[0] != 'pynput' and not entry[0].startswith('pynput.')]
pyz = PYZ(a.pure)
# Separate console bootloader is essential: --windowed sets sys.stdin/out to None.
main_scripts = [entry for entry in a.scripts if entry[0] != 'worker_entry']
worker_scripts = [entry for entry in a.scripts if entry[0] != 'app']
icon = str(root / 'assets' / 'app.ico')
assistant = EXE(pyz, main_scripts, [], exclude_binaries=True,
                name='JoyCon2Assistant', console=False, icon=icon,
                upx=False, contents_directory='_internal')
worker = EXE(pyz, worker_scripts, [], exclude_binaries=True,
             name='JoyCon2Worker', console=True, icon=icon,
             upx=False, contents_directory='_internal')
collection = COLLECT(assistant, worker, a.binaries, a.datas,
                     name='JoyCon2Assistant', upx=False)
