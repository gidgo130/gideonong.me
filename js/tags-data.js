// tags-data.js
// The ONE controlled tag vocabulary, shared by js/projects-data.js and
// js/experience-data.js. Entries in both files store tag IDS from this list;
// the pill LABEL comes from translations.js via `key`, so a tag reads
// correctly in both languages and a language switch cannot change the
// ?tag=<id> filter state (which stores ids, never labels).
//
//   id   stable, url-safe, never displayed — what the data files reference
//        and what projects.html?tag=<id> carries
//   key  i18n key → EN + ES label (tag<IdCamel>)
//
// Vocabulary settled in the 2026-09-27 content interview (staging/copy-en.md
// § Tags). Adding a tag = one line here + tag<IdCamel> in translations.js.
//
// Loaded on every page that renders projects or bands — always BEFORE the
// data files and before js/data-helpers.js.
const TAGS = [
  { id: "python", key: "tagPython" },
  { id: "matlab", key: "tagMatlab" },
  { id: "machine-learning", key: "tagMachineLearning" },
  { id: "data-analysis", key: "tagDataAnalysis" },
  { id: "automation", key: "tagAutomation" },
  { id: "cad", key: "tagCad" },
  { id: "fabrication", key: "tagFabrication" },
  { id: "solid-mechanics", key: "tagSolidMechanics" },
  { id: "thermo-fluids", key: "tagThermoFluids" },
  { id: "transportation", key: "tagTransportation" },
  { id: "leadership", key: "tagLeadership" }
];
