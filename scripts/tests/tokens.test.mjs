// Drift test for the two copied token blocks in learning/assets/learning.css. Node built-ins only:
//   node --test "scripts/tests/*.test.mjs"
//
// The hub (learning/index.html) wraps its series bands in a main-site frame (.hub-frame) and
// previews the Reflections theme in its Reflections band (.ref-panel). The offline copy ships
// neither css/style.css nor learning/reflections/reflections.css, so learning.css carries COPIES
// of their token values, and the comments beside those blocks say "keep in step". This test is
// that rule, made mechanical: it parses the three stylesheets (no CSS library: a comment strip and
// a brace scanner) and fails on the first value that differs.
//
// What is compared
//   .hub-frame                      ↔ css/style.css
//     light                           the one live `:root { … }` (the active palette)
//     OS dark and data-theme dark     the LAST `:root[data-theme="dark"] { … }` (the §6 block, which
//                                     wins the cascade; the hub mirrors §6 for OS dark too, on purpose)
//     readability light / dark        `:root[data-readability]` / `:root[data-theme="dark"][data-readability]`
//     mapping                         --paper→--bg, --ink, --muted, --rule→--border, --accent→--bronze,
//                                     --nav-bg, --footer-bg, --footer-text
//     not compared                    --footer-accent (not a copy: documented in the audit, Gideon's call)
//   .ref-panel                      ↔ learning/reflections/reflections.css `:root[data-series="reflections"]`
//     light, OS dark, data-theme dark, readability light / dark; --paper, --plot, --rule, --ink,
//     --muted, --accent and the three font stacks
//     not compared                    --note-bg (the panel uses the paper color on purpose: row hover)
// Also: each copied block's OS-dark rule must equal its data-theme-dark rule (same values twice).
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");

// ---- a small CSS reader: rules as { selector, media, decls }, comments stripped, @media flattened
function parseCss(text) {
  const src = text.replace(/\/\*[\s\S]*?\*\//g, "");
  const rules = [];
  function walk(s, media) {
    let i = 0;
    while (i < s.length) {
      const open = s.indexOf("{", i);
      if (open < 0) break;
      let head = s.slice(i, open).trim();
      head = head.slice(head.lastIndexOf(";") + 1).trim();   // drop statements before it (@import …;)
      // find the matching close brace
      let depth = 1, j = open + 1;
      while (j < s.length && depth) { if (s[j] === "{") depth++; else if (s[j] === "}") depth--; j++; }
      const body = s.slice(open + 1, j - 1);
      if (head.startsWith("@media")) walk(body, head.replace(/^@media\s*/, "").replace(/\s+/g, " "));
      else if (!head.startsWith("@")) {
        const decls = {};
        for (const d of body.split(";")) {
          const k = d.indexOf(":"); if (k < 0) continue;
          decls[d.slice(0, k).trim()] = d.slice(k + 1).trim();
        }
        for (const sel of head.split(",")) rules.push({ selector: sel.trim().replace(/\s+/g, " "), media: media || "", decls });
      }
      i = j;
    }
  }
  walk(src, "");
  return rules;
}
// The declarations of a selector: `which` = "first" | "last" (the cascade keeps the last), merged
// over every matching rule in that order so a split block still reads as one.
function decls(rules, selector, { media = "", which = "last" } = {}) {
  const hits = rules.filter((r) => r.selector === selector && (media === "*" || r.media === media));
  assert.ok(hits.length, `no rule for ${selector}${media ? " in @media " + media : ""}`);
  return which === "first" ? hits[0].decls : Object.assign({}, ...hits.map((r) => r.decls));
}
const norm = (v) => String(v).trim().toLowerCase().replace(/\s+/g, " ").replace(/"/g, "'");
function same(label, a, aKey, b, bKey) {
  assert.ok(aKey in a, `${label}: ${aKey} missing in the copy`);
  assert.ok(bKey in b, `${label}: ${bKey} missing in the source`);
  assert.equal(norm(a[aKey]), norm(b[bKey]), `${label}: ${aKey} = ${a[aKey]} but the source ${bKey} = ${b[bKey]}`);
}

const L = parseCss(read("learning/assets/learning.css"));
const S = parseCss(read("css/style.css"));
const R = parseCss(read("learning/reflections/reflections.css"));
const DARK_MEDIA = "(prefers-color-scheme: dark)";

// ---------------------------------------------------------------- .hub-frame ↔ css/style.css
const HUB_MAP = [["--paper", "--bg"], ["--ink", "--ink"], ["--muted", "--muted"], ["--rule", "--border"],
  ["--accent", "--bronze"], ["--nav-bg", "--nav-bg"], ["--footer-bg", "--footer-bg"], ["--footer-text", "--footer-text"]];

test("hub frame, light: .hub-frame mirrors the live :root palette of css/style.css", () => {
  const hub = decls(L, ".hub-frame");
  const site = decls(S, ":root", { which: "first" });
  assert.ok("--bg" in site && "--bronze" in site, "style.css's first live :root is not the palette block");
  for (const [h, s] of HUB_MAP) same("light", hub, h, site, s);
});

test("hub frame, dark: both dark rules mirror the LAST :root[data-theme=\"dark\"] block (§6) of css/style.css", () => {
  const site = decls(S, ':root[data-theme="dark"]', { which: "last" });
  const hubData = decls(L, ':root[data-theme="dark"] .hub-frame');
  const hubOs = decls(L, ':root:not([data-theme="light"]) .hub-frame', { media: DARK_MEDIA });
  for (const [h, s] of HUB_MAP) { same("data-theme dark", hubData, h, site, s); same("OS dark", hubOs, h, site, s); }
  // style.css has an older :root[data-theme="dark"] block too; make sure the §6 one really is last
  const all = S.filter((r) => r.selector === ':root[data-theme="dark"]');
  assert.ok(all.length >= 1);
  assert.equal(norm(all[all.length - 1].decls["--bg"]), norm(site["--bg"]));
});

test("hub frame, readability: the muted values mirror css/style.css §6", () => {
  same("readability light", decls(L, ":root[data-readability] .hub-frame"), "--muted", decls(S, ":root[data-readability]"), "--muted");
  const siteDark = decls(S, ':root[data-theme="dark"][data-readability]');
  same("readability dark", decls(L, ':root[data-readability][data-theme="dark"] .hub-frame'), "--muted", siteDark, "--muted");
  same("readability OS dark", decls(L, ':root[data-readability]:not([data-theme="light"]) .hub-frame', { media: DARK_MEDIA }), "--muted", siteDark, "--muted");
});

// ---------------------------------------------------------------- .ref-panel ↔ reflections.css
const REF_KEYS = ["--paper", "--plot", "--rule", "--ink", "--muted", "--accent"];
const FONT_KEYS = ["--font-display", "--font-body", "--font-mono"];

test("Reflections band, light: .ref-panel mirrors reflections.css's series tokens and fonts", () => {
  const panel = decls(L, ".ref-panel");
  const src = decls(R, ':root[data-series="reflections"]');
  for (const k of [...REF_KEYS, ...FONT_KEYS]) same("light", panel, k, src, k);
});

test("Reflections band, dark: both dark rules mirror reflections.css", () => {
  const srcData = decls(R, ':root[data-series="reflections"][data-theme="dark"]');
  const srcOs = decls(R, ':root[data-series="reflections"]:not([data-theme="light"])', { media: DARK_MEDIA });
  const panelData = decls(L, ':root[data-theme="dark"] .ref-panel');
  const panelOs = decls(L, ':root:not([data-theme="light"]) .ref-panel', { media: DARK_MEDIA });
  for (const k of REF_KEYS) { same("data-theme dark", panelData, k, srcData, k); same("OS dark", panelOs, k, srcOs, k); same("source self-consistency", srcData, k, srcOs, k); }
});

test("Reflections band, readability: muted mirrors reflections.css", () => {
  same("readability light", decls(L, ":root[data-readability] .ref-panel"), "--muted", decls(R, ':root[data-series="reflections"][data-readability]'), "--muted");
  const srcDark = decls(R, ':root[data-series="reflections"][data-readability][data-theme="dark"]');
  same("readability dark", decls(L, ':root[data-readability][data-theme="dark"] .ref-panel'), "--muted", srcDark, "--muted");
  same("readability OS dark", decls(L, ':root[data-readability]:not([data-theme="light"]) .ref-panel', { media: DARK_MEDIA }), "--muted", srcDark, "--muted");
});

test("each copied block says the same thing in its OS-dark and data-theme-dark rules", () => {
  for (const [os, data] of [[':root:not([data-theme="light"]) .hub-frame', ':root[data-theme="dark"] .hub-frame'], [':root:not([data-theme="light"]) .ref-panel', ':root[data-theme="dark"] .ref-panel']]) {
    const a = decls(L, os, { media: DARK_MEDIA }), b = decls(L, data);
    assert.deepEqual(Object.fromEntries(Object.entries(a).map(([k, v]) => [k, norm(v)])), Object.fromEntries(Object.entries(b).map(([k, v]) => [k, norm(v)])), os + " vs " + data);
  }
});

test("the parser itself: a deliberate drift is caught", () => {
  const broken = read("learning/assets/learning.css").replace(/(\.hub-frame\s*\{[^}]*--paper:\s*)#fafaf8/i, "$1#fafaf9");
  const hub = decls(parseCss(broken), ".hub-frame");
  assert.notEqual(norm(hub["--paper"]), norm(decls(S, ":root", { which: "first" })["--bg"]), "the mutation did not change the parsed value");
});
