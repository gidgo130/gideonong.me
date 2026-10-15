// check-staged-data.js — run by .githooks/pre-commit before every commit.
// The repo is public on GitHub, so analytics data and secrets must never be
// committed. Checks the STAGED version of each added / changed file (not the
// working copy) and exits 1, blocking the commit, on any hit:
//
//   a  *.ndjson / *.jsonl anywhere; *.csv / *.csv.gz / *.tsv under scripts/analytics/;
//      goatcounter*.csv(.gz) anywhere
//   b  a CSV (or .csv.gz) anywhere whose first line is GoatCounter's export header
//   c  a collector record in any text file: "visitor" followed by a 16-hex value
//   d  a notebook under scripts/ with any cell output or execution count
//   e  a token-looking value: a Bearer header with a literal token, one of the
//      secret env names set to a 20+ character literal, or a redis:// URL with
//      a password in it
//
// Docs and comments use placeholders (<16 hex>, <ANALYTICS_EXPORT_TOKEN>), which
// these rules skip. For a genuine false positive: git commit --no-verify.
// `node scripts/check-staged-data.js --all` runs the same rules over every
// tracked file (the index), e.g. after changing a rule.
// Node built-ins only. CLAUDE.md → Analytics.
"use strict";

const { execFileSync } = require("child_process");
const zlib = require("zlib");

const MAX_SCAN = 20 * 1024 * 1024; // content rules read at most this much per file

const RECORD = /"visitor"\s*:\s*"[0-9a-f]{16}"/;
// GoatCounter writes the version glued to the first field ("2Path,Title,Event,…",
// exportcsv.go); its docs show "2,Path". Match both.
const GC_HEADER = /^﻿?\d+,?Path,Title,Event,/;
const SECRET_RULES = [
  { re: /Bearer\s+[A-Za-z0-9._~+\/=-]{20,}/, what: "a Bearer header with a literal token" },
  { re: /\b(ANALYTICS_EXPORT_TOKEN|ANALYTICS_SALT_SECRET|KV_REST_API_TOKEN|KV_REST_API_READ_ONLY_TOKEN|UPSTASH_REDIS_REST_TOKEN)\b["']?\s*[:=]\s*["']?[A-Za-z0-9_\-]{20,}/, what: "a secret env var set to a literal value" },
  { re: /rediss?:\/\/[^\s:@\/]*:[^\s@\/<]{20,}@/, what: "a redis:// URL with a password" },
];

function git(args, asBuffer) {
  return execFileSync("git", args, { encoding: asBuffer ? "buffer" : "utf8", maxBuffer: 256 * 1024 * 1024 });
}

const staged = (process.argv.includes("--all")
  ? git(["ls-files", "-z"])
  : git(["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"])).split("\0").filter(Boolean);
const problems = [];
const flag = (file, rule, why) => problems.push(`  ${file}\n      rule ${rule}: ${why}`);

for (const file of staged) {
  const lower = file.toLowerCase();
  const name = lower.split("/").pop();

  // a — by name
  if (/\.(ndjson|jsonl)$/.test(lower)) flag(file, "a", "NDJSON / JSONL data file");
  else if (/^scripts\/analytics\//.test(lower) && /\.(csv|csv\.gz|tsv)$/.test(lower)) flag(file, "a", "data file under scripts/analytics/");
  else if (/^goatcounter.*\.csv(\.gz)?$/.test(name)) flag(file, "a", "GoatCounter export");

  let buf;
  try { buf = git(["show", ":" + file], true); } catch (e) { continue; }
  if (buf.length > MAX_SCAN) buf = buf.subarray(0, MAX_SCAN);
  if (lower.endsWith(".gz")) {
    try { buf = zlib.gunzipSync(buf, { maxOutputLength: MAX_SCAN }); } catch (e) { /* not gzip, or too big: scan as is */ }
  }
  if (buf.subarray(0, 8000).includes(0)) continue; // binary (images, PDFs): no content rules
  const text = buf.toString("utf8");

  // b — GoatCounter header in a CSV
  if (/\.csv(\.gz)?$/.test(lower) && GC_HEADER.test(text)) flag(file, "b", "GoatCounter export header");

  // c — collector record
  if (RECORD.test(text)) flag(file, "c", 'contains a collector record ("visitor" + 16 hex)');

  // d — notebook outputs under scripts/
  if (/^scripts\/.*\.ipynb$/.test(lower)) {
    try {
      const nb = JSON.parse(text);
      const dirty = (nb.cells || []).filter((c) => (c.outputs && c.outputs.length) || (c.execution_count !== undefined && c.execution_count !== null));
      if (dirty.length) flag(file, "d", `${dirty.length} cell(s) with outputs or an execution count: regenerate it (python scripts/analytics/make-notebook.py)`);
    } catch (e) {
      flag(file, "d", "notebook is not valid JSON");
    }
  }

  // e — secrets
  for (const rule of SECRET_RULES) {
    if (rule.re.test(text)) { flag(file, "e", rule.what); break; }
  }
}

if (problems.length) {
  console.error("\npre-commit: blocked — this would publish analytics data or a secret (the repo is public):\n");
  console.error(problems.join("\n"));
  console.error("\nUnstage the file (git restore --staged <file>). Data belongs in the gitignored");
  console.error("scripts/analytics/data/ or in Colab only. For a genuine false positive: git commit --no-verify\n");
  process.exit(1);
}
