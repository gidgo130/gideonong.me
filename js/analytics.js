// Analytics — loaded (defer) from the <head> of every main-site page.
// Two cookieless tools; neither needs a consent banner. CLAUDE.md → Analytics.
//
//   1. Vercel Web Analytics — page views, referrers, countries, devices.
//      Script is served same-origin by Vercel at /_vercel/insights/script.js
//      (only exists on Vercel deploys). Dashboard: Vercel project → Analytics.
//   2. GoatCounter — page views PLUS click events (below). Dashboard:
//      https://<GC_CODE>.goatcounter.com
//
// Neither loads on the dev hosts (same list as siteData.isDev in
// js/data-helpers.js), so Live Server stays console-clean and your own
// local previews are never counted.
//
// Click events (GoatCounter only; delegated, so JS-rendered links count too):
//   doc-<type>-<lang>   a data-doc-link button (resume / cv / transcript)
//   email               any mailto: link
//   out-<host>          any link to another site (linkedin.com, github.com, …)
//   lang-<en|es>        the EN/ES toggle, named for the language switched TO
// Each event's title is the page it was clicked on.
(function () {
  "use strict";

  var GC_CODE = "gideonong"; // GoatCounter site code → gideonong.goatcounter.com

  var h = location.hostname;
  if (location.protocol === "file:" || h === "localhost" || h === "127.0.0.1" || h === "[::1]" || h === "::1") return;

  function load(src, attrs) {
    var s = document.createElement("script");
    s.async = true;
    s.src = src;
    Object.keys(attrs || {}).forEach(function (k) { s.setAttribute(k, attrs[k]); });
    document.head.appendChild(s);
  }

  // 1. Vercel — queue stub first so calls made before the script arrives aren't lost.
  window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
  load("/_vercel/insights/script.js");

  // 2. GoatCounter — counts the page view on load by itself.
  load("https://gc.zgo.at/count.js", { "data-goatcounter": "https://" + GC_CODE + ".goatcounter.com/count" });

  function sendEvent(name) {
    if (!window.goatcounter || typeof window.goatcounter.count !== "function") return; // blocked or not loaded yet
    window.goatcounter.count({ path: name, title: location.pathname, event: true });
  }

  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) return;

    // Language toggle — main.js has already swapped <html lang> by the time
    // the click bubbles up to document, so lang is the NEW language.
    if (t.closest("[data-lang-toggle]")) {
      sendEvent("lang-" + (document.documentElement.getAttribute("lang") || "unknown"));
      return;
    }

    var a = t.closest("a[href]");
    if (!a) return;

    var doc = a.getAttribute("data-doc-link");
    if (doc) {
      // Manifest paths are ".../<type>/<lang> Gideon Ong …" — read the language from the file name.
      var file = decodeURIComponent(a.pathname.split("/").pop() || "");
      var lang = /^(en|es)\b/.test(file) ? file.slice(0, 2) : "unknown";
      sendEvent("doc-" + doc + "-" + lang);
      return;
    }

    if (a.protocol === "mailto:") { sendEvent("email"); return; }

    if ((a.protocol === "http:" || a.protocol === "https:") && a.hostname !== location.hostname) {
      sendEvent("out-" + a.hostname.replace(/^www\./, ""));
    }
  });
})();
