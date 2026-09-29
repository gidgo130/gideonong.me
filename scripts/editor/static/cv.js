/* CV & résumé page — Phase 1b (vanilla JS, no build step). */
(function () {
  "use strict";
  const { token, $, el, api, toast, setBanner, clearBanner, fmtTime } = window.Editor;

  const state = {
    masters: [],       // /api/cv/state → masters
    checks: {},        // id → check result
    job: null,
    open: null,        // id whose details are shown
    pollTimer: null,
  };

  // ---------------------------------------------------------------- rendering
  function pill(cls, text, title) { return el("span", { class: "pill " + cls, title: title || null }, text); }

  function fitCell(c) {
    if (!c) return el("span", { class: "muted" }, "—");
    if (!c.fit) return el("span", { class: "muted" }, "n/a");
    const s = c.fit.summary;
    if (!s.count) return el("span", { class: "muted" }, "no entry lines");
    const w = s.worst;
    const cls = s.overflow ? "st-todo" : s.tight ? "st-same" : "st-both";
    const label = s.overflow ? `${s.overflow} too long` : s.tight ? `${s.tight} tight` : `${s.count} fit`;
    const wrap = el("span", null, pill(cls, label, "One-line estimate from the .docx; the PDF check is the authority"));
    if (w) wrap.append(" ", el("span", { class: "muted small" }, `worst: ${w.left_pt} pt left`));
    return wrap;
  }

  function pdfCell(m, c) {
    const p = m.pdf;
    if (!p.exists) return el("span", { class: "muted" }, "not exported");
    const wrap = el("span", null, fmtTime(p.mtime));
    if (c && c.pdf && c.pdf.exists) {
      wrap.append(" · ", `${c.pdf.pages} page${c.pdf.pages === 1 ? "" : "s"}`);
      if (c.pdf.stale) wrap.append(" ", pill("st-todo", "stale", "older than the master"));
    }
    return wrap;
  }

  function checksCell(c) {
    if (!c) return el("span", { class: "muted" }, "not checked");
    const wrap = el("span");
    if (c.errors.length) wrap.append(pill("st-todo", `${c.errors.length} error${c.errors.length > 1 ? "s" : ""}`));
    if (c.warnings.length) wrap.append(" ", pill("st-same", `${c.warnings.length} warning${c.warnings.length > 1 ? "s" : ""}`));
    if (!c.errors.length && !c.warnings.length) wrap.append(pill("st-both", "clean"));
    return wrap;
  }

  function renderTable() {
    const t = $("#docs");
    t.replaceChildren(el("tr", null, el("th", null, "Document"), el("th", null, "Master (.docx)"), el("th", null, "PDF"), el("th", null, "Fit"), el("th", null, "Checks"), el("th")));
    for (const m of state.masters) {
      const c = state.checks[m.id];
      const row = el("tr", { "data-id": m.id, class: state.open === m.id ? "is-open" : "" });
      const name = el("td", null, el("strong", null, m.title), el("div", { class: "muted small" }, m.publishType ? `publishes as assets/pdfs/${m.publishType}/` : "private — never published"));
      const master = el("td");
      if (!m.exists) master.append(pill("st-todo", "missing"), " ", el("code", null, m.file));
      else {
        master.append(fmtTime(m.mtime));
        if (m.openInWord) master.append(" ", pill("st-todo", "open in Word", "Close it in Word before exporting"));
      }
      const actions = el("td", { class: "actions" });
      const running = state.job && state.job.running;
      actions.append(
        el("button", { type: "button", class: "ghost", disabled: (!m.exists || m.openInWord || running) ? "" : null, onclick: () => startExport([m.id]) }, "Export"),
        " ",
        el("button", { type: "button", class: "ghost", onclick: () => { state.open = state.open === m.id ? null : m.id; renderTable(); renderDetails(); } }, state.open === m.id ? "Hide" : "Details"));
      row.append(name, master, el("td", null, pdfCell(m, c)), el("td", null, fitCell(c)), el("td", null, checksCell(c)), actions);
      t.append(row);
    }
    const anyOpen = state.masters.some((m) => m.openInWord);
    $("#exportBtn").disabled = !!(state.job && state.job.running) || !state.masters.some((m) => m.exists && !m.openInWord);
    $("#exportBtn").title = anyOpen ? "Masters open in Word are skipped" : "Export every master to PDF with a private Word instance";
  }

  function meter(line) {
    const pct = Math.max(0, Math.min(100, 100 - line.left_pct));
    const cls = line.status === "overflow" ? "over" : line.status === "tight" ? "tight" : "";
    return el("div", { class: "meter " + cls, title: `${line.used_pt} of ${line.avail_pt} pt used` }, el("div", { class: "bar", style: `width:${pct}%` }));
  }

  function renderDetails() {
    const box = $("#details");
    box.replaceChildren();
    const m = state.masters.find((x) => x.id === state.open);
    const c = state.open && state.checks[state.open];
    if (!m) return;
    box.append(el("h2", null, m.title, " ", el("span", { class: "muted small" }, m.file)));
    if (!c) { box.append(el("p", { class: "muted" }, "Not checked yet — click Run checks.")); return; }
    if (c.errors.length) box.append(el("div", { class: "gate err" }, el("strong", null, "Errors (block publishing):"), el("ul", null, ...c.errors.map((e) => el("li", null, e.message)))));
    if (c.warnings.length) box.append(el("div", { class: "gate warn" }, el("strong", null, "Warnings:"), el("ul", null, ...c.warnings.map((w) => el("li", null, w.message)))));
    if (c.fit && c.fit.lines.length) {
      const tbl = el("table", { class: "lines" }, el("tr", null, el("th", null, "Entry line"), el("th", null, "Date"), el("th", null, "Space left"), el("th", { class: "meterhead" }, "Used")));
      for (const l of c.fit.lines) {
        const pdfLine = c.pdf && c.pdf.entryLines && c.pdf.entryLines.find((e) => e.text.startsWith(l.text.slice(0, 40)));
        const status = pdfLine ? (pdfLine.ok ? pill("st-both", "PDF: one line") : pill("st-todo", "PDF: wrapped")) : null;
        tbl.append(el("tr", { class: "fit-" + l.status }, el("td", null, l.text, " ", status), el("td", null, l.date), el("td", null, `${l.left_pt} pt (${l.left_pct}%)`), el("td", null, meter(l))));
      }
      box.append(el("h3", null, "One-line fit"), tbl);
    }
    if (c.pdf && c.pdf.exists && c.pdf.missing && c.pdf.missing.length) {
      box.append(el("h3", null, "Paragraphs not found in the PDF"), el("ul", { class: "plain" }, ...c.pdf.missing.map((t) => el("li", null, t))));
    }
    if (c.pdf && c.pdf.exists && c.pdf.blocklist && c.pdf.blocklist.length) {
      box.append(el("h3", null, "Blocked terms"), el("ul", { class: "plain" }, ...c.pdf.blocklist.map((h) => el("li", null, el("strong", null, h.term), h.reason ? ` — ${h.reason}: ` : ": ", el("span", { class: "muted" }, h.context)))));
    }
    if (c.parity && c.parity.length) box.append(el("h3", null, "EN / ES differences"), el("ul", { class: "plain" }, ...c.parity.map((n) => el("li", null, n))));
  }

  function renderJob() {
    const panel = $("#jobPanel");
    const j = state.job;
    if (!j) { panel.hidden = true; return; }
    panel.hidden = false;
    const log = $("#jobLog");
    log.textContent = j.log.join("\n") + (j.running ? "\n…" : "");
    log.scrollTop = log.scrollHeight;
  }

  // ---------------------------------------------------------------- data
  async function loadState() {
    const d = await api("/api/cv/state");
    state.masters = d.masters;
    state.job = d.job;
    $("#mastersDir").textContent = d.mastersDir + "/";
    if (d.fonts) setBanner("fonts", "warn", d.fonts + ". The one-line estimate cannot run; the PDF check still does."); else clearBanner("fonts");
    if (d.blocklist.warning) setBanner("blocklist", "warn", d.blocklist.warning + ". Add one term per line (term | reason).", []); else clearBanner("blocklist");
    renderTable();
    renderJob();
    if (state.job && state.job.running) pollJob();
  }

  async function runChecks(ids) {
    $("#checkBtn").disabled = true;
    try {
      const r = await api("/api/cv/check", { method: "POST", body: ids ? { ids } : {} });
      Object.assign(state.checks, r.checks);
      state.masters = r.masters;
      renderTable();
      renderDetails();
      const errs = Object.values(state.checks).reduce((n, c) => n + c.errors.length, 0);
      toast(errs ? `Checks done: ${errs} error${errs > 1 ? "s" : ""} block publishing.` : "Checks done: nothing blocks publishing.");
    } catch (e) { toast("Checks failed: " + e.message, 6000); }
    $("#checkBtn").disabled = false;
  }

  async function startExport(ids) {
    let r;
    try { r = await api("/api/cv/export", { method: "POST", body: ids ? { ids } : {} }); }
    catch (e) { toast("Export refused: " + e.message, 6000); return; }
    if (!r || r.ok === false) { toast("Export refused: " + (r && r.error), 6000); return; }
    state.job = r.job;
    if (Object.keys(r.job.refused || {}).length) setBanner("refused", "warn", "Skipped: " + Object.values(r.job.refused).join("; "));
    renderTable();
    renderJob();
    pollJob();
  }

  function pollJob() {
    clearTimeout(state.pollTimer);
    state.pollTimer = setTimeout(async () => {
      try {
        const r = await api("/api/cv/job");
        state.job = r.job;
        renderJob();
        if (state.job && state.job.running) pollJob();
        else {
          const failed = Object.keys((state.job && state.job.failed) || {}).length;
          toast(failed ? `Export finished with ${failed} failure${failed > 1 ? "s" : ""} — see the log.` : "Export finished. Running the checks…", 5000);
          const d = await api("/api/cv/state");
          state.masters = d.masters;
          renderTable();
          await runChecks(state.job ? state.job.done : null);
        }
      } catch (e) { toast("Lost the export status: " + e.message); }
    }, 500);
  }

  // ---------------------------------------------------------------- publish
  async function openPublish() {
    const dlg = $("#publishDlg");
    const body = $("#publishBody");
    body.replaceChildren(el("p", { class: "muted" }, "Checking…"));
    $("#publishGo").disabled = true;
    dlg.showModal();
    await refreshPlan();
  }

  async function refreshPlan() {
    const body = $("#publishBody");
    const date = $("#publishDate").value.trim();
    let p;
    try { p = await api("/api/cv/publish-plan" + (date ? "?date=" + encodeURIComponent(date) : "")); }
    catch (e) { body.replaceChildren(el("p", null, "Could not plan: " + e.message)); return; }
    if (!$("#publishDate").value) $("#publishDate").value = p.date;
    body.replaceChildren();
    const ul = el("ul", { class: "changes" });
    for (const it of p.items) {
      const li = el("li", null, el("strong", null, it.title + ": "), it.action === "overwrite" ? "overwrite " : "add ", el("code", null, it.target));
      if (it.moves.length) li.append(el("div", { class: "muted small" }, "moves to the backup set: " + it.moves.join(", ")));
      ul.append(li);
    }
    body.append(el("p", null, "Publishing copies the exported PDFs from ", el("code", null, "staging/cv-out/"), " and then regenerates ", el("code", null, "js/docs-data.js"), " (as the pre-commit hook would). Every file overwritten or moved is backed up first. Nothing is committed."), ul);
    if (p.errors.length) body.append(el("div", { class: "gate err" }, el("strong", null, "Blocked — fix these first:"), el("ul", null, ...p.errors.map((e) => el("li", null, e.message)))));
    if (p.warnings.length) body.append(el("div", { class: "gate warn" }, el("strong", null, "Warnings (publishing is allowed):"), el("ul", null, ...p.warnings.map((w) => el("li", null, w.message)))));
    $("#publishGo").disabled = !p.ok;
  }

  async function doPublish() {
    $("#publishGo").disabled = true;
    const date = $("#publishDate").value.trim();
    let r;
    try { r = await api("/api/cv/publish", { method: "POST", body: { date } }); }
    catch (e) { toast("Publish failed: " + e.message, 6000); $("#publishGo").disabled = false; return; }
    if (!r.ok) { toast(r.message || r.error, 7000); if (r.plan) await refreshPlan(); else $("#publishGo").disabled = false; return; }
    $("#publishDlg").close();
    const n = r.added.length + r.overwritten.length;
    const man = r.manifest && r.manifest.ok ? "js/docs-data.js regenerated." : "js/docs-data.js NOT regenerated: " + (r.manifest && r.manifest.output);
    toast(`Published ${n} PDF${n === 1 ? "" : "s"} (backup set ${r.backup}). ${man}`, 9000);
    setBanner("published", "", `Published on ${r.plan.date}: ${r.added.concat(r.overwritten).join(", ")}${r.moved.length ? " — moved to backup " + r.backup + ": " + r.moved.join(", ") : ""}. ${man} Check the Download buttons in Preview ↗, then commit.`, [{ label: "Dismiss", onclick: () => clearBanner("published") }]);
    await loadState();
    await runChecks();
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
    $("#checkBtn").addEventListener("click", () => runChecks());
    $("#exportBtn").addEventListener("click", () => startExport());
    $("#publishBtn").addEventListener("click", openPublish);
    $("#publishGo").addEventListener("click", doPublish);
    $("#publishDate").addEventListener("change", refreshPlan);
    $("#openOutBtn").addEventListener("click", async () => { try { await api("/api/cv/open-out", { method: "POST", body: {} }); } catch (e) { toast("Could not open the folder: " + e.message); } });
    $("#previewLink").addEventListener("click", async (e) => {
      e.preventDefault();
      try { await api("/api/open-preview", { method: "POST", body: {} }); toast("Preview opened in your browser."); }
      catch (err) { toast("Could not open the preview: " + err.message); }
    });
    loadState().then(() => runChecks()).catch((e) => setBanner("load", "err", "Could not load the CV state: " + e.message));
    heartbeat();
    setInterval(heartbeat, 5000);
  }
  init();
  window.__cv = state; // for tests
})();
