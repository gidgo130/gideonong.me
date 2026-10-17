// theme-dashes.js — dashed and dotted chart lines stay readable on screen (CLAUDE.md, /learning
// hub-wide rule: data lines ≥ 2 px; dashed = 10 px dashes / 6 px gaps; dotted = round 3.25 px dots
// every 6 px; dash ≥ 3× the dot). Two angles:
//   A. pixels: a synthetic page with the real stylesheet at the width a Reading Your Fits chart
//      gets at 375 px (343 px for a 420-unit viewBox, --k 1.2245) and a Reflections-style svg with
//      main.js's inline dash styles, screenshotted in Chromium AND Firefox and read back as
//      grayscale run lengths with pngjs; plus Firefox's computed calc(var(--k)) stroke on the first
//      ready module page that draws a .ci-bar-fix.
//   B. DOM geometry: every svg with dashed or dotted strokes on EVERY page L.pages() lists, at
//      375 px, in screen pixels (stroke-dasharray × the viewBox scale).
//   node learning/workshop/tests/theme-dashes.js
// The synthetic page lives in out/virtual/ (served by lib's server at the same URL path) and is
// deleted at the end; nothing is written into the repo.
"use strict";
const fs = require("fs"), path = require("path");
const L = require("./lib");
const { chromium, firefox } = L.pw();
const { PNG } = L.pngjs();
const { base, close } = L.serve();
const c = new L.Checker("theme-dashes");
const R = L.registries();

// ---- synthetic page: one svg.chart (fits classes, k = 420/343) and one Reflections-style svg (k = 1)
const SYN = `<!doctype html><html data-series="fits"><meta charset="utf-8"><link rel="stylesheet" href="/learning/assets/learning.css">
<style>body{margin:0;background:#fff}.wrap{width:343px}</style>
<div class="wrap"><svg class="chart" id="syn" viewBox="0 0 420 120" style="--k:1.2245">
<line class="truth" x1="10" y1="15" x2="410" y2="15"/><line class="fix" x1="10" y1="40" x2="410" y2="40"/>
<line class="thresh" x1="10" y1="65" x2="410" y2="65"/><line class="ci-bar-fix" x1="10" y1="90" x2="410" y2="90"/><line class="fit" x1="10" y1="110" x2="410" y2="110"/></svg></div>
<div class="wrap"><svg id="refl" viewBox="0 0 343 60" style="width:343px"><path d="M10,15 L333,15" style="fill:none;stroke:#000;stroke-width:2;stroke-dasharray:10 6;stroke-linecap:round"/>
<path d="M10,40 L333,40" style="fill:none;stroke:#000;stroke-width:3.25;stroke-dasharray:0 6;stroke-linecap:round"/></svg></div></html>`;
const SYN_URL = "/learning/_syn.html";
const synFile = path.join(L.virtual, "learning", "_syn.html");
fs.mkdirSync(path.dirname(synFile), { recursive: true });
fs.writeFileSync(synFile, SYN);
const cleanup = () => { try { fs.unlinkSync(synFile); } catch (e) {} };

// ---- grayscale run lengths along a row (the darkest row within ±5 px of the guess)
const gray = (png, x, y) => { const i = (y * png.width + x) * 4; return 0.299 * png.data[i] + 0.587 * png.data[i + 1] + 0.114 * png.data[i + 2]; };
function runsAt(png, y, x0, x1) {
  const seq = []; let cur = null, len = 0;
  for (let x = x0; x < x1; x++) { const d = gray(png, x, y) < 140; if (d === cur) len++; else { if (cur !== null) seq.push({ d: cur, len }); cur = d; len = 1; } }
  seq.push({ d: cur, len });
  const dark = seq.filter((s) => s.d).map((s) => s.len).slice(1, -1), gaps = seq.filter((s) => !s.d).map((s) => s.len).slice(1, -1);
  const med = (a) => a.length ? a.slice().sort((p, q) => p - q)[a.length >> 1] : null;
  return { dark: med(dark), gap: med(gaps), n: dark.length, darkPx: dark.reduce((a, b) => a + b, 0), y };
}
function runs(png, yGuess, x0, x1) { let best = null; for (let y = yGuess - 5; y <= yGuess + 5; y++) { const r = runsAt(png, y, x0, x1); if (!best || r.darkPx > best.darkPx) best = r; } return best; }
// thickest vertical dark run in a band of rows, scanning x = 8..60
function thickness(png, y0, y1) { let best = 0; for (let x = 8; x <= 60; x++) { let run = 0, t = 0; for (let y = y0; y <= y1; y++) { run = gray(png, x, y) < 140 ? run + 1 : 0; t = Math.max(t, run); } best = Math.max(best, t); } return best; }
const f = (x) => JSON.stringify(x);

// ---- page-side: dashed / dotted / solid strokes per chart, in screen px
const geometryInPage = () => {
  const out = [];
  document.querySelectorAll("svg[id], svg.chart").forEach((svg) => {
    const vb = svg.viewBox.baseVal; if (!vb.width) return;
    const s = svg.getBoundingClientRect().width / vb.width; if (!s) return;
    const d = { id: svg.id || "(chart)", dashed: [], dotted: [], solid: [] };
    svg.querySelectorAll("line, path").forEach((el) => {
      const cs = getComputedStyle(el); if (cs.stroke === "none" || /axis|gridl|gridline|zero/.test(el.getAttribute("class") || "")) return;
      if (/stroke:var\(--grid\)/.test(el.getAttribute("style") || "")) return;
      const w = parseFloat(cs.strokeWidth) * s, da = cs.strokeDasharray === "none" ? [] : cs.strokeDasharray.split(",").map((v) => parseFloat(v) * s);
      if (!da.length) d.solid.push(w); else if (da[0] < 1) d.dotted.push({ w, sp: da[1] }); else d.dashed.push({ w, dash: da[0], gap: da[1] });
    });
    if (d.dashed.length || d.dotted.length) out.push(d);
  });
  return out;
};

(async () => {
  const T0 = Date.now();
  // ============================================================ A. pixels, Chromium and Firefox
  c.section("A. grayscale run lengths at 375 px on the synthetic page (" + SYN_URL + "), Chromium and Firefox");
  for (const [bname, launcher] of [["chromium", chromium], ["firefox", firefox]]) {
    const browser = await launcher.launch();
    const page = await browser.newPage({ viewport: { width: 375, height: 300 }, deviceScaleFactor: 1 });
    const log = []; L.watch(page, log);
    await page.goto(base + SYN_URL); await page.waitForLoadState("load"); await page.waitForTimeout(400);
    const png = PNG.sync.read(await page.screenshot());
    const sc = 343 / 420, r = {};
    r.truth = runs(png, Math.round(15 * sc), 20, 330); r.fix = runs(png, Math.round(40 * sc), 20, 330);
    r.thresh = runs(png, Math.round(65 * sc), 20, 330); r.ciBarFix = runs(png, Math.round(90 * sc), 20, 330);
    r.truthT = thickness(png, 0, 25); r.fixT = thickness(png, 25, 45); r.fitT = thickness(png, 80, 100);
    const y2 = Math.round(120 * sc) + 2;   // the second svg starts after the first (height 120 × sc)
    r.reflDash = runs(png, y2 + 15, 20, 330); r.reflDot = runs(png, y2 + 40, 20, 330);
    r.reflDashT = thickness(png, y2 + 5, y2 + 25); r.reflDotT = thickness(png, y2 + 30, y2 + 50);
    console.log(`  ${bname}: truth ${f(r.truth)} ${r.truthT}px | fix ${f(r.fix)} ${r.fixT}px | thresh ${f(r.thresh)} | ci-bar-fix ${f(r.ciBarFix)} | fit ${r.fitT}px | refl dash ${f(r.reflDash)} ${r.reflDashT}px | refl dots ${f(r.reflDot)} ${r.reflDotT}px`);
    c.ok(r.truth.dark >= 9 && r.truth.dark <= 12 && r.truth.gap >= 4 && r.truthT >= 2, `${bname}: truth dashes 9–12 px with gaps ≥ 4 at ≥ 2 px thick (${f(r.truth)}, ${r.truthT}px)`);
    c.ok(r.fix.dark >= 3 && r.fix.dark <= 4 && r.fix.dark + r.fix.gap >= 5 && r.fixT >= 3, `${bname}: fix dots 3–4 px every ≥ 5 at ≥ 3 px thick (${f(r.fix)}, ${r.fixT}px)`);
    c.ok(r.truth.dark / r.fix.dark >= 2.5, `${bname}: dash ÷ dot = ${(r.truth.dark / r.fix.dark).toFixed(2)} ≥ 2.5`);
    c.ok(r.reflDash.dark >= 9 && r.reflDash.dark <= 12 && r.reflDash.gap >= 4 && r.reflDashT >= 2, `${bname}: Reflections dashed path 9–12 / ≥ 4 at ≥ 2 px (${f(r.reflDash)}, ${r.reflDashT}px)`);
    c.ok(r.reflDot.dark >= 3 && r.reflDot.dark <= 4 && r.reflDot.dark + r.reflDot.gap >= 5 && r.reflDotT >= 3 && r.reflDash.dark / r.reflDot.dark >= 2.5, `${bname}: Reflections dotted path 3–4 px every ≥ 5 at ≥ 3 px, dash ÷ dot ${(r.reflDash.dark / r.reflDot.dark).toFixed(2)} (${f(r.reflDot)}, ${r.reflDotT}px)`);
    c.ok(r.fitT >= 2 && r.ciBarFix.dark >= 3, `${bname}: fit ${r.fitT}px ≥ 2, ci-bar-fix dots ${f(r.ciBarFix)} ≥ 3`);
    c.ok(log.length === 0, `${bname}: synthetic page console clean: ` + log.join(" | "));
    if (bname === "firefox") {
      // the first ready module page that draws a .ci-bar-fix: its computed stroke via calc(var(--k)) must be 3.25 px on screen
      let found = null;
      for (const m of R.readyModules) {
        await page.goto(base + m.url); await page.waitForLoadState("load"); await page.waitForTimeout(700);
        const r2 = await page.evaluate(() => { const l = document.querySelector(".ci-bar-fix"); if (!l) return null; const s = l.closest("svg"); const sc = s.getBoundingClientRect().width / s.viewBox.baseVal.width; const cs = getComputedStyle(l); return { svg: s.id, k: s.style.getPropertyValue("--k"), scale: +sc.toFixed(3), w: +(parseFloat(cs.strokeWidth) * sc).toFixed(2), dash: cs.strokeDasharray }; });
        if (r2) { found = Object.assign({ module: m.slug }, r2); break; }
      }
      if (found) { console.log("  firefox .ci-bar-fix:", f(found)); c.ok(Math.abs(found.w - 3.25) < 0.1, `firefox ${found.module} #${found.svg}: .ci-bar-fix renders ${found.w} px via calc(var(--k)) (want 3.25)`); }
      else console.log("  note: no ready module page draws a .ci-bar-fix in its initial state — Firefox calc(var(--k)) check skipped");
    }
    await browser.close();
  }

  // ============================================================ B. DOM geometry per chart on every page
  c.section("B. per-chart dash / dot geometry at 375 px on every page (" + L.pages().length + " pages)");
  {
    const browser = await chromium.launch();
    const ctx = await L.context(browser, { width: 375 }); const page = await ctx.newPage();
    const min = { stroke: Infinity, dash: Infinity, gap: Infinity, dotSpacing: Infinity, ratio: Infinity };
    let charts = 0;
    for (const p of L.pages()) {
      await page.goto(base + p.url); await page.waitForLoadState("load"); await page.waitForTimeout(p.kind === "reflection" ? 900 : 600);
      const rows = await page.evaluate(geometryInPage);
      for (const ch of rows) {
        charts++;
        for (const x of ch.dashed) { min.dash = Math.min(min.dash, x.dash); min.gap = Math.min(min.gap, x.gap); }
        for (const x of ch.dotted) { min.dotSpacing = Math.min(min.dotSpacing, x.sp); min.stroke = Math.min(min.stroke, x.w); }
        c.ok(ch.dashed.every((x) => x.dash >= 6 && x.gap >= 4), `${p.name} #${ch.id}: dashes ≥ 6 px with gaps ≥ 4 (${ch.dashed.map((x) => x.dash.toFixed(1) + "/" + x.gap.toFixed(1)).join(", ")})`);
        c.ok(ch.dotted.every((x) => x.sp >= 5 && x.w >= 3), `${p.name} #${ch.id}: dots ≥ 3 px every ≥ 5 (${ch.dotted.map((x) => x.w.toFixed(2) + " every " + x.sp.toFixed(1)).join(", ")})`);
        if (ch.dashed.length && ch.dotted.length) { const ratio = Math.min(...ch.dashed.map((x) => x.dash)) / Math.max(...ch.dotted.map((x) => x.w)); min.ratio = Math.min(min.ratio, ratio); c.ok(ratio >= 2.5, `${p.name} #${ch.id}: min dash ÷ max dot = ${ratio.toFixed(2)} ≥ 2.5`); }
      }
    }
    c.ok(charts > 0, `charts with dashed or dotted strokes found (${charts})`);
    const fmt = (v) => isFinite(v) ? +v.toFixed(2) : null;
    console.log(`  smallest at 375 across ${charts} charts: dash ${fmt(min.dash)} px, gap ${fmt(min.gap)} px, dot ${fmt(min.stroke)} px every ${fmt(min.dotSpacing)} px, dash ÷ dot ${fmt(min.ratio)}`);
    await browser.close();
  }

  cleanup();
  close();
  process.exit(c.summary(`wall time ${Math.round((Date.now() - T0) / 1000)} s`));
})().catch((e) => { console.error(e); cleanup(); close(); process.exit(1); });
