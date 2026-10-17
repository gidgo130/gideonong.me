// pages.js — "every page" plumbing for /learning, driven by the registries (lib.pages()):
//   1. trailing slash: a folder URL without the slash lands on the slashed URL
//   2. raw HTML: noindex, the full OG set + twitter:card, og:url, the 1200×630 card PNG, the
//      footer's .fb-slot, feedback.js last, strings-common.js before it (Reflections), html attrs
//   3. registry text rendered: hub EN/ES, module <title>/h1, module list, books, book pages, reflections
//   4. a11y per page (desktop) + report-only notes
//   5. the feedback dialog's focus handling (one page per kind)
//   6. 375 px matrix (theme × readability × colorblind) + 768/1280 light/dark: overflow, console,
//      <html> attributes, data-series, --k on every visible svg.chart, base font
//   7. from disk (file://): folder links rewritten, every relative link target exists, console, KaTeX
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
  out.readoutsLive = [...document.querySelectorAll(".readout")].filter((r) => r.closest("[aria-live]") || r.getAttribute("aria-live")).length;
  const lt = document.querySelector(".lang-toggle");
  out.langToggle = lt ? { hidden: lt.hidden, pressed: lt.getAttribute("aria-pressed") } : null;
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
  for (const lang of ["en", "es"]) {
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
    for (const lang of ["en", "es"]) {
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
    const notes = [];
    if (a.svgLabelNoRole.length) notes.push(`${a.svgLabelNoRole.length} svg with aria-label but no role (${a.svgLabelNoRole.join(", ")})`);
    if (a.readouts) notes.push(`.readout with aria-live: ${a.readoutsLive}/${a.readouts}`);
    if (a.langToggle && !a.langToggle.hidden && a.langToggle.pressed === null) notes.push("lang toggle has no aria-pressed");
    notes.push(`skip link: ${a.skipLink}, <main>: ${a.hasMain}`);
    console.log(`  note ${pg.name}: ${notes.join("; ")}`);
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

  // ---------- 6. 375 px matrix + 768/1280 ----------
  c.section("6. 375 px matrix (theme × readability × colorblind) and 768 / 1280 light/dark (every page)");
  const variants = [];
  for (const theme of ["light", "dark"]) for (const read of [false, true]) for (const cb of [false, true]) variants.push({ width: 375, height: 740, theme, dark: theme === "dark", read, cb, mobile: true, tag: `375px ${theme}${read ? " +read" : ""}${cb ? " +cb" : ""}` });
  for (const width of [768, 1280]) for (const dark of [false, true]) variants.push({ width, height: 900, theme: "", dark, read: false, cb: false, mobile: false, tag: `${width}px ${dark ? "dark" : "light"} (OS scheme)` });
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

  // ---------- 7. from disk ----------
  c.section("7. from disk (file://): hub, one module, all-books, every reflection");
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
