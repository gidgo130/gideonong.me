// Analytics — loaded (defer) from the <head> of every main-site page.
// Three cookieless tools; none needs a consent banner. CLAUDE.md → Analytics.
//
//   1. Vercel Web Analytics — page views, referrers, countries, devices.
//      Script is served same-origin by Vercel at /_vercel/insights/script.js
//      (only exists on Vercel deploys). Dashboard: Vercel project → Analytics.
//   2. GoatCounter — page views PLUS click events (below). Dashboard:
//      https://<GC_CODE>.goatcounter.com
//   3. The self-built collector, api/hit.js — event-level records in Upstash,
//      pulled into Colab by scripts/analytics/. Sent with navigator.sendBeacon
//      to same-origin /api/hit:
//        pageview   on load
//        click      the same click events GoatCounter gets
//        leave      each time the tab is hidden: visible time so far (ms) and
//                   max scroll % so far (one page view can send several)
//      Fields on every event: type, path (normalized, see normPath), ref
//      (referrer host), lang (site language), nav (navigator.language), vw
//      (width bucket), tz, sid (random per tab, sessionStorage), utm
//      (utm_source). The server adds time, geo, coarse UA and a daily visitor
//      hash; it never stores the IP or the raw User-Agent.
//
// None loads on the dev hosts (same list as siteData.isDev in
// js/data-helpers.js), so Live Server stays console-clean and your own
// local previews are never counted.
//
// Click events (delegated, so JS-rendered links count too):
//   doc-<type>-<lang>   a data-doc-link button (resume / cv / transcript)
//   email               any mailto: link
//   out-<host>          any link to another site (linkedin.com, github.com, …)
//   lang-<en|es>        the EN/ES toggle, named for the language switched TO
// Each GoatCounter event's title is the page it was clicked on.
//
// "Exclude me" flag: visit any page with ?notrack=1 to stop counting this
// browser (sets localStorage.noTrack = "1" and GoatCounter's own skipgc = "t");
// ?notrack=0 clears both. While set, none of the tools load.
//
// Collector test flag (dev only): ?collectortest=1 sets localStorage
// collectorTest = "1" (?collectortest=0 clears it). While set, this browser
// loads ONLY the collector, on any host (dev hosts included, noTrack ignored),
// never Vercel or GoatCounter. Used with `vercel dev` and preview deploys; the
// server files those events under dev: / preview: keys. Don't leave it set on
// gideonong.me, where its events would count as real.
//
// Both params are stripped from the address bar (other params and the #hash
// stay). This part runs on dev hosts too.
(function () {
  "use strict";

  var GC_CODE = "gideonong"; // GoatCounter site code → gideonong.goatcounter.com

  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function lsDel(k) { try { localStorage.removeItem(k); } catch (e) {} }

  var url = null;
  try { url = new URL(location.href); } catch (e) { /* very old browser */ }
  if (url && (url.searchParams.has("notrack") || url.searchParams.has("collectortest"))) {
    var nt = url.searchParams.get("notrack");
    if (nt === "1") { lsSet("noTrack", "1"); lsSet("skipgc", "t"); }
    else if (nt === "0") { lsDel("noTrack"); lsDel("skipgc"); }
    var ct = url.searchParams.get("collectortest");
    if (ct === "1") lsSet("collectorTest", "1");
    else if (ct === "0") lsDel("collectorTest");
    url.searchParams.delete("notrack");
    url.searchParams.delete("collectortest");
    try { history.replaceState(history.state, "", url.pathname + url.search + url.hash); } catch (e) {}
  }

  var h = location.hostname;
  var isDev = location.protocol === "file:" || h === "localhost" || h === "127.0.0.1" || h === "[::1]" || h === "::1";
  var thirdParty; // load Vercel + GoatCounter?
  if (lsGet("collectorTest") === "1") thirdParty = false;
  else if (isDev || lsGet("noTrack") === "1") return;
  else thirdParty = true;

  function load(src, attrs) {
    var s = document.createElement("script");
    s.async = true;
    s.src = src;
    Object.keys(attrs || {}).forEach(function (k) { s.setAttribute(k, attrs[k]); });
    document.head.appendChild(s);
  }

  if (thirdParty) {
    // 1. Vercel — queue stub first so calls made before the script arrives aren't lost.
    window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
    load("/_vercel/insights/script.js");

    // 2. GoatCounter — counts the page view on load by itself.
    load("https://gc.zgo.at/count.js", { "data-goatcounter": "https://" + GC_CODE + ".goatcounter.com/count" });
  }

  // 3. Collector.

  // "/", "/index.html" and "/portfolio" are one page; ".html" is dropped, so
  // the data reads the same before and after the clean-URL switch.
  function normPath(p) {
    p = p.replace(/\/index\.html$/, "/").replace(/\.html$/, "");
    if (p.length > 1) p = p.replace(/\/+$/, "");
    if (p === "/portfolio") p = "/";
    return p || "/";
  }

  function vwBucket(w) {
    return w < 480 ? "<480" : w < 768 ? "480-767" : w < 1024 ? "768-1023" : w < 1440 ? "1024-1439" : "1440+";
  }

  function randomId() {
    var b = new Uint8Array(8);
    if (window.crypto && crypto.getRandomValues) crypto.getRandomValues(b);
    else for (var i = 0; i < b.length; i++) b[i] = Math.floor(Math.random() * 256);
    return Array.prototype.map.call(b, function (x) { return ("0" + x.toString(16)).slice(-2); }).join("");
  }

  var sid = null;
  try { sid = sessionStorage.getItem("aSid"); } catch (e) {}
  if (!sid) {
    sid = randomId();
    try { sessionStorage.setItem("aSid", sid); } catch (e) {}
  }

  var ref = "";
  try { if (document.referrer) ref = new URL(document.referrer).host.replace(/^www\./, ""); } catch (e) {}
  var tz = "";
  try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) {}
  var utm = url ? (url.searchParams.get("utm_source") || "") : "";
  var path = normPath(location.pathname);

  function hit(type, extra) {
    if (!navigator.sendBeacon) return;
    var o = {
      type: type,
      path: path,
      ref: ref,
      lang: document.documentElement.getAttribute("lang") || "",
      nav: navigator.language || "",
      vw: vwBucket(window.innerWidth || 0),
      tz: tz,
      sid: sid,
      utm: utm
    };
    Object.keys(extra || {}).forEach(function (k) { o[k] = extra[k]; });
    try { navigator.sendBeacon("/api/hit", JSON.stringify(o)); } catch (e) {}
  }

  hit("pageview");

  // Visible time and max scroll, for "leave".
  var visibleMs = 0;
  var visibleSince = document.visibilityState === "visible" ? performance.now() : null;
  var maxScroll = 0;
  var scrollQueued = false;

  function measureScroll() {
    scrollQueued = false;
    var total = document.documentElement.scrollHeight;
    var seen = (window.scrollY || window.pageYOffset || 0) + window.innerHeight;
    var pct = total > 0 ? Math.min(100, Math.round(seen / total * 100)) : 100;
    if (pct > maxScroll) maxScroll = pct;
  }
  window.addEventListener("scroll", function () {
    if (!scrollQueued) { scrollQueued = true; requestAnimationFrame(measureScroll); }
  }, { passive: true });
  // First reading once images have their height; deferred scripts run before "load".
  if (document.readyState === "complete") measureScroll();
  else window.addEventListener("load", measureScroll);

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") {
      if (visibleSince !== null) { visibleMs += performance.now() - visibleSince; visibleSince = null; }
      hit("leave", { ms: Math.round(visibleMs), scroll: maxScroll });
    } else if (visibleSince === null) {
      visibleSince = performance.now();
    }
  });

  function sendEvent(name) {
    hit("click", { event: name });
    if (!thirdParty || !window.goatcounter || typeof window.goatcounter.count !== "function") return; // blocked or not loaded yet
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
