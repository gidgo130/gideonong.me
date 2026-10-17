// run.js — run the /learning browser suites: all of them, or the ones named on the command line.
//   node learning/workshop/tests/run.js                 every suite, in the order below
//   node learning/workshop/tests/run.js pages hub       a subset
//   node learning/workshop/tests/run.js --list          the suite names and what each covers
// Starts one static server for the repo (lib.serve) and hands it to every suite through
// LEARN_BASE, runs them one after another (they share the browser cache and :5599), echoes their
// output, and ends with a table. Exit code 1 if any suite fails or crashes. Needs the external
// Playwright install (README.md here); Node built-ins only in the repo.
"use strict";
const { spawn } = require("child_process");
const path = require("path");
const L = require("./lib");

const SUITES = [
  ["pages", "every page: trailing slash, noindex + OG, feedback slot, registry text rendered, a11y, 375 px matrix, from disk"],
  ["hub", "learning/index.html: frame and bands matrix, contrast, faces, token sync by rendered values, hidden band, fonts, cap, sticky bar"],
  ["reflections", "every book / reflection page: registry rendering, math, chart text, overlaps, twins, resize, controls, contrast, balanced-plant specifics"],
  ["theme-dashes", "dash and dot geometry on screen in Chromium and Firefox (synthetic page), and per chart on every page"],
  ["feedback-widget", "the feedback widget end to end with a mocked /api/feedback: flows, strings EN/ES, owner mode, dry-run, file:, layout, contrast"],
  ["offline-stage", "build.ps1 -StageOnly, then the staged copy from file:// online and with the network cut"],
];

const args = process.argv.slice(2);
if (args.includes("--list")) { for (const [n, d] of SUITES) console.log(`${n.padEnd(16)} ${d}`); process.exit(0); }
const wanted = args.filter((a) => !a.startsWith("--"));
const unknown = wanted.filter((w) => !SUITES.some(([n]) => n === w));
if (unknown.length) { console.error("unknown suite(s): " + unknown.join(", ") + "\nknown: " + SUITES.map(([n]) => n).join(", ")); process.exit(2); }
const chosen = SUITES.filter(([n]) => !wanted.length || wanted.includes(n));

try { L.pw(); } catch (e) { console.error(e.message); process.exit(2); }
const { base, close } = L.serve();
// The suites run as child processes, asynchronously: this process's event loop must stay free so
// the server above can answer them (spawnSync would block it and every page.goto would time out).
function runSuite(name) {
  return new Promise((resolve) => {
    const file = path.join(__dirname, name + ".js");
    console.log(`\n${"=".repeat(78)}\n${name}  (${file})\n${"=".repeat(78)}`);
    const t0 = Date.now();
    let stdout = "";
    const child = spawn(process.execPath, [file, ...args.filter((a) => a.startsWith("--") && a !== "--list")], { env: Object.assign({}, process.env, { LEARN_BASE: base }) });
    child.stdout.on("data", (d) => { stdout += d; process.stdout.write(d); });
    child.stderr.on("data", (d) => process.stderr.write(d));
    child.on("close", (status) => {
      const m = /(\d+) passed, (\d+) failed\s*$/m.exec(stdout);
      resolve({ name, status, passed: m ? +m[1] : null, failed: m ? +m[2] : null, seconds: Math.round((Date.now() - t0) / 1000), crashed: status !== 0 && !m });
    });
  });
}
(async () => {
const results = [];
for (const [name] of chosen) results.push(await runSuite(name));
close();
console.log(`\n${"=".repeat(78)}\nsuite             passed  failed  time\n${"-".repeat(78)}`);
let bad = 0;
for (const r of results) {
  const state = r.crashed ? "CRASHED" : r.failed ? "FAILED" : "ok";
  if (r.crashed || r.failed) bad++;
  console.log(`${r.name.padEnd(17)} ${String(r.passed == null ? "-" : r.passed).padStart(6)}  ${String(r.failed == null ? "-" : r.failed).padStart(6)}  ${String(r.seconds + "s").padStart(5)}  ${state}`);
}
console.log(`${"-".repeat(78)}\n${results.length - bad} of ${results.length} suites clean; ${results.reduce((a, r) => a + (r.passed || 0), 0)} checks passed, ${results.reduce((a, r) => a + (r.failed || 0), 0)} failed`);
process.exit(bad ? 1 : 0);
})();
