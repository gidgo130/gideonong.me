// pages.js — "every page" plumbing for /learning, driven by the registries (lib.pages()):
//   1. trailing slash: a folder URL without the slash lands on the slashed URL
//   2. raw HTML: noindex, the full OG set + twitter:card, og:url, the 1200×630 card PNG, the
//      footer's .fb-slot, feedback.js last, strings-common.js before it (Reflections), html attrs
//   3. registry text rendered: hub EN/ES, module <title>/h1, module list, books, book pages, reflections
//   4. a11y per page (desktop) + report-only notes
//   5. the feedback dialog's focus handling (one page per kind)
//   6. view settings (assets/view-settings.js, 2026-10-17): the View button and popover (markup,
//      registry texts, open / Esc / outside click, Dark / System, colorblind "1" / "0", readability),
//      the .cb-hint under the first legend, ES re-render; 6b. View button = EN/ES toggle box, one bar
//      row at 375 px; 6c. prefers-contrast: more → data-colorblind unless viewColorblind is "0"
//   7. skip link: first in <body>, registry text, hidden until focused, first Tab stop, #main has the h1
//   8. forced colors: charts keep forced-color-adjust none, a painted background, distinct strokes
//   9. highlighted points / flagged bars: ink outline 1 × --k, 2 × / 1.75 × under data-colorblind
//  10. decks and play pages: noindex + og:url in the first 2048 bytes, one charset first; play OG set
//  11. 375 px matrix (theme × readability × colorblind) + 768/1280 light/dark: overflow, console,
//      <html> attributes, data-series, --k on every visible svg.chart, base font
//  12. from disk (file://): folder links rewritten, every relative link target exists, console, KaTeX
// Expected text always comes from lib.registries(); nothing here is copied from the pages.
// Ported 2026-10-16 from the scratchpad suites audit.js, test.js (§1, §7, §8) and test-theme.js (§C).
"use strict";
const fs = require("fs"), path = require("path");
const { pathToFileURL } = require("url");
const L = require("./lib");
const { chromium } = L.pw();
const { base, close } = L.serve();
const c = new L.Checker("pages");
const R = L.registries();
const PAGES = L.pages();
const SITE = "https://gideonong.me";
const IGNORE = /fonts\.g(oogleapis|static)\.com/;   // Google Fonts come from the network, not the page
const t0 = Date.now();

async function get(url) { const r = await fetch(url); return { status: r.status, buf: Buffer.from(await r.arrayBuffer()) }; }
const meta = (html, prop) => { const m = new RegExp(`<meta\\s+(?:property|name)="${prop}"\\s+content="([^"]*)"`).exec(html); return m ? m[1] : null; };
const hasAttr = (tag, name) => new RegExp(`\\s${name}(?=[\\s>=])`).test(tag);
const attrVal = (tag, name) => { const m = new RegExp(`\\s${name}="([^"]*)"`).exec(tag); return m ? m[1] : null; };
async function settle(page, pg, ms) {
  await page.waitForLoadState("load");
  if (pg.kind === "hub") { try { await page.waitForSelector("#reflections:not([hidden])", { timeout: 5000 }); } catch (e) { /* asserted below */ } }
  await page.waitForTimeout(ms || (pg.kind === "reflection" ? 500 : 200));
}
const text = (page, sel) => page.$eval(sel, (e) => e.textContent).then(L.norm, () => null);
const texts = (page, sel) => page.$$eval(sel, (es) => es.map((e) => e.textContent)).then((a) => a.map(L.norm));
const same = (a, b) => L.norm(a) === L.norm(b);
const byKind = {}; PAGES.forEach((p) => { if (!byKind[p.kind]) byKind[p.kind] = p; });
const byDate = (a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0);

// ---- page-side functions (serialized by page.evaluate) ----
const A11Y = () => {
  const out = {};
  const hs = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].filter((h) => !h.closest("dialog"));
  const skips = []; let prev = 0;
  hs.forEach((h) => { const n = +h.tagName[1]; if (prev && n > prev + 1) skips.push(`${prev}→${n} at "${h.textContent.trim().slice(0, 40)}"`); prev = n; });
  out.headingSkips = skips; out.h1Count = hs.filter((h) => h.tagName === "H1").length;
  const unl = [];
  document.querySelectorAll("input,select,textarea,button").forEach((el) => {
    if (el.type === "hidden") return;
    const id = el.id;
    const has = el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") || (id && document.querySelector(`label[for="${CSS.escape(id)}"]`)) || el.closest("label") || (el.tagName === "BUTTON" && el.textContent.trim()) || el.getAttribute("title");
    if (!has) unl.push(el.tagName + (id ? "#" + id : "") + (el.className ? "." + String(el.className).split(" ")[0] : "") + " type=" + el.type);
  });
  out.unlabeled = unl;
  const svgs = [...document.querySelectorAll("svg")].filter((s) => !s.closest("dialog") && !s.closest(".katex"));
  out.chartsBad = [...document.querySelectorAll("svg.chart")].filter((s) => s.getAttribute("role") !== "img" || !s.getAttribute("aria-label")).map((s) => "svg#" + s.id);
  out.svgLabelNoRole = svgs.filter((s) => s.getAttribute("aria-label") && s.getAttribute("role") !== "img").map((s) => "svg#" + s.id);
  out.imgNoAlt = [...document.querySelectorAll("img")].filter((i) => !i.hasAttribute("alt")).map((i) => i.getAttribute("src"));
  out.posTabindex = [...document.querySelectorAll("[tabindex]")].filter((e) => +e.getAttribute("tabindex") > 0).map((e) => e.tagName + (e.id ? "#" + e.id : ""));
  const ids = [...document.querySelectorAll("[id]")].map((e) => e.id);
  out.dupIds = [...new Set(ids.filter((v, i) => ids.indexOf(v) !== i))];
  out.newTabNoNoopener = [...document.querySelectorAll('a[target="_blank"]')].filter((a) => !/noopener|noreferrer/.test(a.rel)).map((a) => a.getAttribute("href"));
  out.readouts = document.querySelectorAll(".readout").length;
  // a readout counts as live when it is a live region, sits in one, or has learning.js's mirror beside it
  out.readoutsLive = [...document.querySelectorAll(".readout")].filter((r) => r.closest("[aria-live]") || r.getAttribute("aria-live") || (r.nextElementSibling && r.nextElementSibling.getAttribute("aria-live"))).length;
  const lt = document.querySelector(".lang-toggle");
  out.langToggle = lt ? { hidden: lt.hidden, pressed: lt.getAttribute("aria-pressed"), label: lt.getAttribute("aria-label") } : null;
  out.thNoScope = [...document.querySelectorAll("th")].filter((t) => !t.getAttribute("scope")).length;
  out.newTabNoHint = [...document.querySelectorAll('a[target="_blank"]')].filter((a) => { const d = a.getAttribute("aria-describedby"); const el = d && document.getElementById(d); return !(el && el.textContent.trim()); }).map((a) => a.getAttribute("href"));
  out.newTabNote = (document.getElementById("new-tab-note") || {}).textContent || "";
  out.newTabLinks = document.querySelectorAll('a[target="_blank"]').length;
  // "§1What…": a section label glued to its heading reads as one word
  out.gluedHeadings = [...document.querySelectorAll("h2")].filter((h) => /§\d+[^\d\s]/.test(h.textContent.replace(/\s+/g, " ").trim())).map((h) => h.textContent.trim().slice(0, 30));
  out.skipLink = !!document.querySelector('a[href^="#"][class*="skip"], a.skip-link, a[href="#main"], a[href="#content"]');
  out.hasMain = !!document.querySelector("main");
  return out;
};
const LAYOUT = () => {
  const html = document.documentElement, sw = html.scrollWidth, iw = innerWidth, off = [];
  if (sw > iw) document.querySelectorAll("body *").forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.right > iw + 1 && r.width > 0 && getComputedStyle(el).position !== "fixed") {
      const p = el.parentElement, po = p && ["auto", "scroll"].includes(getComputedStyle(p).overflowX);
      if (!po) off.push(el.tagName + (el.id ? "#" + el.id : "") + (typeof el.className === "string" && el.className ? "." + el.className.split(" ")[0] : "") + " right=" + Math.round(r.right));
    }
  });
  const charts = [...document.querySelectorAll("svg.chart")].filter((s) => s.clientWidth > 0);
  return { sw, iw, offenders: off.slice(0, 6), theme: html.getAttribute("data-theme"), read: html.getAttribute("data-readability"), cb: html.getAttribute("data-colorblind"),
    series: html.getAttribute("data-series"), font: getComputedStyle(document.body).fontFamily.split(",")[0].replace(/"/g, "").trim(),
    charts: charts.length, k: charts.map((s) => parseFloat(s.style.getPropertyValue("--k"))) };
};
const DISK = () => ({
  hrefs: [...document.querySelectorAll("a[href]")].map((a) => a.getAttribute("href")).filter((h) => !/^[a-z][a-z0-9+.-]*:/i.test(h) && h[0] !== "#"),
  katex: document.querySelectorAll(".katex").length, errors: document.querySelectorAll(".katex-error").length,
  fontsLoaded: [...document.fonts].some((f) => /KaTeX_Main/.test(f.family) && f.status === "loaded"),
  refs: document.getElementById("reflections") ? !document.getElementById("reflections").hidden : null,
});

(async () => {
  const browser = await chromium.launch();

  // ---------- 1. trailing slash ----------
  c.section("1. trailing slash (every page)");
  {
    const ctx = await L.context(browser); const page = await ctx.newPage();
    for (const pg of PAGES) {
      const bare = pg.url.replace(/\/$/, "");
      await page.goto(base + bare); await page.waitForLoadState("load"); await page.waitForTimeout(250);
      c.ok(page.url() === base + pg.url, `${pg.name}: ${bare} → ${page.url()} (expected ${base + pg.url})`);
    }
    await ctx.close();
  }

  // ---------- 2. raw HTML ----------
  c.section("2. raw HTML: noindex, OG set, card, footer slot, scripts, html attributes (every page)");
  const OG = ["og:type", "og:site_name", "og:locale", "og:title", "og:description", "og:url", "og:image", "og:image:width", "og:image:height", "og:image:alt"];
  for (const pg of PAGES) {
    const { status, buf } = await get(base + pg.url); const html = buf.toString("utf8");
    c.ok(status === 200, `${pg.name}: served (${status})`);
    c.ok(html.includes('<meta name="robots" content="noindex">'), `${pg.name}: noindex meta`);
    const missing = OG.filter((t) => meta(html, t) === null).concat(meta(html, "twitter:card") === null ? ["twitter:card"] : []);
    c.ok(missing.length === 0, `${pg.name}: OG set complete (missing: ${missing.join(", ")})`);
    c.ok(meta(html, "og:url") === SITE + pg.url, `${pg.name}: og:url ${meta(html, "og:url")} === ${SITE + pg.url}`);
    c.ok(meta(html, "og:type") === "website" && meta(html, "twitter:card") === "summary_large_image" && meta(html, "og:image:width") === "1200" && meta(html, "og:image:height") === "630", `${pg.name}: og:type website, twitter summary_large_image, 1200×630 declared`);
    const img = meta(html, "og:image") || "";
    c.ok(img.startsWith(SITE + "/learning/assets/og/"), `${pg.name}: og:image is an absolute card URL under /learning/assets/og/ (${img})`);
    if (img.startsWith(SITE)) {
      const r = await get(base + img.slice(SITE.length));
      const sig = r.buf.length > 24 && r.buf.toString("hex", 0, 8) === "89504e470d0a1a0a";
      const w = sig ? r.buf.readUInt32BE(16) : 0, h = sig ? r.buf.readUInt32BE(20) : 0;
      c.ok(r.status === 200 && sig && w === 1200 && h === 630, `${pg.name}: card ${img.slice(SITE.length)} answers ${r.status}, PNG ${sig}, ${w}×${h}`);
    }
    const foot = /<(?:p|footer)[^>]*class="[^"]*\bfoot\b[^"]*"[\s\S]*?<\/p>/.exec(html);
    c.ok(foot && /<span class="fb-slot"/.test(foot[0]), `${pg.name}: .fb-slot span inside the footer`);
    c.ok(/<script[^>]+src="[^"]*assets\/feedback\.js"[^>]*>\s*<\/script>\s*<\/body>/.test(html), `${pg.name}: feedback.js is the last script before </body>`);
    const iCommon = html.search(/<script[^>]+assets\/strings-common\.js/), iFb = html.search(/<script[^>]+assets\/feedback\.js/), iI18n = html.search(/<script[^>]+assets\/learning-i18n\.js/);
    c.ok(iCommon >= 0 && iFb > iCommon, `${pg.name}: strings-common.js loads before feedback.js`);
    const htmlTag = (/<html\b[^>]*>/.exec(html) || [""])[0];
    if (pg.kind === "module") {
      c.ok(attrVal(htmlTag, "data-series") === "fits" && hasAttr(htmlTag, "data-es-ready"), `${pg.name}: <html data-series="fits" data-es-ready> (${htmlTag})`);
      c.ok(iI18n >= 0 && iI18n < iFb, `${pg.name}: learning-i18n.js loads before feedback.js`);
    } else if (pg.kind === "hub") {
      c.ok(attrVal(htmlTag, "data-series") === null, `${pg.name}: <html> carries no data-series (${htmlTag})`);
      c.ok(iI18n >= 0 && iI18n < iFb, `${pg.name}: learning-i18n.js loads before feedback.js`);
    } else {
      c.ok(attrVal(htmlTag, "data-series") === "reflections" && !hasAttr(htmlTag, "data-es-ready"), `${pg.name}: <html data-series="reflections">, no data-es-ready (${htmlTag})`);
      c.ok(iI18n < 0, `${pg.name}: Reflections page does not load learning-i18n.js`);
    }
  }

  // ---------- 3. registry text rendered ----------
  c.section("3. registry text rendered on the page");
  const hubPage = byKind.hub;
  for (const lang of L.LANGS) {
    const H = R.hub[lang];
    const ctx = await L.context(browser, { lang }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    await page.goto(base + hubPage.url); await settle(page, hubPage);
    c.ok(await page.evaluate(() => document.documentElement.lang) === lang, `hub [${lang}]: <html lang>`);
    c.ok(same(await page.title(), H.pageTitle), `hub [${lang}]: <title> "${await page.title()}" === pageTitle`);
    for (const [sel, key] of [["h1", "h1"], [".lead", "lead"], ["#reading-your-fits [data-i18n=seriesIntro]", "seriesIntro"], ["#reflections h2", "refTitle"], ["#reflections [data-i18n=refIntro]", "refIntro"], ["#reflections .ref-all a", "refAll"]]) {
      const got = await text(page, sel);
      c.ok(same(got, H[key]), `hub [${lang}]: ${sel} renders ${key} (got "${got}")`);
    }
    c.ok(await page.evaluate(() => !document.getElementById("reflections").hidden), `hub [${lang}]: Reflections block shown`);
    const titles = await texts(page, "#module-list .m-title");
    const want = R.modules.map((m) => L.norm(m.title[lang]));
    c.ok(JSON.stringify(titles) === JSON.stringify(want), `hub [${lang}]: module list shows every mod<Key>Title in registry order (got ${JSON.stringify(titles)})`);
    const descs = await texts(page, "#module-list .m-desc");
    c.ok(JSON.stringify(descs) === JSON.stringify(R.modules.map((m) => L.norm(m.desc[lang]))), `hub [${lang}]: module list shows every mod<Key>Desc`);
    const links = await page.$$eval("#module-list a.module-row", (as) => as.map((a) => a.getAttribute("href")));
    c.ok(JSON.stringify(links) === JSON.stringify(R.readyModules.map((m) => `fits/${m.slug}/`)), `hub [${lang}]: ready modules link to fits/<slug>/ (${links.join(", ")})`);
    const rows = await page.$$eval("#ref-list .ref-row", (as) => as.map((a) => ({ href: a.getAttribute("href"), book: a.querySelector(".ref-book").textContent, title: a.querySelector(".m-title").textContent, date: a.querySelector(".ref-date").textContent, desc: a.querySelector(".m-desc").textContent, langs: [a.querySelector(".ref-book").getAttribute("lang"), a.querySelector(".m-title").getAttribute("lang")] })));
    const newest = R.readyReflections.slice().sort(byDate).slice(0, 3);
    c.ok(rows.length === newest.length && newest.every((x, i) => rows[i].href === `reflections/${x.book}/${x.slug}/` && same(rows[i].title, x.title) && same(rows[i].book, x.bookTitle) && same(rows[i].date, L.fmtDate(x.date, lang)) && same(rows[i].desc, x.summary) && rows[i].langs.join() === "en,en"),
      `hub [${lang}]: Reflections rows = the ${newest.length} newest ready reflections (title, book, ${lang} date, summary, lang="en") (got ${JSON.stringify(rows)})`);
    c.ok(log.length === 0, `hub [${lang}]: console clean: ${log.join(" | ")}`);
    await ctx.close();
  }
  for (const pg of PAGES.filter((p) => p.kind === "module")) {
    for (const lang of L.LANGS) {
      const S = pg.module.strings && pg.module.strings[lang];
      if (!S || !S.pageTitle || !S.h1) { console.log(`  note ${pg.name} [${lang}]: no pageTitle/h1 in strings.js, skipped`); continue; }
      const ctx = await L.context(browser, { lang }); const page = await ctx.newPage();
      await page.goto(base + pg.url); await settle(page, pg);
      const title = await page.title(), h1 = await text(page, "h1");
      c.ok(same(title, S.pageTitle), `${pg.name} [${lang}]: <title> "${title}" === strings.${lang}.pageTitle`);
      c.ok(same(h1, S.h1), `${pg.name} [${lang}]: h1 "${h1}" === strings.${lang}.h1`);
      await ctx.close();
    }
  }
  {
    const pg = byKind.books;
    const ctx = await L.context(browser); const page = await ctx.newPage();
    await page.goto(base + pg.url); await settle(page, pg);
    const rows = await page.$$eval("#book-list > li", (lis) => lis.map((li) => ({ a: !!li.querySelector("a"), href: li.querySelector("a") && li.querySelector("a").getAttribute("href"), title: li.querySelector(".b-title").textContent, count: li.querySelector(".b-count").textContent, has: li.querySelector(".b-count").classList.contains("has"), meta: li.querySelector(".b-meta").textContent })));
    c.ok(rows.length === R.books.length && R.books.every((b, i) => rows[i] && same(rows[i].title, b.title)), `${pg.name}: lists every registry book title in order (${rows.length} rows)`);
    const notYet = [...new Set(rows.filter((r) => !r.has).map((r) => L.norm(r.count)))];
    for (let i = 0; i < R.books.length && i < rows.length; i++) {
      const b = R.books[i], n = (b.reflections || []).filter((r) => r.ready).length, row = rows[i];
      if (n) c.ok(row.a && row.href === `${b.slug}/` && row.has && new RegExp(`^${n}\\b`).test(L.norm(row.count)), `${pg.name}: "${b.title}" links to ${b.slug}/ with count ${n} (got ${row.href}, "${row.count}")`);
      else c.ok(!row.a && !row.has && notYet.length === 1, `${pg.name}: "${b.title}" has no link and the shared not-yet label (got a=${row.a}, "${row.count}")`);
      c.ok(same(row.meta, `${b.authors}, ${b.year}${b.edition ? " · " + b.edition : ""}`), `${pg.name}: "${b.title}" meta = authors, year, edition (got "${row.meta}")`);
    }
    await ctx.close();
  }
  for (const pg of PAGES.filter((p) => p.kind === "book")) {
    const ctx = await L.context(browser); const page = await ctx.newPage();
    await page.goto(base + pg.url); await settle(page, pg);
    const h1 = await text(page, "h1");
    c.ok(same(h1, pg.book.title), `${pg.name}: h1 "${h1}" === registry title`);
    const rows = await page.$$eval("#ref-list .ref-row", (as) => as.map((a) => ({ href: a.getAttribute("href"), title: a.querySelector(".m-title").textContent, date: a.querySelector(".ref-date").textContent, desc: a.querySelector(".m-desc").textContent })));
    const want = pg.book.ready.slice().sort(byDate);
    c.ok(rows.length === want.length, `${pg.name}: ${want.length} ready reflection row(s) (got ${rows.length})`);
    want.forEach((r, i) => { const row = rows[i] || {}; c.ok(row.href === `${r.slug}/` && same(row.title, r.title) && same(row.date, L.fmtDate(r.date, "en")) && same(row.desc, r.summary), `${pg.name}: row "${r.title}" shows title, ${L.fmtDate(r.date, "en")}, summary, link ${r.slug}/ (got ${JSON.stringify(row)})`); });
    c.ok(await page.evaluate(() => { const a = document.getElementById("book-about"); return a ? a.hidden : null; }) === !pg.book.about, `${pg.name}: #book-about hidden iff the registry's about is empty`);
    await ctx.close();
  }
  for (const pg of PAGES.filter((p) => p.kind === "reflection")) {
    const ctx = await L.context(browser); const page = await ctx.newPage();
    await page.goto(base + pg.url); await settle(page, pg);
    const h1 = await text(page, "h1"), title = await page.title();
    c.ok(same(h1, pg.reflection.title), `${pg.name}: h1 "${h1}" === registry title`);
    c.ok(title.startsWith(pg.reflection.title), `${pg.name}: <title> starts with the registry title ("${title}")`);
    await ctx.close();
  }

  // ---------- 4. a11y per page ----------
  c.section("4. a11y per page (desktop, EN)");
  for (const pg of PAGES) {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    await page.goto(base + pg.url); await settle(page, pg, 400);
    const a = await page.evaluate(A11Y);
    c.ok(a.unlabeled.length === 0, `${pg.name}: no unlabeled form control (${a.unlabeled.join(", ")})`);
    c.ok(a.headingSkips.length === 0, `${pg.name}: no heading level skips (${a.headingSkips.join("; ")})`);
    c.ok(a.h1Count === 1, `${pg.name}: exactly one h1 (${a.h1Count})`);
    c.ok(a.dupIds.length === 0, `${pg.name}: no duplicate ids (${a.dupIds.join(", ")})`);
    c.ok(a.posTabindex.length === 0, `${pg.name}: no positive tabindex (${a.posTabindex.join(", ")})`);
    c.ok(a.imgNoAlt.length === 0, `${pg.name}: every <img> has alt (${a.imgNoAlt.join(", ")})`);
    c.ok(a.chartsBad.length === 0, `${pg.name}: every svg.chart has role="img" and an aria-label (${a.chartsBad.join(", ")})`);
    c.ok(a.newTabNoNoopener.length === 0, `${pg.name}: every target=_blank link has rel noopener (${a.newTabNoNoopener.join(", ")})`);
    c.ok(log.length === 0, `${pg.name}: console clean on load: ${log.join(" | ")}`);
    // batch E (2026-10-17): these were report-only notes; they count now
    c.ok(a.svgLabelNoRole.length === 0, `${pg.name}: every labelled svg has role="img" (${a.svgLabelNoRole.join(", ")})`);
    if (a.readouts) c.ok(a.readoutsLive === a.readouts, `${pg.name}: every .readout is live or has a live mirror (${a.readoutsLive}/${a.readouts})`);
    if (a.langToggle && !a.langToggle.hidden) c.ok(a.langToggle.pressed === "false" && same(a.langToggle.label, R.common.en.langToggleAria), `${pg.name}: lang toggle aria-pressed="false" in EN with the registry label (${a.langToggle.pressed}, "${a.langToggle.label}")`);
    c.ok(a.thNoScope === 0, `${pg.name}: every <th> has a scope (${a.thNoScope} without)`);
    if (a.newTabLinks) c.ok(a.newTabNoHint.length === 0 && same(a.newTabNote, R.common.en.newTabNote), `${pg.name}: every target=_blank link is described by the "${R.common.en.newTabNote}" note (${a.newTabNoHint.join(", ")}; note "${a.newTabNote}")`);
    c.ok(a.gluedHeadings.length === 0, `${pg.name}: section labels are not glued to their headings (${a.gluedHeadings.join("; ")})`);
    console.log(`  note ${pg.name}: skip link: ${a.skipLink}, <main>: ${a.hasMain}`);
    await ctx.close();
  }

  // ---------- 4b. live readouts and the toggle state (batch E) ----------
  c.section("4b. live mirrors announce settled values; the toggle's pressed state follows the language");
  const READ = () => [...document.querySelectorAll(".readout")].map((ro) => {
    const walker = document.createTreeWalker(ro, NodeFilter.SHOW_TEXT), parts = []; let n;
    while ((n = walker.nextNode())) { const s = n.data.replace(/\s+/g, " ").trim(); if (s) parts.push(s); }
    const m = ro.nextElementSibling && ro.nextElementSibling.getAttribute("aria-live") ? ro.nextElementSibling : null;
    return { id: ro.id || "", text: parts.join(" "), mirror: m ? m.textContent : null, atomic: m ? m.getAttribute("aria-atomic") : null };
  });
  for (const pg of PAGES.filter((p) => p.kind === "module" || p.kind === "reflection")) {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    await page.goto(base + pg.url); await settle(page, pg, 400); await page.waitForTimeout(1300);
    const before = await page.evaluate(READ);
    c.ok(before.length > 0 && before.every((r) => r.mirror === "" && r.atomic === "true"), `${pg.name}: mirrors exist, are atomic and stay silent on load (${before.map((r) => r.id + ":" + JSON.stringify(r.mirror)).join(", ")})`);
    // move the first slider that has a readout in its figure / trial, then wait past the debounce
    const moved = await page.evaluate(() => {
      const ranges = [...document.querySelectorAll('input[type="range"]')];
      for (const el of ranges) {
        const box = el.closest(".trial, .fig, section, figure") || document;
        if (!box.querySelector(".readout")) continue;
        const v = +el.value === +el.max ? el.min : el.max;
        el.value = v; el.dispatchEvent(new Event("input", { bubbles: true })); el.dispatchEvent(new Event("change", { bubbles: true }));
        return el.id || el.name || "range";
      }
      return null;
    });
    await page.waitForTimeout(250);
    const mid = await page.evaluate(READ);
    await page.waitForTimeout(900);
    const after = await page.evaluate(READ);
    const changed = after.filter((r, i) => r.text !== before[i].text);
    c.ok(moved && changed.length > 0, `${pg.name}: moving ${moved} changed a readout`);
    c.ok(changed.every((r) => r.mirror === r.text), `${pg.name}: after the debounce every changed readout's mirror equals its text (${changed.map((r) => r.id + " mirror=" + JSON.stringify(r.mirror && r.mirror.slice(0, 30))).join("; ")})`);
    c.ok(mid.filter((r, i) => r.text !== before[i].text).every((r) => r.mirror === ""), `${pg.name}: 250 ms after the move the mirrors are still silent (debounced)`);
    if (pg.kind === "module") {
      await page.click(".lang-toggle"); await page.waitForTimeout(200);
      const t = await page.evaluate(() => { const b = document.querySelector(".lang-toggle"); return { pressed: b.getAttribute("aria-pressed"), label: b.getAttribute("aria-label"), lang: document.documentElement.lang }; });
      c.ok(t.lang === "es" && t.pressed === "true" && same(t.label, R.common.es.langToggleAria), `${pg.name}: after the toggle aria-pressed="true" and the ES label (${JSON.stringify(t)})`);
    }
    c.ok(log.length === 0, `${pg.name}: console clean: ${log.join(" | ")}`);
    await ctx.close();
  }

  // ---------- 5. feedback dialog focus (one page per kind) ----------
  c.section("5. feedback dialog: open, focus inside, Tab stays, Esc returns focus (one page per kind)");
  for (const pg of Object.values(byKind)) {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    await page.goto(base + pg.url); await settle(page, pg);
    c.ok(await page.locator(".foot .fb-slot button.fb-open").count() === 1, `${pg.name}: the footer slot holds the feedback button`);
    await page.click("button.fb-open"); await page.waitForTimeout(150);
    c.ok(await page.evaluate(() => document.querySelector("dialog.fb-panel").open && !!document.activeElement.closest("dialog.fb-panel")), `${pg.name}: dialog opens with focus inside`);
    // showModal makes the page inert: Tab cycles through the dialog's controls. Between the last and
    // the first, headless Chromium parks focus on the browser UI (activeElement === body) before
    // wrapping; what must never happen is focus landing on a page element outside the dialog.
    const seq = [];
    for (let i = 0; i < 25; i++) { await page.keyboard.press("Tab"); seq.push(await page.evaluate(() => { const a = document.activeElement; return a.closest("dialog.fb-panel") ? "in" : a === document.body ? "body" : a.tagName + "." + a.className; })); }
    c.ok(seq.every((s) => s === "in" || s === "body") && seq.filter((s) => s === "in").length >= 20 && seq.indexOf("in", seq.indexOf("body")) > 0, `${pg.name}: Tab never reaches a page element outside the dialog and wraps back in (${seq.join(" ")})`);
    await page.keyboard.press("Escape"); await page.waitForTimeout(150);
    c.ok(await page.evaluate(() => !document.querySelector("dialog.fb-panel").open && document.activeElement === document.querySelector("button.fb-open")), `${pg.name}: Esc closes and focus returns to the button`);
    c.ok(log.length === 0, `${pg.name}: console clean: ${log.join(" | ")}`);
    await ctx.close();
  }

  // ---------- 6. view settings (assets/view-settings.js) ----------
  c.section("6. view settings: the View button and popover, choices applied at once, the colorblind hint, ES re-render, prefers-contrast (every page)");
  const VIEW = () => {
    const bar = document.querySelector(".series-bar"), btn = bar && bar.querySelector("button.view-toggle"), pop = document.getElementById("view-pop");
    const lt = bar && bar.querySelector(".lang-toggle");
    const q = (s) => (pop ? pop.querySelector(s) : null), tx = (el) => (el ? el.textContent.replace(/\s+/g, " ").trim() : null);
    const hint = document.querySelector(".cb-hint"), legend = document.querySelector(".legend-key, .legend");
    return {
      btnCount: document.querySelectorAll("button.view-toggle").length, popCount: document.querySelectorAll(".view-pop").length,
      afterToggle: lt ? lt.nextElementSibling === btn : btn && btn.nextElementSibling === pop,
      btn: btn ? { text: tx(btn), label: btn.getAttribute("aria-label"), expanded: btn.getAttribute("aria-expanded"), haspopup: btn.getAttribute("aria-haspopup"), controls: btn.getAttribute("aria-controls"), type: btn.getAttribute("type") } : null,
      pop: pop ? { cls: pop.className, role: pop.getAttribute("role"), labelledby: pop.getAttribute("aria-labelledby"), hidden: pop.hidden, inBar: pop.parentElement === bar } : null,
      title: tx(q("#view-title")), themeLabel: tx(q(".view-label")),
      themes: [...(pop ? pop.querySelectorAll(".view-seg button[data-theme]") : [])].map((b) => ({ v: b.getAttribute("data-theme"), text: tx(b), pressed: b.getAttribute("aria-pressed") })),
      checks: [...(pop ? pop.querySelectorAll("label.view-check") : [])].map((l) => ({ type: l.querySelector("input") && l.querySelector("input").type, text: tx(l.querySelector("span")), checked: !!(l.querySelector("input") && l.querySelector("input").checked) })),
      note: tx(q("p.view-note")), close: tx(q("button.view-close")),
      focusIn: !!(pop && document.activeElement && pop.contains(document.activeElement)), focusBtn: document.activeElement === btn,
      theme: document.documentElement.getAttribute("data-theme"), cb: document.documentElement.getAttribute("data-colorblind"), read: document.documentElement.getAttribute("data-readability"),
      ls: { theme: localStorage.getItem("viewTheme"), cb: localStorage.getItem("viewColorblind"), read: localStorage.getItem("viewReadability") },
      legend: !!legend, hint: hint ? { afterLegend: legend && legend.nextElementSibling === hint, text: tx(hint.querySelector("span.cb-hint-text")), btn: tx(hint.querySelector("button.cb-hint-btn")), pressed: hint.querySelector("button.cb-hint-btn") && hint.querySelector("button.cb-hint-btn").getAttribute("aria-pressed") } : null,
    };
  };
  const expectTexts = (r, S, label, state) => {
    c.ok(r.btn && same(r.btn.text, S.viewBtn) && same(r.btn.label, S.viewTitle), `${label}: View button text viewBtn and aria-label viewTitle (${JSON.stringify(r.btn)})`);
    c.ok(same(r.title, S.viewTitle) && same(r.themeLabel, S.viewTheme) && same(r.note, S.viewNote) && same(r.close, S.viewClose), `${label}: popover title / theme label / note / close from the registry (${r.title} | ${r.themeLabel} | ${r.note} | ${r.close})`);
    c.ok(r.themes.length === 3 && r.themes.map((t) => t.v).join() === "system,light,dark" && same(r.themes[0].text, S.viewSystem) && same(r.themes[1].text, S.viewLight) && same(r.themes[2].text, S.viewDark), `${label}: three theme buttons system|light|dark with viewSystem/viewLight/viewDark (${JSON.stringify(r.themes)})`);
    c.ok(r.checks.length === 2 && r.checks.every((k) => k.type === "checkbox") && same(r.checks[0].text, S.viewColorblind) && same(r.checks[1].text, S.viewReadability), `${label}: two checkboxes labelled viewColorblind, viewReadability (${JSON.stringify(r.checks)})`);
    if (r.legend) {
      const on = state && state.cb;
      c.ok(r.hint && r.hint.afterLegend && same(r.hint.text, on ? S.cbHintOn + " ·" : S.cbHintOff) && same(r.hint.btn, on ? S.cbTurnOff : S.cbTurnOn) && r.hint.pressed === (on ? "true" : "false"), `${label}: .cb-hint after the first legend reads ${on ? "cbHintOn · / cbTurnOff" : "cbHintOff / cbTurnOn"} with aria-pressed ${on} (${JSON.stringify(r.hint)})`);
    } else c.ok(r.hint === null, `${label}: no legend, so no .cb-hint`);
  };
  for (const pg of PAGES) {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    await page.goto(base + pg.url); await settle(page, pg, 300);
    let r = await page.evaluate(VIEW);
    c.ok(r.btnCount === 1 && r.popCount === 1 && r.afterToggle, `${pg.name}: one button.view-toggle right after .lang-toggle (or last) and one .view-pop (${r.btnCount}, ${r.popCount}, ${r.afterToggle})`);
    c.ok(r.btn && r.btn.type === "button" && r.btn.expanded === "false" && r.btn.haspopup === "dialog" && r.btn.controls === "view-pop", `${pg.name}: button type, aria-expanded=false, aria-haspopup=dialog, aria-controls=view-pop (${JSON.stringify(r.btn)})`);
    c.ok(r.pop && r.pop.role === "dialog" && r.pop.labelledby === "view-title" && r.pop.hidden && r.pop.inBar, `${pg.name}: #view-pop role=dialog aria-labelledby=view-title, hidden, inside the bar (${JSON.stringify(r.pop)})`);
    c.ok(r.themes[0] && r.themes[0].pressed === "true" && r.themes.slice(1).every((t) => t.pressed === "false") && !r.checks.some((k) => k.checked), `${pg.name}: defaults: System pressed, nothing checked (${JSON.stringify(r.themes.map((t) => t.pressed))}, ${JSON.stringify(r.checks.map((k) => k.checked))})`);
    expectTexts(r, R.common.en, pg.name + " [en]", { cb: false });
    // open → focus inside; Esc → closed, focus on the button
    await page.click("button.view-toggle"); await page.waitForTimeout(100);
    r = await page.evaluate(VIEW);
    c.ok(r.pop && !r.pop.hidden && r.btn.expanded === "true" && r.focusIn, `${pg.name}: click opens (hidden ${r.pop && r.pop.hidden}, aria-expanded ${r.btn && r.btn.expanded}, focus inside ${r.focusIn})`);
    await page.keyboard.press("Escape"); await page.waitForTimeout(100);
    r = await page.evaluate(VIEW);
    c.ok(r.pop && r.pop.hidden && r.btn.expanded === "false" && r.focusBtn, `${pg.name}: Esc closes and returns focus to the button (hidden ${r.pop && r.pop.hidden}, expanded ${r.btn && r.btn.expanded}, focus ${r.focusBtn})`);
    // open → click outside (on the h1) → closed
    await page.click("button.view-toggle"); await page.waitForTimeout(100);
    await page.click("h1", { position: { x: 2, y: 2 } }); await page.waitForTimeout(100);
    r = await page.evaluate(VIEW);
    c.ok(r.pop && r.pop.hidden && r.btn.expanded === "false", `${pg.name}: a click outside closes (hidden ${r.pop && r.pop.hidden}, expanded ${r.btn && r.btn.expanded})`);
    // Dark, then System
    await page.click("button.view-toggle"); await page.waitForTimeout(100);
    await page.click('#view-pop .view-seg button[data-theme="dark"]'); await page.waitForTimeout(100);
    r = await page.evaluate(VIEW);
    c.ok(r.theme === "dark" && r.ls.theme === "dark" && r.themes.map((t) => t.pressed).join() === "false,false,true", `${pg.name}: Dark → data-theme="dark", viewTheme="dark", Dark pressed (${r.theme}, ${r.ls.theme}, ${r.themes.map((t) => t.pressed)})`);
    await page.click('#view-pop .view-seg button[data-theme="system"]'); await page.waitForTimeout(100);
    r = await page.evaluate(VIEW);
    c.ok(r.theme === null && r.ls.theme === null && r.themes.map((t) => t.pressed).join() === "true,false,false", `${pg.name}: System → no data-theme, viewTheme removed, System pressed (${r.theme}, ${r.ls.theme}, ${r.themes.map((t) => t.pressed)})`);
    // colorblind checkbox: on = "1", off = "0" (explicitly off)
    await page.click("#view-pop label.view-check:nth-of-type(1) input"); await page.waitForTimeout(100);
    r = await page.evaluate(VIEW);
    c.ok(r.cb === "1" && r.ls.cb === "1" && r.checks[0].checked, `${pg.name}: colorblind on → data-colorblind="1", viewColorblind="1" (${r.cb}, ${r.ls.cb})`);
    if (r.legend) expectTexts(r, R.common.en, pg.name + " [en, cb on]", { cb: true });
    await page.click("#view-pop label.view-check:nth-of-type(1) input"); await page.waitForTimeout(100);
    r = await page.evaluate(VIEW);
    c.ok(r.cb === null && r.ls.cb === "0" && !r.checks[0].checked, `${pg.name}: colorblind off → no data-colorblind, viewColorblind="0" (${r.cb}, ${r.ls.cb})`);
    // readability: on = "1", off = removed
    await page.click("#view-pop label.view-check:nth-of-type(2) input"); await page.waitForTimeout(100);
    r = await page.evaluate(VIEW);
    c.ok(r.read === "1" && r.ls.read === "1" && r.checks[1].checked, `${pg.name}: readability on → data-readability="1", viewReadability="1" (${r.read}, ${r.ls.read})`);
    await page.click("#view-pop label.view-check:nth-of-type(2) input"); await page.waitForTimeout(100);
    r = await page.evaluate(VIEW);
    c.ok(r.read === null && r.ls.read === null && !r.checks[1].checked, `${pg.name}: readability off → no data-readability, viewReadability removed (${r.read}, ${r.ls.read})`);
    await page.click("#view-pop button.view-close"); await page.waitForTimeout(100);
    r = await page.evaluate(VIEW);
    c.ok(r.pop.hidden && r.focusBtn, `${pg.name}: Close button closes and returns focus (hidden ${r.pop.hidden}, focus ${r.focusBtn})`);
    // the hint button toggles the mode in place
    if (r.legend) {
      await page.click("button.cb-hint-btn"); await page.waitForTimeout(100);
      r = await page.evaluate(VIEW);
      c.ok(r.cb === "1" && r.ls.cb === "1" && r.checks[0].checked && r.hint.pressed === "true" && same(r.hint.btn, R.common.en.cbTurnOff), `${pg.name}: hint button turns colorblind on in place and the checkbox follows (${r.cb}, ${r.ls.cb}, checked ${r.checks[0].checked}, "${r.hint.btn}")`);
      await page.click("button.cb-hint-btn"); await page.waitForTimeout(100);
      r = await page.evaluate(VIEW);
      c.ok(r.cb === null && r.ls.cb === "0" && !r.checks[0].checked && r.hint.pressed === "false" && same(r.hint.btn, R.common.en.cbTurnOn), `${pg.name}: hint button turns it off again (${r.cb}, ${r.ls.cb}, "${r.hint.btn}")`);
    }
    // bilingual pages: everything re-renders in Spanish after the toggle
    if (pg.kind === "hub" || pg.kind === "module") {
      await page.click(".lang-toggle"); await page.waitForTimeout(250);
      r = await page.evaluate(VIEW);
      expectTexts(r, R.common.es, pg.name + " [es]", { cb: false });
      c.ok(same(await text(page, "a.skip-link"), R.common.es.skipLink), `${pg.name} [es]: skip link reads skipLink`);
    }
    c.ok(log.length === 0, `${pg.name}: console clean: ${log.join(" | ")}`);
    await ctx.close();
  }
  // 6b. View button = EN/ES toggle box (bilingual pages), one row at 375 px, nothing overflows
  c.section("6b. View button matches the EN/ES toggle; the bar stays one row at 375 px (every page, 1280 and 375)");
  const BAR = () => {
    const bar = document.querySelector(".series-bar"), vt = bar.querySelector("button.view-toggle"), lt = bar.querySelector(".lang-toggle");
    const box = (el) => { const b = el.getBoundingClientRect(); const s = getComputedStyle(el); return { top: b.top, h: b.height, w: b.width, ff: s.fontFamily, fs: s.fontSize, border: [s.borderTopWidth, s.borderTopStyle, s.borderTopColor, s.borderRadius].join(" ") }; };
    const bb = bar.getBoundingClientRect();
    const hubBar = document.querySelector(".hub-bar");
    return { vt: vt ? box(vt) : null, lt: lt && !lt.hidden ? box(lt) : null, bar: { top: bb.top, h: bb.height, bottom: bb.bottom },
      hubBarH: hubBar ? hubBar.getBoundingClientRect().height : null, varH: hubBar ? parseFloat(getComputedStyle(document.body).getPropertyValue("--hub-bar-h")) : null,
      sw: document.documentElement.scrollWidth, iw: innerWidth };
  };
  for (const width of [1280, 375]) {
    const ctx = await L.context(browser, { width, height: width === 375 ? 740 : 900, lang: "en", ctx: width === 375 ? { hasTouch: true, isMobile: true, deviceScaleFactor: 2 } : {} });
    const page = await ctx.newPage();
    for (const pg of PAGES) {
      await page.goto(base + pg.url); await settle(page, pg, 300);
      const r = await page.evaluate(BAR), label = `${pg.name} ${width}px`;
      c.ok(r.vt && r.vt.top >= r.bar.top - 0.5 && r.vt.top + r.vt.h <= r.bar.bottom + 0.5, `${label}: the View button sits inside the bar (button ${r.vt && Math.round(r.vt.top)}–${r.vt && Math.round(r.vt.top + r.vt.h)}, bar ${Math.round(r.bar.top)}–${Math.round(r.bar.bottom)})`);
      c.ok(r.sw <= r.iw, `${label}: nothing overflows (scrollWidth ${r.sw} ≤ ${r.iw})`);
      if (pg.kind === "hub" || pg.kind === "module") {
        c.ok(r.lt, `${label}: the EN/ES toggle is shown`);
        if (r.lt) {
          c.ok(Math.abs(r.lt.h - r.vt.h) <= 1, `${label}: View and toggle heights equal within 1 px (${r.vt.h.toFixed(2)} vs ${r.lt.h.toFixed(2)})`);
          c.ok(r.lt.ff === r.vt.ff && r.lt.fs === r.vt.fs, `${label}: same font-family and size (${r.vt.ff} ${r.vt.fs} vs ${r.lt.ff} ${r.lt.fs})`);
          c.ok(r.lt.border === r.vt.border, `${label}: same border (${r.vt.border} vs ${r.lt.border})`);
          c.ok(Math.abs(r.lt.top - r.vt.top) <= 1, `${label}: both buttons share the same top (${r.vt.top.toFixed(1)} vs ${r.lt.top.toFixed(1)}): no wrap below the crumbs`);
        }
      }
      if (pg.kind === "hub") c.ok(Math.abs(r.hubBarH - r.varH) <= 1, `${label}: hub bar rendered ${r.hubBarH} = --hub-bar-h ${r.varH} (±1)`);
    }
    await ctx.close();
  }
  // 6c. prefers-contrast: more turns the colorblind cues on while viewColorblind is absent, not when it is "0"
  c.section("6c. prefers-contrast: more → data-colorblind unless viewColorblind is \"0\" (head snippet alone, then with the script; one page per kind)");
  for (const pg of Object.values(byKind)) {
    for (const stored of [null, "0", "1"]) {
      for (const scriptOn of [false, true]) {
        const ctx = await L.context(browser, { lang: "en", ctx: { contrast: "more" } });
        if (stored !== null) await ctx.addInitScript((v) => { try { localStorage.setItem("viewColorblind", v); } catch (e) {} }, stored);
        if (!scriptOn) await ctx.route(/view-settings\.js/, (route) => route.fulfill({ status: 200, contentType: "text/javascript", body: "/* blocked by pages.js 6c: head snippet alone */" }));
        const page = await ctx.newPage();
        await page.goto(base + pg.url); await settle(page, pg, 200);
        const r = await page.evaluate(() => ({ contrast: matchMedia("(prefers-contrast: more)").matches, cb: document.documentElement.getAttribute("data-colorblind"), hasView: !!document.querySelector("button.view-toggle"), checked: (() => { const i = document.querySelector("#view-pop label.view-check input"); return i ? i.checked : null; })() }));
        const want = stored === "0" ? null : "1";
        c.ok(r.contrast, `${pg.name} contrast:more${stored === null ? "" : ` viewColorblind=${stored}`} ${scriptOn ? "with script" : "head snippet only"}: the media query is emulated`);
        c.ok(r.cb === want && r.hasView === scriptOn, `${pg.name} contrast:more${stored === null ? "" : ` viewColorblind=${stored}`} ${scriptOn ? "with script" : "head snippet only"}: data-colorblind ${r.cb} (expected ${want}); view button ${r.hasView}`);
        if (scriptOn) c.ok(r.checked === (want === "1"), `${pg.name} contrast:more${stored === null ? "" : ` viewColorblind=${stored}`}: the checkbox reflects it (${r.checked})`);
        await ctx.close();
      }
    }
  }

  // ---------- 7. skip link ----------
  c.section("7. skip link: first in <body>, registry text, hidden until focused, the first Tab stop, #main holds the h1 (every page)");
  const SKIP = () => {
    const a = document.body.firstElementChild, main = document.getElementById("main");
    const rect = a ? a.getBoundingClientRect() : null;
    return { tag: a && a.tagName, cls: a && a.className, href: a && a.getAttribute("href"), i18n: a && a.getAttribute("data-i18n"), text: a && a.textContent.trim(),
      aboveViewport: rect ? rect.bottom <= 0 : null, mainTag: main && main.tagName, mainHasH1: !!(main && main.querySelector("h1")), h1Count: document.querySelectorAll("h1").length, mainCount: document.querySelectorAll("main").length };
  };
  for (const pg of PAGES) {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage();
    await page.goto(base + pg.url); await settle(page, pg, 200);
    const r = await page.evaluate(SKIP);
    c.ok(r.tag === "A" && /\bskip-link\b/.test(r.cls) && r.href === "#main", `${pg.name}: <body>'s first element is <a class="skip-link" href="#main"> (${r.tag}.${r.cls} ${r.href})`);
    c.ok(same(r.text, R.common.en.skipLink), `${pg.name}: skip link reads skipLink ("${r.text}")`);
    if (pg.kind === "hub" || pg.kind === "module") c.ok(r.i18n === "skipLink", `${pg.name}: data-i18n="skipLink" on the bilingual page (${r.i18n})`);
    c.ok(r.aboveViewport, `${pg.name}: visually hidden before focus (bounding box above the viewport: ${r.aboveViewport})`);
    c.ok(r.mainTag === "MAIN" && r.mainCount === 1 && r.mainHasH1 && r.h1Count === 1, `${pg.name}: one <main id="main"> and it contains the page's h1 (${r.mainTag}, mains ${r.mainCount}, h1 inside ${r.mainHasH1})`);
    await page.keyboard.press("Tab"); await page.waitForTimeout(80);
    const f = await page.evaluate(() => { const a = document.activeElement, b = a.getBoundingClientRect(); return { isSkip: a === document.body.firstElementChild && a.classList.contains("skip-link"), top: b.top, bottom: b.bottom, visible: b.top >= 0 && b.bottom <= innerHeight && b.width > 0 && b.height > 0 }; });
    c.ok(f.isSkip && f.visible, `${pg.name}: the first Tab lands on the skip link and it is inside the viewport (skip ${f.isSkip}, top ${Math.round(f.top)}, bottom ${Math.round(f.bottom)})`);
    await page.keyboard.press("Enter"); await page.waitForTimeout(80);
    c.ok(await page.evaluate(() => location.hash === "#main"), `${pg.name}: Enter on the skip link goes to #main`);
    await ctx.close();
  }

  // ---------- 8. forced colors ----------
  c.section("8. forced colors (Windows High Contrast): charts keep their own colors (every module page, every ready reflection)");
  const FORCED = (kind) => {
    const T = "rgba(0, 0, 0, 0)";
    const svgs = [...document.querySelectorAll(kind === "module" ? "svg.chart" : ".essay .fig svg")].filter((s) => s.getClientRects().length);
    const bad = svgs.filter((s) => { const cs = getComputedStyle(s); return cs.forcedColorAdjust !== "none" || cs.backgroundColor === T || cs.backgroundColor === "transparent"; }).map((s) => "svg#" + s.id + " " + getComputedStyle(s).forcedColorAdjust + " " + getComputedStyle(s).backgroundColor);
    let a = null, b = null, pair = null;
    if (kind === "module") {
      const truth = document.querySelector(".chart .truth, .chart .truth-curve"), fit = document.querySelector(".chart .fit, .chart .fit-curve");
      if (truth && fit) { a = getComputedStyle(truth).stroke; b = getComputedStyle(fit).stroke; pair = ".truth vs .fit"; }
    } else {
      const paths = [...document.querySelectorAll(".essay .fig svg path[style*='var(--s']")];
      const tok = (p) => (/var\(--(s\d)\)/.exec(p.getAttribute("style")) || [])[1];
      const first = paths[0], second = first && paths.find((p) => tok(p) && tok(p) !== tok(first));
      if (first && second) { a = getComputedStyle(first).stroke; b = getComputedStyle(second).stroke; pair = `--${tok(first)} vs --${tok(second)}`; }
    }
    const swatches = kind === "module" ? [...document.querySelectorAll(".legend-key .sw")].filter((s) => getComputedStyle(s).forcedColorAdjust !== "none").length : 0;
    return { forced: matchMedia("(forced-colors: active)").matches, n: svgs.length, bad, a, b, pair, swatches };
  };
  for (const pg of PAGES.filter((p) => p.kind === "module" || p.kind === "reflection")) {
    const ctx = await L.context(browser, { lang: "en", ctx: { forcedColors: "active" } }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    await page.goto(base + pg.url); await settle(page, pg, pg.kind === "reflection" ? 600 : 300);
    const r = await page.evaluate(FORCED, pg.kind);
    c.ok(r.forced && r.n > 0, `${pg.name} forced-colors: emulated (${r.forced}), ${r.n} chart svg(s)`);
    c.ok(r.bad.length === 0, `${pg.name} forced-colors: every chart has forced-color-adjust none and a painted background (${r.bad.join("; ")})`);
    c.ok(r.pair && r.a !== r.b && r.a !== "rgba(0, 0, 0, 0)" && r.b !== "rgba(0, 0, 0, 0)" && r.a !== "none" && r.b !== "none", `${pg.name} forced-colors: ${r.pair} keep different strokes (${r.a} / ${r.b})`);
    if (pg.kind === "module") c.ok(r.swatches === 0, `${pg.name} forced-colors: legend swatches keep their colors (${r.swatches} forced)`);
    c.ok(log.length === 0, `${pg.name} forced-colors: console clean: ${log.join(" | ")}`);
    await ctx.close();
  }

  // ---------- 9. highlighted points and bars ----------
  c.section("9. highlighted points / flagged bars: ink outline 1 px × --k (bars 1 px), 2 × / 1.75 × under data-colorblind (module pages that have them)");
  const HI = () => {
    const probe = document.createElement("i"); probe.style.cssText = "position:absolute;visibility:hidden;color:var(--ink)"; document.body.appendChild(probe);
    const ink = getComputedStyle(probe).color; probe.remove();
    const items = [];
    for (const svg of document.querySelectorAll("svg.chart")) {
      if (!svg.getClientRects().length) continue;
      const k = parseFloat(svg.style.getPropertyValue("--k")) || NaN;
      svg.querySelectorAll("circle.pt-hi, rect.bar-hi").forEach((el) => { const cs = getComputedStyle(el); items.push({ svg: svg.id, kind: el.classList.contains("pt-hi") ? "pt" : "bar", k, stroke: cs.stroke, sw: parseFloat(cs.strokeWidth) }); });
    }
    return { ink, items, cb: document.documentElement.getAttribute("data-colorblind") };
  };
  let hiPages = 0;
  for (const pg of PAGES.filter((p) => p.kind === "module")) {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage();
    await page.goto(base + pg.url); await settle(page, pg, 300);
    await page.evaluate(() => document.querySelectorAll("details").forEach((d) => { d.open = true; })); await page.waitForTimeout(150);
    const plain = await page.evaluate(HI);
    const pts = plain.items.filter((i) => i.kind === "pt").length, bars = plain.items.filter((i) => i.kind === "bar").length;
    if (!plain.items.length) { console.log(`  note ${pg.name}: no circle.pt-hi / rect.bar-hi on load, skipped`); await ctx.close(); continue; }
    hiPages++;
    console.log(`  note ${pg.name}: ${pts} .pt-hi, ${bars} .bar-hi`);
    const check = (res, label, ptW, barW) => {
      c.ok(res.items.every((i) => i.k > 0), `${label}: --k set on every chart with highlights`);
      c.ok(res.items.every((i) => i.stroke === res.ink), `${label}: every highlight stroke = --ink ${res.ink} (${[...new Set(res.items.map((i) => i.stroke))].join(", ")})`);
      const off = res.items.filter((i) => Math.abs(i.sw - (i.kind === "pt" ? ptW : barW) * i.k) > 0.2);
      c.ok(off.length === 0, `${label}: stroke-width ≈ ${ptW} × k (points) / ${barW} × k (bars) within 0.2 (off: ${off.slice(0, 4).map((i) => `${i.svg} ${i.kind} ${i.sw.toFixed(2)} vs ${((i.kind === "pt" ? ptW : barW) * i.k).toFixed(2)}`).join("; ")})`);
    };
    check(plain, `${pg.name} plain`, 1, 1);
    await page.evaluate(() => window.LEARN_VIEW.setColorblind(true)); await page.waitForTimeout(150);
    const cbr = await page.evaluate(HI);
    c.ok(cbr.cb === "1" && cbr.items.length === plain.items.length, `${pg.name} colorblind: mode on, same ${plain.items.length} highlights (${cbr.cb}, ${cbr.items.length})`);
    check(cbr, `${pg.name} colorblind`, 2, 1.75);
    await ctx.close();
  }
  c.ok(hiPages > 0, `at least one module page has highlighted points or bars on load (${hiPages})`);

  // ---------- 10. decks and play pages ----------
  c.section("10. decks (slides.html, slides.es.html) and play pages: noindex, og:url, charset first (every ready module)");
  async function getStable(url) {   // a play page may be mid-export: wait for a complete file
    let r;
    for (let i = 0; i < 8; i++) {
      r = await get(url);
      if (r.status === 200 && /<\/html>\s*$/i.test(r.buf.toString("utf8").slice(-200))) return r;
      await new Promise((res) => setTimeout(res, 5000));
    }
    return r;
  }
  const countAll = (html, re) => (html.match(re) || []).length;
  const series = R.common.en.seriesName;
  for (const m of R.readyModules) {
    for (const deck of ["slides.html", "slides.es.html"]) {
      const url = `/learning/fits/${m.slug}/${deck}`;
      const { status, buf } = await get(base + url); const html = buf.toString("utf8"), head = buf.subarray(0, 2048).toString("utf8");
      c.ok(status === 200, `${m.slug}/${deck}: served (${status})`);
      c.ok(head.includes('<meta name="robots" content="noindex">'), `${m.slug}/${deck}: noindex within the first 2048 bytes`);
      c.ok(meta(head, "og:url") === SITE + url, `${m.slug}/${deck}: og:url ${meta(head, "og:url")} === ${SITE + url} within the first 2048 bytes`);
      const charsets = countAll(html, /<meta\s+charset=["']?utf-8["']?\s*\/?>/gi), firstMeta = html.search(/<meta\b/i), firstCharset = html.search(/<meta\s+charset=/i);
      c.ok(charsets === 1 && firstCharset >= 0 && firstCharset === firstMeta, `${m.slug}/${deck}: exactly one <meta charset="utf-8"> (${charsets}) and it is the first <meta> (at ${firstCharset}, first meta at ${firstMeta})`);
    }
    const url = `/learning/fits/${m.slug}/play/`;
    const { status, buf } = await getStable(base + url); const html = buf.toString("utf8");
    c.ok(status === 200, `${m.slug}/play/: served (${status})`);
    const one = (re) => countAll(html, re) === 1;
    c.ok(one(/<meta\s+name="robots"\s+content="noindex">/g), `${m.slug}/play/: exactly one noindex (${countAll(html, /<meta\s+name="robots"/g)})`);
    c.ok(one(/<meta\s+property="og:url"/g) && meta(html, "og:url") === SITE + url, `${m.slug}/play/: one og:url = ${SITE + url} (${meta(html, "og:url")})`);
    c.ok(one(/<meta\s+property="og:image"/g) && meta(html, "og:image") === `${SITE}/learning/assets/og/${m.slug}.png`, `${m.slug}/play/: one og:image = /learning/assets/og/${m.slug}.png (${meta(html, "og:image")})`);
    c.ok(one(/<meta\s+property="og:title"/g) && (meta(html, "og:title") || "").endsWith("· " + series), `${m.slug}/play/: one og:title ending in "· ${series}" ("${meta(html, "og:title")}")`);
    c.ok(one(/<meta\s+name="twitter:card"/g) && meta(html, "twitter:card") === "summary_large_image", `${m.slug}/play/: one twitter:card summary_large_image (${meta(html, "twitter:card")})`);
  }

  // ---------- 11. 375 px matrix + 768/1280 ----------
  c.section("11. 375 px matrix (theme × readability × colorblind) and 768 / 1280 light/dark (every page)");
  const variants = [];
  for (const theme of L.THEMES) for (const read of L.READS) for (const cb of L.CBS) variants.push({ width: 375, height: 740, theme, dark: theme === "dark", read, cb, mobile: true, tag: `375px ${theme}${read ? " +read" : ""}${cb ? " +cb" : ""}` });
  for (const width of L.DESKTOP_WIDTHS) for (const dark of L.DARKS) variants.push({ width, height: 900, theme: "", dark, read: false, cb: false, mobile: false, tag: `${width}px ${dark ? "dark" : "light"} (OS scheme)` });
  for (const v of variants) {
    const ctx = await L.context(browser, { width: v.width, height: v.height, dark: v.dark, theme: v.theme, read: v.read, cb: v.cb, lang: "en", ctx: v.mobile ? { hasTouch: true, isMobile: true, deviceScaleFactor: 2 } : {} });
    const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    for (const pg of PAGES) {
      log.length = 0;
      await page.goto(base + pg.url); await settle(page, pg, pg.kind === "reflection" ? 500 : 250);
      await page.evaluate(() => document.querySelectorAll("details").forEach((d) => { d.open = true; })); await page.waitForTimeout(150);
      const r = await page.evaluate(LAYOUT);
      const label = `${pg.name} ${v.tag}`;
      c.ok(r.sw <= r.iw, `${label}: no sideways scroll (${r.sw} > ${r.iw}; ${r.offenders.join(", ")})`);
      c.ok(log.length === 0, `${label}: console clean: ${log.join(" | ")}`);
      if (v.width === 375) c.ok(r.theme === v.theme && r.read === (v.read ? "1" : null) && r.cb === (v.cb ? "1" : null), `${label}: <html> data-theme/data-readability/data-colorblind applied (${r.theme}, ${r.read}, ${r.cb})`);
      if (pg.kind === "module") c.ok(r.series === "fits" && r.charts > 0 && r.k.length === r.charts && r.k.every((k) => k > 0.5 && k < 2.5) && /Source Serif/.test(r.font), `${label}: data-series fits, --k set on all ${r.charts} visible charts (${r.k.map((k) => k.toFixed(2)).join(", ")}), body font ${r.font}`);
      else if (pg.kind === "hub") c.ok(r.series === null, `${label}: hub has no data-series (${r.series})`);
      else c.ok(r.series === "reflections" && /IBM Plex Serif/.test(r.font), `${label}: data-series reflections, body font ${r.font}`);
    }
    await ctx.close();
  }

  // ---------- 12. from disk ----------
  c.section("12. from disk (file://): hub, one module, all-books, every reflection");
  const diskPages = [byKind.hub, byKind.module, byKind.books, ...PAGES.filter((p) => p.kind === "reflection")].filter(Boolean);
  for (const pg of diskPages) {
    const file = path.join(L.repo, pg.file);
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    await page.goto(pathToFileURL(file).href); await page.waitForLoadState("load"); await page.waitForTimeout(pg.kind === "reflection" ? 900 : 500);
    const r = await page.evaluate(DISK);
    const folder = r.hrefs.filter((h) => /\/$/.test(h) || h === "." || h === "..");
    c.ok(folder.length === 0, `${pg.name} file: folder links rewritten to index.html (left: ${folder.join(", ")})`);
    const missing = r.hrefs.filter((h) => !fs.existsSync(path.resolve(path.dirname(file), decodeURIComponent(h.split(/[?#]/)[0]) || ".")));
    c.ok(missing.length === 0, `${pg.name} file: every relative link target exists on disk (missing: ${missing.join(", ")})`);
    if (pg.kind === "hub") c.ok(r.refs === true, `${pg.name} file: Reflections block shown from disk`);
    if (r.katex > 0) c.ok(r.errors === 0 && r.fontsLoaded, `${pg.name} file: KaTeX renders locally (${r.katex} expressions, ${r.errors} errors, KaTeX_Main loaded ${r.fontsLoaded})`);
    else if (pg.kind === "reflection") console.log(`  note ${pg.name} file: no .katex on this page`);
    c.ok(log.length === 0, `${pg.name} file: console clean: ${log.join(" | ")}`);
    await ctx.close();
  }

  await browser.close(); close();
  process.exit(c.summary(`wall time ${Math.round((Date.now() - t0) / 1000)} s`));
})().catch((e) => { console.error(e); close(); process.exit(1); });
