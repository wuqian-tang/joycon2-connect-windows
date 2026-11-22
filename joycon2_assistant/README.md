# Developer guide

The player guide is the [repository README](../README.md). This document covers source layout, builds and implementation details.

## Repository layout

```text
joycon2-connect-windows/
├── joycon2_assistant/     # Python package and offline static/ frontend
├── installer/            # Frozen entry points, spec, build requirements and setup recipe
├── scripts/              # Build, verify, icon and shortcut utilities
├── tests/                # Backend contracts and frontend preferences
├── assets/               # Reproducible transparent app icons
├── docs/                 # Screenshots and release history
├── vendor/               # Pinned upstream controller support and SDK
├── licenses/             # Dependency notices, license texts and required sources
├── .github/              # Release automation and contribution templates
├── LICENSE
└── README.md
```

The layout follows the separation of application, tests, assets, documentation and automation used by [BetterJoy](https://github.com/Davidobot/BetterJoy), [HidHide](https://github.com/nefarius/HidHide) and [Bleak](https://github.com/hbldh/bleak). Generated runtime data, build output and local configuration are ignored by Git.

## Run and build

Use Windows x64, Python **3.10**, PowerShell and Node.js for frontend tests. Pinned dependencies were verified with Python 3.10.6. Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r installer/requirements-build.txt
.\.venv\Scripts\python.exe -m joycon2_assistant.launcher
```

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --test tests/test_i18n.cjs
.\scripts\build-portable.ps1 -Python .\.venv\Scripts\python.exe
```

The portable build tests the source, builds both EXEs and verifies a real packaged service on a private port. The local smoke also tests passive Bluetooth scan/cancel. Hosted CI uses `-SkipBluetoothScan` because its runner has no adapter. These checks do not prove real controller or game compatibility.

Output is `dist/JoyCon2Assistant`, plus a ZIP and SHA-256 file in `releases`. Keep both EXEs and `_internal` together. Build the installer with the official Inno Setup compiler:

```powershell
.\scripts\build-setup.ps1 -SkipPortableBuild
```

The GitHub Windows runner provides the compiler. Locally, pass `-Compiler <path-to-ISCC.exe>` or use the optional verified `scripts/bootstrap-inno.ps1`. Installer languages follow the OS: English, Simplified Chinese or Traditional Chinese.

The frontend is plain HTML/CSS/JavaScript, with no npm build or CDN. Rebuild SVG, multi-size ICO and PNG icons with `python scripts/make_icon.py` after installing build dependencies.

## Runtime architecture

```text
Browser ← loopback HTTP → Server ← JSON pipes → Worker ← BLE controllers
                                                  ↓
                                             vJoy device
                                                  ↓
                                              Steam/game
```

- `launcher.py`: singleton startup and browser launch.
- `server.py`: local API and fixed static-asset routes.
- `bridge.py`: worker lifecycle, normalized status and localized event keys.
- `worker.py` / `protocol.py`: advertisements, input parsing and forwarding.
- `driver.py` / `prerequisites.py`: driver readiness and explicit setup actions.
- `paths.py`: source/frozen resources, writable runtime and version.

The windowed launcher and console worker are separate EXEs so JSON pipes remain usable. The UI displays actual received input. Closing the browser retains the service; explicit exit stops the worker and server.

## Driver and compatibility

Use [official Brunner vJoy 2.2.2.0](https://github.com/BrunnerInnovation/vJoy/releases/tag/v2.2.2.0). Device 1 needs at least 24 buttons and X/Y/Rx/Ry. Guided configuration enables all eight original axes to keep established Steam axis indices stable.

The SDK DLL is not a system driver. Setup downloads a fixed official installer, verifies SHA-256 and its Windows signature, and opens its interactive wizard. Configuration is explicit and blocked while a feeder is active. Ready drivers are not reinstalled. The app/setup EXEs are currently unsigned.

Output is DirectInput vJoy; games may need Steam Input. Initial hardware checks used Windows 10 and vJoy 2.2.2.0. Adapters and Windows installations can differ. Windows ARM, original Joy-Con and Switch 2 Pro Controller are outside the tested scope.

## Preferences and local data

Initial language follows the first system preference: supported English, Simplified Chinese or Traditional Chinese (Taiwan), otherwise English. Manual language/theme choices persist in this browser. Theme initially follows the OS; reduced-motion preferences disable animations.

Normal use is offline. Optional driver setup downloads its fixed official GitHub release; Steam/driver links open external services. There is no account, analytics or cloud service.

The server binds to `127.0.0.1:19862`, validates Host/Origin and uses a per-run action token. Logs go in `runtime` beside the app, with `%LOCALAPPDATA%\JoyCon2Assistant\runtime` as a read-only-folder fallback. Normal logs redact Bluetooth addresses. Do not publish runtime data or personal configuration.

## Licenses and contributions

Original code and drawings use [MIT](../LICENSE). Third-party components retain their licenses; see [notices](../licenses/NOTICE.md), including the replaceable LGPL pynput source and rebuild instructions. Preserve notices when redistributing.

See [contributing](../.github/CONTRIBUTING.md). This community tool is unaffiliated with Nintendo, Microsoft or Valve.
