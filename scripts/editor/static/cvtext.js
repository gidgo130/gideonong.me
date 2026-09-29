/* CV text page — Phase 4: the editor over staging/cv-content/content.json (4b) and the
   import of the masters (4a). Vanilla JS, no build step. Item ids never show; every
   edit is an op the server applies to its draft. */
(function () {
  "use strict";
  const { token, $, el, api, toast, setBanner, clearBanner, banners, renderDiff, fmtTime } = window.Editor;

  const state = { data: null, variant: "full", selected: "header", unsaved: false, addSection: null };
  const LANGS = ["en", "es"];

  // ---------------------------------------------------------------- helpers
  function pill(cls, text, title) { return el("span", { class: "pill " + cls, title: title || null }, text); }
  function autosize(ta) { ta.style.height = "auto"; ta.style.height = Math.max(30, ta.scrollHeight + 2) + "px"; }
  const content = () => state.data && state.data.data;
  const variants = () => (state.data && state.data.variants) || [];
  const vlabel = (v) => { const x = variants().find((o) => o.id === v); return x ? x.label : v; };
  function issuesFor(key) { return ((state.data && state.data.issues) || []).filter((i) => i.key === key); }
  function issuesUnder(item, iid) {
    const keys = [iid].concat(Object.keys((item && item.children) || {}));
    return ((state.data && state.data.issues) || []).filter((i) => keys.includes(i.key));
  }
  function touched(id) { return ((state.data && state.data.touched) || []).includes(id); }
  function findNode(id) {
    const c = content();
    if (!c) return null;
    if (c.items[id]) return { kind: "item", node: c.items[id] };
    for (const [pid, it] of Object.entries(c.items)) if (it.children && it.children[id]) return { kind: "child", parent: pid, node: it.children[id] };
    return null;
  }
  function itemLabel(item) {
    const t = item.kind === "entry" ? (item.role.en || item.role.es) : (item.text.en || item.text.es);
    return t || "(untitled)";
  }
  function short(s, n) { s = s || ""; return s.length > (n || 60) ? s.slice(0, (n || 60) - 1) + "…" : s; }
  function includedLetters(node) { return variants().map((v) => el("span", { class: "vflag" + (node.include[v.id] ? " on" : ""), title: (node.include[v.id] ? "in " : "not in ") + v.label }, v.label[0])); }

  // ---------------------------------------------------------------- api
  function applyReply(r, fullForm) {
    if (!r || r.ok === false) { toast("Rejected: " + (r && r.error), 6000); return false; }
    const { ok, result, ...rest } = r;
    state.data = rest;
    renderAll(fullForm);
    return r;
  }
  async function op(body, fullForm) {
    try { return applyReply(await api("/api/cvtext/op", { method: "POST", body }), fullForm); }
    catch (e) { toast("Failed: " + e.message, 6000); return false; }
  }
  const pendingText = {};
  function queueText(path, value) {
    const k = path.join(".");
    clearTimeout(pendingText[k]);
    pendingText[k] = setTimeout(() => op({ op: "set", path, value }, false), 350);
  }

  // ---------------------------------------------------------------- variant switch
  function renderVariants() {
    const box = $("#variants");
    box.replaceChildren();
    for (const v of variants()) {
      box.append(el("a", { href: "#" + v.id, class: state.variant === v.id ? "active" : "", onclick: (e) => { e.preventDefault(); state.variant = v.id; renderAll(true); } }, v.label));
    }
  }

  // ---------------------------------------------------------------- left list
  function renderList() {
    const box = $("#list");
    box.replaceChildren();
    const c = content();
    if (!c) return;
    const row = (id, title, meta, cls, pills) => {
      const a = el("a", { href: "#" + state.variant + "/" + id, class: "entry " + (cls || "") + (state.selected === id ? " active" : ""), onclick: (ev) => { ev.preventDefault(); select(id); } });
      a.append(el("div", { class: "entry-title" }, title));
      if (meta) a.append(el("div", { class: "entry-meta" }, meta));
      if (pills && pills.length) a.append(el("div", { class: "entry-pills" }, ...pills));
      return a;
    };
    const hIssues = ((state.data.issues) || []).filter((i) => i.key.startsWith("header."));
    const hErr = hIssues.some((i) => i.level === "error");
    box.append(row("header", "Header", "name · title · contact", (touched("header.name") || touched("header.contact") || variants().some((v) => touched("header.title." + v.id)) ? "has-draft " : "") + (hErr ? "has-error" : "")));
    const sections = state.data.listing[state.variant];
    for (const sec of sections) {
      const sIss = issuesFor("section." + sec.id);
      const inVariant = sec.variants.includes(state.variant);
      const h = el("h3", { class: inVariant ? "" : "excluded" });
      h.append(el("a", { href: "#", class: "linkish small" + (state.selected === "section." + sec.id ? " active" : ""), onclick: (ev) => { ev.preventDefault(); select("section." + sec.id); } }, sec.heading.en || sec.id));
      if (!inVariant) h.append(" ", el("span", { class: "muted" }, "(not in " + vlabel(state.variant) + ")"));
      if (sIss.some((i) => i.level === "error") || touched("section." + sec.id)) h.append(" ", pill(sIss.some((i) => i.level === "error") ? "st-todo" : "draft", sIss.some((i) => i.level === "error") ? "error" : "draft"));
      box.append(h);
      const rows = (ids, excluded) => {
        for (const iid of ids) {
          const it = c.items[iid];
          if (!it) continue;
          const iss = issuesUnder(it, iid);
          const errs = iss.filter((i) => i.level === "error").length;
          const isTouched = touched(iid) || Object.keys(it.children || {}).some(touched);
          const pills = includedLetters(it);
          if (isTouched) pills.push(pill("draft", "draft"));
          if (errs) pills.push(pill("st-todo", errs + " error" + (errs > 1 ? "s" : "")));
          else if (iss.length) pills.push(pill("st-same", iss.length + " warning" + (iss.length > 1 ? "s" : "")));
          const meta = it.kind === "entry" ? short(it.org.en, 50) + (it.date.en ? " · " + it.date.en : "") : null;
          box.append(row(iid, short(itemLabel(it), 56), meta, (excluded ? "excluded " : "") + (isTouched ? "has-draft " : "") + (errs ? "has-error" : ""), pills));
        }
      };
      rows(sec.items, false);
      rows(sec.others, true);
      box.append(el("button", { type: "button", class: "ghost small addlink", onclick: () => openAdd(sec.id) }, "+ Add item…"));
    }
  }
  function select(id) { state.selected = id; location.hash = state.variant + "/" + id; renderList(); renderForm(); }

  // ---------------------------------------------------------------- widgets
  function textPair(path, label, values, opts) {
    const o = opts || {};
    const wrap = el("div", { class: "pair" }, el("div", { class: "pair-label" }, label, o.note ? el("span", { class: "muted small" }, " " + o.note) : null));
    const cols = el("div", { class: "cols" });
    for (const lang of LANGS) {
      const ta = el("textarea", { rows: 1, lang, spellcheck: "true" });
      ta.value = values[lang] || "";
      ta.placeholder = lang.toUpperCase();
      if (o.disabled) ta.disabled = true;
      ta.addEventListener("input", () => { autosize(ta); queueText(path.concat([lang]), ta.value); });
      cols.append(el("div", null, el("label", null, lang.toUpperCase()), ta));
    }
    wrap.append(cols);
    return wrap;
  }
  function includeBoxes(id, node) {
    const box = el("div", { class: "tagbox" });
    for (const v of variants()) {
      const cb = el("input", { type: "checkbox" });
      cb.checked = !!node.include[v.id];
      cb.addEventListener("change", () => op({ op: "include", id, variant: v.id, on: cb.checked, current: state.variant }, true));
      box.append(el("label", { class: "chk" }, cb, " " + v.label));
    }
    return el("div", { class: "field" }, el("span", null, "In these documents"), box);
  }
  function moveButtons(id, order) {
    const i = order.indexOf(id);
    const inThis = i >= 0;
    return el("span", { class: "moves" },
      el("button", { type: "button", class: "ghost small", disabled: (!inThis || i === 0) ? "" : null, title: inThis ? "move up in " + vlabel(state.variant) : "not in " + vlabel(state.variant), onclick: () => op({ op: "move", id, variant: state.variant, delta: -1 }, true) }, "↑"),
      el("button", { type: "button", class: "ghost small", disabled: (!inThis || i === order.length - 1) ? "" : null, title: inThis ? "move down in " + vlabel(state.variant) : "not in " + vlabel(state.variant), onclick: () => op({ op: "move", id, variant: state.variant, delta: 1 }, true) }, "↓"));
  }
  function issueBox(node, iss) {
    node.replaceChildren();
    const errs = iss.filter((i) => i.level === "error"), warns = iss.filter((i) => i.level === "warning");
    if (errs.length) node.append(el("div", { class: "gate err" }, el("strong", null, "Errors (block saving):"), el("ul", null, ...errs.map((i) => el("li", null, (i.lang ? i.lang.toUpperCase() + ": " : "") + i.message)))));
    if (warns.length) node.append(el("div", { class: "gate warn" }, el("strong", null, "Warnings:"), el("ul", null, ...warns.map((i) => el("li", null, (i.lang ? i.lang.toUpperCase() + ": " : "") + i.message)))));
  }
  function meter(f) {
    if (!f) return el("span", { class: "muted small" }, "no measure");
    const pct = Math.max(0, Math.min(100, (f.used_pt / f.avail_pt) * 100));
    const cls = f.status === "overflow" ? "over" : f.status === "tight" ? "tight" : "";
    const label = f.status === "overflow" ? `${(-f.left_pt).toFixed(1)} pt too wide` : `${f.left_pt.toFixed(1)} pt left · ${f.left_pct.toFixed(1)} %`;
    return el("div", { class: "fitcell" }, el("div", { class: "meter " + cls, title: `${f.used_pt.toFixed(1)} of ${f.avail_pt.toFixed(1)} pt` }, el("div", { class: "bar", style: "width:" + pct + "%" })), el("div", { class: "small " + (cls === "over" ? "err-text" : cls === "tight" ? "warn-text" : "muted") }, label));
  }
  function fitTable(iid) {
    const fits = (state.data.fits || {})[iid] || {};
    const wrap = el("div", { class: "fits", id: "fitBox" });
    const rows = Object.entries(fits);
    if (!rows.length) { wrap.append(el("p", { class: "muted small" }, "Not in any document.")); return wrap; }
    const t = el("table", { class: "docs fits" }, el("tr", null, el("th", null, "One-line fit"), el("th", null, "EN"), el("th", null, "ES")));
    for (const [v, langs] of rows) t.append(el("tr", null, el("td", null, vlabel(v)), el("td", null, meter(langs.en)), el("td", null, meter(langs.es))));
    wrap.append(t);
    if (state.data.fitWarning) wrap.append(el("div", { class: "warn-text" }, state.data.fitWarning));
    return wrap;
  }

  // ---------------------------------------------------------------- forms
  function renderForm() {
    const box = $("#form");
    box.replaceChildren();
    const c = content();
    if (!c) return;
    if (state.data.readOnly) { box.append(el("div", { class: "gate err" }, "Read-only: " + state.data.readOnly)); return; }
    const id = state.selected;
    if (id === "header") renderHeader(box, c);
    else if (id.startsWith("section.")) renderSection(box, c, id.slice(8));
    else {
      const f = findNode(id);
      if (!f) { box.append(el("p", { class: "muted" }, "Pick an item on the left.")); return; }
      if (f.kind === "child") { select(f.parent); return; }
      renderItem(box, c, id, f.node);
    }
    requestAnimationFrame(() => box.querySelectorAll("textarea").forEach(autosize));
  }
  function renderHeader(box, c) {
    box.append(el("h2", null, "Header"));
    const ib = el("div", { id: "issueBox" });
    box.append(ib);
    issueBox(ib, (state.data.issues || []).filter((i) => i.key.startsWith("header.")));
    const name = el("input", { type: "text", value: c.header.name });
    name.addEventListener("input", () => queueText(["header", "name"], name.value));
    box.append(el("div", { class: "form-grid" }, el("label", { class: "field" }, el("span", null, "Name (all six documents)"), name)));
    for (const v of variants()) {
      const t = c.header.title[v.id];
      if (t) box.append(textPair(["header", "title", v.id], "Title line — " + v.label, t));
      else box.append(el("div", { class: "pair" }, el("div", { class: "pair-label" }, "Title line — " + v.label, " ", el("span", { class: "muted small" }, "(the " + v.label + " masters have no title line)"))));
    }
    box.append(textPair(["header", "contact"], "Contact line", c.header.contact, { note: "the +1 (918) phone lives here only (decision 9) — it is allowed in the published CV / résumé PDFs and nowhere else" }));
  }
  function renderSection(box, c, sid) {
    const sec = c.sections.find((s) => s.id === sid);
    if (!sec) { box.append(el("p", { class: "muted" }, "Unknown section.")); return; }
    box.append(el("h2", null, sec.heading.en || sid, " ", el("span", { class: "muted small" }, "section")));
    const ib = el("div", { id: "issueBox" });
    box.append(ib);
    issueBox(ib, issuesFor("section." + sid));
    box.append(textPair(["sections", c.sections.indexOf(sec), "heading"], "Heading", sec.heading));
    const inV = Object.entries(sec.order).filter(([, o]) => o.length).map(([v]) => vlabel(v));
    box.append(el("p", { class: "muted small" }, "Appears in: " + (inV.join(", ") || "no document") + ". A section appears in a document when at least one of its items does; its heading is written by Apply (4c)."));
    box.append(el("button", { type: "button", class: "ghost", onclick: () => openAdd(sid) }, "+ Add item to this section…"));
  }
  function renderItem(box, c, iid, item) {
    const sec = state.data.listing[state.variant].find((s) => s.items.includes(iid) || s.others.includes(iid));
    const order = sec ? sec.items : [];
    const head = el("h2", null, short(itemLabel(item), 90), " ", el("span", { class: "muted small" }, item.kind === "entry" ? "entry" : "line"));
    box.append(el("div", { class: "rowline" }, head, el("span", { class: "spacer" }), moveButtons(iid, order)));
    const ib = el("div", { id: "issueBox" });
    box.append(ib);
    issueBox(ib, issuesFor(iid));
    box.append(includeBoxes(iid, item));
    if (item.kind === "entry") {
      box.append(textPair(["items", iid, "role"], "Role", item.role, { note: "bold" }), textPair(["items", iid, "org"], "Organization", item.org, { note: "after “ · ”; may be empty" }), textPair(["items", iid, "date"], "Date", item.date, { note: "right-aligned at the tab" }));
      box.append(fitTable(iid));
      box.append(el("h3", null, "Bullets and lines ", el("span", { class: "muted small" }, "in " + vlabel(state.variant) + " order")));
      const corder = (item.order || {})[state.variant] || [];
      const shown = new Set();
      const card = (cid, excluded) => {
        const ch = item.children[cid];
        if (!ch) return null;
        shown.add(cid);
        const k = el("div", { class: "card" + (excluded ? " excluded" : ""), "data-cid": cid });
        const bar = el("div", { class: "rowline" }, el("strong", { class: "small" }, ch.kind === "bullet" ? "Bullet" : "Line"), el("span", { class: "spacer" }), moveButtons(cid, corder),
          el("button", { type: "button", class: "ghost small danger", onclick: () => { if (confirm("Delete this " + ch.kind + "?\n\n" + short(ch.text.en || ch.text.es, 100) + "\n\nIt leaves every document it is in. Nothing is written until you Review & save.")) op({ op: "delete", id: cid }, true); } }, "Delete"));
        k.append(bar);
        const cib = el("div", { class: "child-issues" });
        issueBox(cib, issuesFor(cid));
        k.append(cib);
        k.append(textPair(["items", iid, "children", cid, "text"], "", ch.text));
        k.append(includeBoxes(cid, ch));
        return k;
      };
      for (const cid of corder) { const k = card(cid, false); if (k) box.append(k); }
      const others = Object.keys(item.children).filter((cid) => !shown.has(cid));
      if (others.length) box.append(el("div", { class: "pair-label" }, "Not in " + vlabel(state.variant) + ":"));
      for (const cid of others) { const k = card(cid, true); if (k) box.append(k); }
      const canAdd = !!item.include[state.variant];
      box.append(el("div", { class: "rowline" },
        el("button", { type: "button", class: "ghost", disabled: canAdd ? null : "", title: canAdd ? "" : "include the entry in " + vlabel(state.variant) + " first", onclick: () => op({ op: "add-child", item: iid, kind: "bullet", variant: state.variant }, true) }, "Add bullet"),
        el("button", { type: "button", class: "ghost", disabled: canAdd ? null : "", title: canAdd ? "" : "include the entry in " + vlabel(state.variant) + " first", onclick: () => op({ op: "add-child", item: iid, kind: "line", variant: state.variant }, true) }, "Add line")));
    } else {
      box.append(textPair(["items", iid, "text"], "Text", item.text));
    }
    const inV = variants().filter((v) => item.include[v.id]).map((v) => v.label);
    box.append(el("div", { class: "rowline danger-zone" }, el("button", { type: "button", class: "ghost danger", onclick: () => { if (confirm("Delete " + item.kind + " “" + short(itemLabel(item), 80) + "”?\n\nIt leaves " + (inV.join(", ") || "no document") + (item.kind === "entry" ? " with all its bullets" : "") + ". Nothing is written until you Review & save.")) { op({ op: "delete", id: iid }, true).then((r) => { if (r) { state.selected = "header"; renderList(); renderForm(); } }); } } }, "Delete…")));
  }
  function refreshLight() {
    // keep the textareas (the user may be typing): only issues, meters and the list change
    const id = state.selected;
    const ib = $("#issueBox");
    if (ib) {
      if (id === "header") issueBox(ib, (state.data.issues || []).filter((i) => i.key.startsWith("header.")));
      else issueBox(ib, issuesFor(id));
    }
    for (const card of document.querySelectorAll("#form .card[data-cid]")) {
      const cib = card.querySelector(".child-issues");
      if (cib) issueBox(cib, issuesFor(card.dataset.cid));
    }
    const fb = $("#fitBox");
    if (fb && content() && content().items[id]) fb.replaceWith(fitTable(id));
  }

  // ---------------------------------------------------------------- add
  function openAdd(sectionId) {
    state.addSection = sectionId;
    const sec = content().sections.find((s) => s.id === sectionId);
    $("#addTitle").textContent = "Add item to “" + ((sec && sec.heading.en) || sectionId) + "”";
    $("#addKind").value = "entry";
    $("#addEn").value = "";
    $("#addEnLabel").textContent = "Role (EN)";
    $("#addNote").textContent = "The new item goes to the end of the section in " + vlabel(state.variant) + " only; tick the other documents in its form. Its Spanish text is required before saving.";
    $("#addDlg").showModal();
    $("#addEn").focus();
  }
  async function doAdd() {
    const kind = $("#addKind").value, en = $("#addEn").value.trim();
    if (!en) { toast("Type the English text first — it names the item."); return; }
    const r = await op({ op: "add-item", section: state.addSection, kind, en, variant: state.variant }, true);
    if (r) { $("#addDlg").close(); select(r.result.id); }
  }

  // ---------------------------------------------------------------- import (4a)
  function renderStatus() {
    const d = state.data;
    const t = el("table", { class: "docs" }, el("tr", null, el("th", null, "Master"), el("th", null, "Modified"), el("th", null, "State")));
    for (const m of d.masters) {
      t.append(el("tr", null, el("td", null, m.title, " ", el("span", { class: "muted small" }, m.file)), el("td", null, m.exists ? fmtTime(m.mtime) : "—"),
        el("td", null, m.exists ? (m.openInWord ? pill("st-todo", "open in Word") : pill("st-both", "present")) : pill("st-todo", "missing"))));
    }
    const box = el("div");
    box.append(t);
    if (d.content) box.append(el("p", null, el("strong", null, "Content set: "), `${d.content.items} items (${d.content.entries} entries, ${d.content.children} bullets / lines under them), ${d.content.sections} sections, ${d.content.shared} items shared by more than one variant — `, el("code", null, d.contentPath), ` written ${fmtTime(d.content.modified)}.`));
    else box.append(el("p", { class: "muted" }, "No content set yet — run Import masters."));
    return box;
  }
  function renderReport(r) {
    const box = $("#report");
    box.replaceChildren();
    if (!r) return;
    box.append(el("h3", null, r.ok ? "Last import — lossless on all six" : "Import blocked — the round trip is not lossless", " ", el("span", { class: "muted small" }, r.ran ? `${r.ran} · ${r.seconds} s` : "")));
    if (r.message) box.append(el("div", { class: "gate " + (r.ok ? "info" : "err") }, r.message));
    const t = el("table", { class: "docs" }, el("tr", null, el("th", null, "Master"), el("th", null, "Round trip")));
    for (const [name, problems] of Object.entries(r.proof || {})) {
      t.append(el("tr", null, el("td", null, name), el("td", null, problems.length ? el("ul", { class: "plain" }, ...problems.map((p) => el("li", { class: "warn-text" }, p))) : pill("st-both", "identical"))));
    }
    box.append(t);
    const rep = r.report || {};
    const v = rep.variants || {};
    box.append(el("ul", { class: "plain" },
      ...Object.entries(v).map(([name, s]) => el("li", null, el("strong", null, name + ": "), `${s.entries} new entries, ${s.lines} new lines, ${s.children} new bullets / sub-lines, ${s.sharedWithEarlier} already known from an earlier variant`)),
      el("li", null, el("strong", null, "Shared: "), `${rep.shared} items appear in more than one variant`)));
    const unpaired = Object.entries(rep.unpaired || {}).flatMap(([vn, notes]) => notes.map((n) => vn + ": " + n));
    if (unpaired.length) box.append(el("div", { class: "gate warn" }, el("strong", null, "Paragraphs with no twin in the other language (imported with empty text there):"), el("ul", null, ...unpaired.map((n) => el("li", null, n)))));
    if (rep.nearDuplicates && rep.nearDuplicates.length) box.append(el("div", { class: "gate warn" }, el("strong", null, "Same English wording, different Spanish (kept as separate items):"), el("ul", null, ...rep.nearDuplicates.map((ids) => el("li", null, ids.join(" ↔ "))))));
    if (rep.formatting && rep.formatting.length) box.append(el("details", null, el("summary", null, `${rep.formatting.length} formatting note${rep.formatting.length > 1 ? "s" : ""} in the masters (fix in Word if you want)`), el("ul", { class: "plain" }, ...rep.formatting.map((n) => el("li", null, n)))));
  }
  function openImport() {
    $("#status").replaceChildren(el("h3", null, "Masters"), renderStatus());
    renderReport(state.data.lastImport);
    const d = state.data;
    $("#importGo").disabled = d.masters.some((m) => !m.exists) || d.draftCount > 0;
    $("#importGo").title = d.draftCount > 0 ? "save or discard the drafts first" : "";
    $("#importDlg").showModal();
  }
  async function runImport() {
    if (state.data.content && !confirm("Re-import the masters?\n\nThe current content set is backed up and replaced by what the masters say now.")) return;
    $("#importGo").disabled = true;
    toast("Importing and proving the round trip…", 8000);
    let r;
    try { r = await api("/api/cvtext/import", { method: "POST", body: {} }); }
    catch (e) { toast("Import failed: " + e.message, 7000); $("#importGo").disabled = false; return; }
    if (r.proof) renderReport(r);
    if (r.ok) toast(`Imported: ${Object.keys(r.proof).length} masters lossless, content set written${r.backup ? " (previous one in backup " + r.backup + ")" : ""}.`, 7000);
    else toast(r.message || r.error, 8000);
    await loadState();
    $("#status").replaceChildren(el("h3", null, "Masters"), renderStatus());
    $("#importGo").disabled = false;
  }

  // ---------------------------------------------------------------- review & save
  function renderCounts() {
    const n = (state.data && state.data.draftCount) || 0;
    $("#draftCount").textContent = String(n);
    $("#draftCount").hidden = n === 0;
    state.unsaved = n > 0;
  }
  function issueList(items) { return el("ul", null, ...items.map((i) => el("li", null, el("strong", null, short(i.label || "", 50)), (i.lang ? " (" + i.lang.toUpperCase() + ")" : ""), ": " + i.message))); }
  async function openReview() {
    const dlg = $("#reviewDlg"), body = $("#reviewBody");
    body.replaceChildren(el("p", { class: "muted" }, "Preparing…"));
    $("#saveBtn").disabled = true;
    dlg.showModal();
    let r;
    try { r = await api("/api/cvtext/review"); } catch (e) { body.replaceChildren(el("p", null, "Review failed: " + e.message)); return; }
    body.replaceChildren();
    if (r.readOnly) { body.append(el("div", { class: "gate err" }, "Read-only: " + r.error)); return; }
    if (r.noop) { body.append(el("p", { class: "muted" }, "No changes — content.json already matches.")); return; }
    body.append(el("ul", { class: "changes" }, ...r.changes.map((c) => el("li", null, c.text))));
    const mt = el("table", { class: "docs" }, el("tr", null, el("th", null, "Master"), el("th", null, "What Apply (4c) would do")));
    for (const m of r.masters) {
      const parts = [];
      if (m.changed.length) parts.push(`${m.changed.length} paragraph${m.changed.length > 1 ? "s" : ""} rewritten`);
      if (m.added.length) parts.push(`${m.added.length} added`);
      if (m.removed.length) parts.push(`${m.removed.length} removed`);
      mt.append(el("tr", null, el("td", null, m.title), el("td", null, parts.length ? parts.join(", ") : el("span", { class: "muted" }, "unchanged"))));
    }
    body.append(el("h3", null, "Masters"), el("p", { class: "muted small" }, "Saving writes only content.json. The Word masters are rewritten by Apply, which comes with 4c."), mt);
    if (r.diskChanged) body.append(el("div", { class: "gate err" }, "content.json changed on disk since it was loaded. Close this, click Reload in the banner, then review again."));
    const g = r.gate;
    if (g.blocking.length) body.append(el("div", { class: "gate err" }, el("strong", null, "Blocking errors (fix before saving):"), issueList(g.blocking)));
    if (g.warnings.length) body.append(el("div", { class: "gate warn" }, el("strong", null, "Warnings (saving is allowed):"), issueList(g.warnings.slice(0, 15)), g.warnings.length > 15 ? el("p", { class: "muted" }, "… and " + (g.warnings.length - 15) + " more") : null));
    if (g.preexisting.length) body.append(el("div", { class: "gate info" }, el("strong", null, "Pre-existing errors elsewhere (not blocking):"), issueList(g.preexisting)));
    body.append(el("h3", null, r.file), renderDiff(r.diff));
    $("#saveBtn").disabled = !r.ok;
  }
  async function doSave() {
    $("#saveBtn").disabled = true;
    let r;
    try { r = await api("/api/cvtext/save", { method: "POST", body: {} }); } catch (e) { toast("Save failed: " + e.message); $("#saveBtn").disabled = false; return; }
    if (!r.ok) { toast(r.message || r.error, 7000); if (r.error === "changed-on-disk") { $("#reviewDlg").close(); showDiskBanner(r.message); } else $("#saveBtn").disabled = false; return; }
    $("#reviewDlg").close();
    toast(r.message, 6000);
    await loadState();
  }
  async function discardAll() {
    if (!state.data.draftCount) { $("#reviewDlg").close(); return; }
    if (!confirm("Discard all " + state.data.draftCount + " CV text edit(s)? content.json is not touched.")) return;
    await api("/api/cvtext/drafts/discard", { method: "POST", body: {} });
    $("#reviewDlg").close();
    await loadState();
    toast("Drafts discarded.");
  }

  // ---------------------------------------------------------------- state
  function showDiskBanner(msg) {
    if (!banners.disk) setBanner("disk", "warn", msg || "content.json changed on disk (VS Code, Claude Code, an import). Saving is refused until you reload; drafts are kept.", [{ label: "Reload", primary: true, onclick: reloadFromDisk }]);
  }
  async function reloadFromDisk() {
    const d = await api("/api/cvtext/reload", { method: "POST", body: {} });
    clearBanner("disk");
    await loadState(d);
    toast("Reloaded from disk.");
  }
  function renderAll(fullForm) {
    renderVariants();
    renderCounts();
    renderList();
    if (fullForm) renderForm(); else refreshLight();
  }
  async function loadState(via) {
    const d = via || (await api("/api/cvtext/state"));
    state.data = d;
    const has = !!d.data;
    $("#editor").hidden = !has;
    $("#noContent").hidden = has;
    $("#reviewBtn").hidden = !has;
    if (!has) {
      $("#statusOnly").replaceChildren(el("h2", null, "Masters"), renderStatus());
      if (d.loadError) setBanner("readonly", "err", d.loadError); else clearBanner("readonly");
      renderVariants();
      return;
    }
    if (d.readOnly) setBanner("readonly", "err", "Read-only: " + d.readOnly); else clearBanner("readonly");
    if (d.diskChanged) showDiskBanner(); else clearBanner("disk");
    if (d.autosave) setBanner("autosave", "warn", "Unsaved CV text edits from " + d.autosave.saved + " were found.", [
      { label: "Restore drafts", primary: true, onclick: async () => { const r = await api("/api/cvtext/autosave/restore", { method: "POST", body: {} }); clearBanner("autosave"); toast(r.applied ? "Drafts restored" + (r.fileChanged ? " (content.json changed on disk since — check the review)" : "") : "Nothing to restore — the file already matched"); await loadState(); } },
      { label: "Discard", onclick: async () => { await api("/api/cvtext/autosave/discard", { method: "POST", body: {} }); clearBanner("autosave"); } }]);
    else clearBanner("autosave");
    const m = location.hash.replace(/^#/, "").match(/^(full|professional|resume)(?:\/(.+))?$/);
    if (m) { state.variant = m[1]; if (m[2]) state.selected = decodeURIComponent(m[2]); }
    if (!(state.selected === "header" || state.selected.startsWith("section.") || findNode(state.selected))) state.selected = "header";
    renderAll(true);
  }
  let hbFailures = 0;
  async function heartbeat() {
    try { await api("/api/heartbeat", { method: "POST", body: {} }); hbFailures = 0; clearBanner("offline"); }
    catch (e) { if (++hbFailures >= 2) setBanner("offline", "err", "The editor server is not answering. If it was closed, close this window and start the editor again."); }
  }

  // ---------------------------------------------------------------- wiring
  function init() {
    window.Editor.initTabs();
    if (!token) { window.Editor.noToken(); return; }
    $("#importBtn").addEventListener("click", openImport);
    $("#importGo").addEventListener("click", runImport);
    $("#reviewBtn").addEventListener("click", openReview);
    $("#saveBtn").addEventListener("click", doSave);
    $("#discardBtn").addEventListener("click", discardAll);
    $("#addGo").addEventListener("click", doAdd);
    $("#addKind").addEventListener("change", () => { $("#addEnLabel").textContent = $("#addKind").value === "entry" ? "Role (EN)" : "Text (EN)"; });
    $("#addDlg").addEventListener("keydown", (e) => { if (e.key === "Enter" && e.target.tagName === "INPUT") { e.preventDefault(); doAdd(); } });
    document.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); if (state.data && state.data.data && !$("#reviewDlg").open) openReview(); } });
    window.addEventListener("beforeunload", (e) => { if (state.unsaved && !window.__navigating) { e.preventDefault(); e.returnValue = ""; } });
    window.addEventListener("hashchange", () => { const m = location.hash.replace(/^#/, "").match(/^(full|professional|resume)(?:\/(.+))?$/); if (m && state.data) { state.variant = m[1]; if (m[2]) state.selected = decodeURIComponent(m[2]); renderAll(true); } });
    loadState().catch((e) => setBanner("load", "err", "Could not load: " + e.message));
    heartbeat();
    setInterval(heartbeat, 5000);
  }
  init();
  window.__cvtext = state; // for tests
})();
