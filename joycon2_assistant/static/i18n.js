(function (root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.JC2I18n = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const STORAGE_KEY = "jc2-language";
  const THEME_STORAGE_KEY = "jc2-theme";
  const choices = ["system", "en", "zh-CN", "zh-TW"];
  function normalizeChoice(choice) {
    return choices.includes(choice) ? choice : "system";
  }
  function resolveSystemLocale(languages) {
    const first = Array.isArray(languages) ? languages[0] : languages;
    const tag =
      typeof first === "string"
        ? first.trim().toLowerCase().replace(/_/g, "-")
        : "";
    if (/^en(?:-|$)/.test(tag)) return "en";
    if (tag === "zh" || /^zh-(?:cn|hans)(?:-|$)/.test(tag)) return "zh-CN";
    if (/^zh-(?:tw|hant)(?:-|$)/.test(tag)) return "zh-TW";
    return "en";
  }
  function resolveLocale(choice, languages) {
    const selected = normalizeChoice(choice);
    return selected === "system" ? resolveSystemLocale(languages) : selected;
  }
  function readChoice(storage) {
    try {
      return normalizeChoice(storage.getItem(STORAGE_KEY));
    } catch (_) {
      return "system";
    }
  }
  function saveChoice(storage, choice) {
    try {
      storage.setItem(STORAGE_KEY, normalizeChoice(choice));
    } catch (_) {
      /* Private browsing may block storage. */
    }
  }
  function normalizeThemeChoice(choice) {
    return choice === "light" || choice === "dark" ? choice : "system";
  }
  function resolveTheme(choice, systemDark) {
    const selected = normalizeThemeChoice(choice);
    return selected === "system" ? (systemDark ? "dark" : "light") : selected;
  }
  function toggleTheme(theme) {
    return theme === "dark" ? "light" : "dark";
  }
  function readThemeChoice(storage) {
    try {
      return normalizeThemeChoice(storage.getItem(THEME_STORAGE_KEY));
    } catch (_) {
      return "system";
    }
  }
  function saveThemeChoice(storage, choice) {
    try {
      storage.setItem(THEME_STORAGE_KEY, normalizeThemeChoice(choice));
    } catch (_) {
      /* Session choice remains available. */
    }
  }
  const rows = {
    app_title: [
      "Joy-Con 2 Connection Assistant",
      "Joy-Con 2 连接助手",
      "Joy-Con 2 連線助手",
    ],
    app_short: ["Connection Assistant", "连接助手", "連線助手"],
    language: ["Language", "语言", "語言"],
    switch_dark: ["Switch to dark theme", "切换为深色主题", "切換為深色主題"],
    switch_light: ["Switch to light theme", "切换为浅色主题", "切換為淺色主題"],
    connection_progress: ["Connection progress", "连接进度", "連線進度"],
    flow_environment: ["Check PC", "检查环境", "檢查環境"],
    flow_left: ["Pair left", "配对左手", "配對左側"],
    flow_right: ["Pair right", "配对右手", "配對右側"],
    flow_test: ["Test & play", "测试与游戏", "測試與遊戲"],
    setup_heading: ["Set up this PC", "准备电脑环境", "準備電腦環境"],
    install_driver: ["Install vJoy", "安装 vJoy", "安裝 vJoy"],
    configure_device: [
      "Configure controller",
      "配置虚拟手柄",
      "設定虛擬控制器",
    ],
    recheck_environment: ["Recheck", "重新检查", "重新檢查"],
    setup_launched: [
      "Setup opened. Finish the Windows installer, then choose Recheck.",
      "已打开安装程序。请完成 Windows 安装向导后，点击“重新检查”。",
      "已開啟安裝程式。請完成 Windows 安裝精靈後，點選「重新檢查」。",
    ],
    configuration_saved: [
      "Controller configuration updated. Checking again…",
      "虚拟手柄配置已更新，正在重新检查…",
      "虛擬控制器設定已更新，正在重新檢查…",
    ],
    driver_download_progress: [
      "Driver download progress",
      "驱动下载进度",
      "驅動程式下載進度",
    ],
    setup_idle: [
      "Check this PC before connecting.",
      "连接前先检查电脑环境。",
      "連線前先檢查電腦環境。",
    ],
    setup_downloading: [
      "Downloading the official vJoy installer…",
      "正在下载官方 vJoy 安装程序…",
      "正在下載官方 vJoy 安裝程式…",
    ],
    setup_installer_opened: [
      "Complete the vJoy installer and approve the Windows prompt. Then choose Recheck.",
      "请完成 vJoy 安装向导并允许 Windows 提示，然后点击“重新检查”。",
      "請完成 vJoy 安裝精靈並允許 Windows 提示，然後點選「重新檢查」。",
    ],
    setup_configuring: [
      "Configuring the virtual controller…",
      "正在配置虚拟手柄…",
      "正在設定虛擬控制器…",
    ],
    setup_ready: [
      "This PC is ready. Start connecting your controllers.",
      "电脑环境已就绪，可以开始连接手柄。",
      "電腦環境已就緒，可以開始連接控制器。",
    ],
    setup_failed: [
      "Setup could not be completed. Check the Windows installer, then try again.",
      "安装未完成。请查看 Windows 安装程序后重试。",
      "安裝未完成。請查看 Windows 安裝程式後再試一次。",
    ],
    setup_busy: [
      "Setup is already in progress. Finish the current step first.",
      "安装或配置正在进行，请先完成当前步骤。",
      "安裝或設定正在進行，請先完成目前步驟。",
    ],
    setup_download_failed: [
      "The driver download failed. Check your internet connection and try again.",
      "驱动下载失败。请检查网络连接后重试。",
      "驅動程式下載失敗。請檢查網路連線後再試一次。",
    ],
    setup_cancelled: [
      "Setup was cancelled. Run it again when you are ready.",
      "安装已取消，可以重新开始。",
      "安裝已取消，可以重新開始。",
    ],
    setup_config_tool_missing: [
      "The vJoy configuration tool was not found. Repair the official vJoy installation, then recheck.",
      "未找到 vJoy 配置工具。请修复官方 vJoy 安装后重新检查。",
      "找不到 vJoy 設定工具。請修復官方 vJoy 安裝後重新檢查。",
    ],
    language_system: ["System", "跟随系统", "跟隨系統"],
    nav_devices: ["Controllers", "手柄", "控制器"],
    nav_guide: ["Pairing guide", "配对指引", "配對指引"],
    nav_help: ["Help & activity", "帮助与记录", "說明與紀錄"],
    navigation: ["Page navigation", "页面导航", "頁面導覽"],
    heading: ["Controllers", "手柄连接", "控制器連線"],
    intro: [
      "Connect both Joy-Con 2 controllers and test every input here.",
      "连接左右 Joy-Con 2，在这里实时测试摇杆和按键。",
      "連接左右 Joy-Con 2，在這裡即時測試搖桿與按鍵。",
    ],
    local_running: ["Local service online", "本机服务运行中", "本機服務執行中"],
    local_checking: [
      "Checking local service…",
      "正在检查本机服务…",
      "正在檢查本機服務…",
    ],
    local_offline: ["Local service offline", "本机服务离线", "本機服務離線"],
    local_only: ["Runs on this PC", "只在这台电脑上运行", "只在這台電腦上執行"],
    offline_private: [
      "Offline. No account needed.",
      "离线可用，无需账号。",
      "離線可用，無須帳號。",
    ],
    exit: ["Disconnect & exit", "断开并退出", "中斷並結束"],
    exit_title: ["Exit the assistant", "退出助手", "結束助手"],
    connection: ["Connection", "设备连接", "裝置連線"],
    phase_tag_idle: ["Ready to connect", "准备连接", "準備連線"],
    phase_tag_busy: ["Pairing", "正在配对", "正在配對"],
    phase_tag_connected: ["Connected", "已连接", "已連線"],
    phase_tag_error: ["Needs attention", "需要处理", "需要處理"],
    title_idle: ["Connect your controllers", "连接左右手柄", "連接左右控制器"],
    title_starting: ["Getting things ready…", "正在准备连接…", "正在準備連線…"],
    title_scanning_left: [
      "Pair the left controller.",
      "先配对左手。",
      "先配對左側控制器。",
    ],
    title_connecting_left: [
      "Connecting the left side…",
      "正在连接左手…",
      "正在連接左側控制器…",
    ],
    title_scanning_right: [
      "Now pair the right one.",
      "现在，配对右手。",
      "現在，配對右側控制器。",
    ],
    title_connecting_right: [
      "Connecting the right side…",
      "正在连接右手…",
      "正在連接右側控制器…",
    ],
    title_connected: [
      "Both controllers ready",
      "左右手柄已就绪",
      "左右控制器已就緒",
    ],
    title_stopping: [
      "Disconnecting safely…",
      "正在安全断开…",
      "正在安全中斷連線…",
    ],
    title_error: ["Connection interrupted", "连接中断", "連線中斷"],
    title_external: [
      "Another bridge is running.",
      "发现其他连接程序。",
      "發現其他連線程式。",
    ],
    phase_idle: [
      "Put the Switch 2 console to sleep, then start connecting. Pair the left controller first, followed by the right.",
      "先让 Switch 2 主机进入睡眠，再开始连接。助手会先配对左手，再配对右手。",
      "先讓 Switch 2 主機進入睡眠，再開始連線。助手會先配對左側，再配對右側控制器。",
    ],
    phase_starting: [
      "Preparing the Bluetooth connection and virtual controller.",
      "正在准备蓝牙连接和虚拟手柄。",
      "正在準備藍牙連線與虛擬控制器。",
    ],
    phase_scanning_left: [
      "Hold the small round SYNC button on the left controller’s magnetic inner edge until the four lights cycle.",
      "长按左手磁吸内侧的小圆同步键，直到四灯循环闪烁。",
      "長按左側控制器磁吸內側的小圓形同步鍵，直到四燈循環閃爍。",
    ],
    phase_connecting_left: [
      "Left controller found. Keep it nearby while the connection completes.",
      "已找到左手，请放在电脑附近，等待连接完成。",
      "已找到左側控制器，請放在電腦附近，等待連線完成。",
    ],
    phase_scanning_right: [
      "Left side ready. Now hold the right controller’s small round SYNC button until the four lights cycle.",
      "左手已就绪。现在长按右手的小圆同步键，直到四灯循环闪烁。",
      "左側已就緒。現在長按右側控制器的小圓形同步鍵，直到四燈循環閃爍。",
    ],
    phase_connecting_right: [
      "Right controller found. Finishing the connection…",
      "已找到右手，正在完成连接…",
      "已找到右側控制器，正在完成連線…",
    ],
    phase_connected: [
      "Both controllers are connected. Move the sticks or press a button to check your inputs, then open Steam.",
      "左右手柄已连接。移动摇杆或按下按键确认输入，然后打开 Steam。",
      "左右控制器已連線。移動搖桿或按下按鍵確認輸入，然後開啟 Steam。",
    ],
    phase_stopping: [
      "Disconnecting the controllers and stopping the connection process.",
      "正在断开手柄并停止连接程序。",
      "正在中斷控制器連線並停止連線程式。",
    ],
    phase_error: [
      "The connection was interrupted. Check the message below, then reconnect.",
      "连接已中断。请查看下方提示后重新连接。",
      "連線已中斷。請查看下方提示後重新連線。",
    ],
    phase_external: [
      "Close the older Start-Joy2Win.cmd connection window, then choose Check again.",
      "请先关闭用 Start-Joy2Win.cmd 打开的旧版连接窗口，再点击“重新检测”。",
      "請先關閉用 Start-Joy2Win.cmd 開啟的舊版連線視窗，再點選「重新偵測」。",
    ],
    connect: ["Start connecting", "开始连接", "開始連線"],
    reconnect: ["Reconnect", "重新连接", "重新連線"],
    check_again: ["Check again", "重新检测", "重新偵測"],
    connecting: ["Connecting…", "正在连接…", "正在連線…"],
    disconnect: ["Disconnect", "断开连接", "中斷連線"],
    cancel: ["Cancel connection", "取消连接", "取消連線"],
    open_steam: ["Open Steam", "打开 Steam", "開啟 Steam"],
    steam_opened: [
      "Steam launch requested.",
      "已请求打开 Steam。",
      "已要求開啟 Steam。",
    ],
    footnote_idle: [
      "Charge both controllers and keep them near this PC.",
      "请为手柄充电，并放在电脑附近。",
      "請為控制器充電，並放在電腦附近。",
    ],
    footnote_busy: [
      "Keep the console asleep. Pair only the side requested.",
      "让主机保持睡眠，只配对当前提示的那一只。",
      "讓主機保持睡眠，只配對目前提示的那一側。",
    ],
    footnote_connected: [
      "You can close this page. Keep the assistant running while playing.",
      "可以关闭网页，游戏时请保持助手运行。",
      "可以關閉網頁，遊戲時請保持助手執行。",
    ],
    driver_ready: [
      "Virtual controller ready",
      "虚拟手柄已就绪",
      "虛擬控制器已就緒",
    ],
    driver_checking: [
      "Checking virtual controller",
      "正在检查虚拟手柄",
      "正在檢查虛擬控制器",
    ],
    driver_unavailable: [
      "Virtual controller needs attention",
      "虚拟手柄需要处理",
      "虛擬控制器需要處理",
    ],
    technical_details: ["Technical details", "技术详情", "技術詳細資料"],
    controllers: ["Input test", "输入测试", "輸入測試"],
    count_connected: [
      "{count} / 2 connected",
      "{count} / 2 已连接",
      "{count} / 2 已連線",
    ],
    live_hint: [
      "Input is shown only when received from your controllers.",
      "只显示手柄实际传来的输入。",
      "只顯示控制器實際傳來的輸入。",
    ],
    left_name: ["Left Joy-Con 2", "左手 Joy-Con 2", "左側 Joy-Con 2"],
    right_name: ["Right Joy-Con 2", "右手 Joy-Con 2", "右側 Joy-Con 2"],
    left_subtitle: ["Movement & direction", "移动与方向", "移動與方向"],
    right_subtitle: ["Camera & action", "视角与操作", "視角與操作"],
    connected: ["Connected", "已连接", "已連線"],
    disconnected: ["Not connected", "未连接", "未連線"],
    pairing: ["Waiting to pair", "等待配对", "等待配對"],
    badge_connecting: ["Connecting", "连接中", "連線中"],
    waiting_connection: ["Waiting for connection", "等待连接", "等待連線"],
    waiting_input: ["Waiting for input", "等待输入", "等待輸入"],
    input_received: ["Receiving input", "正在接收输入", "正在接收輸入"],
    press_to_test: [
      "Move a stick or press any button.",
      "移动摇杆，或按下任意按键。",
      "移動搖桿，或按下任意按鍵。",
    ],
    connect_to_test: [
      "Connect to test your controls.",
      "连接后即可测试摇杆和按键。",
      "連線後即可測試搖桿與按鍵。",
    ],
    pressed_buttons: [
      "Pressed: {buttons}",
      "按下：{buttons}",
      "按下：{buttons}",
    ],
    packet_count: [
      "{count} input packets",
      "已接收 {count} 帧输入",
      "已接收 {count} 筆輸入",
    ],
    bluetooth: ["Bluetooth", "蓝牙连接", "藍牙連線"],
    sync_hint: [
      "Hold the small round SYNC button.",
      "请长按小圆同步键。",
      "請長按小圓形同步鍵。",
    ],
    front_view: ["Front view", "正面", "正面"],
    inner_controls: ["Inner edge", "内侧按键", "內側按鍵"],
    axes: ["Stick position", "摇杆位置", "搖桿位置"],
    guide_eyebrow: ["Pairing guide", "配对指引", "配對指引"],
    guide_title: ["Find the SYNC button", "找到同步键", "找到同步鍵"],
    guide_intro: [
      "Look at the magnetic inner edge: the small round button sits below the long black connector, between the SL and SR buttons.",
      "查看手柄磁吸内侧：小圆同步键在黑色长条接口下方，位于 SL、SR 两条长按键之间。",
      "查看控制器磁吸內側：小圓形同步鍵在黑色長條接點下方，位於 SL、SR 兩條長按鍵之間。",
    ],
    step_left_title: ["Pair the left side first", "先配对左手", "先配對左側"],
    step_left_text: [
      "Hold SYNC on the blue inner edge. Release when the four lights start cycling.",
      "长按蓝色内侧的小圆同步键，四灯循环闪烁后松开。",
      "長按藍色內側的小圓形同步鍵，四燈循環閃爍後放開。",
    ],
    step_right_title: ["Then pair the right side", "再配对右手", "再配對右側"],
    step_right_text: [
      "When prompted, repeat on the right controller’s orange inner edge.",
      "网页提示后，对橘色内侧的右手重复同样操作。",
      "網頁提示後，對橘色內側的右側控制器重複相同步驟。",
    ],
    step_done_title: [
      "Test your controls. Open Steam.",
      "测试输入，然后打开 Steam",
      "測試輸入，然後開啟 Steam",
    ],
    step_done_text: [
      "When both cards say Connected, move both sticks and check the buttons above.",
      "两张卡片均显示“已连接”后，移动摇杆并测试上方按键。",
      "兩張卡片皆顯示「已連線」後，移動搖桿並測試上方按鍵。",
    ],
    guide_zoom: [
      "Enlarge the SYNC button guide",
      "放大同步键位置图",
      "放大同步鍵位置圖",
    ],
    guide_alt: [
      "Original diagram of both magnetic inner edges. The small round SYNC button is circled below each black connector, between SL and SR.",
      "原创示意图：左右手柄磁吸内侧，黑色接口下方、SL 和 SR 之间的小圆同步键已圈出。",
      "原創示意圖：左右控制器磁吸內側，黑色接點下方、SL 和 SR 之間的小圓形同步鍵已圈出。",
    ],
    guide_caption: [
      "SYNC is circled. Select to enlarge.",
      "圆圈内是同步键 · 点击放大",
      "圓圈內是同步鍵 · 點選放大",
    ],
    guide_dialog_caption: [
      "Hold the circled round button until the four lights cycle.",
      "按住圈内的小圆按钮，直到四灯循环闪烁。",
      "按住圈內的小圓形按鈕，直到四燈循環閃爍。",
    ],
    close_guide: ["Close diagram", "关闭图示", "關閉圖示"],
    help: ["Help", "常见问题", "常見問題"],
    faq_lights_title: [
      "Lights cycle, but it will not connect",
      "四灯闪烁，却一直连不上",
      "四燈閃爍，卻一直連不上",
    ],
    faq_lights_text: [
      "Make sure you are holding the small round SYNC button shown above and keep the Switch 2 console asleep. Hold SYNC for about 3 seconds and release; wait for the lights to turn off, then hold it again to enter a fresh pairing session.",
      "确认按的是上图中的小圆同步键，并让 Switch 2 主机保持睡眠。按住同步键约 3 秒后松开，等灯全灭，再长按一次进入新的配对模式。",
      "確認按的是上圖中的小圓形同步鍵，並讓 Switch 2 主機保持睡眠。按住同步鍵約 3 秒後放開，等燈全滅，再長按一次進入新的配對模式。",
    ],
    faq_steam_title: [
      "Steam sees the controller, but a game does not",
      "Steam 测试通过，游戏却没反应",
      "Steam 測試通過，遊戲卻沒反應",
    ],
    faq_steam_text: [
      "In your Steam Library, right-click the game and open Properties → Controller → Enable Steam Input. Restart the game after changing this setting. An XInput Controller label is normal.",
      "在 Steam 收藏库中右键游戏，选择“属性 → 控制器 → 启用 Steam 输入”，然后重新启动游戏。显示 XInput Controller 是正常的。",
      "在 Steam 收藏庫中以滑鼠右鍵點選遊戲，選擇「內容 → 控制器 → 啟用 Steam 輸入」，然後重新啟動遊戲。顯示 XInput Controller 是正常的。",
    ],
    faq_close_title: [
      "Can I close this page?",
      "可以关闭网页吗？",
      "可以關閉網頁嗎？",
    ],
    faq_close_text: [
      "Yes. The connection service continues in the background. Use Disconnect to stop the controllers, or Disconnect & exit to also stop the assistant. Reopen it with the desktop shortcut.",
      "可以。连接服务会继续在后台运行。点击“断开连接”可断开手柄；点击“断开并退出”还会停止助手。可通过桌面快捷方式重新打开。",
      "可以。連線服務會繼續在背景執行。點選「中斷連線」可中斷控制器；點選「中斷並結束」也會停止助手。可透過桌面捷徑重新開啟。",
    ],
    faq_legacy_title: [
      "An older connection process is running",
      "提示旧版连接程序正在运行",
      "提示舊版連線程式正在執行",
    ],
    faq_legacy_text: [
      "Close the window opened with Start-Joy2Win.cmd, then choose Check again. Only one connection process can use the controllers at a time.",
      "请先关闭用 Start-Joy2Win.cmd 打开的连接窗口，再点击“重新检测”。同一时间只能运行一份连接程序。",
      "請先關閉用 Start-Joy2Win.cmd 開啟的連線視窗，再點選「重新偵測」。同一時間只能執行一份連線程式。",
    ],
    activity: ["Connection activity", "连接记录", "連線紀錄"],
    live_updates: ["Live updates", "实时更新", "即時更新"],
    empty_activity: [
      "Your connection steps will appear here.",
      "连接过程会显示在这里。",
      "連線過程會顯示在這裡。",
    ],
    empty_activity_detail: [
      "Start connecting to see progress and tips.",
      "开始连接后，进度和提示会自动记录。",
      "開始連線後，進度與提示會自動記錄。",
    ],
    footer: [
      "A small bridge to your next game.",
      "连接交给助手，冒险留给你。",
      "連線交給助手，冒險留給你。",
    ],
    offline_title: [
      "Cannot reach the assistant.",
      "暂时联系不到连接助手。",
      "暫時聯絡不到連線助手。",
    ],
    offline_message: [
      "Open the desktop Connection Assistant shortcut again. If it has just started, give it a moment.",
      "请通过桌面上的连接助手快捷方式重新打开。如果刚刚启动，请稍候。",
      "請透過桌面上的連線助手捷徑重新開啟。如果剛剛啟動，請稍候。",
    ],
    state_unavailable: [
      "Status unavailable",
      "状态暂不可用",
      "狀態暫時無法取得",
    ],
    state_unknown: ["Status unknown", "状态未知", "狀態未知"],
    exiting: ["Exiting the assistant…", "正在退出助手…", "正在結束助手…"],
    exited: ["Assistant has exited", "助手已退出", "助手已結束"],
    exit_heading: [
      "Disconnecting and exiting…",
      "正在断开并退出…",
      "正在中斷並結束…",
    ],
    exit_message: [
      "The assistant is safely disconnecting your controllers before stopping the service.",
      "助手正在安全断开手柄，完成后会结束后台服务。",
      "助手正在安全中斷控制器連線，完成後會結束背景服務。",
    ],
    exited_heading: [
      "See you next game.",
      "下次游戏，再见。",
      "下次遊戲，再見。",
    ],
    exited_message: [
      "The background service has stopped. Use the desktop shortcut to open the assistant next time.",
      "后台服务已退出。下次可通过桌面快捷方式重新打开。",
      "背景服務已結束。下次可透過桌面捷徑重新開啟。",
    ],
    exit_pending: [
      "The assistant is still exiting. Please wait a moment.",
      "助手仍在退出，请稍候。",
      "助手仍在結束中，請稍候。",
    ],
    request_failed: [
      "The action could not be completed. Please try again.",
      "操作未完成，请重试。",
      "操作未完成，請再試一次。",
    ],
    request_timeout: [
      "The assistant took too long to respond. Please try again.",
      "助手响应超时，请重试。",
      "助手回應逾時，請再試一次。",
    ],
    steam_unavailable: [
      "Steam was not found. Open it from your desktop.",
      "没有找到 Steam，请从桌面手动打开。",
      "找不到 Steam，請從桌面手動開啟。",
    ],
    refresh_required: [
      "Refresh this page and try again.",
      "请刷新页面后重试。",
      "請重新整理頁面後再試一次。",
    ],
    required_version: [
      "Required vJoy: {version}",
      "所需 vJoy：{version}",
      "所需 vJoy：{version}",
    ],
    sdk_version: [
      "Interface version: {version}",
      "接口版本：{version}",
      "介面版本：{version}",
    ],
    driver_version: [
      "Driver version: {version}",
      "驱动版本：{version}",
      "驅動程式版本：{version}",
    ],
    start_session: [
      "Starting a new connection: left side, then right.",
      "开始新连接，先左手，再右手。",
      "開始新連線，先左側，再右側。",
    ],
    stopped: [
      "Controllers disconnected.",
      "手柄已断开。",
      "控制器已中斷連線。",
    ],
    reconnect_mode: [
      "The controller is reconnecting to a console. Hold SYNC again to start a fresh pairing session.",
      "手柄正在回连主机，请再次长按同步键进入新的配对模式。",
      "控制器正在重新連接主機，請再次長按同步鍵進入新的配對模式。",
    ],
    gatt_unreachable: [
      "Bluetooth could not reach the controller. Keep it close and enter pairing mode again.",
      "蓝牙无法访问手柄。请将其靠近电脑，并重新进入配对模式。",
      "藍牙無法存取控制器。請將它靠近電腦，並重新進入配對模式。",
    ],
    connection_timeout: [
      "Pairing timed out. Hold the small round SYNC button again, then reconnect.",
      "配对超时。请再次长按小圆同步键，然后重新连接。",
      "配對逾時。請再次長按小圓形同步鍵，然後重新連線。",
    ],
    virtual_device_unavailable: [
      "The virtual controller is unavailable. Close other controller bridges and check the vJoy driver.",
      "虚拟手柄不可用。请关闭其他手柄连接程序，并检查 vJoy 驱动。",
      "虛擬控制器無法使用。請關閉其他控制器連線程式，並檢查 vJoy 驅動程式。",
    ],
    configure_virtual_device: [
      "Configure vJoy device 1 with at least 24 buttons and the X, Y, Rx, and Ry axes, then reconnect.",
      "请将 vJoy 设备 1 配置为至少 24 个按键，并启用 X、Y、Rx、Ry 轴，然后重新连接。",
      "請將 vJoy 裝置 1 設定為至少 24 個按鍵，並啟用 X、Y、Rx、Ry 軸，然後重新連線。",
    ],
    virtual_device_busy: [
      "Another controller bridge is using vJoy device 1. Close it, then reconnect.",
      "其他手柄连接程序正在使用 vJoy 设备 1。请将其关闭后重新连接。",
      "其他控制器連線程式正在使用 vJoy 裝置 1。請將它關閉後重新連線。",
    ],
    disconnected_left: [
      "Left controller disconnected.",
      "左手已断开。",
      "左側控制器已中斷連線。",
    ],
    disconnected_right: [
      "Right controller disconnected.",
      "右手已断开。",
      "右側控制器已中斷連線。",
    ],
    input_interrupted: [
      "Controller input was interrupted. Reconnect to resume.",
      "手柄输入已中断，请重新连接。",
      "控制器輸入已中斷，請重新連線。",
    ],
    bridge_exited: [
      "The connection process stopped unexpectedly. Reconnect to try again.",
      "连接程序意外退出，请重新连接。",
      "連線程式意外結束，請重新連線。",
    ],
    bridge_start_failed: [
      "The connection process could not start. Close other bridges and try again.",
      "连接程序无法启动，请关闭其他连接程序后重试。",
      "連線程式無法啟動，請關閉其他連線程式後再試一次。",
    ],
    legacy_bridge: [
      "An older connection bridge is running. Close its window and choose Check again.",
      "旧版连接程序正在运行。请关闭旧版窗口，再点击“重新检测”。",
      "舊版連線程式正在執行。請關閉舊版視窗，再點選「重新偵測」。",
    ],
    missing_driver: [
      "The vJoy driver was not found. Install or repair vJoy before connecting.",
      "未找到 vJoy 驱动。请安装或修复 vJoy 后再连接。",
      "找不到 vJoy 驅動程式。請安裝或修復 vJoy 後再連線。",
    ],
    version_mismatch: [
      "The vJoy driver and interface versions do not match. Repair the vJoy installation.",
      "vJoy 驱动与接口版本不一致，请修复 vJoy 安装。",
      "vJoy 驅動程式與介面版本不一致，請修復 vJoy 安裝。",
    ],
    unknown_error: [
      "The connection could not be completed. Check Bluetooth and the virtual controller, then try again.",
      "连接未完成。请检查蓝牙和虚拟手柄后重试。",
      "連線未完成。請檢查藍牙與虛擬控制器後再試一次。",
    ],
    unknown_event: [
      "Connection service update.",
      "连接服务更新。",
      "連線服務更新。",
    ],
    button_Left: ["Left", "左", "左"],
    button_Right: ["Right", "右", "右"],
    button_Up: ["Up", "上", "上"],
    button_Down: ["Down", "下", "下"],
    button_Capture: ["Capture", "截图", "擷取"],
    button_Home: ["HOME", "HOME", "HOME"],
    button_GameChat: ["C", "C", "C"],
    button_L3: ["Left stick", "左摇杆按下", "左搖桿按下"],
    button_R3: ["Right stick", "右摇杆按下", "右搖桿按下"],
  };
  const messages = { en: {}, "zh-CN": {}, "zh-TW": {} };
  for (const [key, values] of Object.entries(rows)) {
    ["en", "zh-CN", "zh-TW"].forEach((locale, index) => {
      messages[locale][key] = values[index];
    });
  }
  function t(locale, key, params) {
    const dictionary = messages[locale] || messages.en;
    const template = dictionary[key] || dictionary.unknown_event;
    return template.replace(/\{(\w+)\}/g, (_, name) =>
      params && params[name] != null ? String(params[name]) : "{" + name + "}",
    );
  }
  return {
    STORAGE_KEY,
    THEME_STORAGE_KEY,
    messages,
    normalizeChoice,
    resolveSystemLocale,
    resolveLocale,
    readChoice,
    saveChoice,
    normalizeThemeChoice,
    resolveTheme,
    toggleTheme,
    readThemeChoice,
    saveThemeChoice,
    t,
  };
});
