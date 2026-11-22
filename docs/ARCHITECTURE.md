# Project layout / 项目结构

```text
joycon2-connect-windows/
├── joycon2_assistant/     # Application package / 程序源码
│   ├── launcher.py       # Single service + browser startup
│   ├── server.py         # Loopback HTTP API and static assets
│   ├── bridge.py         # Worker lifecycle and status
│   ├── worker.py         # Bluetooth input to vJoy
│   ├── protocol.py       # Input / advertisement parsing
│   ├── driver.py         # Read-only driver prerequisites
│   ├── prerequisites.py  # Explicit official driver setup actions
│   ├── paths.py          # Source / frozen resource layout
│   └── static/           # Offline HTML, CSS, JS and SVG
├── assets/               # Original app / desktop icons
├── tests/                # Python and frontend preference tests
├── scripts/              # Build, verify, icon and shortcut tools
├── installer/            # Per-user Windows setup recipe and translations
├── docs/                 # Architecture and screenshots
├── vendor/               # Pinned upstream hardware support + licenses
├── licenses/             # Runtime dependency notices and required sources
├── .github/              # Release workflow, issue and PR templates
├── launcher.py           # Convenient source entry point
├── app.py                # Frozen GUI entry point
├── worker_entry.py       # Frozen console worker entry point
├── JoyCon2Assistant.spec  # Reproducible Windows packaging specification
├── README.md             # English / Chinese user guide
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
└── NOTICE.md
```

Generated `.venv`, `build`, `dist`, `releases` and `runtime` directories are not source and are ignored by Git. Source lives in an importable package; root entry points are intentionally thin. The portable ZIP contains the built program rather than this development tree.

自动生成的虚拟环境、构建产物、发布包与运行日志不进入源码仓库。业务代码放在可导入的程序包中；根目录只保留薄入口和项目配置。便携版 ZIP 供普通用户使用，源码树供开发者维护。

## Data flow / 数据流

```text
Browser ← loopback HTTP → Local server ← JSON pipes → Worker
                                                   ↓
                                          BLE Joy-Con 2 pair
                                                   ↓
                                          vJoy virtual device
                                                   ↓
                                            Steam / game
```

The UI renders actual received status. It does not access Bluetooth directly. The controller worker has its own console-compatible executable so its standard input/output remain usable even though the launcher is windowed. Closing the page retains the local service; the explicit exit action stops the worker and server.

网页只显示实际收到的状态，不直接操作蓝牙。工作进程使用独立的控制台兼容 EXE，以便在主程序隐藏窗口时仍能正常通过标准输入输出通信。关闭网页保留连接；显式退出会结束工作进程和本地服务。

## Organization references / 组织方式参考

The layout follows the separation of application, tests, assets, documentation and automation seen in [BetterJoy](https://github.com/Davidobot/BetterJoy), [HidHide](https://github.com/nefarius/HidHide), and Python BLE library [Bleak](https://github.com/hbldh/bleak). It is adapted to this small Python application; it does not reuse their application code or imply the same hardware support.

参考以上成熟项目对源码、测试、资源、文档和自动化的分工，并按本工具规模调整目录；这些参考不表示复用了它们的业务代码，也不表示具备相同的硬件支持范围。
