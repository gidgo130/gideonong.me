/* Site editor — Phase 1 UI (vanilla JS, no build step). */
(function () {
  "use strict";

  // token, api(), el(), toast, banners, renderDiff: static/common.js
  const { token, $, el, api, toast, setBanner, clearBanner, banners, fold, renderDiff } = window.Editor;

  const STATUS_LABEL = { both: "EN + ES", "en-only": "EN only", "es-only": "ES only", same: "ES = EN", todo: "TODO" };
  const STATUS_ORDER = ["both", "same", "todo", "en-only", "es-only"];

  const state = {
    data: null,           // /api/state payload
    drafts: {},           // "en.key" -> value (local, optimistic)
    serverDrafts: {},     // "en.key" -> value as the server last confirmed it
    issuesByKey: {},      // key -> [issue]
    statusByKey: {},      // key -> status (live, with drafts)
    query: "",
    attention: false,
    statusFilter: null,
    unsaved: false,
  };

  // ---------------------------------------------------------------- helpers
  function liveValue(lang, key) {
    const k = lang + "." + key;
    if (k in state.drafts) return state.drafts[k];
    const e = state.data.file.entries[key];
    return e ? e[lang] : null;
  }
  function autosize(ta) { ta.style.height = "auto"; ta.style.height = Math.max(34, ta.scrollHeight + 2) + "px"; }
  function computeStatuses() {
    state.statusByKey = {};
    for (const key of state.data.file.keys) {
      const e = state.data.file.entries[key];
      const en = liveValue("en", key), es = liveValue("es", key);
      let st;
      if (en === null) st = "es-only";
      else if (es === null) st = "en-only";
      else if (/\bTODO\b/.test(en) || /\bTODO\b/.test(es)) st = "todo";
      else if (en === es && e.status === "same") st = "same";
      else if (en === es && !(key in state.drafts)) st = e.status; // server decided (allow-list)
      else if (en === es) st = "same";
      else st = "both";
      state.statusByKey[key] = st;
    }
  }
  function rowNeedsAttention(key) {
    return state.statusByKey[key] !== "both" || (state.issuesByKey[key] || []).length > 0 ||
      ("en." + key) in state.drafts || ("es." + key) in state.drafts;
  }
  function rowMatches(key) {
    if (state.statusFilter && state.statusByKey[key] !== state.statusFilter) return false;
    if (state.attention && !rowNeedsAttention(key)) return false;
    if (!state.query) return true;
    const hay = fold(key + " " + (liveValue("en", key) || "") + " " + (liveValue("es", key) || ""));
    return state.query.split(/\s+/).filter(Boolean).every((tok) => hay.includes(tok));
  }

  // ---------------------------------------------------------------- render
  function renderCounts() {
    const c = $("#counts");
    c.replaceChildren();
    const counts = {};
    for (const key of state.data.file.keys) counts[state.statusByKey[key]] = (counts[state.statusByKey[key]] || 0) + 1;
    for (const st of STATUS_ORDER) {
      if (!counts[st]) continue;
      const p = el("span", {
        class: "pill st-" + st + (state.statusFilter === st ? " active" : ""),
        title: "Show only " + STATUS_LABEL[st],
        onclick: () => { state.statusFilter = state.statusFilter === st ? null : st; renderCounts(); applyFilters(); },
      }, STATUS_LABEL[st] + " " + counts[st]);
      c.append(p);
    }
    const n = Object.keys(state.drafts).length;
    $("#draftCount").textContent = String(n);
    $("#draftCount").hidden = n === 0;
    state.unsaved = n > 0;
  }

  function renderIssues(key, ul) {
    ul.replaceChildren();
    for (const i of state.issuesByKey[key] || []) {
      ul.append(el("li", { class: i.level, title: i.code }, (i.lang ? i.lang.toUpperCase() + ": " : "") + i.message));
    }
    const row = ul.closest(".row");
    if (row) row.classList.toggle("has-error", (state.issuesByKey[key] || []).some((i) => i.level === "error"));
  }

  function renderRow(key) {
    const e = state.data.file.entries[key];
    const row = el("article", { class: "row", id: "key-" + key, "data-key": key });
    const head = el("div", { class: "rowhead" }, el("code", null, key), el("span", { class: "pill st-" + state.statusByKey[key] }, STATUS_LABEL[state.statusByKey[key]]));
    const hint = e.enNote || e.esNote;
    if (hint) head.append(el("span", { class: "hint", title: "Comment in the file" }, hint));
    row.append(head);
    const cols = el("div", { class: "cols" });
    for (const lang of ["en", "es"]) {
      const wrap = el("div");
      wrap.append(el("label", null, lang.toUpperCase() + (e[lang + "Line"] ? "  · line " + e[lang + "Line"] : "")));
      if (e[lang] === null || e[lang] === undefined) {
        wrap.append(el("div", { class: "missing" }, "missing in " + lang.toUpperCase() + " — adding keys comes in a later phase"));
      } else {
        const ta = el("textarea", { "data-lang": lang, "data-key": key, rows: 1, spellcheck: lang === "en" ? "true" : "true", lang: lang });
        ta.value = liveValue(lang, key);
        if ((lang + "." + key) in state.drafts) ta.classList.add("draft");
        if (state.data.readOnly) ta.disabled = true;
        ta.addEventListener("input", () => { autosize(ta); queueDraft(lang, key, ta.value); });
        wrap.append(ta);
      }
      cols.append(wrap);
    }
    row.append(cols);
    const ul = el("ul", { class: "issues" });
    row.append(ul);
    renderIssues(key, ul);
    row.classList.toggle("has-draft", ("en." + key) in state.drafts || ("es." + key) in state.drafts);
    return row;
  }

  function renderAll() {
    const list = $("#list");
    const nav = $("#sections");
    list.replaceChildren();
    nav.replaceChildren();
    if (!state.data.file) {
      list.append(el("div", { class: "empty-state" }, "The file could not be loaded. See the banner above."));
      return;
    }
    for (const s of state.data.file.sections) {
      const sec = el("section", { id: "sec-" + s.id, "data-section": s.id });
      sec.append(el("h2", null, s.title + (s.esOnly ? " (ES only)" : "")));
      if (s.note) sec.append(el("p", { class: "note" }, s.note));
      for (const key of s.keys) sec.append(renderRow(key));
      list.append(sec);
      nav.append(el("a", { href: "#sec-" + s.id, "data-section": s.id }, s.title, el("span", { class: "n" }, String(s.keys.length))));
    }
    requestAnimationFrame(() => document.querySelectorAll("#list textarea").forEach(autosize));
    applyFilters();
    focusHashTarget();
  }

  function applyFilters() {
    let shown = 0;
    for (const sec of document.querySelectorAll("#list section")) {
      let n = 0;
      for (const row of sec.querySelectorAll(".row")) {
        const ok = rowMatches(row.dataset.key);
        row.hidden = !ok;
        if (ok) n++;
      }
      sec.hidden = n === 0;
      shown += n;
      const link = $('#sections a[data-section="' + sec.dataset.section + '"]');
      if (link) { link.classList.toggle("empty", n === 0); link.querySelector(".n").textContent = String(n); }
    }
    let empty = $("#list .empty-state");
    if (shown === 0) {
      if (!empty) $("#list").append(el("div", { class: "empty-state" }, "No keys match."));
    } else if (empty) empty.remove();
    requestAnimationFrame(() => document.querySelectorAll("#list .row:not([hidden]) textarea").forEach(autosize));
  }

  function focusHashTarget() {
    const h = location.hash.replace(/^#/, "");
    if (!h) return;
    const t = document.getElementById(h);
    if (t) { t.scrollIntoView({ block: "start" }); if (t.classList.contains("row")) t.classList.add("is-target"); }
  }

  function refreshRowUI(key) {
    const row = document.getElementById("key-" + key);
    if (!row) return;
    const pill = row.querySelector(".rowhead .pill");
    pill.className = "pill st-" + state.statusByKey[key];
    pill.textContent = STATUS_LABEL[state.statusByKey[key]];
    for (const ta of row.querySelectorAll("textarea")) ta.classList.toggle("draft", (ta.dataset.lang + "." + key) in state.drafts);
    row.classList.toggle("has-draft", ("en." + key) in state.drafts || ("es." + key) in state.drafts);
    renderIssues(key, row.querySelector(".issues"));
  }

  // ---------------------------------------------------------------- drafts
  const pending = {};
  function queueDraft(lang, key, value) {
    const k = lang + "." + key;
    clearTimeout(pending[k]);
    // optimistic local state so filters/counts follow typing
    const disk = state.data.file.entries[key][lang];
    if (value === disk) delete state.drafts[k]; else state.drafts[k] = value;
    computeStatuses();
    renderCounts();
    refreshRowUI(key);
    pending[k] = setTimeout(() => sendDraft(lang, key, value), 300);
  }
  async function sendDraft(lang, key, value) {
    const k = lang + "." + key;
    try {
      const r = await api("/api/draft", { method: "POST", body: { lang, key, value } });
      if (!r || r.ok === false) { toast("Draft rejected: " + (r && r.error)); revertDraft(lang, key, value); return; }
      // the server drops a draft equal to the disk value; mirror that
      if (value === state.data.file.entries[key][lang]) delete state.serverDrafts[k]; else state.serverDrafts[k] = value;
      state.issuesByKey[key] = r.issues || [];
      applyGate(r.gate);
      refreshRowUI(key);
    } catch (e) {
      toast("Could not send draft: " + e.message);
      revertDraft(lang, key, value);
    }
  }
  // The POST failed, so the server never got `value`: put the row back to what
  // the server last confirmed, unless the user has typed again since (then the
  // newer value is already queued and will be sent on its own).
  function revertDraft(lang, key, value) {
    const k = lang + "." + key;
    if (state.drafts[k] !== value) return;
    if (k in state.serverDrafts) state.drafts[k] = state.serverDrafts[k]; else delete state.drafts[k];
    const row = document.getElementById("key-" + key);
    const ta = row && row.querySelector('textarea[data-lang="' + lang + '"]');
    if (ta) { ta.value = liveValue(lang, key); autosize(ta); }
    computeStatuses();
    renderCounts();
    refreshRowUI(key);
  }
  function applyGate(gate) {
    if (!gate) return;
    const pre = gate.preexisting || [];
    if (pre.length) {
      const c = el("div", null, `${pre.length} pre-existing error${pre.length > 1 ? "s" : ""} in keys this draft doesn't touch. They don't block saving, and adding keys comes in a later phase.`);
      const ul = el("ul");
      for (const i of pre.slice(0, 8)) ul.append(el("li", null, i.key + (i.lang ? " (" + i.lang.toUpperCase() + ")" : "") + ": " + i.message));
      if (pre.length > 8) ul.append(el("li", null, "… and " + (pre.length - 8) + " more"));
      c.append(ul);
      setBanner("preexisting", "warn", c);
    } else clearBanner("preexisting");
  }

  // ---------------------------------------------------------------- state
  async function loadState(via) {
    const d = via || (await api("/api/state"));
    state.data = d;
    state.drafts = Object.assign({}, d.drafts || {});
    state.serverDrafts = Object.assign({}, d.drafts || {});
    state.issuesByKey = {};
    for (const i of d.issues || []) (state.issuesByKey[i.key] = state.issuesByKey[i.key] || []).push(i);
    $("#previewLink").href = d.previewUrl;
    $("#fileName").textContent = d.file ? d.file.path : "js/translations.js";
    if (d.readOnly) {
      setBanner("readonly", "err", "Read-only: " + d.loadError + " — the editor refuses to write a file it cannot re-emit byte for byte.");
      $("#reviewBtn").disabled = true;
    } else { clearBanner("readonly"); $("#reviewBtn").disabled = false; }
    if (d.file) computeStatuses();
    renderCounts();
    renderAll();
    applyGate(d.gate);
    if (d.autosave) {
      const a = d.autosave;
      setBanner("autosave", "warn",
        `Unsaved drafts from ${a.saved} were found (${a.count} edit${a.count > 1 ? "s" : ""}${a.fileChanged ? "; the file changed on disk since" : ""}).`,
        [
          { label: "Restore drafts", primary: true, onclick: async () => { const r = await api("/api/autosave/restore", { method: "POST", body: {} }); clearBanner("autosave"); toast(`Restored ${r.applied} draft(s)` + (r.skipped ? `, ${r.skipped} no longer apply` : "")); await loadState(); } },
          { label: "Discard", onclick: async () => { await api("/api/autosave/discard", { method: "POST", body: {} }); clearBanner("autosave"); } },
        ]);
    }
    if (d.git && d.git.status) setBanner("git", "", "git: js/translations.js already has uncommitted changes (" + d.git.status.trim() + ")."); else clearBanner("git");
  }

  async function reloadFromDisk() {
    const d = await api("/api/reload", { method: "POST", body: {} });
    clearBanner("disk");
    await loadState(d);
    toast("Reloaded from disk. " + Object.keys(state.drafts).length + " draft(s) re-applied.");
  }

  // ---------------------------------------------------------------- heartbeat
  let hbFailures = 0;
  async function heartbeat() {
    try {
      const r = await api("/api/heartbeat", { method: "POST", body: {} });
      hbFailures = 0;
      clearBanner("offline");
      if (r.diskChanged) {
        if (!banners.disk) setBanner("disk", "warn", "js/translations.js changed on disk (VS Code, Claude Code, git). Saving is refused until you reload; your drafts are kept and re-applied.",
          [{ label: "Reload", primary: true, onclick: reloadFromDisk }]);
      } else clearBanner("disk");
    } catch (e) {
      if (++hbFailures >= 2) setBanner("offline", "err", "The editor server is not answering. If it was closed, close this window and start the editor again.");
    }
  }

  // ---------------------------------------------------------------- review & save
  function issueList(items) {
    const ul = el("ul");
    for (const i of items) ul.append(el("li", null, i.key + (i.lang ? " (" + i.lang.toUpperCase() + ")" : "") + ": " + i.message));
    return ul;
  }
  async function openReview() {
    const dlg = $("#reviewDlg");
    const body = $("#reviewBody");
    body.replaceChildren(el("p", { class: "muted" }, "Preparing…"));
    $("#saveBtn").disabled = true;
    dlg.showModal();
    let r;
    try { r = await api("/api/review"); } catch (e) { body.replaceChildren(el("p", null, "Review failed: " + e.message)); return; }
    body.replaceChildren();
    $("#reviewFile").textContent = r.file || "";
    if (r.readOnly) { body.append(el("div", { class: "gate err" }, "Read-only: " + r.error)); return; }
    if (r.noop) { body.append(el("p", { class: "muted" }, "No changes — the file on disk already matches. Saving would write nothing.")); return; }
    const ul = el("ul", { class: "changes" });
    for (const c of r.changes) {
      ul.append(el("li", null, el("strong", null, c.section + " › "), el("code", null, c.key), ` (${c.lang.toUpperCase()}): `,
        el("span", { class: "old" }, c.old === null ? "(missing)" : c.old), " → ", el("span", { class: "new" }, c.new)));
    }
    body.append(el("p", null, `${r.changes.length} change${r.changes.length > 1 ? "s" : ""}, ${r.diffStats.removed} line${r.diffStats.removed === 1 ? "" : "s"} replaced. Saving writes exactly the diff below, then re-reads the file.`), ul);
    const g = r.gate;
    if (r.diskChanged) body.append(el("div", { class: "gate err" }, "The file changed on disk since it was loaded. Close this, click Reload in the banner, then review again."));
    if (g.blocking.length) body.append(el("div", { class: "gate err" }, el("strong", null, "Blocking errors (fix before saving):"), issueList(g.blocking)));
    const touched = new Set(r.changes.map((c) => c.key));
    const mine = g.warnings.filter((w) => touched.has(w.key));
    const elsewhere = g.warnings.length - mine.length;
    if (mine.length || elsewhere) {
      const box = el("div", { class: "gate warn" }, el("strong", null, mine.length ? "Warnings on the keys you changed (saving is allowed):" : "Warnings (saving is allowed):"));
      if (mine.length) box.append(issueList(mine));
      if (elsewhere) box.append(el("p", { class: "muted" }, `${elsewhere} pre-existing warning${elsewhere > 1 ? "s" : ""} elsewhere in the file — use “Needs attention” to see them.`));
      body.append(box);
    }
    if (g.preexisting.length) body.append(el("div", { class: "gate info" }, el("strong", null, "Pre-existing errors in untouched keys (not blocking):"), issueList(g.preexisting)));
    body.append(el("h3", null, "Unified diff"), renderDiff(r.diff));
    $("#saveBtn").disabled = !!(r.diskChanged || g.blocking.length);
  }
  async function doSave() {
    $("#saveBtn").disabled = true;
    let r;
    try { r = await api("/api/save", { method: "POST", body: {} }); } catch (e) { toast("Save failed: " + e.message); $("#saveBtn").disabled = false; return; }
    if (!r.ok) {
      toast(r.message || r.error, 6000);
      if (r.error === "changed-on-disk") { $("#reviewDlg").close(); setBanner("disk", "warn", r.message, [{ label: "Reload", primary: true, onclick: reloadFromDisk }]); }
      else $("#saveBtn").disabled = false;
      return;
    }
    $("#reviewDlg").close();
    toast(r.message, 5000);
    await loadState();
  }
  async function discardAll() {
    if (!Object.keys(state.drafts).length) { $("#reviewDlg").close(); return; }
    if (!confirm("Discard all " + Object.keys(state.drafts).length + " draft(s)? The file on disk is not touched.")) return;
    await api("/api/drafts/discard", { method: "POST", body: {} });
    $("#reviewDlg").close();
    await loadState();
    toast("Drafts discarded.");
  }

  // ---------------------------------------------------------------- restore
  async function openRestore() {
    const dlg = $("#restoreDlg");
    const body = $("#restoreBody");
    body.replaceChildren(el("p", { class: "muted" }, "Loading…"));
    dlg.showModal();
    const r = await api("/api/backups");
    body.replaceChildren();
    if (!r.sets.length) { body.append(el("p", { class: "muted" }, "No backups yet. The first save creates one.")); return; }
    const table = el("table", { class: "sets" });
    table.append(el("tr", null, el("th", null, "Set"), el("th", null, "Created"), el("th", null, "Reason"), el("th", null, "Files"), el("th")));
    for (const s of r.sets) {
      const actions = el("td", { class: "actions" });
      const diffRow = el("tr", { hidden: "" }, el("td", { colspan: 5 }));
      actions.append(
        el("button", { type: "button", class: "ghost", onclick: async () => {
          const f = s.files[0];
          if (!f) return;
          const d = await api("/api/backups/" + encodeURIComponent(s.id) + "/file?path=" + encodeURIComponent(f.path));
          diffRow.firstChild.replaceChildren(d.sameAsCurrent ? el("p", { class: "muted" }, "Identical to the current file.") : el("div", { class: "setdiff" }, el("p", { class: "muted" }, "Restoring this set would apply:"), renderDiff(d.diff)));
          diffRow.hidden = !diffRow.hidden;
        } }, "Compare"),
        " ",
        el("button", { type: "button", class: "primary", onclick: async () => {
          if (!confirm("Restore " + s.id + "?\n\nThe current js/translations.js is backed up first, then replaced by this copy.")) return;
          const res = await api("/api/restore", { method: "POST", body: { set: s.id } });
          if (res && res.ok) { dlg.close(); toast("Restored " + res.restored.join(", ") + " (current file saved as " + res.backup + ")", 6000); await loadState(); }
          else toast("Restore failed: " + (res && res.error));
        } }, "Restore"));
      table.append(el("tr", null, el("td", null, el("code", null, s.id)), el("td", null, s.created), el("td", null, s.reason), el("td", null, s.files.map((f) => f.path).join(", ")), actions), diffRow);
    }
    body.append(table);
  }

  // ---------------------------------------------------------------- wiring
  function init() {
    window.Editor.initTabs();
    if (!token) { window.Editor.noToken(); return; }
    $("#search").addEventListener("input", (e) => { state.query = fold(e.target.value.trim()); applyFilters(); });
    $("#attention").addEventListener("change", (e) => { state.attention = e.target.checked; applyFilters(); });
    $("#reviewBtn").addEventListener("click", openReview);
    $("#saveBtn").addEventListener("click", doSave);
    $("#discardBtn").addEventListener("click", discardAll);
    $("#restoreBtn").addEventListener("click", openRestore);
    // Preview opens in the normal browser (the editor window is a WebView2 app window).
    $("#previewLink").addEventListener("click", async (e) => {
      e.preventDefault();
      try { await api("/api/open-preview", { method: "POST", body: {} }); toast("Preview opened in your browser."); }
      catch (err) { window.open($("#previewLink").href, "_blank", "noopener"); }
    });
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); if (!$("#reviewDlg").open) openReview(); }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "f" && !e.shiftKey) { e.preventDefault(); $("#search").focus(); $("#search").select(); }
    });
    // drafts live on the server (and are autosaved), so switching tabs is safe; only warn when leaving otherwise
    window.addEventListener("beforeunload", (e) => { if (state.unsaved && !window.__navigating) { e.preventDefault(); e.returnValue = ""; } });
    window.addEventListener("hashchange", focusHashTarget);
    loadState().catch((e) => setBanner("load", "err", "Could not load the editor state: " + e.message));
    heartbeat();
    setInterval(heartbeat, 5000);
  }
  init();
  window.__editor = state; // for tests
})();
