/* CV text page — Phase 4a: import + proof of losslessness. */
(function () {
  "use strict";
  const { token, $, el, api, toast, setBanner, clearBanner, fmtTime } = window.Editor;
  const state = { data: null, last: null };

  function pill(cls, text, title) { return el("span", { class: "pill " + cls, title: title || null }, text); }

  function renderStatus() {
    const box = $("#status");
    box.replaceChildren(el("h2", null, "Status"));
    const d = state.data;
    const t = el("table", { class: "docs" }, el("tr", null, el("th", null, "Master"), el("th", null, "Modified"), el("th", null, "State")));
    for (const m of d.masters) {
      t.append(el("tr", null, el("td", null, m.title, " ", el("span", { class: "muted small" }, m.file)), el("td", null, m.exists ? fmtTime(m.mtime) : "—"),
        el("td", null, m.exists ? (m.openInWord ? pill("st-todo", "open in Word") : pill("st-both", "present")) : pill("st-todo", "missing"))));
    }
    box.append(t);
    if (d.content) {
      box.append(el("p", null, el("strong", null, "Content set: "), `${d.content.items} items (${d.content.entries} entries, ${d.content.children} bullets / lines under them), ${d.content.sections} sections, ${d.content.shared} items shared by more than one variant — `, el("code", null, d.contentPath), ` written ${fmtTime(d.content.modified)}.`));
    } else {
      box.append(el("p", { class: "muted" }, "No content set yet — run Import masters."));
    }
    $("#importBtn").disabled = d.masters.some((m) => !m.exists);
  }

  function renderReport(r) {
    const box = $("#report");
    box.replaceChildren();
    if (!r) return;
    box.append(el("h2", null, r.ok ? "Last import — lossless on all six" : "Import blocked — the round trip is not lossless", " ", el("span", { class: "muted small" }, r.ran ? `${r.ran} · ${r.seconds} s` : "")));
    if (r.message) box.append(el("div", { class: "gate " + (r.ok ? "info" : "err") }, r.message));
    const t = el("table", { class: "docs" }, el("tr", null, el("th", null, "Master"), el("th", null, "Round trip")));
    for (const [name, problems] of Object.entries(r.proof || {})) {
      t.append(el("tr", null, el("td", null, name), el("td", null, problems.length ? el("ul", { class: "plain" }, ...problems.map((p) => el("li", { class: "warn-text" }, p))) : pill("st-both", "identical"))));
    }
    box.append(el("h3", null, "Proof"), t);
    const rep = r.report || {};
    const v = rep.variants || {};
    box.append(el("h3", null, "What was imported"), el("ul", { class: "plain" },
      ...Object.entries(v).map(([name, s]) => el("li", null, el("strong", null, name + ": "), `${s.entries} new entries, ${s.lines} new lines, ${s.children} new bullets / sub-lines, ${s.sharedWithEarlier} already known from an earlier variant`)),
      el("li", null, el("strong", null, "Shared: "), `${rep.shared} items appear in more than one variant`)));
    if (rep.sections) box.append(el("p", { class: "small" }, "Sections: " + rep.sections.map((s) => `${s.heading} (${s.variants.join(", ")})`).join(" · ")));
    const unpaired = Object.entries(rep.unpaired || {}).flatMap(([vn, notes]) => notes.map((n) => vn + ": " + n));
    if (unpaired.length) box.append(el("div", { class: "gate warn" }, el("strong", null, "Paragraphs with no twin in the other language (imported with empty text there):"), el("ul", null, ...unpaired.map((n) => el("li", null, n)))));
    if (rep.nearDuplicates && rep.nearDuplicates.length) box.append(el("div", { class: "gate warn" }, el("strong", null, "Same English wording, different Spanish (kept as separate items):"), el("ul", null, ...rep.nearDuplicates.map((ids) => el("li", null, ids.join(" ↔ "))))));
    if (rep.formatting && rep.formatting.length) box.append(el("details", null, el("summary", null, `${rep.formatting.length} formatting note${rep.formatting.length > 1 ? "s" : ""} in the masters (fix in Word if you want)`), el("ul", { class: "plain" }, ...rep.formatting.map((n) => el("li", null, n)))));
  }

  async function loadState() {
    const d = await api("/api/cvtext/state");
    state.data = d;
    renderStatus();
    renderReport(d.lastImport);
  }

  async function runImport() {
    if (state.data.content && !confirm("Re-import the masters?\n\nThe current content set is backed up and replaced by what the masters say now.")) return;
    $("#importBtn").disabled = true;
    toast("Importing and proving the round trip…", 8000);
    let r;
    try { r = await api("/api/cvtext/import", { method: "POST", body: {} }); }
    catch (e) { toast("Import failed: " + e.message, 7000); $("#importBtn").disabled = false; return; }
    if (r.proof) renderReport(r);
    if (r.ok) toast(`Imported: ${Object.keys(r.proof).length} masters lossless, content set written${r.backup ? " (previous one in backup " + r.backup + ")" : ""}.`, 7000);
    else toast(r.message || r.error, 8000);
    await loadState();
  }

  let hbFailures = 0;
  async function heartbeat() {
    try { await api("/api/heartbeat", { method: "POST", body: {} }); hbFailures = 0; clearBanner("offline"); }
    catch (e) { if (++hbFailures >= 2) setBanner("offline", "err", "The editor server is not answering. If it was closed, close this window and start the editor again."); }
  }

  function init() {
    window.Editor.initTabs();
    if (!token) { window.Editor.noToken(); return; }
    $("#importBtn").addEventListener("click", runImport);
    loadState().catch((e) => setBanner("load", "err", "Could not load: " + e.message));
    heartbeat();
    setInterval(heartbeat, 5000);
  }
  init();
  window.__cvtext = state;
})();
