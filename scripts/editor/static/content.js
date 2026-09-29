/* Content page — Phase 2: projects, experience, tags (vanilla JS, no build step).
   Keys never appear here: every text field is (file, slug, field, lang) and the
   server resolves or invents the key. */
(function () {
  "use strict";
  const { token, $, el, api, toast, setBanner, clearBanner, banners, renderDiff } = window.Editor;

  const state = { data: null, tab: "projects", selected: { projects: null, experience: null, tags: null, about: "sites" }, unsaved: false };
  const FILE_LABEL = { projects: "project", experience: "role", tags: "tag", about: "entry" };
  // the About lists (js/about-data.js): inline EN/ES fields, no translations keys
  const ABOUT_PAIRS = {
    books: [["titleEN", "titleES", "Title"], ["descEN", "descES", "Description"]],
    faq: [["questionEN", "questionES", "Question"], ["answerEN", "answerES", "Answer"]],
    sites: [["labelEN", "labelES", "Label"], ["descEN", "descES", "Description"]],
  };
  // text field → where the entry stores its key (mirrors core/site/keys.py)
  const TEXT_PATH = {
    projects: { title: ["titleKey"], desc: ["descKey"], longDesc: ["longDescKey"], search: ["searchTextKey"], imageAlt: ["imageAlt"], thumbAlt: ["thumbAltKey"], "page.credit": ["page", "creditKey"] },
    experience: { role: ["roleKey"], org: ["orgKey"], orgShort: ["orgShortKey"], imageAlt: ["imageAltKey"] },
    tags: { label: ["key"] },
  };
  const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

  // ---------------------------------------------------------------- helpers
  function pill(cls, text, title) { return el("span", { class: "pill " + cls, title: title || null }, text); }
  function getPath(obj, path) { let c = obj; for (const p of path) { if (c == null) return undefined; c = c[p]; } return c; }
  function keyOf(file, entry, field) {
    const m = field.match(/^(gallery|page\.sections|page\.facts|page\.photos|bullets)\.(\d+)\.?(\w*)$/);
    if (m) {
      const idx = parseInt(m[2], 10) - 1;
      if (m[1] === "bullets") return getPath(entry, ["bulletKeys", idx]);
      const prop = { alt: "altKey", heading: "headingKey", body: "bodyKey", label: "labelKey", value: "valueKey" }[m[3]];
      return getPath(entry, m[1].split(".").concat([idx, prop]));
    }
    return getPath(entry, TEXT_PATH[file][field]);
  }
  function textOf(file, entry, field, lang) { const k = keyOf(file, entry, field); return k ? (state.data.texts[lang][k] ?? "") : ""; }
  function entryOf(file, slug) { return (state.data[file] || []).find((e) => (e.slug || e.id) === slug); }
  function issuesFor(file, slug) { return state.data.issues[file + ":" + slug] || []; }
  function autosize(ta) { ta.style.height = "auto"; ta.style.height = Math.max(30, ta.scrollHeight + 2) + "px"; }

  // ---------------------------------------------------------------- api
  function applyReply(r, fullForm) {
    if (!r || r.ok === false) { toast("Rejected: " + (r && r.error), 6000); return false; }
    const { ok, result, ...rest } = r;
    state.data = rest;
    renderList();
    renderCounts();
    if (fullForm) renderForm(); else refreshIssues();
    return r;  // truthy; callers that need the op's result read r.result
  }
  async function call(path, body, fullForm) {
    try { return applyReply(await api(path, { method: "POST", body }), fullForm); }
    catch (e) { toast("Failed: " + e.message, 6000); return false; }
  }
  const pendingText = {};
  function queueText(file, slug, field, lang, value) {
    const k = [file, slug, field, lang].join("|");
    clearTimeout(pendingText[k]);
    pendingText[k] = setTimeout(() => call("/api/content/text", { file, slug, field, lang, value }, false), 350);
  }
  const setField = (file, slug, path, value) => call("/api/content/field", { file, slug, path, value }, true);
  const delField = (file, slug, path) => call("/api/content/field", { file, slug, path, delete: true }, true);

  // ---------------------------------------------------------------- list
  function renderList() {
    const box = $("#list");
    box.replaceChildren();
    const file = state.tab;
    for (const a of document.querySelectorAll("#subtabs a")) a.classList.toggle("active", a.dataset.tab === file);
    if (file === "about") {
      const a = state.data.about;
      for (const lst of Object.keys(a.labels)) {
        const entries = a.lists[lst] || [];
        const shown = a.shown[a.sections[lst]];
        const errs = entries.reduce((n, e) => n + issuesFor("about", e.id).filter((i) => i.level === "error").length, 0);
        const row = el("a", { href: "#about/" + lst, class: "entry" + (state.selected.about === lst ? " active" : "") + (entries.some((e) => e._draft) || a.shownDrafts[a.sections[lst]] !== undefined || a.orderDrafts.includes(lst) ? " has-draft" : "") + (errs ? " has-error" : ""), onclick: (ev) => { ev.preventDefault(); select("about", lst); } });
        row.append(el("div", { class: "entry-title" }, a.labels[lst]), el("div", { class: "entry-meta" }, `${entries.length} entr${entries.length === 1 ? "y" : "ies"} · ${shown ? "shown on the site" : "hidden on the site"}`));
        const pills = el("div", { class: "entry-pills" });
        if (errs) pills.append(pill("st-todo", errs + " error" + (errs > 1 ? "s" : "")));
        row.append(pills);
        box.append(row);
      }
      box.append(el("p", { class: "muted small" }, "js/about-data.js and the hidden attribute of each block in about.html."));
      return;
    }
    if (file === "images") {
      box.append(el("p", { class: "muted small" }, "Every file under assets/images/ with what uses it."));
      const pending = Object.keys(state.data.pendingImages || {});
      if (pending.length) box.append(el("h3", null, "Pending imports"), ...pending.map((p) => el("div", { class: "entry has-draft" }, el("div", { class: "entry-title small" }, p.replace(/^assets\/images\//, "")))));
      const removed = state.data.removedImages || [];
      if (removed.length) box.append(el("h3", null, "Removed on save"), ...removed.map((p) => el("div", { class: "entry deleted" }, el("div", { class: "entry-title small" }, p.replace(/^assets\/images\//, "")))));
      return;
    }
    box.append(el("button", { type: "button", class: "primary wide", onclick: openAdd }, "Add " + FILE_LABEL[file] + "…"));
    const items = state.data[file] || [];
    let lastTier = null;
    for (const e of items) {
      const slug = e.slug || e.id;
      const tier = e._tier || "";
      if (file !== "tags" && tier !== lastTier) { box.append(el("h3", null, { featured: "Featured", index: "Index", unlisted: "Unlisted", hidden: "Hidden", visible: "Shown", other: "Other" }[tier] || tier)); lastTier = tier; }
      const iss = issuesFor(file, slug);
      const errs = iss.filter((i) => i.level === "error").length;
      const row = el("a", { href: "#" + file + "/" + slug, class: "entry" + (state.selected[file] === slug ? " active" : "") + (e._draft ? " has-draft" : "") + (errs ? " has-error" : ""), onclick: (ev) => { ev.preventDefault(); select(file, slug); } });
      const title = file === "tags" ? e.id : textOf(file, e, file === "projects" ? "title" : "role", "en") || slug;
      row.append(el("div", { class: "entry-title" }, title));
      const meta = [];
      if (file === "projects") meta.push((e.context || "") + " · " + (e._meta ? e._meta.datesEn : ""));
      if (file === "experience") meta.push((e._meta ? e._meta.datesEn : "") + (e.status === "current" ? " · current" : ""));
      if (file === "tags") meta.push(state.data.texts.en[e.key] + " / " + state.data.texts.es[e.key] + " · used " + e.uses + "×");
      row.append(el("div", { class: "entry-meta" }, meta.join("")));
      const pills = el("div", { class: "entry-pills" });
      if (e._draft) pills.append(pill("draft", "draft"));
      const renamedFrom = ((state.data.renamed || {})[file] || {})[slug];
      if (renamedFrom) pills.append(pill("draft", "renamed from " + renamedFrom));
      if (errs) pills.append(pill("st-todo", errs + " error" + (errs > 1 ? "s" : "")));
      else if (iss.length) pills.append(pill("st-same", iss.length + " warning" + (iss.length > 1 ? "s" : "")));
      if (file === "projects" && e.pinned) pills.append(pill("", "pinned"));
      row.append(pills);
      box.append(row);
    }
    for (const slug of (state.data.deleted[file] || [])) box.append(el("div", { class: "entry deleted" }, el("div", { class: "entry-title" }, slug), el("div", { class: "entry-meta" }, "will be deleted on save")));
  }
  function select(file, slug) { state.selected[file] = slug; location.hash = file + "/" + slug; renderList(); renderForm(); }

  // ---------------------------------------------------------------- form widgets
  function textPair(file, slug, entry, field, label, opts) {
    const o = opts || {};
    const wrap = el("div", { class: "pair" }, el("div", { class: "pair-label" }, label, o.note ? el("span", { class: "muted small" }, " " + o.note) : null));
    const cols = el("div", { class: "cols" });
    for (const lang of ["en", "es"]) {
      const ta = el("textarea", { rows: 1, lang, spellcheck: "true" });
      ta.value = textOf(file, entry, field, lang);
      ta.placeholder = lang.toUpperCase();
      ta.addEventListener("input", () => { autosize(ta); queueText(file, slug, field, lang, ta.value); });
      cols.append(el("div", null, el("label", null, lang.toUpperCase()), ta));
    }
    wrap.append(cols);
    return wrap;
  }
  function selectField(file, slug, entry, path, label, options, opts) {
    const o = opts || {};
    const sel = el("select");
    if (o.allowEmpty) sel.append(el("option", { value: "" }, o.emptyLabel || "—"));
    for (const [v, l] of options) sel.append(el("option", { value: v }, l));
    const cur = getPath(entry, path);
    sel.value = cur == null ? "" : String(cur);
    sel.addEventListener("change", () => setField(file, slug, path, o.nullable && sel.value === "" ? null : sel.value));
    return el("label", { class: "field" }, el("span", null, label), sel);
  }
  function checkField(file, slug, entry, path, label, opts) {
    const cb = el("input", { type: "checkbox" });
    cb.checked = !!getPath(entry, path);
    cb.addEventListener("change", () => (opts && opts.onchange ? opts.onchange(cb.checked) : setField(file, slug, path, cb.checked)));
    return el("label", { class: "chk" }, cb, " " + label);
  }
  function inputField(file, slug, entry, path, label, opts) {
    const o = opts || {};
    const inp = el("input", { type: "text", placeholder: o.placeholder || "" });
    const cur = getPath(entry, path);
    inp.value = cur == null ? "" : String(cur);
    inp.addEventListener("change", () => {
      let v = inp.value.trim();
      if (o.number) { if (v === "") return o.removeWhenEmpty ? delField(file, slug, path) : setField(file, slug, path, null); v = Number(v); if (Number.isNaN(v)) { toast("Not a number"); return; } }
      setField(file, slug, path, v);
    });
    return el("label", { class: "field" }, el("span", null, label), inp);
  }
  function imageField(file, slug, entry, path, label, altField, preset) {
    const sel = el("select");
    sel.append(el("option", { value: "" }, "(none)"));
    for (const img of state.data.images) sel.append(el("option", { value: img.path }, img.path.replace(/^assets\/images\//, "") + (img.pending ? " (pending)" : "")));
    const cur = getPath(entry, path) || "";
    if (cur && !state.data.images.some((i) => i.path === cur)) sel.append(el("option", { value: cur }, cur + " (missing)"));
    sel.value = cur;
    sel.addEventListener("change", () => setField(file, slug, path, sel.value));
    const wrap = el("label", { class: "field" }, el("span", null, label), sel);
    if (altField) wrap.append(el("button", { type: "button", class: "ghost small", onclick: (ev) => { ev.preventDefault(); openImport(file, slug, altField, preset || "main"); } }, "Import…"));
    return wrap;
  }

  // ---------------------------------------------------------------- image import
  const importCtx = {};
  function openImport(file, slug, altField, preset) {
    Object.assign(importCtx, { file, slug, altField });
    const about = file === "about";
    $("#importAltEnField").hidden = about; $("#importAltEsField").hidden = about;
    $("#importNote").textContent = about ? `Cover for book “${slug}” — saved under ${state.data.about.coverDir}/ (covers are decorative; no alt text)` : `For ${FILE_LABEL[file]} “${slug}” → ${altField.replace(/\.(\d+)\.alt$/, " $1").replace("imageAlt", "main image").replace("thumbAlt", "thumbnail")} — saved under assets/images/${file}/${slug}/`;
    const sel = $("#importPreset");
    sel.replaceChildren(...Object.entries(state.data.presets || {}).map(([k, v]) => el("option", { value: k }, v)));
    sel.value = preset;
    $("#importFile").value = ""; $("#importName").value = ""; $("#importAltEn").value = ""; $("#importAltEs").value = ""; $("#importReplace").checked = false;
    $("#importDlg").showModal();
  }
  $("#importFile").addEventListener("change", () => {
    const f = $("#importFile").files[0];
    if (f && !$("#importName").value) $("#importName").value = f.name.replace(/\.[^.]+$/, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    if (f && /\.png$/i.test(f.name) && $("#importPreset").value === "main") $("#importPreset").value = "asis";
  });
  async function doImport() {
    const f = $("#importFile").files[0];
    if (!f) { toast("Pick a file first."); return; }
    const fd = new FormData();
    fd.append("image", f, f.name);
    fd.append("file", importCtx.file); fd.append("slug", importCtx.slug); fd.append("field", importCtx.altField);
    fd.append("preset", $("#importPreset").value); fd.append("name", $("#importName").value.trim());
    fd.append("altEn", $("#importAltEn").value.trim()); fd.append("altEs", $("#importAltEs").value.trim());
    fd.append("replace", $("#importReplace").checked ? "1" : "0");
    $("#importGo").disabled = true;
    try {
      const r = await api("/api/content/images/import", { method: "POST", body: fd });
      if (!r || r.ok === false) { toast("Import refused: " + (r && r.error), 7000); return; }
      const res = r.result;
      applyReply(r, true);
      $("#importDlg").close();
      toast(`Imported ${res.path} (${res.width} × ${res.height}, ${res.kb} KB${res.hadGps ? "; GPS data removed" : res.hadExif ? "; camera data removed" : ""}${res.transposed ? "; rotated upright" : ""}). It shows in the preview now and is written on save.`, 8000);
    } catch (e) { toast("Import failed: " + e.message, 7000); }
    finally { $("#importGo").disabled = false; }
  }

  // ---------------------------------------------------------------- images panel
  let imagesRender = 0;
  async function renderImagesPanel(box) {
    const seq = ++imagesRender;
    box.append(el("h2", null, "Images ", el("span", { class: "muted small" }, "assets/images/ — existing files are never re-encoded")));
    let d;
    try { d = await api("/api/content/images"); } catch (e) { box.append(el("p", null, "Could not list images: " + e.message)); return; }
    if (seq !== imagesRender) return;  // a newer render started while the list was loading
    state.data.presets = d.presets;
    const filter = el("div", { class: "chips" });
    const table = el("table", { class: "docs" });
    let mode = "all";
    function draw() {
      table.replaceChildren(el("tr", null, el("th", null, "File"), el("th", null, "Size"), el("th", null, "Used by"), el("th", null, "Notes"), el("th")));
      let n = 0;
      for (const img of d.images) {
        const unused = !img.users.length;
        if (mode === "unused" && !unused) continue;
        if (mode === "warnings" && !img.warnings.length) continue;
        n++;
        const info = img.info || {};
        const notes = el("td", null, ...img.warnings.map((w) => el("div", { class: "warn-text" }, w)));
        if (img.pending) notes.append(pill("draft", img.pending === "replace" ? "replaces on save" : "added on save"));
        if (img.removed) notes.append(pill("st-todo", "removed on save"));
        const act = el("td", { class: "actions" });
        if (unused && !img.removed && !img.pending) act.append(el("button", { type: "button", class: "ghost danger", onclick: async () => { if (confirm("Remove " + img.path + "?\n\nIt moves to the backup set on Review & save.")) { const ok = await call("/api/content/images/delete", { path: img.path }, false); if (ok) renderForm(); } } }, "Remove"));
        if (img.pending) act.append(el("button", { type: "button", class: "ghost", onclick: async () => { const ok = await call("/api/content/images/delete", { path: img.path }, false); if (ok) renderForm(); } }, "Drop import"));
        table.append(el("tr", { class: img.removed ? "deleted" : "" },
          el("td", null, el("code", null, img.path.replace(/^assets\/images\//, ""))),
          el("td", null, info.width ? `${info.width} × ${info.height} · ${info.kb} KB` : "?"),
          el("td", { class: "small" }, img.users.length ? img.users.join(", ") : el("span", { class: "muted" }, "not used")),
          notes, act));
      }
      if (!n) table.append(el("tr", null, el("td", { colspan: 5, class: "muted center" }, "Nothing to show.")));
    }
    const counts = { all: d.images.length, unused: d.images.filter((i) => !i.users.length).length, warnings: d.images.filter((i) => i.warnings.length).length };
    for (const [id, label] of [["all", "All"], ["unused", "Unused"], ["warnings", "With warnings"]]) {
      filter.append(el("button", { type: "button", class: "chip" + (mode === id ? " active" : ""), onclick: (ev) => { mode = id; for (const c of filter.children) c.classList.toggle("active", c === ev.currentTarget); draw(); } }, `${label} ${counts[id]}`));
    }
    box.append(el("p", { class: "muted small" }, "Import new images from a project or role form (“Import…” beside each image field). Remove only files nothing uses; they move to the backup set on save."), filter, table);
    draw();
  }
  function datesEditor(file, slug, entry) {
    const d = entry.dates || {};
    const box = el("div", { class: "dates" });
    function pointEditor(pt, path, title) {
      const kind = pt && pt.season ? "season" : pt && pt.month ? "month" : "year";
      const wrap = el("div", { class: "point" }, el("span", { class: "muted small" }, title));
      const kindSel = el("select", null, el("option", { value: "season" }, "season"), el("option", { value: "month" }, "month"), el("option", { value: "year" }, "year only"));
      kindSel.value = kind;
      const seasonSel = el("select", null, ...state.data.vocab.seasons.map((s) => el("option", { value: s }, s)));
      seasonSel.value = pt && pt.season || "spring";
      const monthSel = el("select", null, ...MONTHS.map((m, i) => el("option", { value: String(i + 1) }, m)));
      monthSel.value = String(pt && pt.month || 1);
      const year = el("input", { type: "number", min: 2000, max: 2100, value: pt && pt.year || new Date().getFullYear() });
      const commit = () => {
        const p = { year: parseInt(year.value, 10) || new Date().getFullYear() };
        if (kindSel.value === "season") p.season = seasonSel.value;
        if (kindSel.value === "month") p.month = parseInt(monthSel.value, 10);
        const ordered = kindSel.value === "season" ? { season: p.season, year: p.year } : kindSel.value === "month" ? { month: p.month, year: p.year } : { year: p.year };
        setField(file, slug, path, ordered);
      };
      for (const c of [kindSel, seasonSel, monthSel, year]) c.addEventListener("change", commit);
      seasonSel.hidden = kind !== "season"; monthSel.hidden = kind !== "month";
      kindSel.addEventListener("change", () => { seasonSel.hidden = kindSel.value !== "season"; monthSel.hidden = kindSel.value !== "month"; });
      wrap.append(kindSel, seasonSel, monthSel, year);
      return wrap;
    }
    box.append(pointEditor(d.from, ["dates", "from"], "from"));
    const toKind = el("select", null, el("option", { value: "none" }, "no end"), el("option", { value: "present" }, "present"), el("option", { value: "point" }, "ended"));
    toKind.value = d.to === "present" ? "present" : d.to && typeof d.to === "object" ? "point" : "none";
    toKind.addEventListener("change", () => {
      if (toKind.value === "none") delField(file, slug, ["dates", "to"]);
      else if (toKind.value === "present") setField(file, slug, ["dates", "to"], "present");
      else setField(file, slug, ["dates", "to"], { season: "spring", year: new Date().getFullYear() });
    });
    box.append(el("div", { class: "point" }, el("span", { class: "muted small" }, "to"), toKind));
    if (d.to && typeof d.to === "object") box.append(pointEditor(d.to, ["dates", "to"], "ended"));
    const sd = inputField(file, slug, entry, ["sortDate"], "Sort date (YYYY-MM)", { placeholder: entry._meta && entry._meta.suggestedSortDate });
    if (entry._meta && entry._meta.suggestedSortDate && entry._meta.suggestedSortDate !== entry.sortDate) {
      sd.append(el("button", { type: "button", class: "ghost small", onclick: () => setField(file, slug, ["sortDate"], entry._meta.suggestedSortDate) }, "use " + entry._meta.suggestedSortDate));
    }
    box.append(sd, el("div", { class: "muted small" }, "Shows as: " + (entry._meta ? entry._meta.datesEn + " / " + entry._meta.datesEs : "")));
    return el("div", { class: "field" }, el("span", null, "Dates"), box);
  }
  function tagsField(file, slug, entry) {
    const box = el("div", { class: "tagbox" });
    const cur = new Set(entry.tags || []);
    for (const t of state.data.tags) {
      const cb = el("input", { type: "checkbox" });
      cb.checked = cur.has(t.id);
      cb.addEventListener("change", () => { const next = state.data.tags.map((x) => x.id).filter((id) => (id === t.id ? cb.checked : cur.has(id))); setField(file, slug, ["tags"], next); });
      box.append(el("label", { class: "chk" }, cb, " " + (state.data.texts.en[t.key] || t.id)));
    }
    return el("div", { class: "field" }, el("span", null, "Tags"), box);
  }
  function listEditor(file, slug, entry, path, label, itemBuilder, blank, opts) {
    const o = opts || {};
    const items = getPath(entry, path) || [];
    const box = el("div", { class: "listbox" }, el("div", { class: "pair-label" }, label));
    items.forEach((item, i) => {
      const card = el("div", { class: "card" });
      card.append(itemBuilder(item, i));
      const bar = el("div", { class: "rowline" });
      bar.append(
        el("button", { type: "button", class: "ghost small", disabled: i === 0 ? "" : null, onclick: () => { const n = items.slice(); [n[i - 1], n[i]] = [n[i], n[i - 1]]; setField(file, slug, path, n); } }, "↑"),
        el("button", { type: "button", class: "ghost small", disabled: i === items.length - 1 ? "" : null, onclick: () => { const n = items.slice(); [n[i + 1], n[i]] = [n[i], n[i + 1]]; setField(file, slug, path, n); } }, "↓"),
        el("button", { type: "button", class: "ghost small danger", onclick: () => { if (confirm("Remove item " + (i + 1) + "?")) delField(file, slug, path.concat([i])); } }, "Remove"));
      card.append(bar);
      box.append(card);
    });
    if (!o.max || items.length < o.max) box.append(el("button", { type: "button", class: "ghost", onclick: () => setField(file, slug, path.concat([items.length]), blank()) }, "Add " + (o.itemName || "item")));
    return box;
  }

  // ---------------------------------------------------------------- forms
  function renderForm() {
    const box = $("#form");
    box.replaceChildren();
    const file = state.tab, slug = state.selected[file];
    if (state.data.readOnly) { box.append(el("div", { class: "gate err" }, "Read-only: " + state.data.readOnly)); return; }
    if (file === "tags") { renderTagsForm(box); return; }
    if (file === "about") { renderAboutForm(box); requestAnimationFrame(() => box.querySelectorAll("textarea").forEach(autosize)); return; }
    if (file === "images") { renderImagesPanel(box); return; }
    const entry = slug && entryOf(file, slug);
    if (!entry) { box.append(el("p", { class: "muted" }, "Pick a " + FILE_LABEL[file] + " on the left, or add one.")); return; }
    box.append(el("h2", null, slug, " ", el("span", { class: "muted small" }, file === "projects" ? "project" : "role")));
    const iss = issuesFor(file, slug);
    const issueBox = el("div", { id: "issueBox" });
    box.append(issueBox);
    renderIssueBox(issueBox, iss);
    if (file === "projects") renderProjectForm(box, slug, entry); else renderExperienceForm(box, slug, entry);
    const danger = el("div", { class: "rowline danger-zone" });
    if (file === "projects" && entry.listing !== "hidden") danger.append(el("button", { type: "button", class: "ghost", onclick: () => setField(file, slug, ["listing"], "hidden") }, "Hide (listing → hidden)"));
    if (file === "experience" && entry.visible) danger.append(el("button", { type: "button", class: "ghost", onclick: () => setField(file, slug, ["visible"], false) }, "Hide (visible → false)"));
    danger.append(el("button", { type: "button", class: "ghost", onclick: () => openRename(file, slug) }, "Rename slug…"));
    danger.append(el("button", { type: "button", class: "ghost danger", onclick: () => deleteEntry(file, slug) }, "Delete…"));
    box.append(danger);
    requestAnimationFrame(() => box.querySelectorAll("textarea").forEach(autosize));
  }
  function renderIssueBox(node, iss) {
    node.replaceChildren();
    const errs = iss.filter((i) => i.level === "error"), warns = iss.filter((i) => i.level === "warning");
    if (errs.length) node.append(el("div", { class: "gate err" }, el("strong", null, "Errors (block saving):"), el("ul", null, ...errs.map((i) => el("li", null, i.message)))));
    if (warns.length) node.append(el("div", { class: "gate warn" }, el("strong", null, "Warnings:"), el("ul", null, ...warns.map((i) => el("li", null, i.message)))));
  }
  function refreshIssues() {
    const file = state.tab, slug = state.selected[file];
    const node = $("#issueBox");
    if (node && slug) renderIssueBox(node, issuesFor(file, slug));
  }

  function renderProjectForm(box, slug, e) {
    const f = "projects";
    box.append(textPair(f, slug, e, "title", "Title"), textPair(f, slug, e, "desc", "Description", { note: "index row and sub-page" }),
      textPair(f, slug, e, "longDesc", "Long description", { note: "featured card paragraph — required when featured" }),
      textPair(f, slug, e, "search", "Search text", { note: "never shown; tool and method names that are not tags" }));
    const v = state.data.vocab;
    box.append(el("div", { class: "form-grid" },
      selectField(f, slug, e, ["context"], "Context", v.contexts.map((c) => [c, c])),
      selectField(f, slug, e, ["listing"], "Listing", [["index", "index — listed"], ["unlisted", "unlisted — direct URL only"], ["hidden", "hidden — nowhere"]]),
      selectField(f, slug, e, ["experience"], "Part of (role)", state.data.experience.filter((x) => x.visible).map((x) => [x.slug, textOf("experience", x, "org", "en") || x.slug]), { allowEmpty: true, emptyLabel: "(none)" }),
      el("div", { class: "field" }, el("span", null, "Flags"), checkField(f, slug, e, ["featured"], "featured (max 3, index only)"), checkField(f, slug, e, ["pinned"], "pinned to the top of the index")),
      inputField(f, slug, e, ["featuredOrder"], "Featured order (number, blank = none)", { number: true, removeWhenEmpty: true }),
      datesEditor(f, slug, e), tagsField(f, slug, e)));
    box.append(el("h3", null, "Images"), el("div", { class: "form-grid" }, imageField(f, slug, e, ["imageSrc"], "Main image", "imageAlt", "main"), imageField(f, slug, e, ["thumbSrc"], "Thumbnail (optional, index rows)", "thumbAlt", "thumb")));
    if (e.imageSrc) box.append(textPair(f, slug, e, "imageAlt", "Image alt text"));
    if (e.thumbSrc) box.append(textPair(f, slug, e, "thumbAlt", "Thumbnail alt text", { note: e.thumbAltKey && e.thumbAltKey !== ("proj" + camel(slug) + "ThumbAlt") ? "(shared with another field)" : "" }));
    box.append(el("div", { class: "form-grid" }, selectField(f, slug, e, ["homeLayout"], "Home layout", v.homeLayouts.map((x) => [x, x]), { allowEmpty: true, emptyLabel: "(default: stacked)" })));
    if (e.homeLayout === "collage" || e.gallery) {
      box.append(listEditor(f, slug, e, ["gallery"], "Collage gallery (2–4 images; the main image is not a cell)", (item, i) => el("div", null,
        el("div", { class: "form-grid" }, imageField(f, slug, e, ["gallery", i, "src"], "Image " + (i + 1), "gallery." + (i + 1) + ".alt", "main")), textPair(f, slug, e, "gallery." + (i + 1) + ".alt", "Alt text")), () => ({ src: "", altKey: "" }), { max: 4, itemName: "image" }));
    }
    box.append(el("h3", null, "Sub-page"));
    const shell = state.data.shells[slug];
    const exists = state.data.shellsOnDisk.includes(slug);
    const sub = el("div", { class: "rowline" });
    if (shell === "create") sub.append(pill("draft", "will be created on save"), el("code", null, "projects/" + slug + ".html"));
    else if (exists && shell !== "delete") sub.append(pill("st-both", "exists"), el("code", null, "projects/" + slug + ".html"));
    else sub.append(el("span", { class: "muted" }, "no sub-page yet"), el("button", { type: "button", class: "ghost", onclick: () => call("/api/content/shell", { slug }, true) }, "Create sub-page"));
    box.append(sub);
    if (e.subpageUrl || e.page) {
      const page = e.page || {};
      if (!e.page) box.append(el("button", { type: "button", class: "ghost", onclick: () => setField(f, slug, ["page"], { sections: [], facts: [], photos: [], reportPdf: "", creditKey: "" }) }, "Add sub-page content"));
      else {
        box.append(listEditor(f, slug, e, ["page", "sections"], "Sections", (s, i) => el("div", null, textPair(f, slug, e, "page.sections." + (i + 1) + ".heading", "Heading"), textPair(f, slug, e, "page.sections." + (i + 1) + ".body", "Body")), () => ({ headingKey: "", bodyKey: "" }), { itemName: "section" }));
        box.append(listEditor(f, slug, e, ["page", "facts"], "Quick facts", (s, i) => el("div", null, textPair(f, slug, e, "page.facts." + (i + 1) + ".label", "Label"), textPair(f, slug, e, "page.facts." + (i + 1) + ".value", "Value")), () => ({ labelKey: "", valueKey: "" }), { itemName: "fact" }));
        box.append(listEditor(f, slug, e, ["page", "photos"], "Photos", (s, i) => el("div", null, el("div", { class: "form-grid" }, imageField(f, slug, e, ["page", "photos", i, "src"], "Photo " + (i + 1), "page.photos." + (i + 1) + ".alt", "main")), textPair(f, slug, e, "page.photos." + (i + 1) + ".alt", "Alt text")), () => ({ src: "", altKey: "" }), { itemName: "photo" }));
        const pdf = el("select", null, el("option", { value: "" }, "(none)"), ...state.data.pdfs.map((p) => el("option", { value: p }, p)));
        pdf.value = page.reportPdf || "";
        pdf.addEventListener("change", () => setField(f, slug, ["page", "reportPdf"], pdf.value));
        box.append(el("div", { class: "form-grid" }, el("label", { class: "field" }, el("span", null, "Report PDF"), pdf)), textPair(f, slug, e, "page.credit", "Credit line"));
      }
    }
  }
  function camel(slug) { return slug.split(/[-_\s]+/).filter(Boolean).map((p) => p[0].toUpperCase() + p.slice(1)).join(""); }

  function renderExperienceForm(box, slug, e) {
    const f = "experience";
    box.append(textPair(f, slug, e, "role", "Role"), textPair(f, slug, e, "org", "Organization", { note: "full string on the band" }), textPair(f, slug, e, "orgShort", "Short organization", { note: "for “Part of” links; optional" }));
    box.append(listEditor(f, slug, e, ["bulletKeys"], "Bullets", (k, i) => textPair(f, slug, e, "bullets." + (i + 1), "Bullet " + (i + 1)), () => "", { itemName: "bullet" }));
    const v = state.data.vocab;
    box.append(el("div", { class: "form-grid" },
      datesEditor(f, slug, e), tagsField(f, slug, e),
      selectField(f, slug, e, ["layout"], "Layout", v.expLayouts.map((x) => [x, x])),
      el("div", { class: "field" }, el("span", null, "Flags"),
        checkField(f, slug, e, ["visible"], "visible on the site"),
        checkField(f, slug, e, ["status"], "current role (hero status sentence)", { onchange: (on) => setField(f, slug, ["status"], on ? "current" : null) })),
      imageField(f, slug, e, ["imageSrc"], "Band image", "imageAlt", "main"),
      inputField(f, slug, e, ["imageLink"], "Image link (optional, e.g. projects.html?part=" + slug + ")")));
    if (e.imageSrc) box.append(textPair(f, slug, e, "imageAlt", "Image alt text"));
    box.append(el("h3", null, "Band colors ", el("span", { class: "muted small" }, "tints over the section background; none = inherit")));
    if (!e.color) box.append(el("button", { type: "button", class: "ghost", onclick: () => setField(f, slug, ["color"], { light: { bg: "#DED8C9", border: "#948C7E", accent: "#615951" }, dark: { bg: "#302C25", border: "#665E52", accent: "#C4BAA9" } }) }, "Add colors"));
    else {
      const grid = el("div", { class: "form-grid" });
      for (const mode of ["light", "dark"]) for (const part of ["bg", "border", "accent"]) grid.append(inputField(f, slug, e, ["color", mode, part], mode + " " + part, { placeholder: "#RRGGBB" }));
      box.append(grid, el("button", { type: "button", class: "ghost", onclick: () => setField(f, slug, ["color"], null) }, "Remove colors"));
    }
  }

  // ---------------------------------------------------------------- About lists
  const pendingField = {};
  function queueField(file, slug, path, value) {
    const k = [file, slug, path.join(".")].join("|");
    clearTimeout(pendingField[k]);
    pendingField[k] = setTimeout(() => call("/api/content/field", { file, slug, path, value }, false), 350);
  }
  function inlinePair(entry, enField, esField, label) {
    const wrap = el("div", { class: "pair" }, el("div", { class: "pair-label" }, label));
    const cols = el("div", { class: "cols" });
    for (const [lang, field] of [["en", enField], ["es", esField]]) {
      const ta = el("textarea", { rows: 1, lang, spellcheck: "true" });
      ta.value = entry[field] || "";
      ta.placeholder = lang.toUpperCase();
      ta.addEventListener("input", () => { autosize(ta); queueField("about", entry.id, [field], ta.value); });
      cols.append(el("div", null, el("label", null, lang.toUpperCase()), ta));
    }
    wrap.append(cols);
    return wrap;
  }
  function renderAboutForm(box) {
    const a = state.data.about;
    const lst = state.selected.about || "sites";
    const entries = a.lists[lst] || [];
    const section = a.sections[lst];
    box.append(el("h2", null, a.labels[lst], " ", el("span", { class: "muted small" }, "about.html — js/about-data.js")));
    const shownCb = el("input", { type: "checkbox" });
    shownCb.checked = !!a.shown[section];
    shownCb.addEventListener("change", () => call("/api/content/about/shown", { section, shown: shownCb.checked }, true));
    box.append(el("div", { class: "rowline" }, el("label", { class: "chk" }, shownCb, " Shown on the site"), el("span", { class: "muted small" }, "(the hidden attribute on #" + section + " in about.html; the whole block)"),
      el("span", { class: "spacer" }), el("button", { type: "button", class: "primary", onclick: openAdd }, "Add " + (lst === "faq" ? "question" : lst === "books" ? "book" : "site") + "…")));
    const ids = entries.map((e) => e.id);
    entries.forEach((e, i) => {
      const card = el("div", { class: "card" + (e.visible ? "" : " excluded") });
      const iss = issuesFor("about", e.id);
      const bar = el("div", { class: "rowline" }, el("code", null, e.id), e._draft ? pill("draft", "draft") : null, el("span", { class: "spacer" }),
        el("button", { type: "button", class: "ghost small", disabled: i === 0 ? "" : null, onclick: () => { const n = ids.slice(); [n[i - 1], n[i]] = [n[i], n[i - 1]]; call("/api/content/about/order", { list: lst, ids: n }, true); } }, "↑"),
        el("button", { type: "button", class: "ghost small", disabled: i === entries.length - 1 ? "" : null, onclick: () => { const n = ids.slice(); [n[i + 1], n[i]] = [n[i], n[i + 1]]; call("/api/content/about/order", { list: lst, ids: n }, true); } }, "↓"),
        el("button", { type: "button", class: "ghost small danger", onclick: () => { if (confirm("Delete “" + e.id + "”?\n\nNothing happens until you Review & save.")) call("/api/content/delete", { file: "about", slug: e.id }, true); } }, "Delete"));
      card.append(bar);
      const ib = el("div", { class: "child-issues" });
      renderIssueBox(ib, iss);
      card.append(ib);
      const flags = el("div", { class: "form-grid" }, checkField("about", e.id, e, ["visible"], "visible on the page"));
      if (lst === "sites") {
        flags.append(inputField("about", e.id, e, ["url"], "URL (https://… or a site-relative path)"), checkField("about", e.id, e, ["internal"], "opens in the same tab (internal link)"));
      }
      if (lst === "books") flags.append(imageField("about", e.id, e, ["coverSrc"], "Cover", "cover", "portrait"));
      card.append(flags);
      for (const [enF, esF, label] of ABOUT_PAIRS[lst]) card.append(inlinePair(e, enF, esF, label));
      box.append(card);
    });
    if (!entries.length) box.append(el("p", { class: "muted" }, "No entries yet."));
  }

  function renderTagsForm(box) {
    box.append(el("h2", null, "Tags ", el("span", { class: "muted small" }, "js/tags-data.js — ids never change; labels are text")));
    const t = el("table", { class: "docs" }, el("tr", null, el("th", null, "id"), el("th", null, "EN"), el("th", null, "ES"), el("th", null, "Used"), el("th")));
    for (const tag of state.data.tags) {
      const cells = [el("td", null, el("code", null, tag.id))];
      for (const lang of ["en", "es"]) {
        const inp = el("input", { type: "text", value: state.data.texts[lang][tag.key] ?? "" });
        inp.addEventListener("input", () => queueText("tags", tag.id, "label", lang, inp.value));
        cells.push(el("td", null, inp));
      }
      cells.push(el("td", null, String(tag.uses)), el("td", { class: "actions" }, el("button", { type: "button", class: "ghost danger", disabled: tag.uses ? "" : null, title: tag.uses ? "remove it from every entry first" : "", onclick: () => { if (confirm("Delete tag " + tag.id + "?")) call("/api/content/tag/delete", { id: tag.id }, true); } }, "Delete")));
      const row = el("tr", { class: tag._draft ? "has-draft" : "" }, ...cells);
      t.append(row);
      const iss = issuesFor("tags", tag.id);
      if (iss.length) t.append(el("tr", { class: "issuerow" }, el("td", { colspan: 5 }, el("ul", { class: "issues" }, ...iss.map((i) => el("li", { class: i.level }, i.message))))));
    }
    box.append(t);
    for (const slug of (state.data.deleted.tags || [])) box.append(el("p", { class: "muted" }, slug + " will be deleted on save."));
  }

  // ---------------------------------------------------------------- add / delete
  function openAdd() {
    const file = state.tab;
    const lst = state.selected.about;
    $("#addTitle").textContent = file === "about" ? "Add to " + state.data.about.labels[lst] : "Add " + FILE_LABEL[file];
    $("#addEnLabel").textContent = file === "tags" ? "Label (EN)" : file === "projects" ? "Title (EN)" : file === "about" ? (lst === "faq" ? "Question (EN)" : lst === "books" ? "Title (EN)" : "Label (EN)") : "Role (EN)";
    $("#addEsLabel").textContent = file === "tags" ? "Label (ES)" : file === "projects" ? "Title (ES)" : file === "about" ? (lst === "faq" ? "Question (ES)" : lst === "books" ? "Title (ES)" : "Label (ES)") : "Role (ES)";
    $("#addNote").textContent = file === "projects" ? "New projects start hidden with today's season; fill the rest in the form, then set the listing." : file === "experience" ? "New roles start hidden (visible: false)." : file === "about" ? "The id names the entry in js/about-data.js and never changes; the entry starts hidden (visible: false)." : "One line in js/tags-data.js plus the two labels.";
    $("#addSlug").value = ""; $("#addEn").value = ""; $("#addEs").value = "";
    $("#addDlg").showModal();
    $("#addSlug").focus();
  }
  async function doAdd() {
    const file = state.tab, slug = $("#addSlug").value.trim(), en = $("#addEn").value.trim(), es = $("#addEs").value.trim();
    const ok = file === "tags" ? await call("/api/content/tag", { id: slug, en, es }, true)
      : file === "about" ? await call("/api/content/about/add", { list: state.selected.about, id: slug, en, es }, true)
      : await call("/api/content/add", { file, slug, titleEn: en, titleEs: es }, true);
    if (ok) { $("#addDlg").close(); if (file !== "tags" && file !== "about") select(file, slug); }
  }
  const renameCtx = {};
  function openRename(file, slug) {
    Object.assign(renameCtx, { file, slug });
    $("#renameTitle").textContent = "Rename " + FILE_LABEL[file] + " “" + slug + "”";
    $("#renameSlug").value = slug;
    $("#renameNote").textContent = (file === "projects"
      ? "Everything follows in one draft: the text keys (renamed in place in translations.js), the image paths and the sub-page URL, links from roles to this project, the sub-page file and the image folder (moved on save). "
      : "Everything follows in one draft: the text keys (renamed in place), the band image paths, projects that say “Part of” this role, and the image folder (moved on save). ")
      + "Links from outside the site to the old #slug or ?part= stop working. Mentions in CLAUDE.md / plan.md / content.md are for you to edit by hand.";
    $("#renameDlg").showModal();
    $("#renameSlug").focus();
    $("#renameSlug").select();
  }
  async function doRename() {
    const newSlug = $("#renameSlug").value.trim();
    if (!newSlug || newSlug === renameCtx.slug) { $("#renameDlg").close(); return; }
    const r = await call("/api/content/rename", { file: renameCtx.file, slug: renameCtx.slug, newSlug }, true);
    if (r) {
      $("#renameDlg").close();
      const s = r.result;
      toast(`Renamed to “${newSlug}”: ${s.keys.length} key(s), ${s.paths} path(s), ${s.references.length} reference(s), ${s.files.length} file / folder move(s) — Review & save to apply.`, 8000);
      select(renameCtx.file, newSlug);
    }
  }

  async function deleteEntry(file, slug) {
    if (!confirm("Delete " + FILE_LABEL[file] + " “" + slug + "”?\n\nIts text that nothing else uses is removed too" + (file === "projects" ? ", and its sub-page (if any) moves to the backup set" : "") + ". Nothing happens until you Review & save.")) return;
    const r = await call("/api/content/delete", { file, slug }, true);
    if (r) { state.selected[file] = null; renderList(); renderForm(); toast("Marked for deletion — Review & save to apply."); }
  }

  // ---------------------------------------------------------------- review & save
  function renderCounts() {
    const n = (state.data.draftCount || 0) + (state.data.siteTextDrafts || 0);
    $("#draftCount").textContent = String(n);
    $("#draftCount").hidden = n === 0;
    state.unsaved = n > 0;
  }
  function issueList(items) { return el("ul", null, ...items.map((i) => el("li", null, i.key + ": " + i.message))); }
  async function openReview() {
    const dlg = $("#reviewDlg"), body = $("#reviewBody");
    body.replaceChildren(el("p", { class: "muted" }, "Preparing…"));
    $("#saveBtn").disabled = true;
    dlg.showModal();
    let r;
    try { r = await api("/api/content/review"); } catch (e) { body.replaceChildren(el("p", null, "Review failed: " + e.message)); return; }
    body.replaceChildren();
    if (r.readOnly) { body.append(el("div", { class: "gate err" }, "Read-only: " + r.error)); return; }
    if (r.noop) { body.append(el("p", { class: "muted" }, "No changes — the files on disk already match.")); return; }
    body.append(el("ul", { class: "changes" }, ...r.changes.map((c) => el("li", null, c.text))));
    if (r.shells.length) body.append(el("ul", { class: "changes" }, ...r.shells.map((s) => el("li", null, el("strong", null, s.action === "create" ? "Create " : "Delete "), el("code", null, s.path)))));
    if (r.renames && r.renames.length) body.append(el("ul", { class: "changes" }, ...r.renames.map((m) => el("li", null, el("strong", null, "Move "), el("code", null, m.from), " → ", el("code", null, m.to), m.kind === "folder" ? ` (${m.files.length} file${m.files.length === 1 ? "" : "s"})` : ""))));
    if (r.assets && r.assets.length) body.append(el("ul", { class: "changes" }, ...r.assets.map((a) => el("li", null, el("strong", null, { add: "Add ", replace: "Replace ", remove: "Remove " }[a.action]), el("code", null, a.path), a.size ? ` (${a.size}, ${a.kb} KB)` : ""))));
    if (r.diskChanged) body.append(el("div", { class: "gate err" }, "A file changed on disk since it was loaded. Close this, click Reload in the banner, then review again."));
    for (const g of [r.gate, r.siteTextGate]) {
      if (!g) continue;
      if (g.blocking.length) body.append(el("div", { class: "gate err" }, el("strong", null, "Blocking errors (fix before saving):"), issueList(g.blocking)));
      if (g.warnings.length) body.append(el("div", { class: "gate warn" }, el("strong", null, "Warnings (saving is allowed):"), issueList(g.warnings.slice(0, 15)), g.warnings.length > 15 ? el("p", { class: "muted" }, "… and " + (g.warnings.length - 15) + " more") : null));
    }
    for (const f of r.files) body.append(el("h3", null, f.path), renderDiff(f.diff));
    $("#saveBtn").disabled = !!(r.diskChanged || r.gate.blocking.length || r.siteTextGate.blocking.length);
  }
  async function doSave() {
    $("#saveBtn").disabled = true;
    let r;
    try { r = await api("/api/content/save", { method: "POST", body: {} }); } catch (e) { toast("Save failed: " + e.message); $("#saveBtn").disabled = false; return; }
    if (!r.ok) { toast(r.message || r.error, 7000); if (r.error === "changed-on-disk") { $("#reviewDlg").close(); showDiskBanner(r.message); } else $("#saveBtn").disabled = false; return; }
    $("#reviewDlg").close();
    toast(r.message, 6000);
    await loadState();
  }
  async function discardAll() {
    if (!confirm("Discard all content drafts? The files on disk are not touched. (Site text drafts made on the Site text tab are kept.)")) return;
    await api("/api/content/drafts/discard", { method: "POST", body: {} });
    $("#reviewDlg").close();
    await loadState();
    toast("Content drafts discarded.");
  }

  // ---------------------------------------------------------------- state / heartbeat
  function showDiskBanner(msg) {
    if (!banners.disk) setBanner("disk", "warn", msg || "A data file changed on disk (VS Code, Claude Code, git). Saving is refused until you reload; drafts are kept.", [{ label: "Reload", primary: true, onclick: reloadFromDisk }]);
  }
  async function reloadFromDisk() {
    const d = await api("/api/content/reload", { method: "POST", body: {} });
    clearBanner("disk");
    await loadState(d);
    toast("Reloaded from disk.");
  }
  async function loadState(via) {
    const d = via || (await api("/api/content/state"));
    state.data = d;
    $("#previewLink").href = "http://127.0.0.1:5501/projects.html";
    if (d.readOnly) setBanner("readonly", "err", "Read-only: " + d.readOnly); else clearBanner("readonly");
    if (Object.values(d.files).some((f) => f.diskChanged)) showDiskBanner(); else clearBanner("disk");
    if (d.autosave) setBanner("autosave", "warn", "Unsaved content edits from " + d.autosave.saved + " were found.", [
      { label: "Restore drafts", primary: true, onclick: async () => { const r = await api("/api/content/autosave/restore", { method: "POST", body: {} }); clearBanner("autosave"); toast("Restored " + r.applied + " draft item(s)"); await loadState(); } },
      { label: "Discard", onclick: async () => { await api("/api/content/autosave/discard", { method: "POST", body: {} }); clearBanner("autosave"); } }]);
    const m = location.hash.replace(/^#/, "").match(/^(projects|experience|tags|about|images)(?:\/(.+))?$/);
    if (m) { state.tab = m[1]; if (m[2]) state.selected[m[1]] = decodeURIComponent(m[2]); }
    renderCounts();
    renderList();
    renderForm();
  }
  let hbFailures = 0;
  async function heartbeat() {
    try { const r = await api("/api/heartbeat", { method: "POST", body: {} }); hbFailures = 0; clearBanner("offline"); if (r.diskChanged) showDiskBanner(); }
    catch (e) { if (++hbFailures >= 2) setBanner("offline", "err", "The editor server is not answering. If it was closed, close this window and start the editor again."); }
  }

  // ---------------------------------------------------------------- wiring
  function init() {
    window.Editor.initTabs();
    if (!token) { window.Editor.noToken(); return; }
    for (const a of document.querySelectorAll("#subtabs a")) a.addEventListener("click", (ev) => { ev.preventDefault(); state.tab = a.dataset.tab; location.hash = state.tab + (state.selected[state.tab] ? "/" + state.selected[state.tab] : ""); renderList(); renderForm(); });
    $("#reviewBtn").addEventListener("click", openReview);
    $("#saveBtn").addEventListener("click", doSave);
    $("#discardBtn").addEventListener("click", discardAll);
    $("#addGo").addEventListener("click", doAdd);
    $("#renameGo").addEventListener("click", doRename);
    $("#renameDlg").addEventListener("keydown", (e) => { if (e.key === "Enter" && e.target.tagName === "INPUT") { e.preventDefault(); doRename(); } });
    $("#importGo").addEventListener("click", doImport);
    $("#addDlg").addEventListener("keydown", (e) => { if (e.key === "Enter" && e.target.tagName === "INPUT") { e.preventDefault(); doAdd(); } });
    $("#previewLink").addEventListener("click", async (e) => { e.preventDefault(); try { await api("/api/open-preview", { method: "POST", body: {} }); toast("Preview opened in your browser."); } catch (err) { toast("Could not open the preview: " + err.message); } });
    document.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); if (!$("#reviewDlg").open) openReview(); } });
    window.addEventListener("beforeunload", (e) => { if (state.unsaved && !window.__navigating) { e.preventDefault(); e.returnValue = ""; } });
    window.addEventListener("hashchange", () => { const m = location.hash.replace(/^#/, "").match(/^(projects|experience|tags|about|images)(?:\/(.+))?$/); if (m) { state.tab = m[1]; if (m[2]) state.selected[m[1]] = decodeURIComponent(m[2]); renderList(); renderForm(); } });
    loadState().catch((e) => setBanner("load", "err", "Could not load the content state: " + e.message));
    heartbeat();
    setInterval(heartbeat, 5000);
  }
  init();
  window.__content = state; // for tests
})();
