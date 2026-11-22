# Contributing / 参与贡献

Small focused changes are welcome. Before implementing a large change, open an issue describing the user problem and proposed behavior.

欢迎小而明确的改进。较大的功能请先开 issue，说明要解决的问题和预期行为。

## Development

Use Windows x64, Python 3.10, and the pinned dependencies. See [README](README.md) for source and build commands, and [architecture](docs/ARCHITECTURE.md) for module responsibilities.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --test tests/test_i18n.cjs
.\scripts\build-portable.ps1 -Python .\.venv\Scripts\python.exe
```

The full local build smoke includes passive Bluetooth scan/cancel. CI uses `-SkipBluetoothScan` because hosted runners have no physical adapter. Neither unit tests nor a CI build proves real controller or game compatibility; report the hardware checks separately.

完整本地构建包含被动蓝牙扫描与取消测试。CI 因没有实体适配器，使用 `-SkipBluetoothScan`。单元测试和 CI 构建不能替代真实手柄、游戏兼容性测试，请分别说明验证范围。

## Pull requests

- Explain the visible behavior that changes and how it was verified.
- Keep UI text in the English, Simplified Chinese and Traditional Chinese dictionaries. Add stable backend event keys rather than translating raw diagnostics in the browser.
- Keep original code separate from `vendor`; preserve upstream licenses and record any dependency changes in `NOTICE.md`.
- Include focused tests for changed behavior. For visual changes, include light/dark and narrow/wide screenshots.
- Exclude runtime logs, Bluetooth addresses, local configuration, credentials, build output and personal paths.

提交时请说明行为变化与验证结果；同步维护三语言文案。第三方代码保留在 `vendor` 并保留许可证。视觉修改附明暗与宽窄窗口截图。不要上传日志、蓝牙地址、凭据或本机配置。
