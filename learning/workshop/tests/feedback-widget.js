// feedback-widget.js — the /learning feedback widget (assets/feedback.js) end to end, with a mocked
// /api/feedback route:
//   A. footer trigger → panel → payload (field set, same-origin credentials) → success
//   B. selecting text → "Comment on this" → quote + nearest section id in the payload
//   C. failure keeps the text and shows the email; Esc / ✕ close and return focus; a non-JSON 401
//   D. dry-run on localhost (nothing posted, payload logged, the dry-run note)
//   E. file: and the offline copy (LEARN_OFFLINE): the email line only, no widget
//   F. owner mode: #owner-setup, the stored key, the X-Feedback-Owner header, the labels note, forget
//   G. Spanish strings on a bilingual page, the toggle, and a Reflections page staying English
//   H. layout matrix on EVERY page: 375/768/1280 × light/dark × readability, panel fits, no overflow
//   I. contrast on EVERY page: trigger, panel text, privacy line, chips, failure line ≥ 4.5:1
//   J. touch screens: no selection button
//   K. the hub's dark footer: trigger, ES swap, .hub-frame on the panel
// Flows A–G, J, K run on one page of each kind (hub, first ready module, all-books, first book page,
// first ready reflection); H and I run on every page lib.pages() lists. Every expected string comes
// from lib.registries().common (fb*, footMistake); nothing here is copied from the pages.
// Ported 2026-10-16 from the scratchpad suite pw-feedback.mjs (ESM → CommonJS).
"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
const L = require("./lib");
const { chromium } = L.pw();
const { base, close } = L.serve();
const c = new L.Checker("feedback-widget");
const R = L.registries();
const EN = R.common.en, ES = R.common.es;
const PAGES = L.pages();
const first = (kind) => PAGES.find((p) => p.kind === kind);
const P = { hub: first("hub"), module: first("module"), books: first("books"), book: first("book"), essay: first("reflection") };
const EMAIL = (EN.footMistake.match(/\S+@\S+/) || [""])[0];   // the address in the footer's fallback line
const SERIES = { hub: "hub", module: "fits", books: "reflections", book: "reflections", reflection: "reflections" };
// Google Fonts are network; /api/feedback is mocked (its 401 / 502 answers log a browser line, not a JS error)
const IGNORE = /fonts\.g(oogleapis|static)\.com|\/api\/feedback|Failed to load resource: the server responded with a status of (401|403|502)/;
const same = (a, b) => L.norm(a) === L.norm(b);
const fill = (s, vars) => String(s).replace(/\{(\w+)\}/g, (m, k) => (k in vars ? vars[k] : m));
const t0 = Date.now();

function mock(page, status = 200, body = { ok: true }) {
  const hits = [];
  page.route("**/api/feedback", async (route) => {
    const req = route.request();
    hits.push({ headers: await req.allHeaders(), body: JSON.parse(req.postData() || "null") });
    await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
  });
  return hits;
}
async function contrast(page, fgSel, bgSel) {
  return page.evaluate(([f, b]) => {
    const lum = (col) => { const m = col.match(/[\d.]+/g).map(Number); const [r, g, bb] = m.slice(0, 3).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }); return 0.2126 * r + 0.7152 * g + 0.0722 * bb; };
    const fe = document.querySelector(f), be = document.querySelector(b);
    if (!fe || !be) return { ratio: 0, fg: "missing " + f, bg: "missing " + b };
    let bg = getComputedStyle(be).backgroundColor, el = be;
    while (el && (bg === "rgba(0, 0, 0, 0)" || bg === "transparent")) { el = el.parentElement; bg = el ? getComputedStyle(el).backgroundColor : "rgb(255, 255, 255)"; }
    const fg = getComputedStyle(fe).color, L1 = lum(fg), L2 = lum(bg);
    return { ratio: +((Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05)).toFixed(2), fg, bg };
  }, [fgSel, bgSel]);
}
const open = (page, url) => page.goto(base + url).then(() => page.waitForLoadState("load"));
const txt = (page, sel) => page.locator(sel).first().textContent().then(L.norm);

(async () => {
  const browser = await chromium.launch();

  // ---------- A. footer → panel → payload ----------
  c.section("A. footer trigger, payload, success (module, desktop)");
  {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    const hits = mock(page);
    await open(page, P.module.url + "?feedback=live");
    c.ok(await page.locator(".fb-slot .fb-open").count() === 1, "footer slot holds the feedback button");
    c.ok(same(await txt(page, ".fb-open"), EN.fbOpen), `button text === fbOpen ("${await txt(page, ".fb-open")}")`);
    await page.click(".fb-open");
    c.ok(await page.evaluate(() => document.querySelector(".fb-panel").open), "panel opens");
    c.ok(await page.evaluate(() => document.activeElement && document.activeElement.tagName === "TEXTAREA"), "focus lands in the message");
    c.ok(same(await txt(page, "#fb-title"), EN.fbTitle) && same(await txt(page, ".fb-privacy"), EN.fbPrivacy) && same(await txt(page, ".fb-send"), EN.fbSend), "panel title, privacy line and Send === fbTitle / fbPrivacy / fbSend");
    const chips = (await page.locator(".fb-chip span").allTextContents()).map(L.norm);
    c.ok(JSON.stringify(chips) === JSON.stringify([EN.fbKindMistake, EN.fbKindConfusing, EN.fbKindSuggestion, EN.fbKindOther].map(L.norm)), `kind chips === fbKind* EN (${chips.join(" | ")})`);
    await page.locator(".fb-chip", { hasText: EN.fbKindConfusing }).first().click();
    await page.fill(".fb-panel textarea", "Trial 2's caption lost me.");
    await page.fill(".fb-panel input[type=email]", "reader@example.com");
    await page.evaluate(() => { const f = window.fetch; window.fetch = (u, i) => { window.__cred = i && i.credentials; return f(u, i); }; });
    await page.click(".fb-send");
    await page.waitForSelector(".fb-done:not([hidden])");
    c.ok(hits.length === 1, "one POST to /api/feedback");
    c.ok(await page.evaluate(() => window.__cred === "same-origin"), "fetch uses credentials: same-origin (Vercel preview protection cookie)");
    const p = hits[0].body || {}, h = hits[0].headers;
    c.ok(p.kind === "confusing" && p.message === "Trial 2's caption lost me." && p.quote === "" && p.path === P.module.url && p.series === SERIES.module && p.lang === "en" && p.vw === "≥1024" && p.email === "reader@example.com" && typeof p.elapsed === "number" && p.website === "", "payload: kind, message, quote, path, series, lang, vw, email, elapsed, honeypot — " + JSON.stringify(p));
    c.ok(typeof p.section === "string", "payload has section (" + JSON.stringify(p.section) + ")");
    const keys = Object.keys(p).sort().join(",");
    c.ok(keys === "elapsed,email,kind,lang,message,path,quote,section,series,vw,website", "no other fields (" + keys + ")");
    c.ok(!("x-feedback-owner" in h) && h["content-type"] === "application/json", "visitor: no owner header, JSON content type");
    c.ok(same(await txt(page, ".fb-sent"), EN.fbSent), `success state === fbSent ("${await txt(page, ".fb-sent")}")`);
    c.ok(same(await txt(page, ".fb-done .fb-hint"), ""), "no labels note for a visitor");
    await page.screenshot({ path: path.join(L.out, "feedback-a-sent.png") });
    c.ok(log.length === 0, "console clean: " + log.join(" | "));
    await ctx.close();
  }

  // ---------- B. selection → Comment on this ----------
  c.section("B. selection button (reflection, desktop)");
  {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    const hits = mock(page);
    await open(page, P.essay.url + "?feedback=live"); await page.waitForTimeout(400);
    c.ok(await page.evaluate(() => matchMedia("(pointer: fine)").matches), "desktop context reports a fine pointer");
    const sel = await page.evaluate(() => {
      const h = document.querySelector("main h2[id], h2[id]"); if (!h) return null;
      let p = h.nextElementSibling; while (p && p.tagName !== "P") p = p.nextElementSibling; if (!p || !p.firstChild) return null;
      p.scrollIntoView({ block: "center" });
      const r = document.createRange(); r.setStart(p.firstChild, 0); r.setEnd(p.firstChild, Math.min(40, p.firstChild.length));
      const s = getSelection(); s.removeAllRanges(); s.addRange(r);
      return { text: s.toString().replace(/\s+/g, " ").trim(), id: h.id };
    });
    c.ok(sel && sel.text.length >= 3, "a paragraph after the first h2[id] was selected (" + JSON.stringify(sel) + ")");
    await page.waitForTimeout(400);
    c.ok(await page.locator(".fb-sel").isVisible(), "Comment-on-this button appears beside the selection");
    c.ok(same(await txt(page, ".fb-sel"), EN.fbCommentOn), `its text === fbCommentOn ("${await txt(page, ".fb-sel")}")`);
    const selBox = await page.locator(".fb-sel").boundingBox();
    const rangeBox = await page.evaluate(() => { const r = getSelection().getRangeAt(0).getBoundingClientRect(); return { top: r.top, bottom: r.bottom, left: r.left, right: r.right }; });
    c.ok(selBox && Math.abs(selBox.y - (rangeBox.bottom + 8)) < 3 && selBox.x + selBox.width <= rangeBox.right + 2, "button sits just under the selection's end " + JSON.stringify([selBox, rangeBox]));
    await page.click(".fb-sel");
    c.ok(await page.evaluate(() => document.querySelector(".fb-panel").open), "panel opens from the selection button");
    c.ok(!(await page.locator(".fb-quote").isHidden()) && same(await txt(page, ".fb-quote-text"), sel.text) && same(await txt(page, ".fb-quote-label"), EN.fbQuoteLabel), "quote shown in the panel under fbQuoteLabel");
    await page.fill(".fb-panel textarea", "This derivation skips a step.");
    await page.click(".fb-send");
    await page.waitForSelector(".fb-done:not([hidden])");
    const p = (hits[0] || {}).body || {};
    c.ok(p.quote === sel.text && p.section === sel.id && p.series === SERIES.reflection && p.lang === "en" && p.path === P.essay.url, `payload: quote, section ${sel.id}, series reflections, path — ` + JSON.stringify(p));
    await page.screenshot({ path: path.join(L.out, "feedback-b-quote.png") });
    c.ok(log.length === 0, "console clean: " + log.join(" | "));
    await ctx.close();
  }

  // ---------- C. failure, Esc + focus, non-JSON 401 ----------
  c.section("C. failure state, Esc + focus (book page); non-JSON 401 (reflection)");
  {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    mock(page, 502, { ok: false });
    await open(page, P.book.url + "?feedback=live");
    await page.click(".fb-open");
    await page.fill(".fb-panel textarea", "Keep me after failure.");
    await page.click(".fb-send");
    await page.waitForSelector(".fb-fail:not([hidden])");
    c.ok((await page.inputValue(".fb-panel textarea")) === "Keep me after failure.", "failure keeps the text");
    c.ok(same(await txt(page, ".fb-fail span"), EN.fbFail) && same(await txt(page, ".fb-email"), EMAIL), `failure shows fbFail and the footer's email as text ("${await txt(page, ".fb-fail")}")`);
    c.ok(await page.evaluate(() => getComputedStyle(document.querySelector(".fb-email")).userSelect === "all"), "email is select-all");
    await page.screenshot({ path: path.join(L.out, "feedback-c-fail.png") });
    await page.keyboard.press("Escape");
    c.ok(await page.evaluate(() => !document.querySelector(".fb-panel").open), "Esc closes the panel");
    c.ok(await page.evaluate(() => document.activeElement === document.querySelector(".fb-open")), "focus returns to the footer trigger");
    await page.click(".fb-open");
    c.ok((await page.inputValue(".fb-panel textarea")) === "Keep me after failure.", "text still there on reopen");
    c.ok(await page.evaluate(() => document.querySelector(".fb-close").getAttribute("aria-label")) === EN.fbClose, "✕ carries aria-label fbClose");
    await page.click(".fb-close");
    c.ok(await page.evaluate(() => !document.querySelector(".fb-panel").open && document.activeElement === document.querySelector(".fb-open")), "✕ closes and returns focus");
    await page.click(".fb-open"); await page.fill(".fb-panel textarea", ""); await page.click(".fb-send"); await page.waitForTimeout(100);
    c.ok(same(await txt(page, ".fb-fields .fb-status"), EN.fbRequired), `empty message → fbRequired ("${await txt(page, ".fb-fields .fb-status")}")`);
    await page.keyboard.press("Escape");
    c.ok(log.length === 0, "console clean: " + log.join(" | "));
    await ctx.close();
    // Vercel Deployment Protection answers a non-JSON 401 before the function runs
    const ctx2 = await L.context(browser, { lang: "en" }); const page2 = await ctx2.newPage(); const log2 = []; L.watch(page2, log2, { ignore: IGNORE });
    await page2.route("**/api/feedback", (route) => route.fulfill({ status: 401, contentType: "text/html", body: "<!doctype html><title>Authentication Required</title><h1>Log in to Vercel</h1>" }));
    await open(page2, P.essay.url + "?feedback=live");
    await page2.click(".fb-open");
    await page2.fill(".fb-panel textarea", "Behind deployment protection.");
    await page2.click(".fb-send");
    await page2.waitForSelector(".fb-fail:not([hidden])");
    c.ok((await page2.inputValue(".fb-panel textarea")) === "Behind deployment protection." && same(await txt(page2, ".fb-email"), EMAIL) && (await page2.locator(".fb-done").isHidden()), "non-JSON 401 (HTML) → failure state with the email, text kept");
    c.ok(log2.length === 0, "console clean on the 401 path: " + log2.join(" | "));
    await ctx2.close();
  }

  // ---------- D. localhost dry-run ----------
  c.section("D. dry-run on localhost (hub)");
  {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    const hits = mock(page);
    const logs = []; page.on("console", (m) => { if (m.type() === "log") logs.push(m.text()); });
    await open(page, P.hub.url);
    await page.click(".fb-open");
    await page.fill(".fb-panel textarea", "dry run message");
    await page.click(".fb-send");
    await page.waitForSelector(".fb-done:not([hidden])");
    c.ok(hits.length === 0, "no request to /api/feedback");
    c.ok(logs.some((l) => l.startsWith("[feedback dry-run] POST /api/feedback")), "payload logged to the console (" + logs.map((l) => l.slice(0, 60)).join(" | ") + ")");
    c.ok((await txt(page, ".fb-done .fb-hint")).startsWith(L.norm(EN.fbDryRun)), `dry-run note === fbDryRun ("${await txt(page, ".fb-done .fb-hint")}")`);
    c.ok(same(await txt(page, ".fb-sent"), EN.fbSent), "success state shown");
    c.ok(log.length === 0, "console clean (warnings/errors): " + log.join(" | "));
    await ctx.close();
  }

  // ---------- E. file: and offline ----------
  c.section("E. file: and the offline copy: email line only");
  {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage();
    for (const pg of [P.module, P.essay]) {
      await page.goto(pathToFileURL(path.join(L.repo, pg.file)).href); await page.waitForLoadState("load"); await page.waitForTimeout(300);
      c.ok(same(await txt(page, ".fb-slot"), EN.footMistake), `file: ${pg.name} footer shows footMistake ("${await txt(page, ".fb-slot")}")`);
      c.ok((await page.locator(".fb-open, .fb-panel, .fb-sel").count()) === 0, `file: ${pg.name} has no button, panel or selection button`);
    }
    await ctx.close();
    const ctx2 = await L.context(browser, { lang: "en", offline: true }); const page2 = await ctx2.newPage();
    await open(page2, P.module.url); await page2.waitForTimeout(200);
    c.ok(same(await txt(page2, ".fb-slot"), EN.footMistake) && (await page2.locator(".fb-open, .fb-panel, .fb-sel").count()) === 0, "offline (LEARN_OFFLINE set): footMistake line, no widget");
    await ctx2.close();
  }

  // ---------- F. owner mode ----------
  c.section("F. owner setup, owner header, labels note, forget");
  {
    // a plain context: the key must survive navigations, so no per-load localStorage.clear()
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    const hits = mock(page, 200, { ok: true, labels: "direct" });
    await open(page, P.module.url + "?feedback=live#owner-setup");
    c.ok(await page.evaluate(() => document.querySelector(".fb-panel").open && !document.querySelector(".fb-setup").hidden && document.querySelector(".fb-fields").hidden), "#owner-setup opens the key field");
    c.ok(await page.evaluate(() => location.hash === "" && location.search === "?feedback=live"), "hash removed, query kept");
    c.ok(same(await txt(page, ".fb-setup h3"), EN.fbOwnerTitle) && same(await txt(page, ".fb-setup .fb-hint"), EN.fbOwnerHint) && same(await txt(page, ".fb-setup .btn"), EN.fbOwnerSave), "setup title, hint and Save === fbOwnerTitle / fbOwnerHint / fbOwnerSave");
    await page.fill(".fb-setup input", "my-owner-key-0123456789");
    await page.click(".fb-setup .btn");
    c.ok(await page.evaluate(() => localStorage.getItem("learnFeedbackOwner") === "my-owner-key-0123456789"), "key stored in localStorage");
    c.ok((await txt(page, ".fb-setup .fb-status")).startsWith(L.norm(EN.fbOwnerSaved)), `saved note === fbOwnerSaved ("${await txt(page, ".fb-setup .fb-status")}")`);
    await page.keyboard.press("Escape");
    await page.click(".fb-open");
    c.ok(await page.locator(".fb-owner").isVisible() && same(await txt(page, ".fb-owner"), EN.fbOwnerNote), `owner note === fbOwnerNote ("${await txt(page, ".fb-owner")}")`);
    await page.fill(".fb-panel textarea", "owner note");
    await page.click(".fb-send");
    await page.waitForSelector(".fb-done:not([hidden])");
    c.ok(hits.length === 1 && hits[0].headers["x-feedback-owner"] === "my-owner-key-0123456789", "owner key sent as X-Feedback-Owner");
    c.ok(same(await txt(page, ".fb-done .fb-hint"), fill(EN.fbSentLabels, { path: "direct" })), `labels note === fbSentLabels with {path} = direct ("${await txt(page, ".fb-done .fb-hint")}")`);
    await page.screenshot({ path: path.join(L.out, "feedback-f-owner.png") });
    // forget
    await open(page, P.module.url + "#owner-setup");
    c.ok(same(await txt(page, ".fb-setup .fb-link"), EN.fbOwnerForget), `#owner-setup shows fbOwnerForget ("${await txt(page, ".fb-setup .fb-link")}")`);
    await page.click(".fb-setup .fb-link");
    c.ok(await page.evaluate(() => localStorage.getItem("learnFeedbackOwner") === null), "Forget clears the stored key");
    c.ok(same(await txt(page, ".fb-setup .fb-status"), EN.fbOwnerCleared), `cleared note === fbOwnerCleared ("${await txt(page, ".fb-setup .fb-status")}")`);
    await page.keyboard.press("Escape");
    await open(page, P.module.url + "?feedback=live");
    hits.length = 0;
    await page.click(".fb-open");
    c.ok(await page.locator(".fb-owner").isHidden(), "no owner note after forgetting");
    await page.fill(".fb-panel textarea", "visitor again");
    await page.click(".fb-send");
    await page.waitForSelector(".fb-done:not([hidden])");
    c.ok(hits.length === 1 && !("x-feedback-owner" in hits[0].headers), "same browser now sends as a visitor (no owner header)");
    c.ok(log.length === 0, "console clean: " + log.join(" | "));
    await ctx.close();
  }

  // ---------- G. Spanish ----------
  c.section("G. Spanish strings (module, ES stored; then the toggle); Reflections stay English");
  {
    const ctx = await L.context(browser, { lang: "es" }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    await open(page, P.module.url);
    c.ok(same(await txt(page, ".fb-open"), ES.fbOpen), `footer button === es.fbOpen ("${await txt(page, ".fb-open")}")`);
    await page.click(".fb-open");
    c.ok(same(await txt(page, "#fb-title"), ES.fbTitle) && same(await txt(page, ".fb-privacy"), ES.fbPrivacy) && same(await txt(page, ".fb-send"), ES.fbSend), "panel title, privacy line and Send in ES");
    const chips = (await page.locator(".fb-chip span").allTextContents()).map(L.norm);
    c.ok(JSON.stringify(chips) === JSON.stringify([ES.fbKindMistake, ES.fbKindConfusing, ES.fbKindSuggestion, ES.fbKindOther].map(L.norm)), `kind chips in ES (${chips.join(" | ")})`);
    c.ok(same(await page.locator(".fb-field span").nth(0).textContent(), ES.fbMessage) && same(await page.locator(".fb-field span").nth(1).textContent(), ES.fbEmail) && same(await txt(page, ".fb-kinds legend"), ES.fbKindLegend), "message / email labels and the kinds legend in ES");
    c.ok(await page.evaluate(() => document.querySelector(".fb-close").getAttribute("aria-label")) === ES.fbClose, "✕ aria-label in ES");
    await page.screenshot({ path: path.join(L.out, "feedback-g-es.png") });
    await page.keyboard.press("Escape");
    await page.click(".lang-toggle"); await page.waitForTimeout(100);
    c.ok(same(await txt(page, ".fb-open"), EN.fbOpen) && same(await txt(page, "#fb-title"), EN.fbTitle), "toggle to EN re-applies the widget text");
    c.ok(same(await txt(page, ".fb-slot"), EN.fbOpen), "the footer slot shows only the button after the switch (no fallback text restored)");
    c.ok(log.length === 0, "console clean: " + log.join(" | "));
    await ctx.close();
    const ctx2 = await L.context(browser, { lang: "es" }); const page2 = await ctx2.newPage();
    await open(page2, P.essay.url);
    c.ok(same(await txt(page2, ".fb-open"), EN.fbOpen), `Reflections page stays English with ES stored ("${await txt(page2, ".fb-open")}")`);
    await ctx2.close();
  }

  // ---------- H. layout matrix on every page ----------
  c.section("H. layout matrix (every page): 375/768/1280 × light/dark × readability — panel fits, no sideways scroll, console clean");
  for (const w of [375, 768, 1280]) for (const dark of [false, true]) for (const read of [false, true]) {
    const ctx = await L.context(browser, { width: w, height: w < 768 ? 740 : 900, dark, theme: dark ? "dark" : "light", read, lang: "en" });
    const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    for (const pg of PAGES) {
      log.length = 0;
      await open(page, pg.url); await page.waitForTimeout(pg.kind === "reflection" ? 300 : 100);
      await page.click(".fb-open"); await page.waitForTimeout(50);
      const m = await page.evaluate(() => {
        const d = document.querySelector(".fb-panel"), r = d.getBoundingClientRect();
        return { sw: document.documentElement.scrollWidth, iw: innerWidth, ih: innerHeight, d: { x: Math.round(r.x), y: Math.round(r.y), r: Math.round(r.right), b: Math.round(r.bottom), w: Math.round(r.width), h: Math.round(r.height) }, over: d.scrollHeight > d.clientHeight + 1 };
      });
      const fits = m.d.x >= 0 && m.d.y >= 0 && m.d.r <= m.iw + 0.5 && m.d.b <= m.ih + 0.5;
      const tag = `${pg.name} ${w}px ${dark ? "dark" : "light"}${read ? " +read" : ""}`;
      c.ok(m.sw <= m.iw && fits && log.length === 0, `${tag}: scrollWidth ${m.sw}/${m.iw}, panel ${JSON.stringify(m.d)} in ${m.iw}×${m.ih}, inner scroll ${m.over}; ${log.join(" | ")}`);
      if (w === 375 && !dark && !read && ["hub", "module", "reflection"].includes(pg.kind) && pg === P[pg.kind === "reflection" ? "essay" : pg.kind]) await page.screenshot({ path: path.join(L.out, `feedback-h-${pg.kind}-375.png`) });
      await page.keyboard.press("Escape");
    }
    await ctx.close();
  }

  // ---------- I. contrast on every page ----------
  c.section("I. contrast (every page): trigger, panel text, privacy, unselected chip, failure line ≥ 4.5:1");
  for (const dark of [false, true]) for (const read of [false, true]) {
    const ctx = await L.context(browser, { dark, theme: dark ? "dark" : "light", read, lang: "en" }); const page = await ctx.newPage();
    for (const pg of PAGES) {
      await open(page, pg.url); await page.waitForTimeout(pg.kind === "reflection" ? 300 : 100);
      const trig = await contrast(page, ".fb-open", ".fb-open");
      await page.click(".fb-open");
      const body = await contrast(page, ".fb-panel", ".fb-panel");
      const priv = await contrast(page, ".fb-privacy", ".fb-panel");
      const chip = await contrast(page, ".fb-chip input:not(:checked) + span", ".fb-panel");
      await page.evaluate(() => { document.querySelector(".fb-fail").hidden = false; });
      const failc = await contrast(page, ".fb-fail", ".fb-panel");
      const min = Math.min(trig.ratio, body.ratio, priv.ratio, chip.ratio, failc.ratio);
      c.ok(min >= 4.5, `${pg.name} ${dark ? "dark" : "light"}${read ? " +read" : ""}: trigger ${trig.ratio}, panel ${body.ratio}, privacy ${priv.ratio}, chip ${chip.ratio}, fail ${failc.ratio} — ${JSON.stringify({ trig, priv, chip, failc })}`);
      await page.keyboard.press("Escape");
    }
    await ctx.close();
  }

  // ---------- J. touch ----------
  c.section("J. touch screens: footer only, no selection button (reflection)");
  {
    const ctx = await L.context(browser, { width: 375, height: 740, lang: "en", ctx: { hasTouch: true, isMobile: true } }); const page = await ctx.newPage();
    await open(page, P.essay.url); await page.waitForTimeout(300);
    c.ok(await page.evaluate(() => !matchMedia("(pointer: fine)").matches), "mobile context has no fine pointer");
    await page.evaluate(() => { const p = document.querySelector("main p, p"); const r = document.createRange(); r.selectNodeContents(p); const s = getSelection(); s.removeAllRanges(); s.addRange(r); });
    await page.waitForTimeout(400);
    c.ok(await page.locator(".fb-sel").isHidden(), "no Comment-on-this button on touch");
    c.ok((await page.locator(".fb-open").count()) === 1, "footer button present");
    await ctx.close();
  }

  // ---------- K. hub footer ----------
  c.section("K. hub footer on the dark band: trigger, ES swap, .hub-frame");
  {
    const ctx = await L.context(browser, { lang: "en" }); const page = await ctx.newPage(); const log = []; L.watch(page, log, { ignore: IGNORE });
    await open(page, P.hub.url); await page.waitForTimeout(200);
    c.ok(await page.evaluate(() => document.querySelector(".hub-foot .fb-slot .fb-open") !== null), "trigger inside the hub's dark footer");
    await page.click(".lang-toggle"); await page.waitForTimeout(100);
    c.ok(same(await txt(page, ".fb-open"), ES.fbOpen), `hub trigger swaps to es.fbOpen ("${await txt(page, ".fb-open")}")`);
    c.ok(await page.evaluate(() => document.querySelector(".fb-panel").classList.contains("hub-frame")), "hub panel carries .hub-frame");
    c.ok(log.length === 0, "console clean: " + log.join(" | "));
    await ctx.close();
  }

  await browser.close(); close();
  process.exit(c.summary(`wall time ${Math.round((Date.now() - t0) / 1000)} s`));
})().catch((e) => { console.error(e); close(); process.exit(1); });
