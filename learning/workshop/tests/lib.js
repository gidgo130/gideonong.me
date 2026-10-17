// lib.js — shared harness for the /learning browser suites (learning/workshop/tests/*.js).
// Dev-only (learning/workshop/ is in .vercelignore and in build.ps1's $Exclude). Node built-ins
// only; Playwright lives OUTSIDE the repo (see README.md here) and is loaded from LEARN_PW.
//
// What every suite gets from here:
//   repo, out            paths: the repo root; learning/workshop/tests/out/ (gitignored) for shots
//   pw()                 require("playwright") from the external install (clear error if missing)
//   pngjs()              require("pngjs") from the same install
//   serve()              a Vercel-style static server for the repo on :5599, unless run.js already
//                        started one (LEARN_BASE); returns { base, close }
//   Checker              ok(cond, message) / section(title) / summary(): prints "N passed, M failed"
//                        on its own last line (run.js reads it) and exits 1 on any failure
//   watch(page, log)     collects console errors/warnings, page errors, failed requests, HTTP ≥ 400
//   initScript(opts)     an addInitScript function + arg: { lang, theme, read, cb, owner, offline }
//   registries()         the source of truth for expected text: modules.js + strings-common.js +
//                        strings.js (hub) + reflections.js + each module's strings.js, loaded with
//                        vm (no DOM). Suites assert that pages RENDER these; they never hard-code copy.
//   pages()              every /learning page the registries imply, with its kind and URL path
//   fmtDate(iso, lang)   the registry's own date formatting (UTC, from the parts)
//   CR / inPage          contrast helpers; inPage.* are stringified functions for page.evaluate
"use strict";
const fs = require("fs"), path = require("path"), http = require("http"), os = require("os"), vm = require("vm");

const repo = path.resolve(__dirname, "..", "..", "..");
const out = path.join(__dirname, "out");
fs.mkdirSync(out, { recursive: true });
const PORT = 5599;

const PW_DIR = process.env.LEARN_PW || path.join(process.env.LOCALAPPDATA || os.homedir(), "pw", "node_modules");
function external(name) {
  const p = path.join(PW_DIR, name);
  try { return require(p); } catch (e) {
    throw new Error(`${name} not found at ${p}. Install once, outside the repo (README.md here):\n` +
      `  mkdir "$env:LOCALAPPDATA\\pw"; cd "$env:LOCALAPPDATA\\pw"; npm init -y; npm i playwright@1.64.0 pngjs@7.0.0\n` +
      `or point LEARN_PW at a folder that has node_modules/playwright.`);
  }
}
const pw = () => external("playwright");
const pngjs = () => external("pngjs");

// ---- server: a folder URL with or without the trailing slash serves its index.html (no redirect, so
// the pages' own trailing-slash script is what gets exercised). Files missing from the repo are
// looked up in out/virtual/ (suites put synthetic pages there instead of writing into the repo).
const MIME = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript", ".png": "image/png", ".jpg": "image/jpeg",
  ".ico": "image/x-icon", ".woff2": "font/woff2", ".py": "text/x-python", ".ipynb": "application/json", ".svg": "image/svg+xml", ".json": "application/json", ".txt": "text/plain" };
const virtual = path.join(out, "virtual");
function resolveFile(urlPath) {
  for (const root of [repo, virtual]) {
    let f = path.join(root, urlPath);
    if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, "index.html");
    if (fs.existsSync(f) && !fs.statSync(f).isDirectory()) return f;
  }
  return null;
}
function serve() {
  if (process.env.LEARN_BASE) return { base: process.env.LEARN_BASE, close() {} };
  const server = http.createServer((req, res) => {
    const p = decodeURIComponent(req.url.split("?")[0].split("#")[0]);
    const f = resolveFile(p);
    if (!f) { res.writeHead(404); res.end("404 " + p); return; }
    res.writeHead(200, { "Content-Type": MIME[path.extname(f)] || "application/octet-stream" });
    if (req.method === "HEAD") { res.end(); return; }
    res.end(fs.readFileSync(f));
  }).listen(PORT);
  return { base: `http://localhost:${PORT}`, close() { server.close(); } };
}

// ---- checker
class Checker {
  constructor(name) { this.name = name; this.passes = 0; this.fails = 0; this.failed = []; }
  section(title) { console.log(title); }
  ok(cond, msg) { if (cond) this.passes++; else { this.fails++; this.failed.push(msg); console.log("  FAIL " + msg); } return !!cond; }
  summary(extra) {
    if (extra) console.log(extra);
    console.log(`\n${this.passes} passed, ${this.fails} failed`);
    return this.fails ? 1 : 0;
  }
}
function watch(page, log, opts = {}) {
  page.on("console", (m) => { if ((m.type() === "error" || m.type() === "warning") && !(opts.ignore && opts.ignore.test(m.text()))) log.push(m.type() + ": " + m.text()); });
  page.on("pageerror", (e) => log.push("pageerror: " + e.message));
  page.on("requestfailed", (r) => { if (r.method() !== "HEAD" && !(opts.ignore && opts.ignore.test(r.url()))) log.push("requestfailed: " + r.url() + " " + ((r.failure() || {}).errorText || "")); });
  page.on("response", (r) => { if (r.status() >= 400 && !(opts.ignore && opts.ignore.test(r.url()))) log.push(`HTTP ${r.status()}: ${r.url()}`); });
}
// addInitScript(initScript.fn, initScript.arg(opts)): saved viewing settings, language, owner key, the offline flag
const initScript = {
  fn: (o) => {
    try {
      localStorage.clear();
      if (o.lang) localStorage.setItem("lang", o.lang);
      if (o.theme) localStorage.setItem("viewTheme", o.theme);
      if (o.read) localStorage.setItem("viewReadability", "1");
      if (o.cb) localStorage.setItem("viewColorblind", "1");
      if (o.owner) localStorage.setItem("learnFeedbackOwner", o.owner);
    } catch (e) {}
    if (o.offline) window.LEARN_OFFLINE = { version: "9.9", commit: "test", missing: o.missing || [] };
  },
  arg: (o) => Object.assign({ lang: "", theme: "", read: false, cb: false, owner: "", offline: false }, o || {}),
};
async function context(browser, o = {}) {
  const ctx = await browser.newContext(Object.assign({ viewport: { width: o.width || 1280, height: o.height || 900 }, colorScheme: o.dark ? "dark" : "light" }, o.ctx || {}));
  await ctx.addInitScript(initScript.fn, initScript.arg(o));
  return ctx;
}

// ---- registries (the source of truth for expected text)
function loadWindow(rel) {
  const win = {};
  vm.runInNewContext(fs.readFileSync(path.join(repo, rel), "utf8"), { window: win, document: undefined });
  return win;
}
let REG = null;
function registries() {
  if (REG) return REG;
  const modules = loadWindow("learning/assets/modules.js").LEARN_MODULES;
  const common = loadWindow("learning/assets/strings-common.js").LEARN_STRINGS_COMMON;
  const hub = loadWindow("learning/strings.js").LEARN_STRINGS;
  const books = loadWindow("learning/assets/reflections.js").LEARN_BOOKS;
  const mods = modules.map((m) => ({
    key: m.key, slug: m.slug, ready: !!m.ready, url: `/learning/fits/${m.slug}/`,
    title: { en: common.en["mod" + m.key + "Title"], es: common.es["mod" + m.key + "Title"] },
    desc: { en: common.en["mod" + m.key + "Desc"], es: common.es["mod" + m.key + "Desc"] },
    strings: fs.existsSync(path.join(repo, "learning/fits", m.slug, "strings.js")) ? loadWindow(`learning/fits/${m.slug}/strings.js`).LEARN_STRINGS : null,
  }));
  const reflections = [];
  books.forEach((b, i) => (b.reflections || []).forEach((r) => reflections.push({
    book: b.slug, bookTitle: b.title, bookIndex: i + 1, authors: b.authors, year: b.year, edition: b.edition || "",
    slug: r.slug, title: r.title, date: r.date, summary: r.summary, ready: !!r.ready,
    url: `/learning/reflections/${b.slug}/${r.slug}/`, dir: path.join(repo, "learning/reflections", b.slug, r.slug),
  })));
  REG = { modules: mods, readyModules: mods.filter((m) => m.ready), common, hub, books, reflections, readyReflections: reflections.filter((r) => r.ready),
    booksWithPages: books.filter((b) => (b.reflections || []).some((r) => r.ready)).map((b, _, arr) => ({ slug: b.slug, title: b.title, authors: b.authors, year: b.year, edition: b.edition || "", about: b.about || "", index: books.indexOf(b) + 1, url: `/learning/reflections/${b.slug}/`, ready: b.reflections.filter((r) => r.ready) })) };
  return REG;
}
// Every page the registries imply. kind: hub | module | books | book | reflection
function pages() {
  const r = registries();
  return [
    { kind: "hub", name: "hub", url: "/learning/", file: "learning/index.html" },
    ...r.readyModules.map((m) => ({ kind: "module", name: m.slug, url: m.url, file: `learning/fits/${m.slug}/index.html`, module: m })),
    { kind: "books", name: "reflections", url: "/learning/reflections/", file: "learning/reflections/index.html" },
    ...r.booksWithPages.map((b) => ({ kind: "book", name: b.slug, url: b.url, file: `learning/reflections/${b.slug}/index.html`, book: b })),
    ...r.readyReflections.map((x) => ({ kind: "reflection", name: `${x.book}/${x.slug}`, url: x.url, file: `learning/reflections/${x.book}/${x.slug}/index.html`, reflection: x })),
  ];
}
// reflections.js's fmtDate, reproduced: from the parts, UTC, en-US or es
function fmtDate(iso, lang) {
  const p = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
  if (!p) return iso || "";
  return new Date(Date.UTC(+p[1], +p[2] - 1, +p[3])).toLocaleDateString(lang === "es" ? "es" : "en-US", { year: "numeric", month: "long", day: "numeric", timeZone: "UTC" });
}
const norm = (s) => String(s == null ? "" : s).replace(/\s+/g, " ").trim();

// ---- contrast (node side) and page-side snippets
function lum(c) { const m = c.match(/[\d.]+/g).map(Number); const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(m[0]) + 0.7152 * f(m[1]) + 0.0722 * f(m[2]); }
function CR(a, b) { const x = lum(a), y = lum(b); return +((Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05)).toFixed(2); }
// Page-side helpers (pass to page.evaluate as source via `new Function`-free strings: each is a
// self-contained function expression that page.evaluate can take directly).
const inPage = {
  // contrast of every text-bearing element inside `sel` against its nearest painted background
  textContrast: (sel) => {
    const Lum = (c) => { const m = c.match(/[\d.]+/g).map(Number); const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(m[0]) + 0.7152 * f(m[1]) + 0.0722 * f(m[2]); };
    const CR = (a, b) => { const x = Lum(a), y = Lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
    const bgOf = (el) => { for (let e = el; e; e = e.parentElement) { const b = getComputedStyle(e).backgroundColor; if (b !== "rgba(0, 0, 0, 0)" && b !== "transparent") return b; } return "rgb(255, 255, 255)"; };
    const roots = Array.from(document.querySelectorAll(sel));
    const els = roots.flatMap((r0) => [r0, ...r0.querySelectorAll("*")]).filter((e) => !e.closest("[hidden]") && e.getClientRects().length && Array.from(e.childNodes).some((n) => n.nodeType === 3 && n.data.trim()));
    return els.map((e) => ({ t: e.textContent.trim().slice(0, 24), cr: +CR(getComputedStyle(e).color, bgOf(e)).toFixed(2) }));
  },
  // every chart's text: rendered px size, overlapping pairs, scale
  chartText: () => Array.from(document.querySelectorAll("svg[id], svg.chart")).filter((s) => s.querySelector("text") && s.viewBox.baseVal.width).map((svg) => {
    const texts = Array.from(svg.querySelectorAll("text")).filter((t) => t.textContent.trim() && t.getClientRects().length);
    const boxes = texts.map((t) => { const b = t.getBoundingClientRect(); const m = t.getScreenCTM(); return { t: t.textContent.trim(), x: b.left, y: b.top, r: b.right, b: b.bottom, px: parseFloat(getComputedStyle(t).fontSize) * Math.hypot(m.a, m.b) }; });
    const overlaps = [];
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) { const a = boxes[i], b = boxes[j]; if (a.x < b.r - 0.5 && b.x < a.r - 0.5 && a.y < b.b - 0.5 && b.y < a.b - 0.5) overlaps.push(a.t + " × " + b.t); }
    const vb = svg.viewBox.baseVal, w = svg.getBoundingClientRect().width;
    return { id: svg.id, n: boxes.length, px: Math.min(...boxes.map((b) => b.px)), pxMax: Math.max(...boxes.map((b) => b.px)), overlaps, scale: +(w / vb.width).toFixed(3), vbW: vb.width, w: Math.round(w), vb: svg.getAttribute("viewBox"), dataVb: svg.getAttribute("data-vb") };
  }),
  layout: () => ({ sw: document.documentElement.scrollWidth, iw: innerWidth, series: document.documentElement.getAttribute("data-series"), attrs: [...document.documentElement.attributes].map((a) => a.name).join(" ") }),
};

module.exports = { repo, out, virtual, PORT, pw, pngjs, serve, Checker, watch, initScript, context, registries, pages, fmtDate, norm, CR, lum, inPage, MIME };
