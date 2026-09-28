// learning-i18n.js — EN/ES for /learning pages.
// Shares the main site's localStorage key ("lang") and default rule (Spanish or Portuguese
// browser → ES), so a visitor's choice carries between the main site and /learning.
//
// Strings: LEARN_STRINGS_COMMON (assets/strings-common.js) merged with the page's LEARN_STRINGS
// (its own strings.js). A missing ES string falls back to EN.
// Markup:  data-i18n="key"        → textContent
//          data-i18n-html="key"   → innerHTML (our own authored strings only; keys end in "Html")
//          data-i18n-aria="key"   → aria-label
//          data-i18n-title="key"  → document.title (put it on <title>)
// Spanish readiness: a page shows ES (and its EN/ES toggle) only when <html data-es-ready>.
// Until then the toggle stays hidden and the page renders English even if "es" is stored.
// Dev check (localhost / file: only): warns about missing keys and markup text that has
// drifted from its EN string.
(function () {
  "use strict";
  var KEY = "lang";
  var root = document.documentElement;
  var esReady = root.hasAttribute("data-es-ready");
  var C = window.LEARN_STRINGS_COMMON || { en: {}, es: {} };
  var P = window.LEARN_STRINGS || { en: {}, es: {} };
  var S = {
    en: Object.assign({}, C.en, P.en),
    es: Object.assign({}, C.es, P.es)
  };
  var isDev = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname) || location.protocol === "file:";

  function stored() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function detect() {
    var s = stored();
    if (s === "en" || s === "es") return s;
    var nav = (navigator.language || "en").toLowerCase();
    return (nav.indexOf("es") === 0 || nav.indexOf("pt") === 0) ? "es" : "en";
  }
  var wanted = detect();
  var lang = (wanted === "es" && esReady) ? "es" : "en";

  function t(key, vars) {
    var s = S[lang][key];
    if (s === undefined) s = S.en[key];
    if (s === undefined) { if (isDev) console.warn("[learning i18n] missing string:", key); return key; }
    if (vars) s = s.replace(/\{(\w+)\}/g, function (m, k) { return (k in vars) ? String(vars[k]) : m; });
    return s;
  }

  function apply() {
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var k = el.getAttribute("data-i18n");
      if (isDev && lang === "en" && S.en[k] !== undefined && el.textContent.trim() !== S.en[k].trim()) {
        console.warn("[learning i18n] markup differs from EN string:", k);
      }
      el.textContent = t(k);
    });
    document.querySelectorAll("[data-i18n-html]").forEach(function (el) { el.innerHTML = t(el.getAttribute("data-i18n-html")); });
    document.querySelectorAll("[data-i18n-aria]").forEach(function (el) { el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria"))); });
    var ti = document.querySelector("title[data-i18n-title]");
    if (ti) document.title = t(ti.getAttribute("data-i18n-title"));
    root.setAttribute("lang", lang);
    document.querySelectorAll(".lang-toggle .lang-btn").forEach(function (b) {
      b.classList.toggle("is-active", b.getAttribute("data-lang") === lang);
    });
  }

  function setLang(next) {
    if (next === lang) return;
    lang = next;
    try { localStorage.setItem(KEY, next); } catch (e) { /* storage blocked: choice lasts this page view */ }
    apply();
    document.dispatchEvent(new CustomEvent("learnlangchange", { detail: { lang: lang } }));
  }

  document.querySelectorAll(".lang-toggle").forEach(function (btn) {
    btn.hidden = !esReady;
    btn.addEventListener("click", function () { setLang(lang === "en" ? "es" : "en"); });
  });

  if (isDev && esReady) {
    Object.keys(S.en).forEach(function (k) { if (S.es[k] === undefined) console.warn("[learning i18n] no ES string yet:", k); });
  }

  window.LI18N = { t: t, apply: apply, get lang() { return lang; } };
  apply();
}());
