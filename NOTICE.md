# Third-party notices

Joy-Con 2 Local Assistant is an independent community utility. Nintendo,
Windows, Steam, and other product names belong to their respective owners.
This project is not affiliated with Nintendo, Microsoft, or Valve.

The assistant's original code and drawings are provided under LICENSE (MIT).
The following separately licensed components retain their own terms:

* **Joy2Win**, Logan Gaillard / Octokling, commit
  `932d6d7dc1a11402b019ac3ff88056dd4bb8d702`, MIT, copyright 2025 Logan Gaillard.
  The required unmodified source and sample configuration are in
  `vendor/joy2win`; the original license is `vendor/joy2win/LICENSE`.
  Source: https://github.com/Logan-Gaillard/Joy2Win/tree/932d6d7dc1a11402b019ac3ff88056dd4bb8d702
  The assistant uses a vertical pair, disables DSU and mouse mode, and does not
  save Bluetooth addresses. Personal `config.ini` files are not distributed.
* **vJoy SDK v2.2.2.0**, MIT, copyright 2017 Shaul Eizikovich.
  Only the x64 user-mode `vJoyInterface.dll` is included, with its original
  license in `vendor/vjoy/LICENSE.txt`. Source/release:
  https://github.com/BrunnerInnovation/vJoy/releases/tag/v2.2.2.0
  The signed system driver/installer is not redistributed. An explicit setup
  action downloads the unmodified official installer, verifies its pinned
  SHA-256 and Authenticode signature, and opens its interactive wizard.
  Existing matching drivers are not reinstalled. Device 1 configuration uses
  the installed official vJoyConfig tool only after an explicit setup action.
* **pynput 1.8.2**, copyright Moses Palmér and contributors, LGPLv3.
  The portable build keeps its unmodified Python source as replaceable files
  in `_internal/pynput` rather than embedding it in the Python archive.
  `licenses/sources` includes the complete corresponding source archive.
  You may modify or replace that directory with a compatible pynput build,
  and may rebuild this assistant with `scripts/build-portable.ps1` and a
  modified dependency. Reverse engineering for debugging your changes to this
  library is permitted. Full license: `licenses/pynput/COPYING.LGPL` and
  `licenses/pynput/COPYING.GPL`. Source: https://github.com/moses-palmer/pynput
* **Python 3.10.6**, PSF license and included historical licenses:
  `licenses/python/LICENSE.txt`; https://www.python.org/downloads/release/python-3106/
* **bleak 3.1.0**, **pyvjoy 1.0.1**, **six 1.17.0**: MIT.
* **async-timeout 5.0.1**: Apache License 2.0.
* **typing_extensions 4.16.0**: PSF-2.0.
* **PyWinRT 3.2.1 runtime and Windows namespace projections**: MIT;
  https://github.com/pywinrt/pywinrt/tree/v3.2.1
* **PyInstaller 6.22.0** bootloader: GPL-2.0-or-later with the PyInstaller
  distribution exception, permitting distribution of bundled applications
  under their own licenses. Build tools are not runtime application APIs.
* **Pillow 12.1.0** is used only to build the icon, MIT-CMU and bundled
  third-party notices in `licenses/Pillow`.
* **Inno Setup**, copyright Jordan Russell and Martijn Laan, is an optional
  installer build tool. Its license is in `licenses/InnoSetup`; official
  downloads: https://jrsoftware.org/inno-setup/downloads

The `licenses` directory contains the original dependency license texts and
the source package necessary for pynput. The public source and pinned build
dependencies allow rebuilding both executables. The Microsoft runtime DLLs
distributed by CPython/PyInstaller remain subject to Microsoft's terms.
