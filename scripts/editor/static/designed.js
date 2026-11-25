/* Designed CV page: the checklist of the Designed variant on the left, the real page at true
   size (scaled) on the right. Vanilla JS, no build step. Every tick and edit is an op on the
   CV text tab's one draft (so the two tabs always agree); Review & save writes content.json
   only. The preview is the same HTML the PDF is printed from. */
(function () {
  "use strict";
  const { token, $, el, api, toast, setBanner, clearBanner, banners, renderDiff, fmtTime } = window.Editor;

  const state = { data: null, open: new Set(), local: {}, idmap: {}, unsaved: false, grey: false, fit: "width", seq: 0, front: "A", meter: null, dismissed: {} };
  const LANGS = ["es", "en"]; // Spanish first (D12)
  const PAGE_W = 816, PAGE_H = 1056;

  // ---------------------------------------------------------------- helpers
  const pill = (cls, text, title) => el("span", { class: "pill " + cls, title: title || null }, text);
  const short = (s, n) => { s = s || ""; return s.length > (n || 70) ? s.slice(0, (n || 70) - 1) + "…" : s; };
  const autosize = (ta) => { ta.style.height = "auto"; ta.style.height = Math.max(30, ta.scrollHeight + 2) + "px"; };
  const lang = () => state.data.view.lang;
  const tx = (pair) => (pair && (pair[lang()] || pair.en || pair.es)) || "";
  const resolve = (id) => { let n = 0; while (state.idmap[id] && n++ < 20) id = state.idmap[id]; return id; };
  const issuesFor = (key) => (state.data.issues || []).filter((i) => i.key === key);
  const cm = (px) => (Math.abs(px) / 96 * 2.54).toFixed(1);

  // ---------------------------------------------------------------- api
  function take(reply) {
    const { ok, result, ...rest } = reply;
    state.data = rest;
    return result || {};
  }
  async function op(body, before) {
    let r;
    try { r = await api("/api/designed/op", { method: "POST", body }); } catch (e) { toast("Failed: " + e.message, 6000); return null; }
    if (!r || r.ok === false) { toast("Rejected: " + (r && r.error), 6000); return null; }
    const result = take(r);
    if (before) before(result); // e.g. a row whose id changed: remap before the list is redrawn, so the caret stays
    renderAll();
    refreshPreview();
    return result;
  }
  function remap(oldId, newId) {
    if (!newId || oldId === newId) return;
    state.idmap[oldId] = newId;
    if (state.open.delete(oldId)) state.open.add(newId);
    for (const k of Object.keys(state.local)) {
      const parts = k.split("|");
      if (parts[1] === oldId) { parts[1] = newId; state.local[parts.join("|")] = state.local[k]; delete state.local[k]; }
    }
  }
  // text fields: typed text is kept locally and sent 350 ms after the last key
  const timers = {}, senders = {};
  function queue(key, send) {
    clearTimeout(timers[key]);
    senders[key] = send;
    timers[key] = setTimeout(() => flush(key), 350);
  }
  function flush(key) {
    if (!senders[key]) return;
    clearTimeout(timers[key]);
    const send = senders[key];
    delete senders[key]; delete timers[key];
    send();
  }

  // ---------------------------------------------------------------- widgets
  function field(key, lg, value, label, send) {
    const ta = el("textarea", { rows: 1, lang: lg, spellcheck: "true", "data-key": key, placeholder: lg.toUpperCase(), "aria-label": label + " (" + lg.toUpperCase() + ")" });
    ta.value = key in state.local ? state.local[key] : (value || "");
    if (key in state.local && state.local[key] === (value || "")) delete state.local[key];
    ta.addEventListener("input", () => { state.local[key] = ta.value; autosize(ta); queue(key, () => send(ta.value)); });
    ta.addEventListener("blur", () => { flush(key); delete state.local[ta.dataset.key]; });
    return ta;
  }
  function pair(keyBase, label, values, sendFor, note) {
    const wrap = el("div", { class: "pair" }, el("div", { class: "pair-label" }, label, note ? el("span", { class: "muted small" }, " " + note) : null));
    const cols = el("div", { class: "cols" });
    for (const lg of LANGS) cols.append(el("div", null, el("label", null, lg.toUpperCase()), field(keyBase + "|" + lg, lg, (values || {})[lg], label, (v) => sendFor(lg, v))));
    wrap.append(cols);
    return wrap;
  }
  function tools(...buttons) { return el("span", { class: "dz-tools" }, ...buttons.filter(Boolean)); }
  function tool(text, title, onclick, disabled) { return el("button", { type: "button", class: "ghost small", title, "aria-label": title, disabled: disabled ? "" : null, onclick }, text); }
  function toggleOpen(id) { if (state.open.has(id)) state.open.delete(id); else state.open.add(id); renderPicker(); }
  function issueBox(iss) {
    const errs = iss.filter((i) => i.level === "error"), warns = iss.filter((i) => i.level === "warning");
    const box = el("div", { class: "child-issues" });
    if (errs.length) box.append(el("div", { class: "gate err" }, el("strong", null, "Errors (block saving):"), el("ul", null, ...errs.map((i) => el("li", null, (i.lang ? i.lang.toUpperCase() + ": " : "") + i.message)))));
    if (warns.length) box.append(el("div", { class: "gate warn" }, el("strong", null, "Warnings:"), el("ul", null, ...warns.map((i) => el("li", null, (i.lang ? i.lang.toUpperCase() + ": " : "") + i.message)))));
    return box;
  }
  function issuePills(iss) {
    const errs = iss.filter((i) => i.level === "error").length;
    if (errs) return [pill("st-todo", errs + " error" + (errs > 1 ? "s" : ""))];
    return iss.length ? [pill("st-same", iss.length + " warning" + (iss.length > 1 ? "s" : ""))] : [];
  }
  function snapshotText(snap) {
    if (!snap) return "";
    if (snap.text) return tx(snap.text);
    return [tx(snap.role), tx(snap.org), tx(snap.date)].filter(Boolean).join(" · ");
  }
  // "edited for Diseño" / shared / Designed-only, with Reset and the shared-text notice (D18)
  function statusPills(st) {
    if (st.shared) return []; // the usual case: the shared text, unmarked
    if (st.copy && st.sharedGone) return [pill("draft", "edited for Diseño", "The shared text it was copied from no longer exists.")];
    if (st.copy && st.edited) return [pill("draft", "edited for Diseño", "This output has its own wording; the other documents keep the shared text.")];
    if (st.copy) return [pill("", "copy · same as shared", "A copy that reads as the shared text does. Reset folds it back into the shared item.")];
    return [pill("", "Designed only", "Written for this output; it is in no Word document.")];
  }
  function statusBox(id, st) {
    const box = el("div", { class: "dz-status" });
    if (st.shared) { box.append(el("p", { class: "muted small" }, "Shared with the Word documents. Typing here changes the Designed CV only: the first edit makes a copy for this output.")); return box; }
    if (!st.copy) { box.append(el("p", { class: "muted small" }, "Written for the Designed CV only.")); return box; }
    if (st.sharedGone) { box.append(el("p", { class: "muted small" }, "The shared text this was copied from no longer exists; this wording is the Designed CV's own now.")); return box; }
    if (st.sharedChanged && st.edited) {
      box.append(el("div", { class: "gate info" }, el("strong", null, "The shared text has changed since this copy was made."), el("div", { class: "small" }, "Shared now: ", el("span", { class: "dz-shared" }, snapshotText(st.sharedText))), el("div", { class: "small muted" }, "When copied: " + snapshotText(st.base)),
        el("div", { class: "rowline" }, el("button", { type: "button", class: "ghost small", "data-act": "reset", onclick: () => doReset(id) }, "Reset to shared text"), el("button", { type: "button", class: "ghost small", "data-act": "keep", onclick: () => op({ op: "keep", id: resolve(id) }) }, "Keep mine"))));
      return box;
    }
    box.append(el("div", { class: "rowline" },
      el("span", { class: "muted small" }, st.edited ? "Shared text: " : "Reads as the shared text. ", st.edited ? el("span", { class: "dz-shared" }, snapshotText(st.sharedText)) : null),
      el("button", { type: "button", class: "ghost small", "data-act": "reset", onclick: () => doReset(id) }, "Reset to shared text")));
    return box;
  }
  function doReset(id) {
    const sent = resolve(id);
    for (const k of Object.keys(state.local)) if (k.split("|")[1] === sent) delete state.local[k]; // what was typed gives way to the shared text
    return op({ op: "reset", id: sent }, (r) => { if (r.id) remap(sent, r.id); });
  }
  function sendText(id, f, lg, value) {
    const sent = resolve(id);
    return op({ op: "text", id: sent, field: f, lang: lg, value }, (r) => { if (r.id) remap(sent, r.id); });
  }

  // ---------------------------------------------------------------- left: the checklist
  function tick(checked, label, onchange, key) {
    const cb = el("input", { type: "checkbox", "aria-label": label, "data-tick": key || null });
    cb.checked = !!checked;
    cb.addEventListener("change", () => onchange(cb.checked));
    return cb;
  }
  function rowShell(opts) {
    const row = el("div", { class: "dz-row" + (opts.sub ? " sub" : "") + (opts.on ? "" : " off") + (opts.open ? " open" : ""), "data-id": opts.id || null });
    const head = el("div", { class: "dz-head" }, opts.tick,
      el("button", { type: "button", class: "dz-label", title: "Edit the text for this output", "aria-expanded": opts.open ? "true" : "false", onclick: opts.toggle }, el("span", { class: "dz-title" }, opts.title || "(empty)"), opts.meta ? el("span", { class: "dz-meta" }, opts.meta) : null),
      el("span", { class: "dz-pills" }, ...(opts.pills || [])), opts.tools);
    row.append(head);
    if (opts.open && opts.body) row.append(el("div", { class: "dz-body" }, ...opts.body.filter(Boolean)));
    return row;
  }
  function childRow(parent, ch, order) {
    const i = order.indexOf(ch.id);
    const open = state.open.has(ch.id);
    const iss = issuesFor(ch.id);
    return rowShell({
      id: ch.id, sub: true, on: ch.on && parent.on, open,
      tick: tick(ch.on, (ch.kind === "bullet" ? "Bullet: " : "Line: ") + short(tx(ch.text), 60), (on) => op({ op: "tick", id: ch.id, on }), ch.id),
      title: short(tx(ch.text), 110), toggle: () => toggleOpen(ch.id),
      pills: statusPills(ch.status).concat(issuePills(iss)),
      tools: tools(tool("↑", "Move up", () => op({ op: "move", id: ch.id, delta: -1 }), i === 0), tool("↓", "Move down", () => op({ op: "move", id: ch.id, delta: 1 }), i === order.length - 1),
        el("a", { class: "ghost small dz-jump", href: "/cvtext#designed/" + encodeURIComponent(parent.id), title: "Open its entry in the CV text tab", onclick: () => { window.__navigating = true; } }, "↗"),
        tool("✕", ch.status.shared ? "Take off this checklist (it stays in the Word documents)" : "Delete (it exists for the Designed CV only)", () => { if (ch.status.shared || confirm("Delete this " + ch.kind + "? It exists for the Designed CV only.")) op({ op: "remove", id: ch.id }); })),
      body: [pair("t|" + ch.id + "|text", ch.kind === "bullet" ? "Bullet" : "Line", ch.text, (lg, v) => sendText(ch.id, "text", lg, v)), statusBox(ch.id, ch.status), issueBox(iss)],
    });
  }
  function itemRow(sec, r, order) {
    const i = order.indexOf(r.id);
    const open = state.open.has(r.id);
    const kids = r.children || [];
    const iss = issuesFor(r.id);
    const isEntry = r.kind === "entry";
    const sections = state.data.checklist.sections;
    const picker = el("select", { "aria-label": "Section in the Designed CV", "data-act": "place" });
    for (const s of sections) picker.append(el("option", { value: s.id, selected: sec && s.id === sec.section ? "" : null }, tx(s.label)));
    if (!sec) picker.prepend(el("option", { value: "", selected: "" }, "— not on the page —"));
    picker.addEventListener("change", () => { if (picker.value) op({ op: "place", id: r.id, section: picker.value }); });
    const body = [];
    if (isEntry) {
      body.push(pair("t|" + r.id + "|role", "Role (the bold line)", r.role, (lg, v) => sendText(r.id, "role", lg, v)),
        pair("t|" + r.id + "|org", "Organization (the line under it)", r.org, (lg, v) => sendText(r.id, "org", lg, v)),
        pair("t|" + r.id + "|date", "Date", r.date, (lg, v) => sendText(r.id, "date", lg, v)));
    } else body.push(pair("t|" + r.id + "|text", "Line", r.text, (lg, v) => sendText(r.id, "text", lg, v)));
    body.push(statusBox(r.id, r.status), issueBox(iss),
      el("div", { class: "rowline" }, el("label", { class: "field dz-inline" }, el("span", null, "Section in the Designed CV only"), picker),
        isEntry ? el("button", { type: "button", class: "ghost small", onclick: async () => { const x = await op({ op: "add-bullet", id: r.id }); if (x && x.id) { state.open.add(x.id); renderPicker(); } } }, "+ Add a bullet (Designed only)") : null));
    const wrap = el("div", { class: "dz-entry" });
    const kidErrs = kids.flatMap((c) => issuesFor(c.id)).filter((x) => x.level === "error").length;
    wrap.append(rowShell({
      id: r.id, on: r.on, open,
      tick: tick(r.on, (isEntry ? "Entry: " : "Line: ") + short(isEntry ? tx(r.role) : tx(r.text), 60), (on) => op({ op: "tick", id: r.id, on }), r.id),
      title: isEntry ? tx(r.role) : short(tx(r.text), 150),
      meta: isEntry ? [tx(r.org), tx(r.date)].filter(Boolean).join(" · ") : null,
      toggle: () => toggleOpen(r.id),
      pills: statusPills(r.status).concat(issuePills(iss), kidErrs ? [pill("st-todo", kidErrs + " in bullets")] : [], isEntry && !r.dated ? [pill("st-same", "no date", "Its date cannot be read, so “Sort newest first” leaves it where it is.")] : []),
      tools: tools(tool("↑", "Move up", () => op({ op: "move", id: r.id, delta: -1 }), i <= 0), tool("↓", "Move down", () => op({ op: "move", id: r.id, delta: 1 }), i < 0 || i === order.length - 1),
        el("a", { class: "ghost small dz-jump", href: "/cvtext#designed/" + encodeURIComponent(r.id), title: "Open it in the CV text tab", onclick: () => { window.__navigating = true; } }, "↗"),
        tool("✕", r.status.shared ? "Take off this checklist (it stays in the Word documents)" : "Delete (it exists for the Designed CV only)", () => { if (confirm(r.status.shared ? "Take “" + short(isEntry ? tx(r.role) : tx(r.text), 50) + "” off the Designed checklist? It stays in the Word documents; tick Designed on it in the CV text tab to bring it back." : "Delete “" + short(isEntry ? tx(r.role) : tx(r.text), 50) + "” and its bullets? It exists for the Designed CV only.")) op({ op: "remove", id: r.id }); })),
      body,
    }));
    const korder = kids.map((c) => c.id);
    for (const c of kids) wrap.append(childRow(r, c, korder));
    return wrap;
  }
  function headingEditor(openKey, label, key, values, note) {
    if (!state.open.has(openKey)) return null;
    return el("div", { class: "dz-body" }, pair("h|" + key + "|heading", label, values, (lg, v) => op({ op: "heading", key, lang: lg, value: v }), note));
  }
  function sectionBlock(sec) {
    const box = el("section", { class: "dz-sec", "data-section": sec.section });
    const hk = "heading:" + sec.section;
    box.append(el("div", { class: "dz-sechead" }, el("h3", null, tx(sec.heading)),
      tools(tool("✎", "Edit this heading for the Designed CV", () => toggleOpen(hk)),
        el("button", { type: "button", class: "ghost small", "data-act": "sort", title: "Order by the entries' dates, newest first (present = today). Rows without a readable date stay where they are.", onclick: async () => { const r = await op({ op: "sort", section: sec.section }); if (r && r.undated && r.undated.length) toast("Not moved (no readable date): " + r.undated.join("; "), 8000); } }, "Sort newest first"))));
    const he = headingEditor(hk, "Heading on this page", "main:" + sec.section, sec.heading, sec.ownHeading ? "(shared heading: " + tx(sec.sharedHeading) + " — clear both to go back to it)" : "(the shared heading; changing it here changes this output only)");
    if (he) box.append(he);
    const order = sec.rows.map((r) => r.id);
    if (!sec.rows.length) box.append(el("p", { class: "muted small" }, "Nothing here yet. Tick “Designed” on an item in the CV text tab to put it on this list."));
    for (const r of sec.rows) box.append(itemRow(sec, r, order));
    return box;
  }
  function singleRow(key, label, node) {
    const open = state.open.has("single:" + key);
    const iss = issuesFor("design." + key);
    return rowShell({
      id: "design." + key, on: node.include, open,
      tick: tick(node.include, label, (on) => op({ op: "single-include", key, on }), "design." + key),
      title: label, meta: short(tx(node.text), 110), toggle: () => toggleOpen("single:" + key), pills: [pill("", "Designed only")].concat(issuePills(iss)),
      tools: tools(),
      body: [pair("s|" + key + "|text", label, node.text, (lg, v) => op({ op: "single-text", key, lang: lg, value: v })), issueBox(iss)],
    });
  }
  function topBlock(d) {
    const box = el("section", { class: "dz-sec", "data-section": "top" }, el("div", { class: "dz-sechead" }, el("h3", null, "Top of the page")));
    const tIss = issuesFor("header.title.designed");
    box.append(rowShell({
      id: "title", on: true, open: state.open.has("title"),
      tick: el("span", { class: "dz-notick", "aria-hidden": "true" }),
      title: "Title line", meta: tx(d.title), toggle: () => toggleOpen("title"), pills: [pill("", "Designed only")].concat(issuePills(tIss)), tools: tools(),
      body: [pair("x|title|title", "Title line (under the name)", d.title || {}, (lg, v) => op({ op: "title", lang: lg, value: v }), "(the name itself is the shared one: CV text › Header)"), issueBox(tIss)],
    }));
    box.append(singleRow("profile", tx(d.design.headings.profile) || "Profile", d.design.profile));
    box.append(singleRow("gpa", "GPA line (under the Education entry)", d.design.gpa));
    const hk = "heading:profile";
    box.append(el("div", { class: "rowline" }, el("button", { type: "button", class: "ghost small", onclick: () => toggleOpen(hk) }, "Headings of the fixed blocks…")));
    if (state.open.has(hk)) {
      const hb = el("div", { class: "dz-body" });
      for (const k of ["profile", "contact", "languages", "skills", "certs", "honors"]) hb.append(pair("h|" + k + "|heading", "Heading: " + k, d.design.headings[k], (lg, v) => op({ op: "heading", key: k, lang: lg, value: v })));
      box.append(hb);
    }
    return box;
  }
  function groupBlock(group) {
    const d = state.data.design;
    const [fa, fb] = d.fields[group];
    const rows = d.groups[group];
    const box = el("section", { class: "dz-sec", "data-section": group });
    box.append(el("div", { class: "dz-sechead" }, el("h3", null, tx(d.headings[group]), " ", el("span", { class: "muted small" }, "sidebar")),
      tools(group === "honors" ? el("button", { type: "button", class: "ghost small", "data-act": "sort", title: "Order by the years, newest first", onclick: async () => { const r = await op({ op: "rows-sort", group }); if (r && r.undated && r.undated.length) toast("Not moved (no year): " + r.undated.join("; "), 8000); } }, "Sort newest first") : null)));
    rows.forEach((r, i) => {
      const key = "design." + group + "." + r.id;
      const open = state.open.has(key);
      const iss = issuesFor(key);
      const st = r.status || {};
      const body = [pair("r|" + group + "/" + r.id + "|" + fa, fa[0].toUpperCase() + fa.slice(1), r[fa], (lg, v) => op({ op: "row-set", group, id: r.id, field: fa, lang: lg, value: v })),
        pair("r|" + group + "/" + r.id + "|" + fb, fb[0].toUpperCase() + fb.slice(1), r[fb], (lg, v) => op({ op: "row-set", group, id: r.id, field: fb, lang: lg, value: v }))];
      if (st.linked) {
        body.push(st.sharedChanged
          ? el("div", { class: "gate info" }, el("strong", null, "The shared line this row came from has changed."), el("div", { class: "small" }, "Shared now: ", el("span", { class: "dz-shared" }, snapshotText(st.sharedText))), el("div", { class: "rowline" }, el("button", { type: "button", class: "ghost small", onclick: () => op({ op: "row-keep", group, id: r.id }) }, "Keep mine")))
          : el("p", { class: "muted small" }, "From the shared line: ", el("span", { class: "dz-shared" }, snapshotText(st.sharedText))));
      } else body.push(el("p", { class: "muted small" }, "Written for the Designed CV only."));
      body.push(issueBox(iss));
      box.append(rowShell({
        id: key, on: r.include, open,
        tick: tick(r.include, d.labels[group] + ": " + tx(r[fa]), (on) => op({ op: "row-include", group, id: r.id, on }), key),
        title: tx(r[fa]), meta: tx(r[fb]), toggle: () => toggleOpen(key),
        pills: (st.linked && st.sharedChanged ? [pill("st-same", "shared line changed")] : []).concat(issuePills(iss)),
        tools: tools(tool("↑", "Move up", () => op({ op: "row-move", group, id: r.id, delta: -1 }), i === 0), tool("↓", "Move down", () => op({ op: "row-move", group, id: r.id, delta: 1 }), i === rows.length - 1),
          tool("✕", "Delete this row", () => { if (confirm("Delete “" + short(tx(r[fa]), 50) + "”?")) op({ op: "row-delete", group, id: r.id }); })),
        body,
      }));
    });
    box.append(el("button", { type: "button", class: "ghost small addlink", onclick: async () => { const r = await op({ op: "row-add", group }); if (r && r.id) { state.open.add("design." + group + "." + r.id); renderPicker(); } } }, "+ Add a row"));
    return box;
  }
  function contactBlock(d) {
    const box = el("section", { class: "dz-sec", "data-section": "contact" }, el("div", { class: "dz-sechead" }, el("h3", null, tx(d.design.headings.contact), " ", el("span", { class: "muted small" }, "sidebar"))));
    const ul = el("ul", { class: "plain" });
    ul.append(el("li", null, d.age.line ? d.age.line[lang()] : el("span", { class: "err-text" }, "no age line: " + d.age.file + " has no readable birth_date"), " ", el("span", { class: "muted small" }, "(computed when the page is drawn; the birth date never prints)")));
    for (const [, text] of d.contact[lang()] || []) ul.append(el("li", null, text));
    box.append(ul, el("p", { class: "muted small" }, "Phone, email, site and LinkedIn are read from the shared contact line, the one place the phone is kept: ", el("a", { href: "/cvtext#designed/header", onclick: () => { window.__navigating = true; } }, "CV text › Header"), ". No location line prints."));
    return box;
  }
  function renderPicker() {
    const box = $("#picker");
    const d = state.data;
    const active = document.activeElement;
    const fk = active && box.contains(active) && active.dataset ? active.dataset.key : null;
    const sel = fk ? [active.selectionStart, active.selectionEnd] : null;
    const scroll = box.scrollTop;
    box.replaceChildren(el("h2", null, "What goes on it"));
    if (d.readOnly) { box.append(el("div", { class: "gate err" }, "Read-only: " + d.readOnly)); return; }
    box.append(topBlock(d));
    for (const sec of d.checklist.main) box.append(sectionBlock(sec));
    if (d.checklist.stray.length) {
      const s = el("section", { class: "dz-sec", "data-section": "stray" }, el("div", { class: "dz-sechead" }, el("h3", null, "Ticked, but under a section this page does not show")),
        el("p", { class: "muted small" }, "These print nowhere until they are given a section of the page (open one and pick its section)."));
      for (const r of d.checklist.stray) s.append(itemRow(null, r, []));
      box.append(s);
    }
    for (const g of ["languages", "skills", "certs", "honors"]) box.append(groupBlock(g));
    box.append(contactBlock(d));
    box.querySelectorAll("textarea").forEach(autosize);
    if (fk) {
      const parts = fk.split("|");
      parts[1] = resolve(parts[1]);
      const n = Array.from(box.querySelectorAll("textarea")).find((t) => t.dataset.key === parts.join("|"));
      if (n) { n.focus(); try { n.setSelectionRange(sel[0], sel[1]); } catch (e) { /* ignore */ } }
    }
    box.scrollTop = scroll;
  }

  // ---------------------------------------------------------------- right: controls, meter, preview
  function seg(label, options, current, onPick, id) {
    const g = el("div", { class: "dz-seg", role: "group", "aria-label": label, id: id || null });
    for (const [value, text] of options) g.append(el("button", { type: "button", "aria-pressed": value === current ? "true" : "false", "data-value": value, onclick: () => onPick(value) }, text));
    return el("div", { class: "dz-ctl" }, el("span", { class: "dz-ctl-label" }, label), g);
  }
  async function setView(values) {
    let r;
    try { r = await api("/api/designed/view", { method: "POST", body: values }); } catch (e) { toast("Failed: " + e.message, 6000); return; }
    if (!r || r.ok === false) { toast("Rejected: " + (r && r.error), 6000); return; }
    state.data.view = r.view;
    state.data.browser = r.browser;
    renderAll();
    refreshPreview();
  }
  function renderControls() {
    const d = state.data, v = d.view, o = d.options;
    const box = $("#controls");
    const icon = el("select", { "aria-label": "Website icon", id: "webIcon" });
    for (const [k, name] of Object.entries(o.webIcons)) icon.append(el("option", { value: k, selected: k === v.webIcon ? "" : null }, name));
    icon.addEventListener("change", () => setView({ webIcon: icon.value }));
    box.replaceChildren(
      seg("Layout", Object.entries(o.layouts).map(([k, name]) => [k, k.toUpperCase() + " · " + name]), v.layout, (x) => setView({ layout: x }), "segLayout"),
      seg("Palette", Object.entries(o.palettes), v.palette, (x) => setView({ palette: x }), "segPalette"),
      seg("Language", o.langs.map((l) => [l, l.toUpperCase()]), v.lang, (x) => setView({ lang: x }), "segLang"),
      seg("Preview", [["color", "Color"], ["grey", "Greyscale"]], state.grey ? "grey" : "color", (x) => { state.grey = x === "grey"; renderControls(); $("#sheet").classList.toggle("grey", state.grey); }, "segInk"),
      seg("Fit", [["width", "Width"], ["page", "Whole page"]], state.fit, (x) => { state.fit = x; renderControls(); scale(); }, "segFit"),
      el("div", { class: "dz-ctl" }, el("span", { class: "dz-ctl-label" }, "Website icon"), icon));
    $("#sheet").classList.toggle("grey", state.grey);
  }
  function renderMeters() {
    const box = $("#meters");
    const m = state.meter;
    if (!m) { box.replaceChildren(el("span", { class: "muted small" }, "Measuring…")); return; }
    const names = { main: "Main column", side: state.data.view.layout === "e" ? "Right rail" : "Sidebar" };
    const cells = [];
    for (const col of ["main", "side"]) {
      const left = m.designedMeter[col];
      if (typeof left !== "number") continue;
      const over = left < 0;
      const pct = over ? 100 : Math.max(0, Math.min(100, 100 - (left / PAGE_H) * 400));
      cells.push(el("div", { class: "dz-meter" + (over ? " over" : ""), id: "meter-" + col, "data-left": String(left) },
        el("div", { class: "small" }, el("strong", null, names[col] + ": "), over ? `over by ${-left} px (about ${cm(left)} cm) — untick something` : `${left} px (${cm(left)} cm) left`),
        el("div", { class: "meter" + (over ? " over" : "") }, el("div", { class: "bar", style: "width:" + pct + "%" }))));
    }
    if (m.fonts && m.fonts !== "ok") cells.push(el("div", { class: "err-text small" }, "Fonts did not load (" + m.fonts + "): the measure is not the PDF's."));
    box.replaceChildren(...cells);
  }
  function scale() {
    const stage = $("#stage"), sheet = $("#sheet");
    // the top bar wraps onto two rows in a narrow window: the checklist sticks below its real height
    document.documentElement.style.setProperty("--dz-top", document.querySelector(".topbar").offsetHeight + "px");
    const cs = getComputedStyle(stage);
    const availW = Math.max(200, stage.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight) - 2);
    let s = Math.min(1, availW / PAGE_W);
    if (state.fit === "page") {
      const top = sheet.getBoundingClientRect().top;
      s = Math.min(s, Math.max(0.2, (window.innerHeight - top - 16) / PAGE_H));
    }
    $("#scaler").style.transform = "scale(" + s + ")";
    sheet.style.width = Math.round(PAGE_W * s) + "px";
    sheet.style.height = Math.round(PAGE_H * s) + "px";
    sheet.dataset.scale = String(s);
  }
  async function refreshPreview() {
    const v = state.data.view;
    const key = String(++state.seq);
    let r;
    try { r = await api(`/api/designed/page?layout=${v.layout}&palette=${v.palette}&lang=${v.lang}&key=${key}`); } catch (e) { $("#meters").replaceChildren(el("span", { class: "err-text small" }, "Preview failed: " + e.message)); return; }
    if (key !== String(state.seq)) return; // a newer draw is on its way
    if (!r || r.ok === false) { $("#meters").replaceChildren(el("span", { class: "err-text small" }, "Preview refused: " + (r && r.error))); return; }
    const back = state.front === "A" ? $("#frameB") : $("#frameA");
    back.dataset.key = key;
    back.srcdoc = r.html;
  }
  // the page posts its own measure once its fonts are in: show that frame, then the numbers
  window.addEventListener("message", (e) => {
    const m = e.data;
    if (!m || !m.designedMeter || m.key !== String(state.seq)) return;
    const back = state.front === "A" ? $("#frameB") : $("#frameA"), front = state.front === "A" ? $("#frameA") : $("#frameB");
    if (e.source !== back.contentWindow) return;
    back.classList.add("front"); back.removeAttribute("aria-hidden");
    front.classList.remove("front"); front.setAttribute("aria-hidden", "true");
    state.front = state.front === "A" ? "B" : "A";
    state.meter = m;
    renderMeters();
  });
  function renderFacts() {
    const d = state.data, box = $("#facts");
    const bits = [];
    const a = d.age;
    bits.push(el("p", { id: "ageFact" }, el("strong", null, "Age on the next PDF: "), a.value === null ? el("span", { class: "err-text" }, "unknown — " + a.file + " has no readable birth_date") : `${a.value} — “${a.line.es}” / “${a.line.en}”. Turns ${a.value + 1} on ${a.nextBirthday}; the birth date itself never prints.`));
    const p = d.photo;
    bits.push(el("p", { class: "muted small" }, p.pixels ? `Photo: ${p.path} (${p.pixels[0]} × ${p.pixels[1]} px) — ${p.dpi.c} dpi at ${p.inches.c} in (layout C), ${p.dpi.e} dpi at ${p.inches.e} in (layout E).` : "Photo: " + p.path + " is missing — the page prints without one."));
    bits.push(el("p", { class: "muted small" }, d.browser ? "Prints with " + d.browser.name + " (headless, its own throwaway profile)." : el("span", { class: "err-text" }, "No Edge or Chrome found — exporting is off."), d.linkedinIcon ? "" : " LinkedIn's logo file is not on this machine: the LinkedIn row uses the generic link icon."));
    const stale = d.exports.filter((x) => x.stale);
    const ex = el("p", { class: "small", id: "exportsFact" }, el("strong", null, `${d.exports.length} PDF${d.exports.length === 1 ? "" : "s"} in ${d.outDir}/`), d.exports.length ? ` — newest ${fmtTime(d.exports[0].mtime)}.` : ".", " ", el("span", { class: "muted" }, d.publish.note));
    bits.push(ex);
    if (stale.length) bits.push(el("div", { class: "gate warn", id: "staleBox" }, el("strong", null, "Rendered before a birthday that has passed:"), el("ul", null, ...stale.map((x) => el("li", null, x.name + " — " + x.note)))));
    box.replaceChildren(...bits);
    if (stale.length) setBanner("stale", "warn", `${stale.length} Designed CV PDF${stale.length > 1 ? "s were" : " was"} ${stale[0].note.replace(": re-render", "")}. Re-render before sending.`, [{ label: "Export PDF…", primary: true, onclick: openExport }]);
    else clearBanner("stale");
  }

  // ---------------------------------------------------------------- review & save (the CV text service's)
  function renderCounts() {
    const n = (state.data && state.data.draftCount) || 0;
    $("#draftCount").textContent = String(n);
    $("#draftCount").hidden = n === 0;
    state.unsaved = n > 0;
  }
  const issueList = (items) => el("ul", null, ...items.map((i) => el("li", null, el("strong", null, short(i.label || "", 50)), (i.lang ? " (" + i.lang.toUpperCase() + ")" : ""), ": " + i.message)));
  async function openReview() {
    Object.keys(senders).forEach(flush);
    const dlg = $("#reviewDlg"), body = $("#reviewBody");
    body.replaceChildren(el("p", { class: "muted" }, "Preparing…"));
    $("#saveBtn").disabled = true;
    dlg.showModal();
    let r;
    try { await new Promise((res) => setTimeout(res, 120)); r = await api("/api/cvtext/review"); } catch (e) { body.replaceChildren(el("p", null, "Review failed: " + e.message)); return; }
    body.replaceChildren();
    if (r.readOnly) { body.append(el("div", { class: "gate err" }, "Read-only: " + r.error)); return; }
    if (r.noop) body.append(el("p", { class: "muted" }, "No changes — content.json already matches."));
    else body.append(el("ul", { class: "changes" }, ...r.changes.map((c) => el("li", null, c.text))));
    body.append(el("p", { class: "muted small" }, "Save writes staging/cv-content/content.json only (backed up first). The Word masters are never touched from this tab."));
    const touchedMasters = (r.masters || []).filter((m) => m.changed.length || m.added.length || m.removed.length);
    if (touchedMasters.length) body.append(el("div", { class: "gate info" }, "The drafts also change shared text that " + touchedMasters.map((m) => m.title).join(", ") + " would take on the next Apply (CV text tab). Saving here does not rewrite them."));
    if (r.diskChanged) body.append(el("div", { class: "gate err" }, "content.json changed on disk since it was loaded. Close this, click Reload in the banner, then review again."));
    const g = r.gate;
    if (g.blocking.length) body.append(el("div", { class: "gate err" }, el("strong", null, "Blocking errors (fix before saving):"), issueList(g.blocking)));
    if (g.warnings.length) body.append(el("div", { class: "gate warn" }, el("strong", null, "Warnings (saving is allowed):"), issueList(g.warnings.slice(0, 15)), g.warnings.length > 15 ? el("p", { class: "muted" }, "… and " + (g.warnings.length - 15) + " more") : null));
    if (g.preexisting.length) body.append(el("div", { class: "gate info" }, el("strong", null, "Pre-existing errors elsewhere (not blocking):"), issueList(g.preexisting)));
    if (!r.noop) body.append(el("h3", null, r.file), renderDiff(r.diff));
    $("#saveBtn").disabled = !r.ok;
  }
  async function doSave() {
    $("#saveBtn").disabled = true;
    let r;
    try { r = await api("/api/cvtext/save", { method: "POST", body: {} }); } catch (e) { toast("Save failed: " + e.message); $("#saveBtn").disabled = false; return; }
    if (!r.ok) { toast(r.message || r.error, 7000); if (r.error === "changed-on-disk") { $("#reviewDlg").close(); showDiskBanner(r.message); } else $("#saveBtn").disabled = false; return; }
    $("#reviewDlg").close();
    toast("Saved content.json. Backup set " + r.backup + ".", 6000);
    await loadState();
  }
  async function discardAll() {
    if (!state.data.draftCount) { $("#reviewDlg").close(); return; }
    if (!confirm("Discard all " + state.data.draftCount + " CV content edit(s) (this tab's and the CV text tab's)? content.json is not touched.")) return;
    await api("/api/cvtext/drafts/discard", { method: "POST", body: {} });
    state.local = {}; state.idmap = {};
    $("#reviewDlg").close();
    await loadState();
    toast("Drafts discarded.");
  }

  // ---------------------------------------------------------------- export
  function exportsTable(list) {
    if (!list.length) return el("p", { class: "muted small" }, "No PDFs yet.");
    const t = el("table", { class: "docs", id: "exportsTable" }, el("tr", null, el("th", null, "PDF"), el("th", null, "Rendered"), el("th", null, "Age it carries")));
    for (const x of list) t.append(el("tr", { class: x.stale ? "is-stale" : "" }, el("td", null, x.name), el("td", null, fmtTime(x.mtime)), el("td", null, x.age === null ? "?" : String(x.age), x.stale ? el("div", { class: "warn-text" }, x.note) : null)));
    return t;
  }
  function openExport() {
    const d = state.data, v = d.view;
    const body = $("#exportBody");
    const boxes = (name, options, current) => el("div", { class: "tagbox", id: name }, ...options.map(([val, text]) => { const cb = el("input", { type: "checkbox", value: val }); cb.checked = val === current; return el("label", { class: "chk" }, cb, " " + text); }));
    const browser = el("select", { id: "browserPick", "aria-label": "Browser" }, ...[["auto", "Edge, else Chrome"], ["edge", "Edge"], ["chrome", "Chrome, else Edge"]].map(([val, text]) => el("option", { value: val, selected: val === v.browser ? "" : null }, text)));
    if (!["auto", "edge", "chrome"].includes(v.browser)) browser.append(el("option", { value: v.browser, selected: "" }, v.browser));
    browser.addEventListener("change", async () => { await setView({ browser: browser.value }); $("#browserNote").textContent = state.data.browser ? state.data.browser.name : "none found"; });
    body.replaceChildren(
      el("div", { class: "form-grid" },
        el("div", { class: "field" }, el("span", null, "Layouts"), boxes("exLayouts", Object.entries(d.options.layouts).map(([k, n]) => [k, k.toUpperCase() + " · " + n]), v.layout)),
        el("div", { class: "field" }, el("span", null, "Languages"), boxes("exLangs", d.options.langs.map((l) => [l, l.toUpperCase()]), v.lang)),
        el("div", { class: "field" }, el("span", null, "Palette"), el("div", null, d.options.palettes[v.palette] + " (as in the preview)")),
        el("label", { class: "field" }, el("span", null, "Browser (headless; ", el("span", { id: "browserNote" }, d.browser ? d.browser.name : "none found"), ")"), browser)),
      el("p", { class: "muted small" }, "Each PDF is printed from the saved content and kept only if it passes: no column over its height, exactly one page, the blocklist, no birth date, every ticked text present. Files go to " + d.outDir + "/ and nowhere else."),
      el("div", { id: "exportBlockers" }),
      el("pre", { class: "joblog", id: "exportLog", hidden: "" }, ""),
      el("div", { id: "exportResult" }),
      el("h3", null, "PDFs in " + d.outDir + "/"),
      el("div", { id: "exportsList" }, exportsTable(d.exports)));
    const blockers = d.exportBlockers || [];
    if (blockers.length) $("#exportBlockers").append(el("div", { class: "gate err" }, el("strong", null, "Export is blocked:"), el("ul", null, ...blockers.map((b) => el("li", null, b)))));
    $("#exportGo").disabled = blockers.length > 0;
    $("#exportDlg").showModal();
  }
  async function runExport() {
    const picked = (id) => Array.from(document.querySelectorAll("#" + id + " input:checked")).map((c) => c.value);
    const layouts = picked("exLayouts"), langs = picked("exLangs");
    if (!layouts.length || !langs.length) { toast("Pick at least one layout and one language."); return; }
    $("#exportGo").disabled = true;
    $("#exportResult").replaceChildren();
    const logBox = $("#exportLog");
    logBox.hidden = false;
    logBox.textContent = "Starting…";
    let res;
    try { res = await api("/api/designed/export", { method: "POST", body: { layouts, langs, palette: state.data.view.palette } }); } catch (e) { logBox.textContent = "Export refused: " + e.message; $("#exportGo").disabled = false; return; }
    if (!res || res.ok === false) { logBox.textContent = "Export refused: " + (res && res.error); $("#exportGo").disabled = false; return; }
    const tickJob = async () => {
      let j;
      try { j = await api("/api/designed/job"); } catch (e) { logBox.textContent += "\nlost the job status: " + e.message; return; }
      const job = j.job;
      if (job) { logBox.textContent = job.log.join("\n") + (job.running ? "\n…" : ""); logBox.scrollTop = logBox.scrollHeight; }
      if (job && job.running) { setTimeout(tickJob, 600); return; }
      const box = $("#exportResult");
      if (job) {
        const failed = Object.entries(job.failed || {});
        if (job.done.length) box.append(el("div", { class: "gate info", id: "exportDone" }, el("strong", null, "Exported: "), el("ul", null, ...job.done.map((x) => el("li", null, x.file, x.warnings.length ? el("details", null, el("summary", { class: "small" }, x.warnings.length + " warning" + (x.warnings.length > 1 ? "s" : "")), el("ul", { class: "plain" }, ...x.warnings.map((w) => el("li", { class: "warn-text" }, w)))) : null)))));
        if (failed.length) box.append(el("div", { class: "gate err", id: "exportFailed" }, el("strong", null, "Not exported:"), el("ul", null, ...failed.map(([tag, why]) => el("li", null, el("strong", null, tag + ": "), why.join(" · "))))));
        if (job.error) box.append(el("div", { class: "gate err" }, "The job stopped: " + job.error));
      }
      $("#exportsList").replaceChildren(exportsTable(j.exports || []));
      $("#exportGo").disabled = false;
      await loadState();
    };
    tickJob();
  }

  // ---------------------------------------------------------------- state
  function showDiskBanner(msg) {
    if (!banners.disk) setBanner("disk", "warn", msg || "content.json changed on disk (VS Code, Claude Code, an import). Saving is refused until you reload; drafts are kept.", [{ label: "Reload", primary: true, onclick: async () => { await api("/api/cvtext/reload", { method: "POST", body: {} }); clearBanner("disk"); await loadState(); toast("Reloaded from disk."); } }]);
  }
  function renderAll() {
    renderCounts();
    renderControls();
    renderPicker();
    renderFacts();
    const d = state.data;
    if (!d.seeded && d.seedAvailable && !d.readOnly) setBanner("seed", "", "The Designed CV is empty. Fill it with the mockup's selection and short bullets (staging/cv-design/seed.json)? It becomes a draft to review before saving.", [{ label: "Seed it", primary: true, onclick: async () => { const r = await op({ op: "seed" }); if (r) toast(`Seeded: ${r.placed} items placed` + (r.missing.length ? `; not found: ${r.missing.join(", ")}` : "."), 8000); } }]);
    else clearBanner("seed");
    if (d.migrated && !state.dismissed.migrated) setBanner("migrated", "", `content.json was moved to version ${d.migrated.to} when the editor started (backup set ${d.migrated.backup}). Nothing in the Word documents changed.`, [{ label: "Dismiss", onclick: () => { state.dismissed.migrated = true; clearBanner("migrated"); } }]);
  }
  async function loadState() {
    const d = await api("/api/designed/state");
    state.data = d;
    const has = !!d.hasDesign;
    $("#editor").hidden = !has;
    $("#noContent").hidden = has;
    $("#reviewBtn").hidden = !has;
    $("#exportBtn").hidden = !has;
    if (!has) {
      if (d.loadError) setBanner("readonly", "err", d.loadError); else clearBanner("readonly");
      if (d.loaded) $("#noContentText").textContent = "This content set has no Designed block yet. Start the editor from its shortcut once so it can migrate content.json (a backup is made first).";
      return;
    }
    if (d.readOnly) setBanner("readonly", "err", "Read-only: " + d.readOnly); else clearBanner("readonly");
    if (d.diskChanged) showDiskBanner(); else clearBanner("disk");
    if (d.autosave) setBanner("autosave", "warn", "Unsaved CV content edits from " + d.autosave.saved + " were found.", [
      { label: "Restore drafts", primary: true, onclick: async () => { const r = await api("/api/cvtext/autosave/restore", { method: "POST", body: {} }); clearBanner("autosave"); toast(r.applied ? "Drafts restored" : "Nothing to restore — the file already matched"); await loadState(); } },
      { label: "Discard", onclick: async () => { await api("/api/cvtext/autosave/discard", { method: "POST", body: {} }); clearBanner("autosave"); } }]);
    else clearBanner("autosave");
    renderAll();
    scale();
    refreshPreview();
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
    $("#reviewBtn").addEventListener("click", openReview);
    $("#saveBtn").addEventListener("click", doSave);
    $("#discardBtn").addEventListener("click", discardAll);
    $("#exportBtn").addEventListener("click", openExport);
    $("#exportGo").addEventListener("click", runExport);
    $("#openOutBtn").addEventListener("click", async () => { try { await api("/api/designed/open-out", { method: "POST", body: {} }); } catch (e) { toast("Could not open the folder: " + e.message); } });
    document.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); if (state.data && state.data.hasDesign && !$("#reviewDlg").open) openReview(); } });
    window.addEventListener("beforeunload", (e) => { if (state.unsaved && !window.__navigating) { e.preventDefault(); e.returnValue = ""; } });
    new ResizeObserver(() => { if (state.data && state.data.hasDesign) scale(); }).observe($("#stage"));
    window.addEventListener("resize", () => { if (state.data && state.data.hasDesign) scale(); });
    loadState().catch((e) => setBanner("load", "err", "Could not load: " + e.message));
    heartbeat();
    setInterval(heartbeat, 5000);
  }
  init();
  window.__designed = state; // for tests
})();
