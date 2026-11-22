"use strict";
const $ = (id) => document.getElementById(id);
const I18N = window.JC2I18n;
const token = document.querySelector('meta[name="jc2-token"]').content;
const busyPhases = [
  "starting",
  "scanning_left",
  "connecting_left",
  "scanning_right",
  "connecting_right",
  "stopping",
];
const sides = ["left", "right"];
const knownButtons = new Set([
  "ZL",
  "L",
  "Minus",
  "SLL",
  "SRL",
  "Left",
  "Down",
  "Up",
  "Right",
  "L3",
  "Capture",
  "ZR",
  "R",
  "Plus",
  "SLR",
  "SRR",
  "Y",
  "B",
  "X",
  "A",
  "R3",
  "Home",
  "GameChat",
]);
let storage;
try {
  storage = window.localStorage;
} catch (_) {
  /* A blocked store still permits a session choice. */
}
let languageChoice = I18N.readChoice(storage);
const preferredLanguages = () =>
  navigator.languages && navigator.languages.length
    ? Array.from(navigator.languages)
    : [navigator.language];
let locale = I18N.resolveLocale(languageChoice, preferredLanguages());
const themeMedia = window.matchMedia("(prefers-color-scheme: dark)");
let themeChoice = I18N.readThemeChoice(storage);
let theme = I18N.resolveTheme(themeChoice, themeMedia.matches);
let actionBusy = false,
  exiting = false,
  exitDone = false,
  serviceKnown = false,
  serviceReachable = false;
let polling = false,
  pollTimer,
  toastTimer,
  toastState = null,
  logSignature = "";
let current = { phase: "idle", running: false, sides: {}, logs: [] };
let lastFlowStep = -1;
const inputElements = Object.fromEntries(
  sides.map((side) => [
    side,
    Array.from($(side + "Controller").querySelectorAll("[data-input]")),
  ]),
);
const t = (key, params) => I18N.t(locale, key, params);
const hasMessage = (key) =>
  typeof key === "string" &&
  Object.prototype.hasOwnProperty.call(I18N.messages.en, key);
const codedMessage = (key, params, fallback) =>
  t(hasMessage(key) ? key : fallback, params);
const setText = (id, value) => {
  const element = $(id);
  if (element.textContent !== value) element.textContent = value;
};

function applyLanguage() {
  locale = I18N.resolveLocale(languageChoice, preferredLanguages());
  document.documentElement.lang = locale;
  document.title = t("app_title");
  $("languageSelect").value = locale;
  for (const element of document.querySelectorAll("[data-i18n]"))
    element.textContent = t(element.dataset.i18n);
  for (const element of document.querySelectorAll("[data-i18n-aria]"))
    element.setAttribute("aria-label", t(element.dataset.i18nAria));
  for (const element of document.querySelectorAll("[data-i18n-alt]"))
    element.setAttribute("alt", t(element.dataset.i18nAlt));
  applyTheme();
  logSignature = "";
  render(current);
  if (toastState) $("toast").textContent = t(toastState.key, toastState.params);
}

function applyTheme() {
  theme = I18N.resolveTheme(themeChoice, themeMedia.matches);
  document.documentElement.dataset.theme = theme;
  const label = t(theme === "dark" ? "switch_light" : "switch_dark");
  $("themeToggle").setAttribute("aria-label", label);
  $("themeToggle").title = label;
}

function actionError(key) {
  const error = new Error(key);
  error.key = key;
  return error;
}
async function request(path, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const options = { signal: controller.signal, cache: "no-store" };
    if (body !== undefined)
      Object.assign(options, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-JC2-Token": token },
        body: JSON.stringify(body),
      });
    const response = await fetch(path, options);
    const data = await response.json();
    if (!response.ok)
      throw actionError(
        hasMessage(data.error_key)
          ? data.error_key
          : path === "/api/open-steam"
            ? "steam_unavailable"
            : response.status === 403
              ? "refresh_required"
              : "request_failed",
      );
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw actionError("request_timeout");
    if (!error.key) throw actionError("request_failed");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

function toast(key, params) {
  toastState = { key, params };
  $("toast").textContent = t(key, params);
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    $("toast").hidden = true;
    toastState = null;
  }, 4500);
}

function axis(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(-1, Math.min(1, number)) : 0;
}
function buttonName(name) {
  const labels = {
    Minus: "−",
    Plus: "+",
    SLL: "SL",
    SRL: "SR",
    SLR: "SL",
    SRR: "SR",
  };
  return (
    labels[name] || (hasMessage("button_" + name) ? t("button_" + name) : name)
  );
}
function renderSide(side, sideData, phase) {
  const data = sideData || {};
  const connected = Boolean(data.connected) && serviceReachable && !exiting;
  const waiting = serviceReachable && !exiting && phase.endsWith("_" + side);
  const card = $(side + "Card");
  card.classList.toggle("connected", connected);
  card.classList.toggle("scanning", waiting && !connected);
  setText(
    side + "Badge",
    !serviceReachable && serviceKnown
      ? t("state_unknown")
      : connected
        ? t("connected")
        : waiting
          ? t(phase.startsWith("connecting") ? "badge_connecting" : "pairing")
          : t("disconnected"),
  );
  const packets =
    connected && Number.isFinite(Number(data.packets))
      ? Math.max(0, Math.floor(Number(data.packets)))
      : 0;
  setText(
    side + "InputLabel",
    t(
      connected
        ? packets
          ? "input_received"
          : "waiting_input"
        : "waiting_connection",
    ),
  );
  const axes = connected && Array.isArray(data.axes) ? data.axes : [0, 0];
  const x = axis(axes[0]),
    y = axis(axes[1]);
  $(side + "Stick").setAttribute(
    "transform",
    `translate(${(x * 12).toFixed(2)} ${(y * 12).toFixed(2)})`,
  );
  setText(side + "Axes", `X ${x.toFixed(2)} · Y ${y.toFixed(2)}`);
  const buttons =
    connected && Array.isArray(data.buttons)
      ? data.buttons.filter((name) => knownButtons.has(name))
      : [];
  const pressed = new Set(buttons);
  for (const element of inputElements[side])
    element.classList.toggle("active", pressed.has(element.dataset.input));
  setText(
    side + "Buttons",
    connected
      ? buttons.length
        ? t("pressed_buttons", { buttons: buttons.map(buttonName).join(" · ") })
        : t("press_to_test")
      : t("connect_to_test"),
  );
  $(side + "Buttons").classList.toggle("has-input", buttons.length > 0);
  setText(
    side + "Footer",
    t(waiting && !connected ? "sync_hint" : "bluetooth"),
  );
  setText(
    side + "Packets",
    t("packet_count", { count: packets.toLocaleString(locale) }),
  );
}

function renderEnvironment(environment) {
  const indicator = $("driverIndicator");
  const ready = Boolean(
    environment &&
      environment.driver_ready &&
      environment.device_ready !== false,
  );
  indicator.classList.toggle("ready", ready);
  indicator.classList.toggle("error", Boolean(environment && !ready));
  setText(
    "driverStatus",
    environment
      ? t(ready ? "driver_ready" : "driver_unavailable")
      : t("driver_checking"),
  );
  $("environmentDetails").hidden = !environment;
  if (environment) {
    const detail = [];
    if (environment.required_version)
      detail.push(
        t("required_version", {
          version: safeVersion(environment.required_version),
        }),
      );
    if (environment.sdk_version)
      detail.push(
        t("sdk_version", { version: safeVersion(environment.sdk_version) }),
      );
    if (environment.driver_version)
      detail.push(
        t("driver_version", {
          version: safeVersion(environment.driver_version),
        }),
      );
    setText(
      "environmentText",
      detail.length
        ? detail.join("\n")
        : t(
            environment.driver_ready
              ? "driver_ready"
              : hasMessage(environment.code)
                ? environment.code
                : "driver_unavailable",
          ),
    );
  }
}
function environmentReady(environment) {
  return Boolean(
    environment &&
      environment.driver_ready &&
      environment.device_ready !== false,
  );
}
function renderFlow(data, phase) {
  const environment = data.environment;
  const needsSetup = Boolean(environment && !environmentReady(environment));
  const setup = data.setup || {};
  const step =
    !environment || needsSetup || setup.busy
      ? 0
      : phase === "connected"
        ? 3
        : phase.endsWith("_right") ||
            (data.sides && data.sides.left && data.sides.left.connected)
          ? 2
          : 1;
  ["flowEnvironment", "flowLeft", "flowRight", "flowTest"].forEach(
    (id, index) => {
      const element = $(id);
      element.classList.toggle("current", index === step);
      element.classList.toggle("complete", index < step);
      if (index === step) element.setAttribute("aria-current", "step");
      else element.removeAttribute("aria-current");
    },
  );
  const pairing = phase.includes("scanning_") || phase.includes("connecting_");
  if (lastFlowStep !== step && pairing) $("pairingDetails").open = true;
  if (lastFlowStep !== step && step === 3) $("pairingDetails").open = false;
  lastFlowStep = step;
  $("stepLeft").hidden = step > 1;
  $("stepRight").hidden = step !== 2;
  $("stepDone").hidden = step !== 3;
  document.querySelector(".actions").hidden = needsSetup || Boolean(setup.busy);
  $("setupActions").hidden = !needsSetup && !setup.busy;
  $("setupBtn").hidden =
    (environment && environment.code === "virtual_device_busy") ||
    setup.state === "installer_opened";
  $("setupBtn").disabled =
    actionBusy || Boolean(setup.busy) || !serviceReachable;
  setText(
    "setupBtn",
    t(
      environment && environment.code === "configure_virtual_device"
        ? "configure_device"
        : "install_driver",
    ),
  );
  $("recheckBtn").disabled = actionBusy || !serviceReachable;
  $("recheckBtn").classList.toggle("primary", Boolean($("setupBtn").hidden));
  $("recheckBtn").classList.toggle("secondary", !$("setupBtn").hidden);
  $("setupProgress").hidden = setup.state !== "downloading";
  const progress = Math.max(0, Math.min(100, Number(setup.progress) || 0));
  $("driverProgress").value = progress;
  setText("driverProgressText", `${Math.round(progress)}%`);
  if ((needsSetup || setup.busy) && serviceReachable && !exiting) {
    setText("phaseTag", t("flow_environment"));
    setText("connectionTitle", t("setup_heading"));
    const setupMessage = [
      "downloading",
      "installer_opened",
      "configuring",
      "error",
    ].includes(setup.state)
      ? setup.message_key
      : environment && environment.code;
    setText(
      "statusMessage",
      codedMessage(setupMessage, {}, "driver_unavailable"),
    );
    setText(
      "smallStatusText",
      t(
        setup.state === "installer_opened"
          ? "setup_installer_opened"
          : "setup_idle",
      ),
    );
  }
}
function safeVersion(value) {
  return String(value)
    .replace(/[^a-zA-Z0-9. _-]/g, "")
    .slice(0, 50);
}

function renderLogs(logs) {
  const recent = Array.isArray(logs) ? logs.slice(-50) : [];
  const signature =
    locale +
    JSON.stringify(
      recent.map((log) => [log.id, log.time, log.key, log.params, log.level]),
    );
  if (signature === logSignature) return;
  logSignature = signature;
  const list = $("logList");
  const atBottom = list.scrollHeight - list.scrollTop - list.clientHeight < 40;
  if (!recent.length) {
    const empty = document.createElement("div");
    empty.className = "empty-log";
    const symbol = document.createElement("span");
    symbol.className = "empty-symbol";
    symbol.textContent = "◷";
    symbol.setAttribute("aria-hidden", "true");
    const line = document.createElement("p");
    line.textContent = t("empty_activity");
    const detail = document.createElement("small");
    detail.textContent = t("empty_activity_detail");
    empty.append(symbol, line, detail);
    list.replaceChildren(empty);
    return;
  }
  list.replaceChildren(
    ...recent.map((log) => {
      const row = document.createElement("div");
      row.className =
        "log-row " +
        (["warning", "error", "info"].includes(log.level) ? log.level : "info");
      const time = document.createElement("time");
      time.textContent = /^\d{2}:\d{2}:\d{2}$/.test(log.time) ? log.time : "—";
      const text = document.createElement("span");
      // Only stable backend codes become user-facing copy; raw diagnostics may be in another language.
      text.textContent = codedMessage(
        log.key,
        safeParams(log.params),
        log.level === "error" ? "unknown_error" : "unknown_event",
      );
      row.append(time, text);
      return row;
    }),
  );
  if (atBottom) list.scrollTop = list.scrollHeight;
}
function safeParams(params) {
  const result = {};
  if (!params || typeof params !== "object") return result;
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === "number") result[key] = value;
    else if (typeof value === "string" && /^[\x20-\x7e]{0,120}$/.test(value))
      result[key] = value;
  }
  return result;
}

function render(data) {
  current = data;
  const phase = typeof data.phase === "string" ? data.phase : "idle";
  const connected = phase === "connected",
    busy = busyPhases.includes(phase);
  const panel = document.querySelector(".connection-panel");
  panel.classList.toggle(
    "connected-panel",
    connected && serviceReachable && !exiting,
  );
  panel.classList.toggle(
    "waiting",
    busy && phase !== "stopping" && serviceReachable,
  );
  $("serviceBadge").classList.toggle(
    "offline",
    (serviceKnown && !serviceReachable) || exiting,
  );
  setText(
    "serviceText",
    t(
      exiting
        ? exitDone
          ? "exited"
          : "exiting"
        : !serviceKnown
          ? "local_checking"
          : serviceReachable
            ? "local_running"
            : "local_offline",
    ),
  );
  setText(
    "connectionTitle",
    t(
      exiting
        ? exitDone
          ? "exited_heading"
          : "exit_heading"
        : serviceKnown && !serviceReachable
          ? "offline_title"
          : hasMessage("title_" + phase)
            ? "title_" + phase
            : "title_idle",
    ),
  );
  setText(
    "phaseTag",
    t(
      connected
        ? "phase_tag_connected"
        : busy
          ? "phase_tag_busy"
          : phase === "error" || phase === "external"
            ? "phase_tag_error"
            : "phase_tag_idle",
    ),
  );
  setText(
    "statusMessage",
    exiting
      ? t(exitDone ? "exited_message" : "exit_message")
      : serviceKnown && !serviceReachable
        ? t("offline_message")
        : codedMessage(
            data.message_key,
            safeParams(data.message_params),
            hasMessage("phase_" + phase) ? "phase_" + phase : "phase_idle",
          ),
  );
  $("connectBtn").hidden = connected && serviceReachable && !exiting;
  $("connectBtn").disabled = actionBusy || busy || !serviceReachable || exiting;
  setText(
    "connectLabel",
    t(
      phase === "error"
        ? "reconnect"
        : phase === "external"
          ? "check_again"
          : busy
            ? "connecting"
            : "connect",
    ),
  );
  $("disconnectBtn").disabled =
    actionBusy ||
    !data.running ||
    phase === "stopping" ||
    !serviceReachable ||
    exiting;
  setText(
    "disconnectBtn",
    t(busy && phase !== "stopping" ? "cancel" : "disconnect"),
  );
  $("steamBtn").classList.toggle(
    "primary",
    connected && serviceReachable && !exiting,
  );
  $("steamBtn").disabled = actionBusy || !serviceReachable || exiting;
  $("exitBtn").disabled = actionBusy || !serviceReachable || exiting;
  const count = sides.filter(
    (side) => data.sides && data.sides[side] && data.sides[side].connected,
  ).length;
  setText(
    "connectedCount",
    serviceKnown && !serviceReachable && !exiting
      ? t("state_unavailable")
      : t("count_connected", { count: exiting ? 0 : count }),
  );
  setText(
    "smallStatusText",
    t(
      connected && serviceReachable && !exiting
        ? "footnote_connected"
        : busy && serviceReachable && !exiting
          ? "footnote_busy"
          : "footnote_idle",
    ),
  );
  const hasError =
    Boolean(data.error || data.error_key) &&
    serviceReachable &&
    !exiting &&
    !(
      data.environment &&
      !environmentReady(data.environment) &&
      data.error_key === data.environment.code
    );
  $("errorBanner").hidden = !hasError;
  setText(
    "errorBanner",
    hasError
      ? codedMessage(
          data.error_key,
          safeParams(data.error_params),
          "unknown_error",
        )
      : "",
  );
  for (const side of sides)
    renderSide(side, data.sides && data.sides[side], phase);
  $("stepLeft").classList.toggle(
    "current",
    serviceReachable && phase.endsWith("_left") && !exiting,
  );
  $("stepRight").classList.toggle(
    "current",
    serviceReachable && phase.endsWith("_right") && !exiting,
  );
  $("stepDone").classList.toggle(
    "current",
    serviceReachable && connected && !exiting,
  );
  renderEnvironment(data.environment);
  renderFlow(data, phase);
  renderLogs(data.logs);
}

function nextPollDelay() {
  return serviceReachable &&
    (current.running ||
      (current.setup && current.setup.busy) ||
      current.phase === "connected" ||
      busyPhases.includes(current.phase))
    ? 100
    : 1000;
}
async function poll() {
  if (exiting || polling) return;
  clearTimeout(pollTimer);
  polling = true;
  try {
    const data = await request("/api/status");
    serviceKnown = true;
    serviceReachable = true;
    if (!exiting) render(data);
  } catch (_) {
    serviceKnown = true;
    serviceReachable = false;
    if (!exiting) render(current);
  } finally {
    polling = false;
    if (!exiting) pollTimer = setTimeout(poll, nextPollDelay());
  }
}
function refreshSoon() {
  clearTimeout(pollTimer);
  if (!polling && !exiting) pollTimer = setTimeout(poll, 0);
}

async function action(path) {
  if (actionBusy || exiting) return;
  actionBusy = true;
  render(current);
  try {
    const data = await request(path, {});
    serviceKnown = true;
    serviceReachable = true;
    if (data.phase) render(data);
    if (path === "/api/open-steam") toast("steam_opened");
  } catch (error) {
    toast(error.key || "request_failed");
  } finally {
    actionBusy = false;
    if (!exiting) {
      render(current);
      refreshSoon();
    }
  }
}
$("connectBtn").addEventListener("click", () => action("/api/connect"));
$("disconnectBtn").addEventListener("click", () => action("/api/disconnect"));
$("steamBtn").addEventListener("click", () => action("/api/open-steam"));
$("recheckBtn").addEventListener("click", () =>
  action("/api/recheck-environment"),
);
$("setupBtn").addEventListener("click", () =>
  action(
    current.environment &&
      current.environment.code === "configure_virtual_device"
      ? "/api/configure-vjoy"
      : "/api/install-driver",
  ),
);
$("exitBtn").addEventListener("click", async () => {
  if (actionBusy || exiting) return;
  actionBusy = true;
  render(current);
  try {
    await request("/api/exit", {});
    exiting = true;
    clearTimeout(pollTimer);
    render(current);
    for (let attempt = 0; attempt < 60; attempt++) {
      try {
        await request("/api/health");
      } catch (_) {
        exitDone = true;
        serviceReachable = false;
        render(current);
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 300));
    }
    toast("exit_pending");
  } catch (error) {
    toast(error.key || "request_failed");
  } finally {
    actionBusy = false;
    render(current);
  }
});
$("languageSelect").addEventListener("change", (event) => {
  languageChoice = I18N.normalizeChoice(event.target.value);
  I18N.saveChoice(storage, languageChoice);
  applyLanguage();
});
$("themeToggle").addEventListener("click", () => {
  themeChoice = I18N.toggleTheme(theme);
  I18N.saveThemeChoice(storage, themeChoice);
  applyTheme();
});
themeMedia.addEventListener("change", () => {
  if (themeChoice === "system") applyTheme();
});
window.addEventListener("languagechange", () => {
  if (languageChoice === "system") applyLanguage();
});
window.addEventListener("storage", (event) => {
  if (event.key === I18N.STORAGE_KEY || event.key === null) {
    languageChoice = I18N.readChoice(storage);
    applyLanguage();
  }
  if (event.key === I18N.THEME_STORAGE_KEY || event.key === null) {
    themeChoice = I18N.readThemeChoice(storage);
    applyTheme();
  }
});
$("guideImageBtn").addEventListener("click", () =>
  $("imageDialog").showModal(),
);
$("closeImageBtn").addEventListener("click", () => $("imageDialog").close());
$("imageDialog").addEventListener("click", (event) => {
  if (event.target === $("imageDialog")) $("imageDialog").close();
});
for (const link of document.querySelectorAll(".nav-item"))
  link.addEventListener("click", () => {
    document.querySelector(".nav-item.active")?.classList.remove("active");
    link.classList.add("active");
  });
applyLanguage();
poll();
