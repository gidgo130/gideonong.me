// view-settings.js — the "View" button in every /learning series bar (2026-10-17).
//
// It sets the SAME localStorage keys and <html> attributes as the main site's About → Viewing
// settings (js/about.js §6), so a choice made here follows the visitor across gideonong.me and
// back, and the head snippet on every page still applies it before first paint:
//   viewTheme        "dark" | "light" | (absent = follow the OS)   → data-theme
//   viewReadability  "1" | (absent)                               → data-readability
//   viewColorblind   "1" | "0" | (absent)                         → data-colorblind
// "0" means the visitor turned the colorblind cues OFF on purpose (here or on About, which writes
// the same "0" since 2026-10-17), so `prefers-contrast: more` does not turn them back on; an
// absent key is "no choice". Changes apply at once, without a reload.
//
// Markup is built here, not in the pages: a <button class="view-toggle"> after the EN/ES toggle
// (same box: learning.css styles both), and a small non-modal popover (role="dialog") with the
// theme as three aria-pressed buttons, two checkboxes and one note. Esc closes it and returns
// focus to the button; a click outside closes it. On pages with charts, one muted line under
// the first legend (.legend-key on module pages, .legend on Reflections) offers the colorblind
// mode in place and, once on, the way back off.
//
// Strings: view* / cbHint* in strings-common.js. Bilingual pages read them through LI18N and
// re-render on learnlangchange; English-only pages (Reflections) read the EN table as plain data.
// Runs from file: and in the offline copy too (localStorage works there), which is how offline
// readers reach these settings at all.
(function () {
  "use strict";
  var root = document.documentElement;
  var S = window.LEARN_STRINGS_COMMON;
  function t(k) {
    if (window.LI18N && typeof LI18N.t === "function") return LI18N.t(k);
    return (S && S.en && S.en[k]) || k;
  }
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { /* storage blocked: the choice lasts this page view */ } }
  var mqContrast = window.matchMedia ? matchMedia("(prefers-contrast: more)") : { matches: false };

  function themeChoice() { var v = get("viewTheme"); return v === "dark" || v === "light" ? v : "system"; }
  function colorblindOn() { var v = get("viewColorblind"); return v === "1" || (v === null && mqContrast.matches); }
  function readabilityOn() { return get("viewReadability") === "1"; }

  function applyAll() {
    var th = themeChoice();
    if (th === "system") root.removeAttribute("data-theme"); else root.setAttribute("data-theme", th);
    if (readabilityOn()) root.setAttribute("data-readability", "1"); else root.removeAttribute("data-readability");
    if (colorblindOn()) root.setAttribute("data-colorblind", "1"); else root.removeAttribute("data-colorblind");
    render();
  }
  function setTheme(v) { set("viewTheme", v === "system" ? null : v); applyAll(); }
  function setColorblind(on) { set("viewColorblind", on ? "1" : "0"); applyAll(); }
  function setReadability(on) { set("viewReadability", on ? "1" : null); applyAll(); }

  // ---- build ----
  function el(tag, cls, attrs) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (attrs) Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    return e;
  }
  var bar = document.querySelector(".series-bar");
  if (!bar) return;
  var btn = el("button", "view-toggle", { type: "button", "aria-expanded": "false", "aria-haspopup": "dialog", "aria-controls": "view-pop" });
  var pop = el("div", "view-pop", { id: "view-pop", role: "dialog", "aria-labelledby": "view-title", hidden: "" });
  var title = el("p", "view-title", { id: "view-title" });
  var themeRow = el("div", "view-row");
  var themeLabel = el("span", "view-label", { id: "view-theme-label" });
  var seg = el("div", "view-seg", { role: "group", "aria-labelledby": "view-theme-label" });
  var themeBtns = {};
  ["system", "light", "dark"].forEach(function (v) {
    var b = el("button", null, { type: "button", "data-theme": v, "aria-pressed": "false" });
    b.addEventListener("click", function () { setTheme(v); });
    themeBtns[v] = b; seg.appendChild(b);
  });
  themeRow.appendChild(themeLabel); themeRow.appendChild(seg);
  function check(onChange) {
    var lab = el("label", "view-check"), inp = el("input", null, { type: "checkbox" }), txt = el("span");
    inp.addEventListener("change", function () { onChange(inp.checked); });
    lab.appendChild(inp); lab.appendChild(txt);
    return { lab: lab, inp: inp, txt: txt };
  }
  var cb = check(setColorblind), rd = check(setReadability);
  var note = el("p", "view-note");
  var close = el("button", "view-close", { type: "button" });
  pop.appendChild(title); pop.appendChild(themeRow); pop.appendChild(cb.lab); pop.appendChild(rd.lab); pop.appendChild(note); pop.appendChild(close);
  var lang = bar.querySelector(".lang-toggle");
  if (lang && lang.nextSibling) bar.insertBefore(btn, lang.nextSibling); else bar.appendChild(btn);
  bar.appendChild(pop);

  // ---- the colorblind hint under the first chart legend ----
  var legend = document.querySelector(".legend-key, .legend");
  var hint = null, hintText = null, hintBtn = null;
  if (legend) {
    hint = el("p", "cb-hint");
    hintText = el("span", "cb-hint-text");
    hintBtn = el("button", "cb-hint-btn", { type: "button" });
    hintBtn.addEventListener("click", function () { setColorblind(!colorblindOn()); });
    hint.appendChild(hintText); hint.appendChild(document.createTextNode(" ")); hint.appendChild(hintBtn);
    legend.parentNode.insertBefore(hint, legend.nextSibling);
  }

  // ---- render (texts and states; called on load, on every change and on a language switch) ----
  function render() {
    btn.textContent = t("viewBtn");
    btn.setAttribute("aria-label", t("viewTitle"));
    title.textContent = t("viewTitle");
    themeLabel.textContent = t("viewTheme");
    var th = themeChoice();
    Object.keys(themeBtns).forEach(function (v) {
      themeBtns[v].textContent = t(v === "system" ? "viewSystem" : v === "light" ? "viewLight" : "viewDark");
      themeBtns[v].setAttribute("aria-pressed", v === th ? "true" : "false");
    });
    cb.txt.textContent = t("viewColorblind"); cb.inp.checked = colorblindOn();
    rd.txt.textContent = t("viewReadability"); rd.inp.checked = readabilityOn();
    note.textContent = t("viewNote");
    close.textContent = t("viewClose");
    if (hint) {
      var on = colorblindOn();
      hintText.textContent = on ? t("cbHintOn") + " ·" : t("cbHintOff");
      hintBtn.textContent = on ? t("cbTurnOff") : t("cbTurnOn");
      hintBtn.setAttribute("aria-pressed", on ? "true" : "false");
    }
  }

  // ---- open / close ----
  function open() {
    pop.hidden = false; btn.setAttribute("aria-expanded", "true");
    (pop.querySelector("button, input") || pop).focus();
    document.addEventListener("keydown", onKey); document.addEventListener("pointerdown", onOutside, true);
  }
  function shut(returnFocus) {
    if (pop.hidden) return;
    pop.hidden = true; btn.setAttribute("aria-expanded", "false");
    document.removeEventListener("keydown", onKey); document.removeEventListener("pointerdown", onOutside, true);
    if (returnFocus) btn.focus();
  }
  function onKey(e) { if (e.key === "Escape" || e.key === "Esc") { e.preventDefault(); shut(true); } }
  function onOutside(e) { if (!pop.contains(e.target) && e.target !== btn && !btn.contains(e.target)) shut(false); }
  btn.addEventListener("click", function () { if (pop.hidden) open(); else shut(true); });
  close.addEventListener("click", function () { shut(true); });

  // ---- keep in step: language switches, OS contrast changes, another tab's choice ----
  document.addEventListener("learnlangchange", render);
  if (mqContrast.addEventListener) mqContrast.addEventListener("change", applyAll);
  window.addEventListener("storage", function (e) { if (!e.key || /^view(Theme|Readability|Colorblind)$/.test(e.key)) applyAll(); });
  applyAll();
  window.LEARN_VIEW = { apply: applyAll, setTheme: setTheme, setColorblind: setColorblind, setReadability: setReadability };
}());
