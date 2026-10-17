// reflections.js — the Reflections section: the all-books page, every book page and every ready
// reflection page, against the registry (learning/assets/reflections.js) as the source of truth.
//   node learning/workshop/tests/reflections.js
// Generic checks iterate L.registries(): registry text rendered, series bar, math (no raw
// delimiters, no KaTeX errors), Python + Colab links, footer, chart text 12–13 px with no overlaps
// at 375 / 768 / 1280 × light / dark, equation twins, resize redraw, every control changes its
// figure, series tokens under data-colorblind, the viewing-settings matrix and rendered contrast.
// Page-specific checks (ported from the balanced-plant scratch suites) run only for that slug.
// Chromium only; expected text is never hard-coded and no color is compared to a literal hex.
"use strict";
const fs = require("fs"), path = require("path"), http = require("http");
const L = require("./lib");
const { chromium } = L.pw();
const { base, close } = L.serve();
const c = new L.Checker("reflections");
const R = L.registries();
const BOOKS_URL = "/learning/reflections/";
const get = (url) => new Promise((res) => http.get(url, (r) => { let b = ""; r.on("data", (d) => b += d); r.on("end", () => res({ status: r.statusCode, body: b })); }).on("error", () => res({ status: 0, body: "" })));
const settle = (ms) => new Promise((r) => setTimeout(r, ms));

// ---- page-side helpers (self-contained functions for page.evaluate) ----
// Charts are drawn by the page's main.js after load; wait until every svg[id] carries data-vb (or there is none).
const chartsReady = () => { const s = Array.from(document.querySelectorAll("svg[id]")); return s.length === 0 || s.every((x) => x.getAttribute("data-vb") && x.innerHTML.length > 0); };
const toRgbInPage = (v) => { const i = document.createElement("i"); i.style.color = v; document.body.appendChild(i); const out = getComputedStyle(i).color; i.remove(); return out; };
// The equation twins: each .eq-wide paired with the .eq-narrow that follows it. Source TeX from
// KaTeX's MathML annotation, else the element's text (the unrendered source).
const twinsInPage = () => Array.from(document.querySelectorAll(".eq-wide")).map((w) => {
  let n = w.nextElementSibling; while (n && !n.classList.contains("eq-narrow")) n = n.nextElementSibling;
  const info = (e) => { if (!e) return null; const d = e.querySelector(".katex-display"); const a = e.querySelector("annotation"); return { shown: getComputedStyle(e).display !== "none", over: d ? d.scrollWidth > d.clientWidth + 1 : null, err: e.querySelectorAll(".katex-error").length, tex: a ? a.textContent : e.textContent }; };
  return { wide: info(w), narrow: info(n) };
});
// Same TeX apart from layout: drop the aligned wrapper, alignment points, line breaks, spacing commands and whitespace.
const texKey = (s) => String(s || "").replace(/\\begin\{aligned\}|\\end\{aligned\}/g, "").replace(/\\\\/g, "").replace(/&/g, "").replace(/\\(qquad|quad|;|,|!|:|>| )/g, "").replace(/\s+/g, "");

async function open(ctx, url, log, settleMs) {
  const page = await ctx.newPage(); if (log) L.watch(page, log);
  await page.goto(base + url); await page.waitForLoadState("load");
  try { await page.waitForFunction(chartsReady, null, { timeout: 5000 }); } catch (e) {}
  await settle(settleMs || 250);
  return page;
}

(async () => {
  const browser = await chromium.launch();
  const T0 = Date.now();

  // ================================================================ 1. all-books page
  c.section("1. all-books page (" + BOOKS_URL + ")");
  {
    const ctx = await L.context(browser, {}); const log = []; const page = await open(ctx, BOOKS_URL, log);
    const rows = await page.evaluate(() => Array.from(document.querySelectorAll("#book-list > li")).map((li) => {
      const a = li.querySelector("a"), q = (s) => { const e = li.querySelector(s); return e ? e.textContent.trim() : null; };
      return { link: !!a, href: a && a.getAttribute("href"), title: q(".b-title"), meta: q(".b-meta"), count: q(".b-count"), about: q(".b-about") };
    }));
    c.ok(rows.length === R.books.length, `all-books: ${rows.length} rows for ${R.books.length} registry books`);
    R.books.forEach((b, i) => {
      const r = rows[i]; if (!r) { c.ok(false, `all-books: row ${i + 1} (${b.slug}) missing`); return; }
      const n = (b.reflections || []).filter((x) => x.ready).length;
      const meta = `${b.authors}, ${b.year}` + (b.edition ? ` · ${b.edition}` : "");
      c.ok(L.norm(r.title) === L.norm(b.title), `all-books ${b.slug}: title "${r.title}" === registry "${b.title}"`);
      c.ok(L.norm(r.meta) === L.norm(meta), `all-books ${b.slug}: meta "${r.meta}" === "${meta}"`);
      if (n) {
        const m = /^(\d+) reflections?$/.exec(r.count || "");
        c.ok(r.link && r.href === b.slug + "/" && m && +m[1] === n && (n === 1) === /reflection$/.test(r.count), `all-books ${b.slug}: links to ${b.slug}/ with "${n} reflection(s)" (got link=${r.link} href=${r.href} count="${r.count}")`);
      } else c.ok(!r.link && r.count === "Not yet", `all-books ${b.slug}: "Not yet" without a link (got link=${r.link} count="${r.count}")`);
      c.ok(b.about ? L.norm(r.about) === L.norm(b.about) : r.about === null, `all-books ${b.slug}: about ${b.about ? "shown" : "absent"}`);
    });
    c.ok(log.length === 0, "all-books console clean: " + log.join(" | "));
    await ctx.close();
  }

  // ================================================================ 2. every book page
  c.section("2. book pages (" + R.booksWithPages.length + ")");
  for (const b of R.booksWithPages) {
    const ctx = await L.context(browser, {}); const log = []; const page = await open(ctx, b.url, log);
    const r = await page.evaluate(() => ({
      rows: Array.from(document.querySelectorAll("#ref-list .ref-row")).map((a) => ({ href: a.getAttribute("href"), title: (a.querySelector(".m-title") || {}).textContent, date: (a.querySelector(".ref-date") || {}).textContent, summary: (a.querySelector(".m-desc") || {}).textContent })),
      about: (() => { const e = document.getElementById("book-about"); return e ? { hidden: e.hidden, text: e.textContent } : null; })(),
      h1: (document.querySelector("h1") || {}).textContent,
    }));
    const want = b.ready.slice().sort((x, y) => x.date < y.date ? 1 : x.date > y.date ? -1 : 0);
    c.ok(L.norm(r.h1) === L.norm(b.title), `${b.slug}: h1 "${r.h1}" === registry title`);
    c.ok(r.rows.length === want.length, `${b.slug}: ${r.rows.length} rows for ${want.length} ready reflections`);
    want.forEach((x, i) => {
      const row = r.rows[i]; if (!row) return;
      c.ok(row.href === x.slug + "/" && L.norm(row.title) === L.norm(x.title) && L.norm(row.date) === L.fmtDate(x.date, "en") && L.norm(row.summary) === L.norm(x.summary),
        `${b.slug} row ${i + 1}: ${x.slug}/ "${x.title}" ${L.fmtDate(x.date, "en")} (got ${row.href} "${row.title}" ${row.date})`);
    });
    c.ok(r.about && (b.about ? !r.about.hidden && L.norm(r.about.text) === L.norm(b.about) : r.about.hidden), `${b.slug}: #book-about ${b.about ? "shows the registry text" : "hidden (no about in the registry)"}`);
    c.ok(log.length === 0, `${b.slug} console clean: ` + log.join(" | "));
    await ctx.close();
  }

  // ================================================================ 3. every ready reflection, generic
  for (const x of R.readyReflections) {
    const name = `${x.book}/${x.slug}`, isBP = x.slug === "balanced-plant";
    c.section(`3. reflection ${name} — page, math, links, footer`);
    const ctx = await L.context(browser, {}); const log = []; const page = await open(ctx, x.url, log, 400);
    const m = await page.evaluate(() => {
      const essay = document.querySelector("main.essay");
      const q = (s, root) => (root || document).querySelector(s);
      return {
        h1: (q("h1") || {}).textContent, essay: !!essay,
        raw: essay ? /\\\(|\$\$/.test(essay.innerText) : null,
        katex: document.querySelectorAll(".katex").length, display: document.querySelectorAll(".katex-display").length,
        inlineOnly: Array.from(document.querySelectorAll(".katex")).filter((k) => !k.closest(".katex-display")).length,
        errors: document.querySelectorAll(".katex-error").length,
        crumbs: Array.from(document.querySelectorAll(".series-bar .crumbs a, .series-bar .crumbs span:not([aria-hidden])")).map((a) => ({ t: a.textContent.trim(), href: a.getAttribute("href") })),
        py: q(".takeaway-links a[download]") && q(".takeaway-links a[download]").href, colab: q(".take-colab") && q(".take-colab").href,
        foot: q(".foot") && q(".foot").textContent,
        fbox: document.querySelectorAll(".katex .fbox").length, underbrace: document.querySelectorAll(".katex .munder .brace-center").length,
        varOp: Array.from(document.querySelectorAll(".katex .mop")).some((e) => e.textContent === "Var"),
        s13: q('a[href="../../../fits/time-order/"]') && q('a[href="../../../fits/time-order/"]').href,
        cap: (() => { const f = q("figcaption"); if (!f) return null; const cs = getComputedStyle(f); return { fam: cs.fontFamily, size: cs.fontSize, weight: cs.fontWeight, body: getComputedStyle(document.documentElement).getPropertyValue("--font-body") }; })(),
      };
    });
    c.ok(L.norm(m.h1) === L.norm(x.title), `${name}: h1 "${m.h1}" === registry "${x.title}"`);
    const hrefs = m.crumbs.map((k) => k.href);
    c.ok(hrefs.length === 4 && hrefs.join(" ") === "../../../../ ../../../ ../../ ../", `${name}: series bar hrefs ${hrefs.join(" ")}`);
    const last = m.crumbs[m.crumbs.length - 1] || { t: "" };
    const exact = L.norm(last.t) === L.norm(x.bookTitle), short = !exact && last.t.length >= 3 && L.norm(x.bookTitle).startsWith(L.norm(last.t));
    c.ok(exact || short, `${name}: last crumb "${last.t}" ${exact ? "=== the book title" : short ? "is the short form (book title starts with it)" : "does not match the book title \"" + x.bookTitle + "\""}`);
    c.ok(m.essay && m.raw === false, `${name}: no raw \\( or $$ in main.essay`);
    if (m.katex) c.ok(m.errors === 0 && m.inlineOnly > 0 && m.display > 0, `${name}: KaTeX ${m.katex} expressions (${m.inlineOnly} inline, ${m.display} display), ${m.errors} error spans`);
    else console.log(`  note: ${name} has no .katex (no math on the page)`);
    if (m.py) { const r = await get(m.py); c.ok(r.status === 200 && /\.py$/.test(m.py), `${name}: Python link answers ${r.status}: ${m.py}`); } else c.ok(false, `${name}: no Python link (.takeaway-links a[download])`);
    const colab = `https://colab.research.google.com/github/gidgo130/gideonong.me/blob/main/learning/reflections/${x.book}/${x.slug}/${x.slug}.ipynb`;
    c.ok(m.colab === colab, `${name}: Colab link ${m.colab} === ${colab}`);
    c.ok(fs.existsSync(path.join(x.dir, x.slug + ".ipynb")), `${name}: ${x.slug}.ipynb on disk`);
    const raw = (await get(base + x.url)).body;
    c.ok(m.foot && m.foot.includes("CC BY-SA 4.0") && m.foot.includes("Built with"), `${name}: footer has the license line and "Built with"`);
    c.ok(/class="fb-slot"[^>]*>[^<]*gao9819@utulsa\.edu/.test(raw), `${name}: footer slot carries the email in the HTML (the feedback widget replaces it on http)`);
    if (m.cap) c.ok(m.cap.fam.split(",")[0].trim() === m.cap.body.split(",")[0].trim() && m.cap.size === "14px" && m.cap.weight === "400", `${name}: figcaption in the body face (${m.cap.fam.split(",")[0]} vs --font-body ${m.cap.body.split(",")[0]}), ${m.cap.size}, weight ${m.cap.weight}`);
    if (isBP) {
      c.ok(m.katex > 40 && m.display >= 15, `balanced-plant: ${m.katex} expressions, ${m.display} display`);
      c.ok(m.fbox >= 1 && m.underbrace >= 4 && m.varOp, `balanced-plant: \\boxed (${m.fbox}), \\underbrace stretchy (${m.underbrace}), Var operator (${m.varOp})`);
      const s13 = m.s13 ? await get(m.s13) : { status: 0 };
      c.ok(s13.status === 200, `balanced-plant: §13 link ../../../fits/time-order/ resolves (${s13.status}) ${m.s13}`);
    }
    c.ok(log.length === 0, `${name} console clean: ` + log.join(" | "));
    await ctx.close();

    // ---------------------------------------------------------------- charts and twins at 3 widths × 2 themes
    c.section(`3b. reflection ${name} — chart text, overlaps, twins at 375 / 768 / 1280 × light / dark`);
    const AUTH = {};
    for (const w of [1280, 768, 375]) for (const dark of [false, true]) {
      const label = `${name} ${w}px ${dark ? "dark" : "light"}`;
      const ctx2 = await L.context(browser, { width: w, dark }); const log2 = []; const page2 = await open(ctx2, x.url, log2, 300);
      const charts = await page2.evaluate(L.inPage.chartText);
      const tw = await page2.evaluate(twinsInPage);
      const bp = isBP ? await page2.evaluate(() => {
        const svg = document.getElementById("bc"); if (!svg) return null;
        const pb = svg.querySelector(".plot-bg"); const pr = pb && pb.getBoundingClientRect();
        const direct = Array.from(svg.querySelectorAll("text")).filter((t) => /^\d (stations|st\.)$/.test(t.textContent.trim())).map((t) => { const b = t.getBoundingClientRect(); return { t: t.textContent.trim(), inMargin: pr ? b.left >= pr.right - 0.5 : null, y: b.top, h: b.height }; });
        const f = document.querySelector('.fig[style*="overflow-x"]'); const t = f && f.querySelector("text");
        const diagram = f ? { scrolls: f.scrollWidth > f.clientWidth + 1, px: t ? parseFloat(getComputedStyle(t).fontSize) * Math.hypot(t.getScreenCTM().a, t.getScreenCTM().b) : null } : null;
        return { direct, diagram };
      }) : null;
      c.ok(charts.length > 0, `${label}: charts found (${charts.length})`);
      for (const ch of charts) {
        c.ok(ch.overlaps.length === 0, `${label} #${ch.id}: text overlaps: ${ch.overlaps.join("; ")}`);
        c.ok(ch.px >= 11.9 && ch.pxMax <= 13.5, `${label} #${ch.id}: chart text ${ch.px.toFixed(1)}–${ch.pxMax.toFixed(1)} px (scale ${ch.scale})`);
        c.ok(!!ch.dataVb, `${label} #${ch.id}: has data-vb`);
        if (w === 1280) { c.ok(Math.abs(ch.vbW - ch.w) <= 1, `${label} #${ch.id}: viewBox width ${ch.vbW} tracks the container ${ch.w}`); AUTH[ch.id] = ch.vb; }
      }
      if (tw.length) {
        for (const [i, p] of tw.entries()) {
          if (!p.narrow) { c.ok(false, `${label} twin ${i + 1}: .eq-wide with no following .eq-narrow`); continue; }
          if (w === 1280) c.ok(p.wide.shown && !p.wide.over && !p.narrow.shown, `${label} twin ${i + 1}: wide shown without overflow, narrow hidden (${JSON.stringify(p)})`);
          if (w === 375) c.ok(p.narrow.shown && !p.narrow.over && p.narrow.err === 0 && !p.wide.shown, `${label} twin ${i + 1}: narrow shown, no overflow, no error, wide hidden (${JSON.stringify(p)})`);
          if (w === 1280 && !dark) c.ok(texKey(p.wide.tex) === texKey(p.narrow.tex), `${label} twin ${i + 1}: same TeX apart from spacing\n    wide   ${texKey(p.wide.tex)}\n    narrow ${texKey(p.narrow.tex)}`);
        }
      } else if (w === 1280 && !dark) console.log(`  note: ${name} has no .eq-wide/.eq-narrow twins`);
      if (bp) {
        if (w >= 768) {
          c.ok(bp.direct.length === 4 && bp.direct.every((d) => d.inMargin), `${label} §8: 4 direct labels in the right margin: ${JSON.stringify(bp.direct)}`);
          if (bp.direct.length > 1) { const ys = bp.direct.map((d) => d.y).sort((a, b) => a - b); const gap = Math.min(...ys.slice(1).map((y, i) => y - ys[i])); const h = bp.direct[0].h; c.ok(gap >= 1.15 * h, `${label} §8: labels ${gap.toFixed(1)} px apart ≥ 1.15 × height ${h.toFixed(1)}`); }
        } else c.ok(bp.direct.length === 0, `${label} §8: direct labels dropped on a phone (${bp.direct.length})`);
        if (w === 375) c.ok(bp.diagram && bp.diagram.scrolls && bp.diagram.px >= 11, `${label} §1: diagram scrolls in its box with ${bp.diagram && bp.diagram.px && bp.diagram.px.toFixed(1)} px text`);
      }
      c.ok(log2.length === 0, `${label} console clean: ` + log2.join(" | "));
      await ctx2.close();
    }

    // ---------------------------------------------------------------- resize round trip
    c.section(`3c. reflection ${name} — resize 1280 → 375 → 1280`);
    {
      const ctx3 = await L.context(browser, { width: 1280 }); const log3 = []; const page3 = await open(ctx3, x.url, log3, 300);
      const before = await page3.evaluate(L.inPage.chartText);
      const walk = isBP ? await page3.evaluate(() => ({ n: document.querySelectorAll("#rc path").length, d: (document.querySelector("#rc path") || {}).getAttribute && document.querySelector("#rc path").getAttribute("d") })) : null;
      await page3.setViewportSize({ width: 375, height: 800 }); await settle(600);
      const narrow = await page3.evaluate(L.inPage.chartText);
      c.ok(narrow.length === before.length && narrow.every((ch) => ch.vbW < 400 && ch.px >= 11), `${name}: after 1280→375 every chart redrew narrow: ` + narrow.map((ch) => `${ch.id} ${ch.vb} ${ch.px.toFixed(1)}px`).join(", "));
      if (walk) c.ok((await page3.evaluate(() => document.querySelectorAll("#rc path").length)) === walk.n, `balanced-plant: random-walk chart keeps its ${walk.n} paths at 375 (no re-simulation)`);
      await page3.setViewportSize({ width: 1280, height: 900 }); await settle(600);
      const back = await page3.evaluate(L.inPage.chartText);
      c.ok(back.every((ch) => ch.vb === before.find((b) => b.id === ch.id).vb), `${name}: after 375→1280 every chart is back to its 1280 viewBox`);
      if (walk) c.ok((await page3.evaluate(() => document.querySelector("#rc path").getAttribute("d"))) === walk.d, "balanced-plant: same random-walk path after the round trip");
      c.ok(log3.length === 0, `${name} resize console clean: ` + log3.join(" | "));
      await ctx3.close();
    }

    // ---------------------------------------------------------------- every control changes its figure
    c.section(`3d. reflection ${name} — every control in .fig .controls`);
    {
      const ctx4 = await L.context(browser, { width: 1280 }); const log4 = []; const page4 = await open(ctx4, x.url, log4, 300);
      const controls = await page4.evaluate(() => Array.from(document.querySelectorAll(".fig .controls input[type=range], .fig .controls select, .fig .controls button")).map((el, i) => {
        el.setAttribute("data-test-ix", String(i));
        return { i, tag: el.tagName.toLowerCase(), id: el.id, min: el.min, max: el.max, value: el.value, options: el.tagName === "SELECT" ? Array.from(el.options).map((o) => o.value) : null };
      }));
      c.ok(controls.length > 0, `${name}: controls found (${controls.length})`);
      const snap = (i) => page4.evaluate((ix) => { const el = document.querySelector(`[data-test-ix="${ix}"]`); const fig = el.closest(".fig"); return Array.from(fig.querySelectorAll("svg")).map((s) => s.innerHTML).join("|") + "||" + Array.from(fig.querySelectorAll(".readout")).map((r) => r.innerHTML).join("|"); }, i);
      for (const k of controls) {
        const before = await snap(k.i);
        if (k.tag === "input") {
          const mn = +k.min, mx = +k.max, cur = +k.value, v = cur > (mn + mx) / 2 ? mn : mx;
          await page4.evaluate(([ix, val]) => { const el = document.querySelector(`[data-test-ix="${ix}"]`); el.value = val; el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true })); }, [k.i, String(v)]);
        } else if (k.tag === "select") {
          const other = k.options.find((o) => o !== k.value);
          await page4.selectOption(`[data-test-ix="${k.i}"]`, other);
        } else {
          await page4.click(`[data-test-ix="${k.i}"]`);
          try { await page4.waitForFunction((ix) => !document.querySelector(`[data-test-ix="${ix}"]`).disabled, k.i, { timeout: 60000 }); } catch (e) {}
        }
        let changed = false; const t0 = Date.now();
        while (Date.now() - t0 < 2000) { if ((await snap(k.i)) !== before) { changed = true; break; } await settle(50); }
        c.ok(changed, `${name}: ${k.tag}#${k.id || k.i} changes its figure's svg or readout`);
      }
      if (isBP) {
        const n = await page4.evaluate(() => document.querySelectorAll("#kc circle").length);
        c.ok(n === 8, `balanced-plant: kSim added 8 simulated points (#kc circle = ${n})`);
        const cues = await page4.evaluate(() => {
          const forms = (id) => new Set(Array.from(document.querySelectorAll("#" + id + " path")).map((p) => ((p.getAttribute("style") || "").match(/stroke-dasharray:([^;]+)/) || [, "solid"])[1].trim()));
          const ring = Array.from(document.querySelectorAll("#cc circle")).filter((k) => /fill:var\(--paper\);stroke:var\(--s4\)/.test(k.getAttribute("style") || "")).length;
          const squares = document.querySelectorAll("#bc rect[style*='stroke:var(--s4)']").length;
          const labels = Array.from(document.querySelectorAll("#bc text[style*='fill:var(--s']")).filter((t) => /^\d (stations|st\.)$/.test(t.textContent.trim())).length;
          return { bc: [...forms("bc")], wc: [...forms("wc")], cc: [...forms("cc")], ring, squares, labels };
        });
        c.ok(cues.bc.length === 3 && cues.wc.length === 3 && cues.cc.length === 3, `balanced-plant: three line forms in #bc #wc #cc: ${JSON.stringify({ bc: cues.bc, wc: cues.wc, cc: cues.cc })}`);
        c.ok(cues.ring === 1, `balanced-plant: one ring marker in #cc (${cues.ring})`);
        // One hollow square per data point of the 5-station series (DATA.bufsweep["5"] in main.js: 7 points
        // until 755cfb5, 9 since), plus one direct label per station count.
        const src = fs.readFileSync(path.join(x.dir, "main.js"), "utf8"), m5 = /"bufsweep":\{[^}]*?"5":\[([^\]]*)\]/.exec(src);
        const nSq = m5 ? m5[1].split(",").filter((s) => s.trim()).length : null;
        c.ok(nSq != null && cues.squares === nSq && cues.labels === 4, `balanced-plant: ${nSq} square markers (one per 5-station data point in main.js) and 4 direct labels in #bc (got ${cues.squares} squares, ${cues.labels} labels)`);
      }
      c.ok(log4.length === 0, `${name} controls console clean: ` + log4.join(" | "));
      await ctx4.close();
    }

    // ---------------------------------------------------------------- series tokens under data-colorblind, both themes
    c.section(`3e. reflection ${name} — series tokens`);
    for (const dark of [false, true]) {
      const tok = {};
      for (const cb of [false, true]) {
        const ctx5 = await L.context(browser, { width: 1280, dark, cb }); const page5 = await open(ctx5, x.url, null, 200);
        tok[cb] = await page5.evaluate((toRgbSrc) => {
          const toRgb = eval("(" + toRgbSrc + ")");
          const s1 = getComputedStyle(document.documentElement).getPropertyValue("--s1").trim();
          const p = document.querySelector('svg[id] path[style*="stroke:var(--s1)"]');
          return { s1, rgb: toRgb(s1), cb: document.documentElement.hasAttribute("data-colorblind"), pathStroke: p ? getComputedStyle(p).stroke : null };
        }, toRgbInPage.toString());
        await ctx5.close();
      }
      const th = dark ? "dark" : "light";
      c.ok(tok[true].cb && !tok[false].cb, `${name} ${th}: data-colorblind set only in the colorblind context`);
      c.ok(tok[true].s1 && tok[false].s1 && tok[true].rgb !== tok[false].rgb, `${name} ${th}: computed --s1 under data-colorblind (${tok[true].s1}) differs from plain (${tok[false].s1})`);
      for (const cb of [false, true]) if (tok[cb].pathStroke) c.ok(tok[cb].pathStroke === tok[cb].rgb, `${name} ${th}${cb ? " colorblind" : ""}: a --s1 path renders the computed token (${tok[cb].pathStroke} vs ${tok[cb].rgb})`);
    }

    // ---------------------------------------------------------------- matrix
    c.section(`4. reflection ${name} — matrix 375 / 768 / 1280 × light / dark × plain / readability / colorblind / both`);
    for (const w of [375, 768, 1280]) for (const dark of [false, true]) for (const mode of ["", "r", "c", "rc"]) {
      const label = `${name} ${w}px ${dark ? "dark" : "light"} ${mode || "plain"}`;
      const ctx6 = await L.context(browser, { width: w, dark, read: mode.includes("r"), cb: mode.includes("c") }); const log6 = []; const page6 = await open(ctx6, x.url, log6, 250);
      const r = await page6.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: innerWidth, raw: /\\\(|\$\$/.test((document.querySelector("main.essay") || document.body).innerText), err: document.querySelectorAll(".katex-error").length, attrs: document.documentElement.getAttribute("data-readability") + "/" + document.documentElement.getAttribute("data-colorblind") }));
      const charts = await page6.evaluate(L.inPage.chartText);
      c.ok(r.sw <= r.iw, `${label}: no sideways scroll (${r.sw} > ${r.iw})`);
      c.ok(!r.raw && r.err === 0, `${label}: no raw delimiters / error spans`);
      if (w < 1280 && charts.length) { const mn = Math.min(...charts.map((ch) => ch.px)); c.ok(mn >= 11, `${label}: smallest chart text ${mn.toFixed(1)} px`); }
      c.ok(log6.length === 0, `${label}: console clean: ` + log6.join(" | "));
      await ctx6.close();
    }

    // ---------------------------------------------------------------- rendered contrast
    c.section(`5. reflection ${name} — rendered contrast, light / dark × readability`);
    for (const dark of [false, true]) for (const read of [false, true]) {
      const label = `${name} ${dark ? "dark" : "light"}${read ? " + readability" : ""}`;
      const ctx7 = await L.context(browser, { width: 1280, dark, read }); const page7 = await open(ctx7, x.url, null, 300);
      const r = await page7.evaluate((toRgbSrc) => {
        const toRgb = eval("(" + toRgbSrc + ")");
        const Lum = (col) => { const m = col.match(/[\d.]+/g).map(Number); const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(m[0]) + 0.7152 * f(m[1]) + 0.0722 * f(m[2]); };
        const cr = (a, b) => { const x = Lum(a), y = Lum(b); return +((Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05)).toFixed(2); };
        const cs = (e) => getComputedStyle(e), root = cs(document.documentElement), tok = (v) => toRgb(root.getPropertyValue(v).trim());
        const bgOf = (el) => { for (let e = el; e; e = e.parentElement) { const b = cs(e).backgroundColor; if (b !== "rgba(0, 0, 0, 0)" && b !== "transparent") return b; } return cs(document.body).backgroundColor; };
        const paper = cs(document.body).backgroundColor, out = { paper }, skipped = [];
        const q = (s) => document.querySelector(s);
        const p = q("main.essay > p") || q("main.essay p"); if (p) out.body = cr(cs(p).color, bgOf(p)); else skipped.push("body paragraph");
        const cap = q("figcaption"); if (cap) out.muted = cr(cs(cap).color, bgOf(cap)); else skipped.push("figcaption");
        const accent = tok("--accent");
        const brass = q(".tie b") || q(".books .tag") || Array.from(document.querySelectorAll("main *")).find((e) => cs(e).color === accent && e.textContent.trim() && e.getClientRects().length);
        if (brass) out.brass = cr(cs(brass).color, bgOf(brass)); else skipped.push("brass element");
        const fig = q(".fig"); const surface = fig ? cs(fig).backgroundColor : tok("--plot");
        const svg = q("svg[id]"); const pbEl = svg && svg.querySelector(".plot-bg"); const tick = svg && Array.from(svg.querySelectorAll("text")).find((t) => !t.getAttribute("style"));
        const sheet = pbEl ? cs(pbEl).fill : null;
        if (tick && sheet) out.tickOnSheet = cr(cs(tick).fill, sheet); else skipped.push("chart tick on sheet");
        const legend = q(".legend"); if (legend) out.legend = cr(cs(legend).color, bgOf(legend)); else skipped.push("legend");
        const lbl = q(".controls label"); if (lbl) out.controlLabel = cr(cs(lbl).color, bgOf(lbl)); else skipped.push("control label");
        const thm = q(".thm"); const orange = thm ? cs(thm).borderLeftColor : tok("--emph");
        out.orangeOnPaper = cr(orange, paper); out.orangeOnSurface = cr(orange, surface);
        out.series = {};
        for (const s of ["--s1", "--s2", "--s3", "--s4"]) { const col = tok(s); out.series[s] = { surface: cr(col, surface), sheet: sheet ? cr(col, sheet) : null }; }
        out.skipped = skipped;
        return out;
      }, toRgbInPage.toString());
      if (r.skipped.length) console.log(`  note: ${label}: no element for ${r.skipped.join(", ")} — those checks skipped`);
      const text = ["body", "muted", "brass", "tickOnSheet", "legend", "controlLabel", "orangeOnPaper", "orangeOnSurface"].filter((k) => r[k] != null);
      for (const k of text) c.ok(r[k] >= 4.5, `${label}: ${k} ${r[k]}:1 ≥ 4.5`);
      for (const [s, v] of Object.entries(r.series)) c.ok(v.surface >= 3 && (v.sheet == null || v.sheet >= 3), `${label}: ${s} on surface ${v.surface}:1 / sheet ${v.sheet}:1 ≥ 3`);
      await ctx7.close();
    }

    // ---------------------------------------------------------------- balanced-plant: vision-deficiency shots (no assertion)
    if (isBP) {
      c.section("6. balanced-plant — vision-deficiency screenshots of #bc / #wc / #cc → " + L.out);
      const ctx8 = await L.context(browser, { width: 1280 }); const page8 = await open(ctx8, x.url, null, 300);
      const cdp = await ctx8.newCDPSession(page8);
      for (const type of ["achromatopsia", "deuteranopia"]) {
        await cdp.send("Emulation.setEmulatedVisionDeficiency", { type });
        for (const id of ["bc", "wc", "cc"]) {
          const loc = page8.locator("#" + id); if (!(await loc.count())) continue;
          await loc.scrollIntoViewIfNeeded(); await settle(80);
          const box = await loc.boundingBox(); if (box) await page8.screenshot({ path: path.join(L.out, `reflections-cvd-${type}-${id}.png`), clip: box });
        }
      }
      await cdp.send("Emulation.setEmulatedVisionDeficiency", { type: "none" });
      await ctx8.close();
    }
  }

  await browser.close();
  close();
  process.exit(c.summary(`wall time ${Math.round((Date.now() - T0) / 1000)} s`));
})().catch((e) => { console.error(e); close(); process.exit(1); });
