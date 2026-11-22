"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const i18n = require("../joycon2_assistant/static/i18n.js");

test("system locale resolves the first preferred language exactly", () => {
  for (const [input, expected] of [
    [["zh-TW"], "zh-TW"],
    [["zh-Hant"], "zh-TW"],
    [["zh-Hant-TW"], "zh-TW"],
    [["ZH-tw"], "zh-TW"],
    [["zh-CN"], "zh-CN"],
    [["zh-Hans"], "zh-CN"],
    [["zh-Hans-CN"], "zh-CN"],
    [["zh"], "zh-CN"],
    [["en"], "en"],
    [["en-GB"], "en"],
    [["en-US"], "en"],
    [["fr-FR", "zh-TW"], "en"],
    [["zh-HK", "en"], "en"],
    [["zh-SG"], "en"],
    [["ja-JP"], "en"],
    [[], "en"],
    [null, "en"],
  ])
    assert.equal(
      i18n.resolveSystemLocale(input),
      expected,
      JSON.stringify(input),
    );
});

test("manual choice overrides system and invalid choices use system", () => {
  assert.equal(i18n.resolveLocale("zh-TW", ["en-US"]), "zh-TW");
  assert.equal(i18n.resolveLocale("zh-CN", ["zh-TW"]), "zh-CN");
  assert.equal(i18n.resolveLocale("en", ["zh-CN"]), "en");
  assert.equal(i18n.resolveLocale("system", ["zh-Hant"]), "zh-TW");
  assert.equal(i18n.resolveLocale("invalid", ["zh-CN"]), "zh-CN");
  assert.equal(i18n.normalizeChoice(null), "system");
});

test("saved choice tolerates blocked storage and persists manual or system choice", () => {
  let value = null;
  const storage = {
    getItem: () => value,
    setItem: (_, next) => {
      value = next;
    },
  };
  assert.equal(i18n.readChoice(storage), "system");
  i18n.saveChoice(storage, "zh-TW");
  assert.equal(i18n.readChoice(storage), "zh-TW");
  i18n.saveChoice(storage, "system");
  assert.equal(i18n.readChoice(storage), "system");
  const blocked = {
    getItem() {
      throw Error("blocked");
    },
    setItem() {
      throw Error("blocked");
    },
  };
  assert.equal(i18n.readChoice(blocked), "system");
  assert.doesNotThrow(() => i18n.saveChoice(blocked, "en"));
});

test("initial language uses system preference until a manual locale is saved", () => {
  let value = null;
  const storage = {
    getItem: () => value,
    setItem: (_, next) => {
      value = next;
    },
  };
  assert.equal(
    i18n.resolveLocale(i18n.readChoice(storage), ["zh-Hant-TW"]),
    "zh-TW",
  );
  assert.equal(
    i18n.resolveLocale(i18n.readChoice(storage), ["fr-FR", "zh-TW"]),
    "en",
  );
  i18n.saveChoice(storage, "zh-CN");
  assert.equal(
    i18n.resolveLocale(i18n.readChoice(storage), ["en-US"]),
    "zh-CN",
  );
});

test("theme initially follows system and manual selection takes precedence", () => {
  assert.equal(i18n.resolveTheme(null, true), "dark");
  assert.equal(i18n.resolveTheme(null, false), "light");
  assert.equal(i18n.resolveTheme("invalid", true), "dark");
  assert.equal(i18n.resolveTheme("light", true), "light");
  assert.equal(i18n.resolveTheme("dark", false), "dark");
  assert.equal(i18n.toggleTheme("light"), "dark");
  assert.equal(i18n.toggleTheme("dark"), "light");
});

test("manual theme survives reload and unavailable storage permits system fallback", () => {
  let value = null;
  const storage = {
    getItem: () => value,
    setItem: (_, next) => {
      value = next;
    },
  };
  assert.equal(i18n.readThemeChoice(storage), "system");
  i18n.saveThemeChoice(storage, "dark");
  assert.equal(i18n.resolveTheme(i18n.readThemeChoice(storage), false), "dark");
  i18n.saveThemeChoice(storage, "light");
  assert.equal(i18n.resolveTheme(i18n.readThemeChoice(storage), true), "light");
  const blocked = {
    getItem() {
      throw Error("blocked");
    },
    setItem() {
      throw Error("blocked");
    },
  };
  assert.equal(i18n.readThemeChoice(blocked), "system");
  assert.doesNotThrow(() => i18n.saveThemeChoice(blocked, "light"));
});

test("all locales cover the same messages and interpolation is safe", () => {
  const keys = Object.keys(i18n.messages.en).sort();
  for (const locale of ["zh-CN", "zh-TW"]) {
    assert.deepEqual(Object.keys(i18n.messages[locale]).sort(), keys);
    for (const key of keys) assert.equal(typeof i18n.t(locale, key), "string");
  }
  assert.equal(i18n.t("en", "packet_count", { count: 42 }), "42 input packets");
  assert.equal(
    i18n.t("en", "pressed_buttons", { buttons: "A · ZR" }),
    "Pressed: A · ZR",
  );
  assert.doesNotMatch(
    Object.values(i18n.messages.en).join(" "),
    /[\u3400-\u9fff]/,
  );
  assert.equal(
    i18n.t("en", "unknown_backend_key"),
    i18n.t("en", "unknown_event"),
  );
  assert.equal(
    i18n.t("zh-TW", "unknown_backend_key"),
    i18n.t("zh-TW", "unknown_event"),
  );
});
