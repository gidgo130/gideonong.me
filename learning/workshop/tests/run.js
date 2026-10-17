// run.js — run the /learning browser suites: all of them, or the ones named on the command line.
//   node learning/workshop/tests/run.js                 every suite, in the order below
//   node learning/workshop/tests/run.js pages hub       a subset
//   node learning/workshop/tests/run.js --quick         the smallest matrix (375 px, light, plain, EN): for iterating
//   node learning/workshop/tests/run.js --parallel 3    up to three suites at once, each in its own browser
//   node learning/workshop/tests/run.js --list          the suite names and what each covers
// Starts one static server for the repo (lib.serve) and hands it to every suite through
// LEARN_BASE, runs them as child processes (asynchronously: this process's event loop must stay
// free so the server can answer them), echoes their output and ends with a table. In parallel mode
// a suite's output is printed when it finishes, so the log stays readable. Every other --flag is
// forwarded to the suites (--quick is read by lib.js). Exit code 1 if any suite fails or crashes.
// Needs the external Playwright install (README.md here); Node built-ins only in the repo.
"use strict";
const { spawn } = require("child_process");
const path = require("path");
const L = require("./lib");

const SUITES = [
  ["pages", "every page: trailing slash, noindex + OG, feedback slot, registry text rendered, a11y, view settings, skip link, forced colors, highlights, decks and play pages, 375 px matrix, from disk"],
  ["hub", "learning/index.html: frame and bands matrix, contrast, faces, token sync by rendered values, hidden band, fonts, cap, sticky bar"],
  ["reflections", "every book / reflection page: registry rendering, math, chart text, overlaps, twins, resize, controls, contrast, balanced-plant specifics"],
  ["theme-dashes", "dash and dot geometry on screen in Chromium and Firefox (synthetic page), and per chart on every page"],
  ["feedback-widget", "the feedback widget end to end with a mocked /api/feedback: flows, strings EN/ES, owner mode, dry-run, file:, layout, contrast"],
  ["offline-stage", "build.ps1 -StageOnly, then the staged copy from file:// online and with the network cut"],
];

const args = process.argv.slice(2);
if (args.includes("--list")) { for (const [n, d] of SUITES) console.log(`${n.padEnd(16)} ${d}`); process.exit(0); }
let parallel = 1;
const forwarded = [];
const wanted = [];
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === "--parallel") { parallel = Math.max(1, parseInt(args[++i], 10) || 1); }
  else if (a.startsWith("--parallel=")) { parallel = Math.max(1, parseInt(a.slice(11), 10) || 1); }
  else if (a.startsWith("--")) forwarded.push(a);
  else wanted.push(a);
}
const unknown = wanted.filter((w) => !SUITES.some(([n]) => n === w));
if (unknown.length) { console.error("unknown suite(s): " + unknown.join(", ") + "\nknown: " + SUITES.map(([n]) => n).join(", ")); process.exit(2); }
const chosen = SUITES.filter(([n]) => !wanted.length || wanted.includes(n)).map(([n]) => n);

try { L.pw(); } catch (e) { console.error(e.message); process.exit(2); }
const { base, close } = L.serve();
const live = parallel === 1;   // sequential: stream each suite's output as it comes
console.log(`${chosen.length} suite(s)${L.quick ? ", --quick matrix" : ""}${parallel > 1 ? `, ${parallel} at a time` : ""}; server ${base}`);

function runSuite(name) {
  return new Promise((resolve) => {
    const file = path.join(__dirname, name + ".js");
    const banner = `\n${"=".repeat(78)}\n${name}  (${file})\n${"=".repeat(78)}\n`;
    if (live) process.stdout.write(banner); else console.log(`  started ${name}`);
    const t0 = Date.now();
    let stdout = "", stderr = "";
    const child = spawn(process.execPath, [file, ...forwarded], { env: Object.assign({}, process.env, { LEARN_BASE: base }) });
    child.stdout.on("data", (d) => { stdout += d; if (live) process.stdout.write(d); });
    child.stderr.on("data", (d) => { stderr += d; if (live) process.stderr.write(d); });
    child.on("close", (status) => {
      const m = /(\d+) passed, (\d+) failed\s*$/m.exec(stdout);
      if (!live) { process.stdout.write(banner + stdout); if (stderr) process.stderr.write(stderr); }
      resolve({ name, status, passed: m ? +m[1] : null, failed: m ? +m[2] : null, seconds: Math.round((Date.now() - t0) / 1000), crashed: status !== 0 && !m });
    });
  });
}
(async () => {
  const results = [];
  const queue = chosen.slice();
  async function worker() { while (queue.length) results.push(await runSuite(queue.shift())); }
  await Promise.all(Array.from({ length: Math.min(parallel, chosen.length) }, worker));
  results.sort((a, b) => chosen.indexOf(a.name) - chosen.indexOf(b.name));
  close();
  console.log(`\n${"=".repeat(78)}\nsuite             passed  failed  time\n${"-".repeat(78)}`);
  let bad = 0;
  for (const r of results) {
    const state = r.crashed ? "CRASHED" : r.failed ? "FAILED" : "ok";
    if (r.crashed || r.failed) bad++;
    console.log(`${r.name.padEnd(17)} ${String(r.passed == null ? "-" : r.passed).padStart(6)}  ${String(r.failed == null ? "-" : r.failed).padStart(6)}  ${String(r.seconds + "s").padStart(5)}  ${state}`);
  }
  console.log(`${"-".repeat(78)}\n${results.length - bad} of ${results.length} suites clean; ${results.reduce((a, r) => a + (r.passed || 0), 0)} checks passed, ${results.reduce((a, r) => a + (r.failed || 0), 0)} failed${L.quick ? " (--quick matrix)" : ""}`);
  process.exit(bad ? 1 : 0);
})();
