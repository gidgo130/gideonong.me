// offline-stage.js — the offline copy (learning/workshop/offline/): build.ps1 -StageOnly, then the staged
// files opened from file:// as the installed app would, online and with the network cut.
//   node learning/workshop/tests/offline-stage.js [--no-build]      (--no-build reuses the last stage/)
//   1. the stage: built, copied to out/stage-copy, none of the dev-only / online-only paths in it
//   2. the hub from file://, online and offline: frame renders, Reflections band hidden and never
//      requested, module rows = the registry, offline footer line from strings-common, no download
//      line, the gideonong.me crumb points at the live site, no missing file, console clean
//   3. every ready module page from file://: play/ link hidden, a not-installed slides file hidden,
//      no .take-offline, "All modules" → ../../index.html, console clean
// The installer appends window.LEARN_OFFLINE to modules.js; this suite appends the same line to the
// COPY (never to stage/ or the repo), with one module's slides listed as missing. The copy is removed
// at the end. Expected text comes from L.registries(); colors from the page's own tokens.
"use strict";
const fs = require("fs"), path = require("path"), { execSync } = require("child_process");
const L = require("./lib");
const { chromium } = L.pw();
const { base, close } = L.serve();   // unused here (file:// only), kept so run.js's shared server is honored
const c = new L.Checker("offline-stage");
const R = L.registries();
const noBuild = process.argv.includes("--no-build");
const STAGE = path.join(L.repo, "learning", "workshop", "offline", "stage");
const COPY = path.join(L.out, "stage-copy");
const FONT_RE = /Archivo|IBM\+Plex|IBM%20Plex/;
const GF_RE = /fonts\.(googleapis|gstatic)\.com/;
const norm = L.norm;
const str = (key, vars) => { let s = R.common.en[key]; for (const k in vars || {}) s = s.replace("{" + k + "}", vars[k]); return s; };
const hubStr = (key) => R.hub.en[key];

// the version the installer would stamp (its only home is the .iss); the commit is ours
const issText = fs.readFileSync(path.join(L.repo, "learning", "workshop", "offline", "ReadingYourFits.iss"), "utf8");
const VERSION = (/^#define AppVersion "([^"]+)"/m.exec(issText) || [])[1] || "0.0";
const COMMIT = "test";
const ready = R.readyModules;
const missingMod = ready[ready.length - 1];          // one module's slides are "not installed"
const MISSING = [`fits/${missingMod.slug}/slides.html`];
const fileUrl = (...parts) => "file:///" + encodeURI(path.join(COPY, ...parts).replace(/\\/g, "/"));
const walk = (dir, acc = []) => { for (const e of fs.readdirSync(dir, { withFileTypes: true })) { const p = path.join(dir, e.name); if (e.isDirectory()) walk(p, acc); else acc.push(path.relative(COPY, p).replace(/\\/g, "/")); } return acc; };
// With the network cut, Chromium logs each blocked font request a second time as a console error
// without its URL; allow exactly as many of those as there are failed Google Fonts requests.
function unexplained(log, online) {
  if (online) return log;
  let n = log.filter((l) => /^requestfailed: .*fonts\.(googleapis|gstatic)\.com/.test(l)).length;
  return log.filter((l) => !GF_RE.test(l) && !(/^error: Failed to load resource: net::ERR_INTERNET_DISCONNECTED$/.test(l) && n-- > 0));
}
const resolveTok = (el, v) => { const p = document.createElement("i"); p.style.cssText = "position:absolute;visibility:hidden;color:var(" + v + ")"; el.appendChild(p); const cc = getComputedStyle(p).color; p.remove(); return cc; };

(async () => {
  const t0 = Date.now();
  // ---------------- 1. stage ----------------
  c.section("1. stage: build.ps1 -StageOnly, copy, exclusions");
  if (!noBuild) {
    let built = true, msg = "";
    try { execSync(`powershell -ExecutionPolicy Bypass -File "${path.join(L.repo, "learning", "workshop", "offline", "build.ps1")}" -StageOnly`, { stdio: "pipe", cwd: L.repo, timeout: 180000 }); }
    catch (e) { built = false; msg = String((e.stdout || "") + (e.stderr || "") + e.message).slice(-600); }
    c.ok(built, `build.ps1 -StageOnly ran: ${msg}`);
  }
  c.ok(fs.existsSync(path.join(STAGE, "learning", "index.html")), `stage exists at ${STAGE}`);
  fs.rmSync(COPY, { recursive: true, force: true });
  fs.cpSync(STAGE, COPY, { recursive: true });
  const files = walk(COPY);
  c.ok(files.length > 50, `copy has ${files.length} files`);
  for (const [what, re] of [["learning/reflections", /^learning\/reflections\//], ["assets/reflections.js", /^learning\/assets\/reflections\.js$/], ["assets/vendor", /^learning\/assets\/vendor\//],
    ["assets/og", /^learning\/assets\/og\//], ["fits/*/play", /^learning\/fits\/[^/]+\/play\//], ["*.md", /\.md$/i], ["*.pdf / *.qmd", /\.(pdf|qmd)$/i], ["learning/workshop", /^learning\/workshop\//]]) {
    const hits = files.filter((f) => re.test(f));
    c.ok(hits.length === 0, `stage has no ${what} (${hits.slice(0, 3).join(", ")})`);
  }
  for (const m of ready) for (const f of ["index.html", "strings.js", "main.js", "slides.html", `${m.slug}.py`]) c.ok(files.includes(`learning/fits/${m.slug}/${f}`), `stage has fits/${m.slug}/${f}`);
  for (const f of ["learning/assets/learning.css", "learning/assets/learning.js", "learning/assets/learning-i18n.js", "learning/assets/strings-common.js", "learning/assets/modules.js", "learning/assets/feedback.js", "learning/strings.js", "assets/glogo.ico", "LICENSE.txt", "LICENSE-CONTENT.txt", "NOTICE.txt"]) c.ok(files.includes(f), `stage has ${f}`);
  // the installer's line, on the copy only
  const mj = path.join(COPY, "learning", "assets", "modules.js");
  fs.appendFileSync(mj, `\r\nwindow.LEARN_OFFLINE = { version: "${VERSION}", commit: "${COMMIT}", missing: ${JSON.stringify(MISSING)} };\r\n`);
  c.ok(!/LEARN_OFFLINE\s*=/.test(fs.readFileSync(path.join(STAGE, "learning", "assets", "modules.js"), "utf8")), "stage/ itself was not altered");

  const browser = await chromium.launch();
  try {
    for (const online of [true, false]) {
      const net = online ? "online" : "network cut";
      // ---------------- 2. the hub from file:// ----------------
      c.section(`2. hub from file:// (${net})`);
      {
        const ctx = await L.context(browser, { ctx: { offline: !online } });
        const page = await ctx.newPage(); const log = []; L.watch(page, log); const reqs = []; page.on("request", (r) => reqs.push(r.url()));
        await page.goto(fileUrl("learning", "index.html")); await page.waitForTimeout(1200);
        const r = await page.evaluate(() => {
          const q = (s) => document.querySelector(s), refs = document.getElementById("reflections"), foot = q(".hub-foot"), oc = q(".hub-foot .offline-copy"), get = document.getElementById("offline-get");
          const resolve = (el, v) => { const p = document.createElement("i"); p.style.cssText = "position:absolute;visibility:hidden;color:var(" + v + ")"; el.appendChild(p); const cc = getComputedStyle(p).color; p.remove(); return cc; };
          return {
            offlineFlag: !!window.LEARN_OFFLINE, reflLoaded: !!window.LEARN_REFLECTIONS, reflDisplay: getComputedStyle(refs).display, reflH: refs.getBoundingClientRect().height, reflHidden: refs.hidden,
            refFontsLink: !!document.getElementById("ref-fonts"), refScript: Array.from(document.scripts).some((s) => /reflections\.js/.test(s.src)),
            h1Face: getComputedStyle(q(".hub-head h1")).fontFamily.split(",")[0].replace(/["']/g, "").trim(), footBg: getComputedStyle(foot).backgroundColor, footTok: resolve(foot, "--footer-bg"),
            rows: Array.from(document.querySelectorAll("#module-list li")).map((li) => { const a = li.querySelector("a.module-row"); return { href: a ? a.getAttribute("href") : null, title: li.querySelector(".m-title").textContent, status: li.querySelector(".m-status").textContent, desc: li.querySelector(".m-desc").textContent }; }),
            offlineCopy: oc ? oc.textContent : null, offlineLink: oc && oc.querySelector("a") ? { href: oc.querySelector("a").getAttribute("href"), target: oc.querySelector("a").getAttribute("target"), text: oc.querySelector("a").textContent } : null,
            getHidden: get ? get.hidden : null, getText: get ? get.textContent : null,
            crumb: q(".crumbs a").getAttribute("href"), lead: q(".lead").textContent, intro: q("#reading-your-fits [data-i18n=seriesIntro]").textContent, h1: q(".hub-head h1").textContent,
            fbSlot: q(".fb-slot") ? q(".fb-slot").textContent : null, fbButton: !!q(".fb-open"), sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, htmlLang: document.documentElement.lang,
          };
        });
        c.ok(r.offlineFlag && r.htmlLang === "en", `${net}: LEARN_OFFLINE set from the appended line, page in EN`);
        c.ok(r.h1Face === "Lora" && norm(r.footBg) === norm(r.footTok) && /^rgb\(/.test(r.footBg), `${net}: frame renders (h1 ${r.h1Face}, footer ${r.footBg} = --footer-bg ${r.footTok})`);
        c.ok(r.reflDisplay === "none" && r.reflH === 0 && r.reflHidden && !r.reflLoaded && !r.refScript && !r.refFontsLink, `${net}: Reflections band display none, registry never loaded (${JSON.stringify({ d: r.reflDisplay, h: r.reflH, hidden: r.reflHidden, loaded: r.reflLoaded, script: r.refScript, fonts: r.refFontsLink })})`);
        c.ok(!reqs.some((u) => FONT_RE.test(u) || /reflections\.js/.test(u)), `${net}: no reflections.js / Archivo / Plex request`);
        const expRows = R.modules.map((m) => ({ href: m.ready ? `fits/${m.slug}/index.html` : null, title: m.title.en, status: str(m.ready ? "statusReady" : "statusSoon"), desc: m.desc.en }));
        c.ok(JSON.stringify(r.rows) === JSON.stringify(expRows), `${net}: module rows = registry with hrefs fits/<slug>/index.html: ${JSON.stringify(r.rows).slice(0, 300)}`);
        c.ok(r.rows.filter((x) => x.href).length === ready.length, `${net}: ${r.rows.filter((x) => x.href).length} linked rows = ${ready.length} ready modules`);
        const expCopy = str("offlineCopy", { v: VERSION, c: COMMIT });
        c.ok(r.offlineCopy !== null && norm(r.offlineCopy) === norm(`${expCopy} · ${str("offlineUpdates")}`), `${net}: offline footer line "${r.offlineCopy}" = "${expCopy} · ${str("offlineUpdates")}"`);
        c.ok(r.offlineLink && /^https:\/\/github\.com\//.test(r.offlineLink.href) && r.offlineLink.target === "_blank" && r.offlineLink.text === str("offlineUpdates"), `${net}: "${str("offlineUpdates")}" links to GitHub in a new tab (${JSON.stringify(r.offlineLink)})`);
        c.ok(r.getHidden === true && !r.getText, `${net}: #offline-get hidden and empty (hidden ${r.getHidden}, text "${r.getText}")`);
        c.ok(r.crumb === "https://gideonong.me/", `${net}: gideonong.me crumb → ${r.crumb}`);
        c.ok(r.lead === hubStr("lead") && r.intro === hubStr("seriesIntro") && r.h1 === hubStr("h1"), `${net}: lead, series intro and h1 from strings.js`);
        c.ok(r.fbSlot === str("footMistake") && !r.fbButton, `${net}: footer keeps the email line, no feedback button ("${r.fbSlot}")`);
        c.ok(r.sw <= r.cw, `${net}: no sideways scroll (${r.sw} > ${r.cw})`);
        const fileFails = log.filter((l) => /file:/.test(l)), http4xx = log.filter((l) => /^HTTP 4/.test(l));
        c.ok(fileFails.length === 0 && http4xx.length === 0, `${net}: no missing file and no 404 (${[...fileFails, ...http4xx].join(" | ")})`);
        const other = unexplained(log, online);
        c.ok(other.length === 0, `${net}: console ${online ? "clean" : "clean apart from Google Fonts"} (${other.join(" | ")})`);
        if (online) await page.screenshot({ path: path.join(L.out, "offline-stage-hub.png"), fullPage: true });
        await ctx.close();
      }
      // ---------------- 3. every ready module page from file:// ----------------
      c.section(`3. module pages from file:// (${net})`);
      for (let i = 0; i < ready.length; i++) {
        const m = ready[i], prev = ready[i - 1], next = ready[i + 1];
        const ctx = await L.context(browser, { ctx: { offline: !online } });
        const page = await ctx.newPage(); const log = []; L.watch(page, log); const reqs = []; page.on("request", (r) => reqs.push(r.url()));
        await page.goto(fileUrl("learning", "fits", m.slug, "index.html")); await page.waitForTimeout(800);
        const r = await page.evaluate(() => {
          const q = (s) => document.querySelector(s), links = Array.from(document.querySelectorAll(".takeaway-links a"));
          const pick = (sel) => { const a = q(sel); return a ? { href: a.getAttribute("href"), hidden: a.hidden } : null; };
          return {
            slides: pick('.takeaway-links a[href="slides.html"]'), py: pick('.takeaway-links a[download]'), play: pick(".takeaway-links .take-play"), colab: pick(".takeaway-links .take-colab"),
            httpOnly: Array.from(document.querySelectorAll("[data-http-only]")).map((e) => e.hidden), takeOffline: !!q(".take-offline"),
            all: pick(".series-nav a.all"), prev: pick(".series-nav a.prev"), next: pick(".series-nav a.next"), soonPrev: !!q(".series-nav .soon.prev"), soonNext: !!q(".series-nav .soon.next"),
            crumbs: Array.from(document.querySelectorAll(".series-bar .crumbs a")).map((a) => a.getAttribute("href")),
            links: links.map((a) => (a.hidden ? "[hidden] " : "") + a.getAttribute("href")), sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
            fbSlot: q(".fb-slot") ? q(".fb-slot").textContent : null, fbButton: !!q(".fb-open"), charts: document.querySelectorAll("svg.chart").length,
          };
        });
        const isMissing = m.slug === missingMod.slug;
        c.ok(r.play && r.play.hidden && r.httpOnly.length > 0 && r.httpOnly.every(Boolean), `${m.slug} ${net}: play/ link (data-http-only) hidden (${JSON.stringify(r.play)}, ${r.httpOnly.length} http-only)`);
        c.ok(r.slides && r.slides.hidden === isMissing, `${m.slug} ${net}: slides link ${isMissing ? "hidden (not installed)" : "shown"} (${JSON.stringify(r.slides)})`);
        c.ok(r.py && !r.py.hidden && r.py.href === `${m.slug}.py`, `${m.slug} ${net}: Python script link shown (${JSON.stringify(r.py)})`);
        c.ok(r.colab && !r.colab.hidden && /^https:\/\/colab\.research\.google\.com\//.test(r.colab.href), `${m.slug} ${net}: Colab link kept (${JSON.stringify(r.colab)})`);
        c.ok(!r.takeOffline, `${m.slug} ${net}: no .take-offline link in the installed copy`);
        c.ok(r.all && r.all.href === "../../index.html", `${m.slug} ${net}: "All modules" → ${r.all && r.all.href}`);
        c.ok(prev ? r.prev && r.prev.href === `../${prev.slug}/index.html` : !r.prev && !r.soonPrev, `${m.slug} ${net}: previous → ${JSON.stringify(r.prev)}`);
        c.ok(next ? r.next && r.next.href === `../${next.slug}/index.html` : !r.next && !r.soonNext, `${m.slug} ${net}: next → ${JSON.stringify(r.next)}`);
        c.ok(r.crumbs[0] === "https://gideonong.me/" && r.crumbs[1] === "../../index.html", `${m.slug} ${net}: crumbs ${JSON.stringify(r.crumbs)}`);
        c.ok(r.fbSlot === str("footMistake") && !r.fbButton, `${m.slug} ${net}: footer keeps the email line, no feedback button`);
        c.ok(r.charts > 0 && r.sw <= r.cw, `${m.slug} ${net}: ${r.charts} charts drawn, no sideways scroll (${r.sw}/${r.cw})`);
        c.ok(!reqs.some((u) => FONT_RE.test(u) || /reflections\.js/.test(u)), `${m.slug} ${net}: no Reflections font or registry request`);
        const fileFails = log.filter((l) => /file:/.test(l)), http4xx = log.filter((l) => /^HTTP 4/.test(l));
        c.ok(fileFails.length === 0 && http4xx.length === 0, `${m.slug} ${net}: no missing file and no 404 (${[...fileFails, ...http4xx].join(" | ")})`);
        const other = unexplained(log, online);
        c.ok(other.length === 0, `${m.slug} ${net}: console ${online ? "clean" : "clean apart from Google Fonts"} (${other.join(" | ")})`);
        await ctx.close();
      }
    }
  } finally {
    await browser.close(); close();
    fs.rmSync(COPY, { recursive: true, force: true });
    c.ok(!fs.existsSync(COPY), "stage copy removed");
  }
  process.exit(c.summary(`wall time ${Math.round((Date.now() - t0) / 1000)}s`));
})().catch((e) => { console.error(e); close(); fs.rmSync(COPY, { recursive: true, force: true }); process.exit(1); });
