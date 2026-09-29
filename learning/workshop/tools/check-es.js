// check-es.js — /learning ES strings check. Run from the repo root: node learning/workshop/tools/check-es.js
// (optional argument: path to learning/; defaults to the learning/ folder this file sits in)
// For each strings file: same key set in en/es, same {placeholders}, same tag counts in *Html,
// every chip has an es phrase, and (advisory) digits with a decimal point in es text.
const fs = require("fs"), path = require("path"), vm = require("vm");
const root = process.argv[2] || path.join(__dirname, "..", "..");
const files = ["assets/strings-common.js", "strings.js",
  ...fs.readdirSync(path.join(root, "fits")).map(s => `fits/${s}/strings.js`)];
let problems = 0;
const bad = (f, msg) => { problems++; console.log(`  FAIL ${msg}`); };
const count = (s, re) => (s.match(re) || []).sort().join(",");

for (const f of files) {
  const ctx = { window: {} };
  vm.runInNewContext(fs.readFileSync(path.join(root, f), "utf8"), ctx);
  const S = ctx.window.LEARN_STRINGS_COMMON || ctx.window.LEARN_STRINGS;
  const en = S.en, es = S.es, ek = Object.keys(en), sk = Object.keys(es);
  console.log(`${f}: ${ek.length} en keys, ${sk.length} es keys`);
  ek.filter(k => !(k in es)).forEach(k => bad(f, `missing in es: ${k}`));
  sk.filter(k => !(k in en)).forEach(k => bad(f, `extra in es: ${k}`));
  for (const k of ek.filter(k => k in es)) {
    const pe = count(en[k], /\{\w+\}/g), ps = count(es[k], /\{\w+\}/g);
    if (pe !== ps) bad(f, `${k} placeholders en [${pe}] es [${ps}]`);
    if (/Html$/.test(k)) {
      const te = count(en[k], /<\/?[a-z]+>/g), ts = count(es[k], /<\/?[a-z]+>/g);
      if (te !== ts) bad(f, `${k} tags en [${te}] es [${ts}]`);
    } else if (/<\/?[a-z]+>/.test(es[k])) bad(f, `${k} has markup but is not an *Html key`);
    const dot = es[k].match(/\d\.\d/g);
    if (dot) console.log(`  note ${k}: decimal point in es text: ${dot.join(" ")}`);
  }
  (S.chips || []).forEach((c, i) => { if (!c.phrase.es) bad(f, `chip ${i} (${c.phrase.en}) has no es phrase`); });
}
console.log(problems ? `\n${problems} problem(s)` : "\nAll files OK");
process.exitCode = problems ? 1 : 0;
