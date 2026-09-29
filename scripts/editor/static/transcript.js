/* Transcript page — Phase 3 (vanilla JS, no build step). */
(function () {
  "use strict";
  const { token, $, el, api, toast, setBanner, clearBanner, banners, fold, renderDiff, fmtTime } = window.Editor;

  const state = {
    data: null,          // /api/transcript/state
    filter: "all",       // all | missing | unverified | same | drafts | attention
    query: "",
    job: null,
    pollTimer: null,
    dirtyTitleIds: new Set(),  // rows edited locally (draft marker until the server confirms)
    unsaved: false,
  };
  const FILTERS = [
    ["all", "All"], ["attention", "Needs attention"], ["missing", "Missing"], ["unverified", "Unverified"], ["same", "ES = EN"], ["drafts", "Drafts"],
  ];

  // ---------------------------------------------------------------- helpers
  function pill(cls, text, title) { return el("span", { class: "pill " + cls, title: title || null }, text); }
  function autosize(ta) { ta.style.height = "auto"; ta.style.height = Math.max(30, ta.scrollHeight + 2) + "px"; }
  function issuesFor(file, key) { return ((state.data.issues || {})[file] || []).filter((i) => i.key === key); }
  function rowIssues(r) { return issuesFor("titles", r.id); }
  function rowMatches(r) {
    const iss = rowIssues(r);
    switch (state.filter) {
      case "missing": if (!r.missing) return false; break;
      case "unverified": if (r.verified || r.missing) return false; break;
      case "same": if (!iss.some((i) => i.code === "same")) return false; break;
      case "drafts": if (!r.draft) return false; break;
      case "attention": if (!(r.missing || iss.length || r.draft)) return false; break;
    }
    if (!state.query) return true;
    const hay = fold([r.code, r.section, r.en, r.es, r.source, r.transcriptTitle].join(" "));
    return state.query.split(/\s+/).filter(Boolean).every((t) => hay.includes(t));
  }
  function markDrafts() {
    // the server sends the live rows (drafts applied); mark rows that differ from disk via the change list later
    for (const r of state.data.titles) r.draft = state.dirtyTitleIds.has(r.id);
  }
  function fileNote(name) {
    const f = state.data.files[name];
    if (!f.loaded) return pill("st-todo", "not loaded", f.readOnly);
    if (f.readOnly) return pill("st-todo", "read-only", f.readOnly);
    return null;
  }

  // ---------------------------------------------------------------- source
  function renderSource() {
    const sel = $("#rawPdf");
    sel.replaceChildren();
    const pdfs = state.data.rawPdfs || [];
    if (!pdfs.length) sel.append(el("option", { value: "" }, `no PDFs in ${state.data.rawDir}/ yet`));
    for (const p of pdfs) sel.append(el("option", { value: p.name }, `${p.name}  (${fmtTime(p.mtime)})`));
    $("#parseBtn").disabled = !pdfs.length || (state.job && state.job.running);
    const d = state.data.data;
    $("#dataInfo").textContent = d.printed ? `transcript-data.json: printed ${d.printed}, parsed ${d.parsedOn}, ${d.blocks.reduce((n, b) => n + b.codes.length, 0)} courses in ${d.blocks.length} blocks, cumulative GPA ${d.gpa || "—"}` : "transcript-data.json not loaded";
  }

  // ---------------------------------------------------------------- titles
  function renderFilters() {
    const box = $("#titleFilters");
    box.replaceChildren();
    const rows = state.data.titles;
    const counts = {
      all: rows.length,
      attention: rows.filter((r) => r.missing || rowIssues(r).length || r.draft).length,
      missing: rows.filter((r) => r.missing).length,
      unverified: rows.filter((r) => !r.verified && !r.missing).length,
      same: rows.filter((r) => rowIssues(r).some((i) => i.code === "same")).length,
      drafts: rows.filter((r) => r.draft).length,
    };
    for (const [id, label] of FILTERS) {
      box.append(el("button", { type: "button", class: "chip" + (state.filter === id ? " active" : ""), onclick: () => { state.filter = id; renderFilters(); renderTitles(); } }, `${label} ${counts[id]}`));
    }
  }

  function titleCell(r, lang) {
    const ta = el("textarea", { rows: 1, lang: lang, spellcheck: "true" });
    ta.value = r[lang] || "";
    ta.placeholder = r.missing ? `${lang.toUpperCase()} title` : "";
    ta.addEventListener("input", () => { autosize(ta); queueTitle(r, lang, ta.value); });
    return ta;
  }

  function renderTitles() {
    const t = $("#titles");
    t.replaceChildren(el("tr", null, el("th", null, "Code"), el("th", null, "On the transcript"), el("th", null, "EN"), el("th", null, "ES"), el("th", null, "Source"), el("th", null, "Verified")));
    const ro = state.data.files.titles.readOnly || !state.data.files.titles.loaded;
    let shown = 0;
    for (const r of state.data.titles) {
      if (!rowMatches(r)) continue;
      shown++;
      const iss = rowIssues(r);
      const tr = el("tr", { class: (r.missing ? "is-missing " : "") + (r.draft ? "has-draft " : "") + (iss.some((i) => i.level === "error") ? "has-error" : "") });
      const code = el("td", null, el("strong", null, r.code));
      if (r.section) code.append(el("div", { class: "muted small" }, "section: " + r.section));
      const on = el("td", { class: "small" });
      if (r.onTranscript) { on.append(r.transcriptTitle || "", el("div", { class: "muted" }, r.terms.join(", "))); }
      else on.append(el("span", { class: "muted" }, "not on this transcript"));
      const src = el("input", { type: "text", value: r.source || "", placeholder: "where the title came from" });
      src.addEventListener("change", () => queueTitle(r, "source", src.value));
      const ver = el("input", { type: "checkbox" });
      ver.checked = !!r.verified;
      ver.addEventListener("change", () => queueTitle(r, "verified", ver.checked));
      const en = titleCell(r, "en"), es = titleCell(r, "es");
      if (ro) for (const x of [src, ver, en, es]) x.disabled = true;
      const issueUl = el("ul", { class: "issues" }, ...iss.map((i) => el("li", { class: i.level }, (i.lang ? i.lang.toUpperCase() + ": " : "") + i.message)));
      tr.append(code, on, el("td", null, en), el("td", null, es), el("td", null, src), el("td", { class: "center" }, ver));
      t.append(tr);
      if (iss.length) t.append(el("tr", { class: "issuerow" }, el("td", { colspan: 6 }, issueUl)));
    }
    if (!shown) t.append(el("tr", null, el("td", { colspan: 6, class: "muted center" }, "No rows match.")));
    requestAnimationFrame(() => t.querySelectorAll("textarea").forEach(autosize));
    const note = fileNote("titles");
    $("#titlesPath").replaceChildren(state.data.files.titles.path, " ", note || "", state.data.titlesSorted ? "" : " (keys not sorted; new codes go last)");
  }

  const pendingTitles = {};
  function queueTitle(r, field, value) {
    const k = r.id + "." + field;
    clearTimeout(pendingTitles[k]);
    r[field] = value;
    r.draft = true;
    state.dirtyTitleIds.add(r.id);
    pendingTitles[k] = setTimeout(() => sendTitle(r, field, value), 350);
  }
  async function sendTitle(r, field, value) {
    try {
      const res = await api("/api/transcript/title", { method: "POST", body: { code: r.code, section: r.section, field, value } });
      if (!res || res.ok === false) { toast("Edit rejected: " + (res && res.error), 6000); return; }
      applyDraftReply(res);
    } catch (e) { toast("Could not send the edit: " + e.message, 6000); }
  }
  function applyDraftReply(res) {
    state.data.issues = res.issues;
    state.data.gates = res.gates;
    state.data.draftCount = res.draftCount;
    // keep local textarea values (the user may still be typing) but refresh the row list membership
    const byId = Object.fromEntries(state.data.titles.map((r) => [r.id, r]));
    state.data.titles = res.titles.map((r) => Object.assign(r, byId[r.id] && byId[r.id].draft ? { draft: true } : {}));
    if (!res.draftCount) state.dirtyTitleIds.clear();
    markDrafts();
    renderCounts();
    renderFilters();
    // only re-render rows when the set of rows changed (a new code appeared) to keep focus while typing
    if (document.querySelectorAll("#titles tr:not(.issuerow)").length - 1 !== state.data.titles.filter(rowMatches).length) renderTitles();
    else refreshIssueRows();
  }
  function refreshIssueRows() {
    // cheap path: rebuild the whole table only if an issue row count changed
    const want = state.data.titles.filter(rowMatches).filter((r) => rowIssues(r).length).length;
    const have = document.querySelectorAll("#titles tr.issuerow").length;
    if (want !== have) renderTitles();
  }

  // ---------------------------------------------------------------- profile
  function field(labelText, value, onchange, opts) {
    const o = opts || {};
    const input = o.multiline ? el("textarea", { rows: o.rows || 3 }) : el("input", { type: "text" });
    input.value = value == null ? "" : value;
    if (o.disabled) input.disabled = true;
    input.addEventListener("change", () => onchange(input.value));
    return el("label", { class: "field" }, el("span", null, labelText), input);
  }
  function renderProfile() {
    const box = $("#profileBody");
    box.replaceChildren();
    const p = state.data.profile;
    $("#profilePath").replaceChildren(state.data.files.profile.path, " ", fileNote("profile") || "");
    if (!p) { box.append(el("p", { class: "muted" }, "profile.json not loaded.")); return; }
    const ro = !!state.data.files.profile.readOnly;
    const send = (path) => (value) => sendDraft("profile", path, value);
    const listSend = (path) => (value) => sendDraft("profile", path, value.split("\n").map((s) => s.trim()).filter(Boolean));
    box.append(el("div", { class: "form-grid" },
      field("Name", p.name, send(["name"]), { disabled: ro }),
      field("Contact line", p.contact, send(["contact"]), { disabled: ro })));
    for (const lang of ["en", "es"]) {
      const l = p[lang] || {};
      box.append(el("h3", null, lang.toUpperCase()), el("div", { class: "form-grid" },
        field("University", l.university, send([lang, "university"]), { disabled: ro }),
        field("Program", l.program, send([lang, "program"]), { disabled: ro }),
        field("Majors (one per line)", (l.majors || []).join("\n"), listSend([lang, "majors"]), { multiline: true, rows: 4, disabled: ro }),
        field("Minors (one per line)", (l.minors || []).join("\n"), listSend([lang, "minors"]), { multiline: true, rows: 5, disabled: ro }),
        field("Expected graduation", l.expected_graduation, send([lang, "expected_graduation"]), { disabled: ro })));
    }
    const iss = (state.data.issues.profile || []);
    if (iss.length) box.append(el("ul", { class: "issues" }, ...iss.map((i) => el("li", { class: i.level }, i.key + ": " + i.message))));
  }

  // ---------------------------------------------------------------- adjustments
  function renderAdjustments() {
    const box = $("#adjBody");
    box.replaceChildren();
    const a = state.data.adjustments;
    $("#adjPath").replaceChildren(state.data.files.adjustments.path, " ", fileNote("adjustments") || "");
    if (!a) { box.append(el("p", { class: "muted" }, "adjustments.json not loaded.")); return; }
    const ro = !!state.data.files.adjustments.readOnly;
    if (a._comment) box.append(el("p", { class: "muted small" }, a._comment));
    const blocks = state.data.data.blocks.map((b) => b.label);
    const adds = a.add || [];
    adds.forEach((item, i) => {
      const c = item.course || {};
      const send = (path, conv) => (value) => sendDraft("adjustments", ["add", i, ...path], conv ? conv(value) : value);
      const card = el("div", { class: "card" });
      const blockSel = el("select");
      for (const b of blocks) blockSel.append(el("option", { value: b, selected: b === item.block ? "" : null }, b));
      if (!blocks.includes(item.block)) blockSel.append(el("option", { value: item.block, selected: "" }, item.block + " (not on transcript)"));
      blockSel.addEventListener("change", () => sendDraft("adjustments", ["add", i, "block"], blockSel.value));
      if (ro) blockSel.disabled = true;
      card.append(el("div", { class: "form-grid" },
        el("label", { class: "field" }, el("span", null, "Block"), blockSel),
        field("After course", item.after, send(["after"]), { disabled: ro }),
        field("Code", c.code, send(["course", "code"]), { disabled: ro }),
        field("Transcript title (as TU prints it, or blank)", c.transcript_title, send(["course", "transcript_title"]), { disabled: ro }),
        field("Credits", c.credits, send(["course", "credits"], (v) => (/^\d+$/.test(v.trim()) ? parseInt(v, 10) : v)), { disabled: ro }),
        field("Grade", c.grade, send(["course", "grade"]), { disabled: ro }),
        field("Reason", item.reason, send(["reason"]), { disabled: ro })));
      const iss = (state.data.issues.adjustments || []).filter((x) => x.key.startsWith(`add[${i}]`));
      if (iss.length) card.append(el("ul", { class: "issues" }, ...iss.map((x) => el("li", { class: x.level }, x.message))));
      if (!ro) card.append(el("button", { type: "button", class: "ghost danger", onclick: () => { if (confirm(`Remove the ${c.code || "(blank)"} adjustment?`)) sendDraft("adjustments", ["add", i], null, true); } }, "Remove"));
      box.append(card);
    });
    if (!adds.length) box.append(el("p", { class: "muted" }, "No adjustments — every course comes from the TU transcript."));
    if (!ro) box.append(el("button", { type: "button", class: "ghost", onclick: () => sendDraft("adjustments", ["add", adds.length], { block: blocks[0] || "", after: "", course: { code: "", transcript_title: "", credits: 3, grade: "P", points: 0.0 }, reason: "" }) }, "Add a course"));
    const other = (state.data.issues.adjustments || []).filter((x) => !x.key.startsWith("add["));
    if (other.length) box.append(el("ul", { class: "issues" }, ...other.map((x) => el("li", { class: x.level }, x.message))));
  }

  async function sendDraft(file, path, value, del) {
    try {
      const res = await api("/api/transcript/draft", { method: "POST", body: { file, path, value, delete: !!del } });
      if (!res || res.ok === false) { toast("Edit rejected: " + (res && res.error), 6000); return; }
      await loadState();
    } catch (e) { toast("Could not send the edit: " + e.message, 6000); }
  }

  // ---------------------------------------------------------------- build
  function renderBuild() {
    const b = state.data.built;
    const parts = [];
    for (const lang of ["en", "es"]) {
      const x = b[lang];
      parts.push(`${lang.toUpperCase()}: ${x ? `${x.name} (${fmtTime(x.mtime)})` : "no PDF built"}`);
    }
    if (state.data.docx.length) parts.push(`Word files: ${state.data.docx.map((d) => d.name).join(", ")}`);
    const box = $("#buildStatus");
    box.replaceChildren(parts.join(" · "));
    if (state.data.rebuildNeeded) box.append(" ", pill("st-todo", "rebuild needed", "the inputs changed after the last build"));
    if (state.data.cvGpaWarning) box.append(" ", pill("st-same", "GPA differs from the CV", state.data.cvGpaWarning));
    $("#buildBtn").disabled = !!(state.job && state.job.running) || state.data.draftCount > 0;
    $("#buildBtn").title = state.data.draftCount > 0 ? "Save or discard the drafts first — the build reads the files on disk" : "";
    if (!$("#buildDate").value && state.data.data.printed) $("#buildDate").placeholder = state.data.data.printed.replace(/-/g, "");
  }
  function renderJob() {
    const j = state.job;
    const log = $("#jobLog");
    if (!j) { log.hidden = true; return; }
    log.hidden = false;
    log.textContent = j.log.join("\n") + (j.running ? "\n…" : "");
    log.scrollTop = log.scrollHeight;
    const sum = $("#buildSummary");
    sum.replaceChildren();
    if (j.running || !j.result) { if (j.error) sum.append(el("div", { class: "gate err" }, j.error)); return; }
    const r = j.result;
    if (j.kind === "build") {
      if (r.stopped && r.stopped.length) sum.append(el("div", { class: "gate err" }, el("strong", null, "The build stopped:"), el("ul", null, ...r.stopped.map((s) => el("li", null, s)))));
      else if (r.ok) sum.append(el("div", { class: "gate info" }, `Built ${r.wrote.length} file${r.wrote.length === 1 ? "" : "s"}.`));
      else sum.append(el("div", { class: "gate err" }, `The build failed (exit code ${r.exit}) — see the log.`));
      if (r.adjustments.length) sum.append(el("div", { class: "gate warn" }, el("strong", null, "Adjustments applied:"), el("ul", null, ...r.adjustments.map((s) => el("li", null, s)))));
      if (r.unverified.length) sum.append(el("details", null, el("summary", null, `${r.unverified.length} unverified title${r.unverified.length === 1 ? "" : "s"} (check against bulletin.utulsa.edu)`), el("ul", { class: "plain" }, ...r.unverified.map((s) => el("li", null, s)))));
    } else if (j.kind === "parse") {
      const box = $("#parseResult");
      box.replaceChildren();
      if (r.exit !== 0) box.append(el("div", { class: "gate err" }, `The parser failed (exit code ${r.exit}) — see the log below. transcript-data.json was backed up as ${r.backup}.`));
      else if (!r.changed) box.append(el("div", { class: "gate info" }, "Parsed: transcript-data.json is unchanged."));
      else box.append(el("div", { class: "gate info" }, `Parsed: transcript-data.json changed (previous copy in backup set ${r.backup}).`), renderDiff(r.diff));
    }
  }
  async function startJob(path, body) {
    let res;
    try { res = await api(path, { method: "POST", body }); } catch (e) { toast("Refused: " + e.message, 6000); return; }
    if (!res || res.ok === false) { toast("Refused: " + (res && res.error), 7000); return; }
    state.job = res.job;
    $("#buildBtn").disabled = true;
    $("#parseBtn").disabled = true;
    renderJob();
    pollJob();
  }
  function pollJob() {
    clearTimeout(state.pollTimer);
    state.pollTimer = setTimeout(async () => {
      try {
        const r = await api("/api/transcript/job");
        state.job = r.job;
        renderJob();
        if (state.job && state.job.running) pollJob();
        else { toast(`${state.job.kind === "parse" ? "Parse" : "Build"} finished.`); await loadState(); }
      } catch (e) { toast("Lost the job status: " + e.message); }
    }, 500);
  }

  // ---------------------------------------------------------------- review & save
  function renderCounts() {
    const n = state.data.draftCount || 0;
    $("#draftCount").textContent = String(n);
    $("#draftCount").hidden = n === 0;
    state.unsaved = n > 0;
  }
  function issueList(items) { return el("ul", null, ...items.map((i) => el("li", null, i.key + (i.lang ? " (" + i.lang.toUpperCase() + ")" : "") + ": " + i.message))); }
  async function openReview() {
    const dlg = $("#reviewDlg"), body = $("#reviewBody");
    body.replaceChildren(el("p", { class: "muted" }, "Preparing…"));
    $("#saveBtn").disabled = true;
    dlg.showModal();
    let r;
    try { r = await api("/api/transcript/review"); } catch (e) { body.replaceChildren(el("p", null, "Review failed: " + e.message)); return; }
    body.replaceChildren();
    if (r.noop) { body.append(el("p", { class: "muted" }, "No changes — the files on disk already match.")); return; }
    for (const f of r.files) {
      body.append(el("h3", null, f.path));
      body.append(el("ul", { class: "changes" }, ...f.changes.map((c) => el("li", null, c.text))));
      if (f.diskChanged) body.append(el("div", { class: "gate err" }, "This file changed on disk since it was loaded. Close this and click Reload in the banner, then review again."));
      const g = f.gate;
      if (g.blocking.length) body.append(el("div", { class: "gate err" }, el("strong", null, "Blocking errors (fix before saving):"), issueList(g.blocking)));
      if (g.warnings.length) body.append(el("div", { class: "gate warn" }, el("strong", null, "Warnings (saving is allowed):"), issueList(g.warnings.slice(0, 12)), g.warnings.length > 12 ? el("p", { class: "muted" }, `… and ${g.warnings.length - 12} more`) : null));
      if (g.preexisting.length) body.append(el("div", { class: "gate info" }, el("strong", null, "Pre-existing errors elsewhere in this file (not blocking):"), issueList(g.preexisting)));
      body.append(renderDiff(f.diff));
    }
    $("#saveBtn").disabled = !r.ok;
  }
  async function doSave() {
    $("#saveBtn").disabled = true;
    let r;
    try { r = await api("/api/transcript/save", { method: "POST", body: {} }); } catch (e) { toast("Save failed: " + e.message); $("#saveBtn").disabled = false; return; }
    if (!r.ok) { toast(r.message || r.error, 7000); if (r.error === "changed-on-disk") { $("#reviewDlg").close(); showDiskBanner(r.message); } else $("#saveBtn").disabled = false; return; }
    $("#reviewDlg").close();
    toast(r.message, 5000);
    state.dirtyTitleIds.clear();
    await loadState();
  }
  async function discardAll() {
    if (!state.data.draftCount) { $("#reviewDlg").close(); return; }
    if (!confirm(`Discard all ${state.data.draftCount} draft edit(s)? The files on disk are not touched.`)) return;
    await api("/api/transcript/drafts/discard", { method: "POST", body: {} });
    $("#reviewDlg").close();
    state.dirtyTitleIds.clear();
    await loadState();
    toast("Drafts discarded.");
  }

  // ---------------------------------------------------------------- publish
  async function openPublish() {
    const dlg = $("#publishDlg"), body = $("#publishBody");
    body.replaceChildren(el("p", { class: "muted" }, "Checking…"));
    $("#publishGo").disabled = true;
    dlg.showModal();
    await refreshPlan();
  }
  async function refreshPlan() {
    const body = $("#publishBody");
    let p;
    try { p = await api("/api/transcript/publish-plan"); } catch (e) { body.replaceChildren(el("p", null, "Could not plan: " + e.message)); return; }
    body.replaceChildren();
    const ul = el("ul", { class: "changes" });
    for (const it of p.items) {
      const li = el("li", null, el("strong", null, it.title + ": "), it.action === "overwrite" ? "overwrite " : "add ", el("code", null, it.target));
      if (it.moves.length) li.append(el("div", { class: "muted small" }, "moves to the backup set: " + it.moves.join(", ")));
      ul.append(li);
    }
    body.append(el("p", null, "Publishing copies the newest built PDFs from ", el("code", null, state.data.builtDir + "/"), " (the date in the name is the one they were built with) and then regenerates ", el("code", null, "js/docs-data.js"), ". Every file overwritten or moved is backed up first. Nothing is committed."), ul);
    if (p.errors.length) body.append(el("div", { class: "gate err" }, el("strong", null, "Blocked — fix these first:"), el("ul", null, ...p.errors.map((e) => el("li", null, e.message)))));
    if (p.warnings.length) body.append(el("div", { class: "gate warn" }, el("strong", null, "Warnings (publishing is allowed):"), el("ul", null, ...p.warnings.map((w) => el("li", null, w.message)))));
    $("#publishGo").disabled = !p.ok;
  }
  async function doPublish() {
    $("#publishGo").disabled = true;
    let r;
    try { r = await api("/api/transcript/publish", { method: "POST", body: {} }); } catch (e) { toast("Publish failed: " + e.message, 6000); $("#publishGo").disabled = false; return; }
    if (!r.ok) { toast(r.message || r.error, 7000); if (r.plan) await refreshPlan(); else $("#publishGo").disabled = false; return; }
    $("#publishDlg").close();
    const man = r.manifest && r.manifest.ok ? "js/docs-data.js regenerated." : "js/docs-data.js NOT regenerated: " + (r.manifest && r.manifest.output);
    setBanner("published", "", `Published: ${r.added.concat(r.overwritten).join(", ")}${r.moved.length ? " — moved to backup " + r.backup + ": " + r.moved.join(", ") : ""}. ${man} Check the Transcript button in Preview ↗ (About page), then commit.`, [{ label: "Dismiss", onclick: () => clearBanner("published") }]);
    toast("Published.", 5000);
    await loadState();
  }

  // ---------------------------------------------------------------- state
  function showDiskBanner(msg) {
    if (!banners.disk) setBanner("disk", "warn", msg || "A transcript input file changed on disk (VS Code, Claude Code, git, or a parse). Saving is refused until you reload; drafts are kept.", [{ label: "Reload", primary: true, onclick: reloadFromDisk }]);
  }
  async function reloadFromDisk() {
    const d = await api("/api/transcript/reload", { method: "POST", body: {} });
    clearBanner("disk");
    await loadState(d);
    toast("Reloaded from disk.");
  }
  async function loadState(via) {
    const d = via || (await api("/api/transcript/state"));
    state.data = d;
    state.job = d.job;
    $("#previewLink").href = "http://127.0.0.1:5501/about.html";
    if (!d.draftCount) state.dirtyTitleIds.clear();
    // rows with drafts: those whose live value differs from disk are unknown client-side; the server's draft flag is per file
    markDrafts();
    const ro = Object.entries(d.files).filter(([n, f]) => f.readOnly && n !== "data").map(([, f]) => f.readOnly);
    if (ro.length) setBanner("readonly", "err", ro.join(" · ")); else clearBanner("readonly");
    if (Object.values(d.files).some((f) => f.diskChanged)) showDiskBanner(); else clearBanner("disk");
    if (d.autosave) {
      setBanner("autosave", "warn", `Unsaved transcript edits from ${d.autosave.saved} were found (${d.autosave.files.join(", ")}).`, [
        { label: "Restore drafts", primary: true, onclick: async () => { const r = await api("/api/transcript/autosave/restore", { method: "POST", body: {} }); clearBanner("autosave"); toast(`Restored drafts in ${r.applied} file(s)` + (r.fileChanged ? " (a file changed on disk since)" : "")); await loadState(); } },
        { label: "Discard", onclick: async () => { await api("/api/transcript/autosave/discard", { method: "POST", body: {} }); clearBanner("autosave"); } },
      ]);
    }
    renderCounts();
    renderSource();
    renderFilters();
    renderTitles();
    renderProfile();
    renderAdjustments();
    renderBuild();
    renderJob();
    if (state.job && state.job.running) pollJob();
  }

  // ---------------------------------------------------------------- heartbeat
  let hbFailures = 0;
  async function heartbeat() {
    try { await api("/api/heartbeat", { method: "POST", body: {} }); hbFailures = 0; clearBanner("offline"); }
    catch (e) { if (++hbFailures >= 2) setBanner("offline", "err", "The editor server is not answering. If it was closed, close this window and start the editor again."); }
  }

  // ---------------------------------------------------------------- wiring
  function init() {
    window.Editor.initTabs();
    if (!token) { window.Editor.noToken(); return; }
    $("#search").addEventListener("input", (e) => { state.query = fold(e.target.value.trim()); renderTitles(); });
    $("#parseBtn").addEventListener("click", () => { const pdf = $("#rawPdf").value; if (!pdf) return; if (confirm(`Parse ${pdf}?\n\ntranscript-data.json is backed up first, then rewritten from this PDF.`)) startJob("/api/transcript/parse", { pdf }); });
    $("#buildBtn").addEventListener("click", () => startJob("/api/transcript/build", { strict: $("#buildStrict").checked, date: $("#buildDate").value.trim(), pdf: $("#buildPdf").checked }));
    $("#reviewBtn").addEventListener("click", openReview);
    $("#saveBtn").addEventListener("click", doSave);
    $("#discardBtn").addEventListener("click", discardAll);
    $("#publishBtn").addEventListener("click", openPublish);
    $("#publishGo").addEventListener("click", doPublish);
    for (const b of document.querySelectorAll("[data-open]")) b.addEventListener("click", async () => { try { await api("/api/transcript/open-folder", { method: "POST", body: { which: b.dataset.open } }); } catch (e) { toast("Could not open the folder: " + e.message); } });
    for (const b of document.querySelectorAll("[data-toggle]")) b.addEventListener("click", () => { const t = document.getElementById(b.dataset.toggle); t.hidden = !t.hidden; b.textContent = b.textContent.replace(/[▸▾]$/, t.hidden ? "▸" : "▾"); });
    $("#previewLink").addEventListener("click", async (e) => { e.preventDefault(); try { await api("/api/open-preview", { method: "POST", body: {} }); toast("Preview opened in your browser (open the About page for the Transcript button)."); } catch (err) { toast("Could not open the preview: " + err.message); } });
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); if (!$("#reviewDlg").open) openReview(); }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "f" && !e.shiftKey) { e.preventDefault(); $("#search").focus(); $("#search").select(); }
    });
    window.addEventListener("beforeunload", (e) => { if (state.unsaved && !window.__navigating) { e.preventDefault(); e.returnValue = ""; } });
    loadState().catch((e) => setBanner("load", "err", "Could not load the transcript state: " + e.message));
    heartbeat();
    setInterval(heartbeat, 5000);
  }
  init();
  window.__transcript = state; // for tests
})();
