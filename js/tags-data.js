// tags-data.js
// The ONE controlled tag vocabulary, shared by js/projects-data.js and
// js/experience-data.js. Entries in both files store tag IDS from this list;
// the pill and filter-button LABEL comes from translations.js via `key`, so a
// tag reads correctly in both languages and a language switch cannot reset an
// active filter (filter state stores ids, never labels).
//
//   id   stable, url-safe, never displayed — what the data files reference
//   key  i18n key → EN + ES label
//
// Order here is the order the projects.html filter row shows tags in (narrowed
// to tags at least one listed entry carries).
//
// Loaded on projects.html, experience.html and index.html — always BEFORE the
// data files and before js/data-helpers.js.
//
// SCAFFOLD NOTE: todo-a … todo-f are the six project placeholders from the old
// PROJECT_TAGS list. The ten ids after them carry the labels the experience
// entries used as free strings before tags were shared; their ES labels are
// "TODO "-prefixed until the vocabulary is settled in the content interviews
// (plan.md open decision #2 on both page specs).
const TAGS = [
  { id: "todo-a", key: "tagTodoA" },
  { id: "todo-b", key: "tagTodoB" },
  { id: "todo-c", key: "tagTodoC" },
  { id: "todo-d", key: "tagTodoD" },
  { id: "todo-e", key: "tagTodoE" },
  { id: "todo-f", key: "tagTodoF" },

  // Carried over from experience-data.js — still placeholders.
  { id: "engineering", key: "tagEngineering" },
  { id: "rd", key: "tagRd" },
  { id: "als", key: "tagAls" },
  { id: "machining", key: "tagMachining" },
  { id: "prototyping", key: "tagPrototyping" },
  { id: "fabrication", key: "tagFabrication" },
  { id: "data-analysis", key: "tagDataAnalysis" },
  { id: "grading", key: "tagGrading" },
  { id: "dynamics", key: "tagDynamics" },
  { id: "research", key: "tagResearch" }
];
