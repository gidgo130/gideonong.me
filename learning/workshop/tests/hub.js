// hub.js — learning/index.html end to end (run: node learning/workshop/tests/hub.js, or through run.js).
//   1. matrix 375/768/1280 × light/dark × plain/readability/colorblind/both × EN/ES: every text element
//      ≥ 4.5:1 against its own band, no sideways scroll, console clean, band geometry, faces loaded,
//      sentence-case eyebrow, bar/footer backgrounds = their computed tokens, brass rule and hover =
//      the panel's computed --accent, rendered text = the registries (hub strings.js, strings-common.js,
//      modules.js, reflections.js with L.fmtDate), lang="en" on English titles; then the EN/ES toggle
//      re-renders both blocks in an America/Chicago context.
//   2. token sync by rendered values: frame = /about.html (main site), Reading Your Fits band = EVERY
//      ready module page, Reflections band = the first ready reflection page.
//   3. hidden really hides (installed copy, missing registry, JavaScript off), font requests, hub cap.
//   4. static head: meta description = og:description (hub, all-books), on-page lead = strings lead,
//      no Reflections font link in the hub's static head.
//   5. sticky series bar: 12 configurations.
// Expected text and colors are never hard-coded here: text comes from L.registries(), colors are
// compared against tokens read from the page at runtime.
"use strict";
const path = require("path");
const L = require("./lib");
const { chromium } = L.pw();
const { base, close } = L.serve();
const c = new L.Checker("hub");
const HUB = base + "/learning/";
const R = L.registries();
const FONT_RE = /Archivo|IBM\+Plex|IBM%20Plex/;
const FACES = { frame: ["Lora", "DM Sans"], fits: ["Barlow Semi Condensed", "Source Serif 4"], refl: ["Archivo", "IBM Plex Serif", "IBM Plex Mono"] };
const FACE_SPECS = ['500 16px "Lora"', '400 16px "DM Sans"', '700 16px "Barlow Semi Condensed"', '400 16px "Source Serif 4"', '700 16px "Archivo"', '400 16px "IBM Plex Serif"', '400 16px "IBM Plex Mono"'];
const HUB_MAX = 3;
const norm = L.norm;

// ---- expected values from the registries ----
// learning-i18n's rule: the hub's own strings first, then strings-common; a key missing in ES falls back to EN.
function str(lang, key) {
  const pick = (S) => (S[lang] && S[lang][key] != null ? S[lang][key] : S.en[key]);
  const v = pick(R.hub);
  return v != null ? v : pick(R.common);
}
const expModules = (lang) => R.modules.map((m, i) => ({
  num: String(i + 1).padStart(2, "0"), href: m.ready ? `fits/${m.slug}/` : null,
  title: m.title[lang] || m.title.en, desc: m.desc[lang] || m.desc.en, status: str(lang, m.ready ? "statusReady" : "statusSoon"),
}));
const byDateDesc = (a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0);
const expReflections = (lang, list = R.readyReflections) => list.slice().sort(byDateDesc).slice(0, HUB_MAX).map((x) => ({
  href: `reflections/${x.book}/${x.slug}/`, book: x.bookTitle, title: x.title, date: L.fmtDate(x.date, lang), desc: x.summary,
}));
const normTok = (s) => String(s == null ? "" : s).trim().toLowerCase().replace(/["']/g, "").replace(/\s+/g, " ");
const sameRGB = (a, b) => norm(a) === norm(b);

// ---- page-side probes ----
// Everything the matrix needs from one page, in one call. Colors are resolved from the element's own
// computed tokens (a hidden probe child painted with var(--x)), never from literals.
const probeHub = () => {
  const resolve = (el, v) => { const p = document.createElement("i"); p.style.cssText = "position:absolute;visibility:hidden;color:var(" + v + ")"; el.appendChild(p); const cc = getComputedStyle(p).color; p.remove(); return cc; };
  const rect = (el) => { const b = el.getBoundingClientRect(); return { x: Math.round(b.left), w: Math.round(b.width), h: Math.round(b.height) }; };
  const ff = (el) => (el ? getComputedStyle(el).fontFamily.split(",")[0].replace(/["']/g, "").trim() : "(missing)");
  const q = (s) => document.querySelector(s);
  const band = (id) => {
    const b = document.getElementById(id), cs = getComputedStyle(b), col = b.querySelector(".hub-col");
    return { display: cs.display, rect: rect(b), col: rect(col), padT: parseFloat(cs.paddingTop), padB: parseFloat(cs.paddingBottom), borderTop: cs.borderTopWidth + " " + cs.borderTopStyle,
      borderColor: cs.borderTopColor, rule: resolve(b, "--rule"), radius: cs.borderRadius, bg: cs.backgroundColor, accent: resolve(b, "--accent") };
  };
  const eb = q(".hub-head .eyebrow"), bar = q(".hub-bar"), foot = q(".hub-foot");
  const vis = (e) => !e.closest("[hidden]");
  return {
    sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, title: document.title, htmlLang: document.documentElement.lang,
    rootPx: parseFloat(getComputedStyle(document.documentElement).fontSize),
    faces: { h1: ff(q(".hub-head h1")), lead: ff(q(".hub-head .lead")), eyebrow: ff(eb), crumbs: ff(q(".series-bar .crumbs a")), foot: ff(q(".hub-foot .foot span")),
      fitsH2: ff(q("#reading-your-fits h2")), fitsP: ff(q("#reading-your-fits .hub-col > p")), fitsTitle: ff(q("#module-list .m-title")),
      reflH2: ff(q("#reflections h2")), reflP: ff(q("#reflections .hub-col > p")), reflTitle: ff(q("#reflections .m-title")), reflDate: ff(q("#reflections .ref-date")) },
    loaded: Array.from(new Set(Array.from(document.fonts).filter((f) => f.status === "loaded").map((f) => f.family.replace(/["']/g, "")))),
    eyebrow: { transform: getComputedStyle(eb).textTransform, text: eb.textContent },
    headCol: rect(q(".hub-head .hub-col")), fits: band("reading-your-fits"), refl: band("reflections"),
    bar: { bg: getComputedStyle(bar).backgroundColor, tok: resolve(bar, "--nav-bg") }, foot: { bg: getComputedStyle(foot).backgroundColor, tok: resolve(foot, "--footer-bg") },
    rule: getComputedStyle(q("#reflections h2"), "::after").backgroundColor,
    i18n: Array.from(document.querySelectorAll("[data-i18n]")).filter(vis).map((e) => ({ key: e.getAttribute("data-i18n"), text: e.textContent })),
    aria: Array.from(document.querySelectorAll("[data-i18n-aria]")).filter(vis).map((e) => ({ key: e.getAttribute("data-i18n-aria"), text: e.getAttribute("aria-label") })),
    mods: Array.from(document.querySelectorAll("#module-list li")).map((li) => { const row = li.querySelector(".module-row"), g = (s) => li.querySelector(s).textContent;
      return { num: g(".m-num"), href: row.tagName === "A" ? row.getAttribute("href") : null, title: g(".m-title"), desc: g(".m-desc"), status: g(".m-status") }; }),
    refl2: Array.from(document.querySelectorAll("#ref-list li a.ref-row")).map((a) => { const g = (s) => a.querySelector(s);
      return { href: a.getAttribute("href"), book: g(".ref-book").textContent, bookLang: g(".ref-book").getAttribute("lang"), title: g(".m-title").textContent, titleLang: g(".m-title").getAttribute("lang"),
        date: g(".ref-date").textContent, desc: g(".m-desc").textContent, descLang: g(".m-desc").getAttribute("lang") }; }),
  };
};
const hoverProbe = ([sel, textSel]) => { const el = document.querySelector(sel), t = textSel ? el.querySelector(textSel) : el; const bg = (e) => { for (; e; e = e.parentElement) { const b = getComputedStyle(e).backgroundColor; if (b !== "rgba(0, 0, 0, 0)" && b !== "transparent") return b; } return "rgb(255, 255, 255)"; }; return { color: getComputedStyle(t).color, bg: bg(el) }; };
const readTokens = ([sel, vars]) => { const cs = getComputedStyle(document.querySelector(sel)); const o = {}; for (const v of vars) o[v] = cs.getPropertyValue(v); return o; };
async function settleFonts(page) {
  await page.waitForSelector("#reflections:not([hidden])", { timeout: 8000 }).catch(() => {});
  await page.evaluate(async (specs) => { await document.fonts.ready; await Promise.all(specs.map((s) => document.fonts.load(s).catch(() => []))); await document.fonts.ready; }, FACE_SPECS);
}

(async () => {
  const t0 = Date.now();
  const browser = await chromium.launch();

  // ---------------- 1. matrix ----------------
  c.section("1. hub matrix: 375/768/1280 × light/dark × plain/read/cb/both × EN/ES");
  const minCR = { frame: 99, fits: 99, refl: 99, foot: 99 };
  let minHover = 99;
  for (const w of L.WIDTHS) for (const dark of L.DARKS) for (const mode of L.MODES) for (const lang of L.LANGS) {
    const label = `${w} ${dark ? "dark" : "light"} ${mode || "plain"} ${lang}`;
    const ctx = await L.context(browser, { width: w, height: 900, dark, lang, read: mode.includes("r"), cb: mode.includes("c") });
    const page = await ctx.newPage(); const log = []; L.watch(page, log);
    await page.goto(HUB); await settleFonts(page);
    const r = await page.evaluate(probeHub);
    const zones = {};
    for (const [z, sel] of Object.entries({ frame: ".hub-bar, .hub-head", fits: "#reading-your-fits", refl: "#reflections", foot: ".hub-foot" })) zones[z] = await page.evaluate(L.inPage.textContrast, sel);
    // layout, console
    c.ok(r.sw <= r.cw, `${label}: no sideways scroll (${r.sw} > ${r.cw})`);
    c.ok(log.length === 0, `${label}: console clean: ${log.join(" | ")}`);
    c.ok(r.htmlLang === lang, `${label}: <html lang> is ${r.htmlLang}`);
    // contrast against each element's own band
    for (const [z, list] of Object.entries(zones)) { c.ok(list.length > 0, `${label} ${z}: has text`); for (const x of list) { minCR[z] = Math.min(minCR[z], x.cr); c.ok(x.cr >= 4.5, `${label} ${z}: "${x.t}" ${x.cr}:1`); } }
    // faces: computed first family, and actually loaded
    const f = r.faces;
    c.ok(f.h1 === FACES.frame[0] && f.lead === FACES.frame[1] && f.eyebrow === FACES.frame[1] && f.crumbs === FACES.frame[1] && f.foot === FACES.frame[1], `${label}: frame faces ${JSON.stringify(f)}`);
    c.ok(f.fitsH2 === FACES.fits[0] && f.fitsTitle === FACES.fits[0] && f.fitsP === FACES.fits[1], `${label}: Reading Your Fits band faces ${JSON.stringify(f)}`);
    c.ok(f.reflH2 === FACES.refl[0] && f.reflTitle === FACES.refl[0] && f.reflP === FACES.refl[1] && f.reflDate === FACES.refl[2], `${label}: Reflections band faces ${JSON.stringify(f)}`);
    const notLoaded = [...FACES.frame, ...FACES.fits, ...FACES.refl].filter((fam) => !r.loaded.includes(fam));
    c.ok(notLoaded.length === 0, `${label}: faces loaded (missing: ${notLoaded.join(", ")}; loaded: ${r.loaded.join(", ")})`);
    // eyebrow: sentence case
    c.ok(r.eyebrow.transform === "none" && !/^[A-Z0-9 ·.]+$/.test(r.eyebrow.text), `${label}: eyebrow sentence case ("${r.eyebrow.text}", transform ${r.eyebrow.transform})`);
    // band geometry: full bleed, 4.5rem padding (72px at 16px), 1px top rule in --rule, column = header column
    for (const [name, g] of [["fits", r.fits], ["refl", r.refl]]) {
      c.ok(g.display !== "none", `${label} ${name} band: shown`);
      c.ok(g.rect.x === 0 && g.rect.w === r.cw, `${label} ${name} band: full bleed (x ${g.rect.x}, ${g.rect.w}/${r.cw})`);
      c.ok(Math.abs(g.padT - 4.5 * r.rootPx) < 0.5 && Math.abs(g.padB - 4.5 * r.rootPx) < 0.5 && g.padT === 72, `${label} ${name} band: padding ${g.padT}/${g.padB} (4.5rem = ${4.5 * r.rootPx})`);
      c.ok(g.borderTop === "1px solid" && sameRGB(g.borderColor, g.rule) && g.radius === "0px", `${label} ${name} band: top rule ${g.borderTop} ${g.borderColor} (--rule ${g.rule}), radius ${g.radius}`);
      c.ok(g.col.x === r.headCol.x && g.col.w === r.headCol.w, `${label} ${name} band: column at ${g.col.x}/${g.col.w} (header ${r.headCol.x}/${r.headCol.w})`);
    }
    // bar and footer paint their tokens, opaque
    c.ok(sameRGB(r.bar.bg, r.bar.tok) && /^rgb\(/.test(r.bar.bg), `${label}: bar background ${r.bar.bg} = --nav-bg ${r.bar.tok}`);
    c.ok(sameRGB(r.foot.bg, r.foot.tok) && /^rgb\(/.test(r.foot.bg), `${label}: footer background ${r.foot.bg} = --footer-bg ${r.foot.tok}`);
    // brass rule under the Reflections h2 = the panel's --accent
    c.ok(sameRGB(r.rule, r.refl.accent), `${label}: brass rule ${r.rule} = panel --accent ${r.refl.accent}`);
    // rendered text = registries
    const i18nBad = r.i18n.filter((x) => norm(x.text) !== norm(str(lang, x.key))).map((x) => `${x.key}: "${norm(x.text).slice(0, 40)}" ≠ "${norm(str(lang, x.key)).slice(0, 40)}"`);
    c.ok(r.i18n.length >= 15 && i18nBad.length === 0, `${label}: every data-i18n element renders its registry string (${r.i18n.length} checked): ${i18nBad.join("; ")}`);
    const ariaBad = r.aria.filter((x) => norm(x.text) !== norm(str(lang, x.key))).map((x) => x.key);
    c.ok(r.aria.length >= 3 && ariaBad.length === 0, `${label}: aria labels from the registry (${r.aria.length}): ${ariaBad.join(", ")}`);
    c.ok(r.title === str(lang, "pageTitle"), `${label}: document.title "${r.title}"`);
    for (const k of ["lead", "seriesIntro", "refTitle", "refIntro", "refAll", "h1", "eyebrow"]) c.ok(r.i18n.some((x) => x.key === k && norm(x.text) === norm(str(lang, k))), `${label}: ${k} rendered`);
    const em = expModules(lang);
    c.ok(JSON.stringify(r.mods) === JSON.stringify(em), `${label}: module rows = registry (${em.length}): got ${JSON.stringify(r.mods).slice(0, 300)}`);
    c.ok(r.mods.filter((m) => m.href).length === R.readyModules.length, `${label}: ${r.mods.filter((m) => m.href).length} linked module rows = ${R.readyModules.length} ready modules`);
    const er = expReflections(lang);
    const got = r.refl2.map(({ href, book, title, date, desc }) => ({ href, book, title, date, desc }));
    c.ok(JSON.stringify(got) === JSON.stringify(er), `${label}: Reflections rows = ${er.length} newest ready, in date order, dates in ${lang}: got ${JSON.stringify(got).slice(0, 300)}`);
    c.ok(r.refl2.length > 0 && r.refl2.every((x) => x.bookLang === "en" && x.titleLang === "en" && x.descLang === "en"), `${label}: lang="en" on book title, title and summary`);
    // hover: brass on the row title and on "All N books", legible on what it sits on
    await page.hover("#reflections .ref-row"); await page.waitForTimeout(120);
    const h1 = await page.evaluate(hoverProbe, ["#reflections .ref-row", ".m-title"]);
    await page.hover("#reflections .ref-all a"); await page.waitForTimeout(120);
    const h2 = await page.evaluate(hoverProbe, ["#reflections .ref-all a", null]);
    await page.hover("#module-list a.module-row"); await page.waitForTimeout(120);
    const h3 = await page.evaluate(hoverProbe, ["#module-list a.module-row", ".m-title"]);
    const cr1 = L.CR(h1.color, h1.bg), cr2 = L.CR(h2.color, h2.bg), cr3 = L.CR(h3.color, h3.bg);
    minHover = Math.min(minHover, cr1, cr2, cr3);
    c.ok(sameRGB(h1.color, r.refl.accent) && sameRGB(h2.color, r.refl.accent), `${label}: Reflections hover ${h1.color} / ${h2.color} = panel --accent ${r.refl.accent}`);
    c.ok(cr1 >= 4.5 && cr2 >= 4.5, `${label}: Reflections hover contrast ${cr1}:1 on ${h1.bg}, link ${cr2}:1 on ${h2.bg}`);
    // batch E (2026-10-17): colorblind light --accent is #006fad so this clears 4.5 like the rest
    c.ok(sameRGB(h3.color, r.fits.accent) && cr3 >= 4.5, `${label}: module row hover ${h3.color} = band --accent ${r.fits.accent}, ${cr3}:1 on ${h3.bg}`);
    if ((w === 375 || w === 1280) && !mode) { await page.mouse.move(0, 0); await page.screenshot({ path: path.join(L.out, `hub-${w}-${dark ? "dark" : "light"}-${lang}.png`), fullPage: true }); }
    await ctx.close();
  }
  console.log(`  smallest text contrast per zone ${JSON.stringify(minCR)}, smallest hover contrast ${minHover}:1`);

  // the toggle re-renders both blocks (America/Chicago: the date comes from its parts, never from the local midnight)
  c.section("1b. EN/ES toggle in an America/Chicago context");
  for (const lang of L.LANGS) {
    const other = lang === "en" ? "es" : "en";
    const ctx = await L.context(browser, { lang, ctx: { timezoneId: "America/Chicago", locale: "en-US" } });
    const page = await ctx.newPage(); const log = []; L.watch(page, log);
    await page.goto(HUB); await page.waitForSelector("#reflections:not([hidden])");
    const snap = () => page.evaluate(() => ({
      all: document.querySelector("#reflections .ref-all a").textContent, h2: document.querySelector("#reflections h2").textContent,
      dates: Array.from(document.querySelectorAll("#ref-list .ref-date")).map((e) => e.textContent), rows: document.querySelectorAll("#ref-list .ref-row").length,
      titles: Array.from(document.querySelectorAll("#module-list .m-title")).map((e) => e.textContent), statuses: Array.from(document.querySelectorAll("#module-list .m-status")).map((e) => e.textContent),
      lead: document.querySelector(".lead").textContent, toggleShown: !document.querySelector(".lang-toggle").hidden, htmlLang: document.documentElement.lang,
    }));
    const before = await snap();
    c.ok(before.toggleShown, `[${lang}] EN/ES toggle shown (data-es-ready)`);
    c.ok(JSON.stringify(before.dates) === JSON.stringify(expReflections(lang).map((x) => x.date)), `[${lang}] dates in Chicago ${JSON.stringify(before.dates)} = ${JSON.stringify(expReflections(lang).map((x) => x.date))}`);
    c.ok(before.all === str(lang, "refAll") && before.h2 === str(lang, "refTitle"), `[${lang}] refAll / refTitle "${before.all}" / "${before.h2}"`);
    await page.click(".lang-toggle"); await page.waitForTimeout(250);
    const after = await snap();
    c.ok(after.htmlLang === other && after.lead === str(other, "lead"), `[${lang}→${other}] <html lang> and lead switched ("${after.lead.slice(0, 30)}…")`);
    c.ok(after.rows === before.rows && after.all === str(other, "refAll") && after.h2 === str(other, "refTitle") && JSON.stringify(after.dates) === JSON.stringify(expReflections(other).map((x) => x.date)), `[${lang}→${other}] Reflections block re-rendered: ${after.all}, ${after.h2}, ${JSON.stringify(after.dates)}`);
    c.ok(JSON.stringify(after.titles) === JSON.stringify(expModules(other).map((m) => m.title)) && JSON.stringify(after.statuses) === JSON.stringify(expModules(other).map((m) => m.status)), `[${lang}→${other}] module list re-rendered: ${JSON.stringify(after.titles).slice(0, 200)}`);
    c.ok(log.length === 0, `[${lang}] console clean through the toggle: ${log.join(" | ")}`);
    await ctx.close();
  }

  // ---------------- 2. token sync by rendered values ----------------
  c.section("2. token sync: frame = main site, Reading Your Fits band = every module page, Reflections band = a reflection page");
  const MAP = { "--paper": "--bg", "--ink": "--ink", "--muted": "--muted", "--rule": "--border", "--accent": "--bronze", "--nav-bg": "--nav-bg", "--footer-bg": "--footer-bg", "--footer-text": "--footer-text", "--font-display": "--font-serif", "--font-body": "--font-sans" };
  for (const [dark, theme] of (L.quick ? [[false, ""]] : [[false, ""], [true, ""], [false, "dark"], [true, "light"]])) for (const mode of L.MODES) {
    const label = `OS ${dark ? "dark" : "light"}${theme ? " + viewTheme " + theme : ""} ${mode || "plain"}`;
    const ctx = await L.context(browser, { dark, theme, read: mode.includes("r"), cb: mode.includes("c") });
    const page = await ctx.newPage();
    await page.goto(HUB); const hub = await page.evaluate(readTokens, [".hub-head", Object.keys(MAP)]);
    await page.goto(base + "/about.html"); const main = await page.evaluate(readTokens, ["html", Object.values(MAP)]);
    const diffs = Object.entries(MAP).filter(([h, m]) => normTok(hub[h]) !== normTok(main[m])).map(([h, m]) => `${h} ${normTok(hub[h])} ≠ ${m} ${normTok(main[m])}`);
    c.ok(diffs.length === 0, `frame = main site, ${label}: ${diffs.join("; ")}`);
    await ctx.close();
  }
  const FITS_VARS = ["--paper", "--plot", "--grid", "--rule", "--ink", "--muted", "--pt", "--fit", "--fix", "--accent", "--emph", "--font-display", "--font-body", "--font-mono"];
  const REF_VARS = ["--paper", "--plot", "--rule", "--ink", "--muted", "--accent", "--font-display", "--font-body", "--font-mono"];
  const firstRef = R.readyReflections.slice().sort(byDateDesc)[0];
  c.ok(!!firstRef && R.readyModules.length > 0, `registries have ${R.readyModules.length} ready modules and ${R.readyReflections.length} ready reflections`);
  for (const dark of L.DARKS) for (const mode of L.MODES) {
    const label = `${dark ? "dark" : "light"} ${mode || "plain"}`;
    const ctx = await L.context(browser, { dark, read: mode.includes("r"), cb: mode.includes("c") });
    const page = await ctx.newPage();
    await page.goto(HUB);
    const fitsBand = await page.evaluate(readTokens, ["#reading-your-fits", FITS_VARS]);
    const reflBand = await page.evaluate(readTokens, ["#reflections", REF_VARS]);
    for (const m of R.readyModules) {
      await page.goto(base + m.url);
      const pg = await page.evaluate(readTokens, ["html", FITS_VARS]);
      const d = FITS_VARS.filter((k) => normTok(fitsBand[k]) !== normTok(pg[k]));
      c.ok(d.length === 0, `Reading Your Fits band = ${m.slug} page, ${label}: ${d.map((k) => `${k} ${normTok(fitsBand[k])} ≠ ${normTok(pg[k])}`).join("; ")}`);
    }
    if (firstRef) {
      await page.goto(base + firstRef.url);
      const pg = await page.evaluate(readTokens, ["html", REF_VARS]);
      const d = REF_VARS.filter((k) => normTok(reflBand[k]) !== normTok(pg[k]));
      c.ok(d.length === 0, `Reflections band = ${firstRef.book}/${firstRef.slug} page, ${label}: ${d.map((k) => `${k} ${normTok(reflBand[k])} ≠ ${normTok(pg[k])}`).join("; ")}`);
    }
    await ctx.close();
  }

  // ---------------- 3. hidden really hides; font requests; hub cap ----------------
  c.section("3. hidden block, font requests, hub cap");
  const OFFLINE_LINE = '\nwindow.LEARN_OFFLINE = { version: "1.0.0", commit: "abc", missing: [] };\n';
  for (const [label, kind] of [["installed copy", "offline"], ["registry missing", "missing"], ["no JavaScript", "nojs"], ["live hub", "live"]]) {
    const ctx = await L.context(browser, { ctx: { javaScriptEnabled: kind !== "nojs" } });
    const page = await ctx.newPage(); const reqs = []; page.on("request", (r) => reqs.push(r.url()));
    // a missing registry is a quiet failure by design: the request 404s (and Chromium logs that one line); nothing else may appear
    const log = []; L.watch(page, log, { ignore: kind === "missing" ? /reflections\.js|status of 404/ : undefined });
    if (kind === "offline") await page.route("**/assets/modules.js", async (route) => { const res = await route.fetch(); route.fulfill({ response: res, body: (await res.text()) + OFFLINE_LINE }); });
    if (kind === "missing") await page.route("**/assets/reflections.js", (route) => route.fulfill({ status: 404, body: "" }));
    await page.goto(HUB); await page.waitForTimeout(1000);
    const r = await page.evaluate(() => { const s = document.getElementById("reflections"); const a = document.querySelector('a[href="reflections/"]');
      return { display: getComputedStyle(s).display, h: s.getBoundingClientRect().height, hidden: s.hidden, link: !!(a && a.getClientRects().length), fontLinks: document.querySelectorAll("#ref-fonts").length, fontHref: (document.getElementById("ref-fonts") || {}).href || "" }; });
    const fontReqs = reqs.filter((u) => FONT_RE.test(u)), regReqs = reqs.filter((u) => /assets\/reflections\.js/.test(u));
    if (kind === "live") {
      c.ok(r.display !== "none" && r.h > 0 && r.link, `${label}: Reflections band shown (${JSON.stringify(r)})`);
      c.ok(regReqs.length === 1, `${label}: reflections.js requested exactly once (${regReqs.length})`);
      c.ok(fontReqs.length >= 1 && fontReqs.every((u) => /display=swap/.test(u)) && r.fontLinks === 1 && /display=swap/.test(r.fontHref), `${label}: Reflections faces requested once with display=swap (${fontReqs.length} requests, ${r.fontLinks} link)`);
    } else {
      c.ok(r.display === "none" && r.h === 0 && !r.link, `${label}: Reflections band not rendered (${JSON.stringify(r)})`);
      c.ok(fontReqs.length === 0 && r.fontLinks === 0, `${label}: no Reflections font request (${fontReqs.join(", ")})`);
      c.ok(kind === "missing" ? regReqs.length === 1 : regReqs.length === 0, `${label}: registry ${kind === "missing" ? "asked for once (and 404s quietly)" : "never requested"} (${regReqs.length})`);
    }
    c.ok(log.length === 0, `${label}: console clean: ${log.join(" | ")}`);
    await ctx.close();
  }
  // hub cap: inject extra ready (and one not-ready) reflections, expect the HUB_MAX newest ready, newest first
  {
    const bookSlugs = R.books.slice(0, 3).map((b) => b.slug);
    const extras = [
      { book: bookSlugs[0], slug: "x1", title: "Test x1", date: "2098-11-02", ready: true },
      { book: bookSlugs[1], slug: "x2", title: "Test x2", date: "2099-12-24", ready: true },
      { book: bookSlugs[2], slug: "x3", title: "Test x3", date: "2097-10-20", ready: true },
      { book: bookSlugs[1], slug: "x4", title: "Test x4", date: "2096-09-01", ready: true },
      { book: bookSlugs[0], slug: "x5", title: "Test x5", date: "2099-11-30", ready: true },
      { book: bookSlugs[1], slug: "nr", title: "Not ready", date: "2099-12-31", ready: false },
    ];
    const inject = "\n(function(){var E=" + JSON.stringify(extras) + ";E.forEach(function(e){window.LEARN_BOOKS.filter(function(b){return b.slug===e.book;})[0].reflections.push({slug:e.slug,title:e.title,date:e.date,summary:\"s\",ready:e.ready});});}());\n";
    const all = R.reflections.concat(extras.map((e) => ({ book: e.book, bookTitle: R.books.find((b) => b.slug === e.book).title, slug: e.slug, title: e.title, date: e.date, summary: "s", ready: e.ready })));
    const expected = expReflections("en", all.filter((x) => x.ready));
    const ctx = await L.context(browser, {}); const page = await ctx.newPage(); const log = []; L.watch(page, log);
    await page.route("**/assets/reflections.js", async (route) => { const res = await route.fetch(); route.fulfill({ response: res, body: (await res.text()) + inject }); });
    await page.goto(HUB); await page.waitForSelector("#reflections:not([hidden])");
    const got = await page.$$eval("#ref-list .ref-row", (as) => as.map((a) => ({ href: a.getAttribute("href"), title: a.querySelector(".m-title").textContent, date: a.querySelector(".ref-date").textContent })));
    c.ok(got.length === HUB_MAX && JSON.stringify(got.map((x) => x.title)) === JSON.stringify(expected.map((x) => x.title)), `hub cap: ${HUB_MAX} newest ready, newest first: ${JSON.stringify(got.map((x) => x.title))} (expected ${JSON.stringify(expected.map((x) => x.title))})`);
    c.ok(JSON.stringify(got.map((x) => x.href)) === JSON.stringify(expected.map((x) => x.href)) && JSON.stringify(got.map((x) => x.date)) === JSON.stringify(expected.map((x) => x.date)), `hub cap: hrefs and dates follow the registry (${JSON.stringify(got)})`);
    c.ok(!got.some((x) => x.title === "Not ready"), "hub cap: a not-ready reflection never shows, however new");
    c.ok(await page.$eval("#reflections .ref-all a", (a) => a.textContent) === str("en", "refAll"), `hub cap: "${str("en", "refAll")}" link after the list`);
    c.ok(log.length === 0, `hub cap: console clean: ${log.join(" | ")}`);
    await ctx.close();
  }

  // ---------------- 4. static head ----------------
  c.section("4. static head (scrapers don't run JS)");
  {
    const meta = (html, re) => { const m = re.exec(html); return m ? m[1] : null; };
    const unesc = (s) => String(s).replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'");
    for (const [name, url] of [["hub", HUB], ["all-books", base + "/learning/reflections/"]]) {
      const html = await (await fetch(url)).text();
      const desc = meta(html, /<meta name="description" content="([^"]*)">/), og = meta(html, /<meta property="og:description" content="([^"]*)">/);
      c.ok(desc && og && desc === og, `${name}: meta description = og:description ("${desc}" / "${og}")`);
      c.ok(/<meta name="robots" content="noindex">/.test(html), `${name}: noindex`);
    }
    const hub = await (await fetch(HUB)).text();
    const lead = meta(hub, /<p class="lead" data-i18n="lead">([^<]*)<\/p>/);
    c.ok(lead !== null && unesc(lead) === str("en", "lead"), `hub: on-page lead = strings lead (EN): "${lead}"`);
    const head = hub.split("<script")[0];
    c.ok(!FONT_RE.test(head) && !/reflections\.js/.test(head), "hub: static head has no Reflections font link or registry script");
    const keysInMarkup = Array.from(hub.matchAll(/data-i18n="([^"]+)"/g)).map((m) => m[1]);
    const missing = keysInMarkup.filter((k) => str("en", k) == null || str("es", k) == null);
    c.ok(keysInMarkup.length > 0 && missing.length === 0, `hub: every data-i18n key in the markup exists in EN and ES (${keysInMarkup.length}; missing ${missing.join(", ")})`);
  }

  // ---------------- 5. sticky series bar ----------------
  c.section("5. sticky series bar: 375/768/1280 × light/dark × readability");
  const stickyProbe = async () => {
    const bar = document.querySelector(".hub-bar"), cs = getComputedStyle(bar);
    const out = { pos: cs.position, top: cs.top, z: parseInt(cs.zIndex, 10), bg: cs.backgroundColor, h: bar.getBoundingClientRect().height,
      varH: parseFloat(getComputedStyle(document.body).getPropertyValue("--hub-bar-h")), sw: document.scrollingElement.scrollWidth, cw: document.documentElement.clientWidth };
    const resolve = (el, v) => { const p = document.createElement("i"); p.style.cssText = "position:absolute;visibility:hidden;color:var(" + v + ")"; el.appendChild(p); const cc = getComputedStyle(p).color; p.remove(); return cc; };
    out.navTok = resolve(bar, "--nav-bg");
    window.scrollTo(0, 900); await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    const b = bar.getBoundingClientRect(); out.pinnedTop = b.top; out.scrollY = scrollY;
    const hit = (x) => { const e = document.elementFromPoint(x, Math.floor(b.height / 2)); return !!(e && bar.contains(e)); };
    out.hits = [hit(20), hit(Math.floor(innerWidth / 2)), hit(innerWidth - 20)];
    out.anchors = {};
    for (const el of document.querySelectorAll("section[id]")) {
      if (el.hidden) { out.anchors[el.id] = "hidden"; continue; }
      location.hash = ""; window.scrollTo(0, 0); location.hash = "#" + el.id;
      await new Promise((r) => setTimeout(r, 150));
      const bb = bar.getBoundingClientRect().bottom, t = el.getBoundingClientRect().top;
      out.anchors[el.id] = { top: Math.round(t), barBottom: Math.round(bb), gap: Math.round(t - bb) };
    }
    window.scrollTo(0, document.body.scrollHeight);
    const btn = document.querySelector(".fb-open"); out.fbBtn = !!btn;
    if (btn) {
      btn.click(); await new Promise((r) => setTimeout(r, 250));
      const d = document.querySelector("dialog.fb-panel"); out.dialogOpen = !!(d && d.open);
      if (d) {
        const db = d.getBoundingClientRect(), bb = bar.getBoundingClientRect();
        const pts = [[Math.floor(db.left + db.width / 2), Math.floor(db.top + 10)]];
        if (db.top < bb.bottom && db.bottom > bb.top) pts.push([Math.floor(db.left + db.width / 2), Math.floor(Math.max(db.top, bb.top) + 2)]);   // where the dialog overlaps the bar
        out.dialogOnTop = pts.every(([x, y]) => { const e = document.elementFromPoint(x, y); return !!(e && d.contains(e)); });
        out.dialogTop = Math.round(db.top); out.dialogOverlapsBar = db.top < bb.bottom && db.bottom > bb.top;
        d.close();
      }
    }
    const sel = document.querySelector(".fb-sel");
    out.selZ = sel ? parseInt(getComputedStyle(sel).zIndex, 10) : null;
    return out;
  };
  for (const w of L.WIDTHS) for (const dark of L.DARKS) for (const read of L.READS) {
    const label = `${w} ${dark ? "dark" : "light"} ${read ? "read" : "plain"}`;
    const ctx = await L.context(browser, { width: w, height: 700, dark, theme: dark ? "dark" : "light", read, lang: "en", ctx: { hasTouch: w < 768 } });
    const page = await ctx.newPage(); const log = []; L.watch(page, log);
    await page.goto(HUB, { waitUntil: "networkidle" }); await page.waitForSelector("#reflections:not([hidden])"); await page.waitForTimeout(200);
    const r = await page.evaluate(stickyProbe);
    c.ok(r.pos === "sticky" && Math.abs(r.pinnedTop) <= 0.5, `${label}: bar sticky (${r.pos}) and pinned at the top after scrolling (top ${r.pinnedTop}, scrollY ${r.scrollY})`);
    c.ok(/^rgb\(/.test(r.bg) && sameRGB(r.bg, r.navTok), `${label}: bar opaque in --nav-bg (${r.bg} / ${r.navTok})`);
    c.ok(r.hits.every(Boolean), `${label}: hit-test inside the bar finds the bar (${r.hits.join(", ")})`);
    c.ok(Math.abs(r.varH - r.h) <= 1, `${label}: --hub-bar-h ${r.varH} = rendered height ${r.h} (±1)`);
    c.ok(r.sw <= r.cw, `${label}: no sideways scroll (${r.sw} > ${r.cw})`);
    const ids = Object.keys(r.anchors);
    c.ok(ids.includes("reading-your-fits") && ids.includes("reflections"), `${label}: both band anchors present (${ids.join(", ")})`);
    for (const [id, a] of Object.entries(r.anchors)) c.ok(a !== "hidden" && a.gap >= 4, `${label}: #${id} lands ≥ 4px below the bar (top ${a.top}, bar bottom ${a.barBottom}, gap ${a.gap})`);
    c.ok(r.fbBtn && r.dialogOpen && r.dialogOnTop, `${label}: feedback dialog opens above the bar (button ${r.fbBtn}, open ${r.dialogOpen}, on top ${r.dialogOnTop}, dialog top ${r.dialogTop}, overlaps bar ${r.dialogOverlapsBar})`);
    c.ok(r.selZ === null || r.selZ > r.z, `${label}: .fb-sel z-index ${r.selZ} > bar ${r.z}`);
    c.ok(log.length === 0, `${label}: console clean: ${log.join(" | ")}`);
    await ctx.close();
  }

  await browser.close(); close();
  process.exit(c.summary(`wall time ${Math.round((Date.now() - t0) / 1000)}s`));
})().catch((e) => { console.error(e); close(); process.exit(1); });
