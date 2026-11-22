Joy-Con 2 Local Assistant 1.1.2 — Windows 10/11 x64

1. Extract the ENTIRE ZIP into a folder you own. Keep _internal and both EXEs.
2. Run JoyCon2Assistant.exe. No Python installation is needed.
3. Follow the environment check. If needed, choose Install vJoy to download,
   verify and open the official signed driver wizard. Complete its Windows
   administrator prompt, restart if requested, then choose Recheck.
   Official release: https://github.com/BrunnerInnovation/vJoy/releases/tag/v2.2.2.0
4. If asked, choose Configure controller to prepare vJoy device 1 with
   24 buttons and the original eight axes. This updates device 1 and requires
   administrator consent; close other vJoy apps first. An already-ready driver
   and controller configuration are left alone. Enable Bluetooth on the PC.
5. Select your language, connect the left controller and then the right.
   Use the small round sync button shown in the illustration.
6. Optional: run scripts/create-shortcut.ps1 to make a desktop shortcut.

Keep the Switch 2 asleep while pairing. Steam configuration is described in
the app. The driver wizard and configuration run only after your explicit
setup action. This utility does not change Windows security settings.

The assistant serves its offline page only on 127.0.0.1:19862. Closing the
browser keeps the service alive. Use the app's exit action to stop it.
Runtime logs go in runtime beside the EXE, with a LocalAppData fallback if
that folder is read-only. Bluetooth device addresses are redacted from logs.

This portable application is unsigned; no signing certificate is claimed.
The separately downloaded official vJoy driver is signed by its publisher.

See LICENSE, licenses/NOTICE.md and _internal/licenses for licenses, including the
LGPL pynput source and replacement/rebuild rights. Keep these notices when
redistributing. Source users launch with python -m joycon2_assistant.launcher
and build with scripts/build-portable.ps1. Developer notes are in
joycon2_assistant/README.md in the public source repository.
