// feedback.js — the /learning feedback widget (CLAUDE.md → /learning → Feedback; decisions
// F1–F10 in learning/learning-plan.md). Loaded at the end of every /learning page after
// strings-common.js (and, on bilingual pages, learning-i18n.js).
//
// What it does:
//   - The footer's `.fb-slot` span (the static "Found a mistake? <email>" line) becomes a
//     "Feedback" button that opens a small panel: kind chips, message, optional email, Send,
//     one line of privacy text. Success: "Thanks. Sent." Failure: the text stays and the
//     email shows as selectable text.
//   - Selecting text in the page (fine pointers only, not touch) shows a "Comment on this"
//     button beside the selection, which opens the same panel with the quote filled in.
//   - POST /api/feedback with kind, message, quote, path, section (nearest heading or section
//     with an id), series, lang, vw (width bucket), email, elapsed (ms since the panel opened),
//     website (honeypot, always empty for people). Nothing else: no IP, UA, cookies.
//   - Owner mode (F5): open any page with #owner-setup once, paste the owner key; it is kept
//     in localStorage "learnFeedbackOwner" and sent as the X-Feedback-Owner header. The hash
//     is removed from the URL. "Posting as Gideon" shows while a key is set.
//   - Where it doesn't send (F8): from file: and in the offline app the footer keeps the email
//     line and nothing else runs. On localhost it dry-runs (logs the payload, shows success)
//     unless the URL has ?feedback=live (then it posts, for `vercel dev`).
//
// Strings: fb* keys in strings-common.js, through LI18N when the page has it (Reading Your
// Fits, the hub), else the EN table (Reflections pages load strings-common.js as plain data).
// Panel = a native <dialog> (showModal): Esc, focus trap and backdrop come from the browser.
(function () {
  "use strict";
  var API = "/api/feedback";
  var OWNER_KEY = "learnFeedbackOwner";
  var EMAIL = "gao9819@utulsa.edu";
  var MAX_MESSAGE = 2000, MAX_QUOTE = 500, MIN_SELECTION = 3;

  var isFile = location.protocol === "file:";
  var isDev = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
  var dryRun = isDev && !/[?&]feedback=live(&|$)/.test(location.search);
  var slot = document.querySelector(".fb-slot");
  if (isFile || window.LEARN_OFFLINE || !slot) return;

  var C = window.LEARN_STRINGS_COMMON || { en: {} };
  function t(k, vars) {
    if (window.LI18N) return window.LI18N.t(k, vars);
    var s = C.en[k] === undefined ? k : C.en[k];
    if (vars) s = s.replace(/\{(\w+)\}/g, function (m, key) { return key in vars ? String(vars[key]) : m; });
    return s;
  }
  function lang() { return window.LI18N ? window.LI18N.lang : (document.documentElement.lang || "en").slice(0, 2); }
  var series = document.documentElement.getAttribute("data-series") || "hub";

  function store(get, value) {
    try {
      if (get) return localStorage.getItem(OWNER_KEY) || "";
      if (value) localStorage.setItem(OWNER_KEY, value); else localStorage.removeItem(OWNER_KEY);
    } catch (e) { /* storage blocked: visitor mode for this page view */ }
    return "";
  }
  function ownerKey() { return store(true); }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  // ---------- the footer trigger ----------
  var trigger = el("button", "fb-open");
  trigger.type = "button";
  slot.textContent = "";
  slot.removeAttribute("data-i18n");   // the i18n engine would otherwise restore the email text on a language switch
  slot.appendChild(trigger);

  // ---------- the panel ----------
  var texts = [];                       // [element, key] pairs re-applied on a language switch
  function T(e, key) { texts.push([e, key]); return e; }
  var dialog = el("dialog", "fb-panel");
  if (document.body.classList.contains("hub")) dialog.classList.add("hub-frame");
  dialog.setAttribute("aria-labelledby", "fb-title");
  var form = el("form", "fb-form");
  form.noValidate = true;
  dialog.appendChild(form);

  var head = el("div", "fb-head");
  var h2 = T(el("h2"), "fbTitle"); h2.id = "fb-title";
  var closeBtn = el("button", "fb-close", "✕"); closeBtn.type = "button";
  head.appendChild(h2); head.appendChild(closeBtn);
  form.appendChild(head);

  var ownerNote = T(el("p", "fb-owner"), "fbOwnerNote"); ownerNote.hidden = true;
  form.appendChild(ownerNote);

  // Owner setup (shown only by #owner-setup)
  var setup = el("div", "fb-setup"); setup.hidden = true;
  var setupTitle = T(el("h3"), "fbOwnerTitle");
  var setupHint = T(el("p", "fb-hint"), "fbOwnerHint");
  var setupLabel = el("label");
  var setupInput = el("input"); setupInput.type = "password"; setupInput.autocomplete = "off"; setupInput.spellcheck = false; setupInput.maxLength = 200;
  setupLabel.appendChild(T(el("span"), "fbOwnerTitle")); setupLabel.appendChild(setupInput);
  var setupRow = el("div", "fb-actions");
  var setupSave = T(el("button", "btn"), "fbOwnerSave"); setupSave.type = "button";
  var setupForget = T(el("button", "fb-link"), "fbOwnerForget"); setupForget.type = "button";
  var setupStatus = el("span", "fb-status"); setupStatus.setAttribute("role", "status");
  setupRow.appendChild(setupSave); setupRow.appendChild(setupForget); setupRow.appendChild(setupStatus);
  setup.appendChild(setupTitle); setup.appendChild(setupHint); setup.appendChild(setupLabel); setup.appendChild(setupRow);
  form.appendChild(setup);

  var fields = el("div", "fb-fields");
  form.appendChild(fields);

  var kinds = el("fieldset", "fb-kinds");
  kinds.appendChild(T(el("legend"), "fbKindLegend"));
  var KINDS = ["mistake", "confusing", "suggestion", "other"];
  KINDS.forEach(function (k, i) {
    var label = el("label", "fb-chip"), input = el("input");
    input.type = "radio"; input.name = "kind"; input.value = k; if (i === 0) input.checked = true;
    label.appendChild(input);
    label.appendChild(T(el("span"), "fbKind" + k.charAt(0).toUpperCase() + k.slice(1)));
    kinds.appendChild(label);
  });
  fields.appendChild(kinds);

  var quoteBox = el("div", "fb-quote"); quoteBox.hidden = true;
  var quoteLabel = T(el("span", "fb-quote-label"), "fbQuoteLabel");
  var quoteText = el("q", "fb-quote-text");
  var quoteRemove = T(el("button", "fb-link"), "fbQuoteRemove"); quoteRemove.type = "button";
  quoteBox.appendChild(quoteLabel); quoteBox.appendChild(quoteText); quoteBox.appendChild(quoteRemove);
  fields.appendChild(quoteBox);

  var msgLabel = el("label", "fb-field");
  var textarea = el("textarea"); textarea.name = "message"; textarea.rows = 5; textarea.maxLength = MAX_MESSAGE; textarea.required = true;
  msgLabel.appendChild(T(el("span"), "fbMessage")); msgLabel.appendChild(textarea);
  fields.appendChild(msgLabel);

  var emailLabel = el("label", "fb-field");
  var emailInput = el("input"); emailInput.type = "email"; emailInput.name = "email"; emailInput.maxLength = 254; emailInput.autocomplete = "email";
  emailLabel.appendChild(T(el("span"), "fbEmail")); emailLabel.appendChild(emailInput);
  fields.appendChild(emailLabel);

  // Honeypot: out of the tab order and the accessibility tree, off screen, autocomplete off.
  var hp = el("label", "fb-hp"); hp.setAttribute("aria-hidden", "true");
  var hpInput = el("input"); hpInput.type = "text"; hpInput.name = "website"; hpInput.tabIndex = -1; hpInput.autocomplete = "off";
  hp.appendChild(el("span", "", "Website")); hp.appendChild(hpInput);
  fields.appendChild(hp);

  fields.appendChild(T(el("p", "fb-privacy"), "fbPrivacy"));

  var actions = el("div", "fb-actions");
  var send = T(el("button", "btn fb-send"), "fbSend"); send.type = "submit";
  var status = el("span", "fb-status"); status.setAttribute("role", "status"); status.setAttribute("aria-live", "polite");
  actions.appendChild(send); actions.appendChild(status);
  fields.appendChild(actions);

  var fail = el("p", "fb-fail"); fail.hidden = true;
  var failText = T(el("span"), "fbFail");
  var failEmail = el("code", "fb-email", EMAIL);
  fail.appendChild(failText); fail.appendChild(document.createTextNode(" ")); fail.appendChild(failEmail);
  fields.appendChild(fail);

  var done = el("div", "fb-done"); done.hidden = true;
  var doneText = T(el("p", "fb-sent"), "fbSent");
  var doneNote = el("p", "fb-hint");
  done.appendChild(doneText); done.appendChild(doneNote);
  form.appendChild(done);

  document.body.appendChild(dialog);

  function applyText() {
    texts.forEach(function (p) { p[0].textContent = t(p[1]); });
    trigger.textContent = t("fbOpen");
    closeBtn.setAttribute("aria-label", t("fbClose"));
    selBtn.textContent = t("fbCommentOn");
    ownerNote.hidden = !ownerKey();
  }

  // ---------- open / close ----------
  var opener = null, openedAt = 0, quote = "";
  function open(from, q) {
    opener = from || trigger;
    quote = q || "";
    quoteText.textContent = quote;
    quoteBox.hidden = !quote;
    openedAt = Date.now();
    setup.hidden = true; fields.hidden = false; done.hidden = true; fail.hidden = true;
    status.textContent = ""; send.disabled = false;
    ownerNote.hidden = !ownerKey();
    if (!dialog.open) dialog.showModal();
    textarea.focus();
  }
  function close() { if (dialog.open) dialog.close(); }
  dialog.addEventListener("close", function () {
    var back = opener && document.contains(opener) && !opener.hidden ? opener : trigger;
    try { back.focus(); } catch (e) { /* nothing to focus */ }
    opener = null;
  });
  closeBtn.addEventListener("click", close);
  dialog.addEventListener("click", function (e) { if (e.target === dialog) close(); });   // backdrop
  trigger.addEventListener("click", function () { sectionAtOpen = sectionId(null); open(trigger, ""); });
  quoteRemove.addEventListener("click", function () { quote = ""; quoteBox.hidden = true; textarea.focus(); });

  // ---------- the payload ----------
  function widthBucket() { var w = window.innerWidth; return w < 480 ? "<480" : w < 1024 ? "<1024" : "≥1024"; }
  // Nearest heading or section with an id: the last one that starts above `fromEl` (a selection)
  // or, with no element, above the upper part of the viewport (the reader's place on the page).
  function sectionId(fromEl) {
    var cands = document.querySelectorAll("h1[id], h2[id], h3[id], h4[id], section[id], article[id]");
    var best = "";
    for (var i = 0; i < cands.length; i++) {
      var c = cands[i];
      if (c.closest(".fb-panel, .series-bar, .foot")) continue;
      if (fromEl) {
        var rel = c.compareDocumentPosition(fromEl);
        if (c === fromEl || c.contains(fromEl) || (rel & Node.DOCUMENT_POSITION_FOLLOWING)) best = c.id; else break;
      } else if (c.getBoundingClientRect().top <= window.innerHeight * 0.4) best = c.id;
    }
    return best;
  }
  var sectionAtOpen = "";
  function payload() {
    var kind = form.querySelector("input[name=kind]:checked");
    return {
      kind: kind ? kind.value : "other",
      message: textarea.value.trim().slice(0, MAX_MESSAGE),
      quote: quote.slice(0, MAX_QUOTE),
      path: location.pathname.slice(0, 200),
      section: sectionAtOpen,
      series: series,
      lang: lang(),
      vw: widthBucket(),
      email: emailInput.value.trim().slice(0, 254),
      elapsed: Date.now() - openedAt,
      website: hpInput.value
    };
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!setup.hidden) { saveOwner(); return; }
    if (!textarea.value.trim()) { status.textContent = t("fbRequired"); textarea.focus(); return; }
    var data = payload();
    fail.hidden = true;
    send.disabled = true;
    status.textContent = t("fbSending");
    if (dryRun) {
      console.log("[feedback dry-run] POST " + API, data, ownerKey() ? "(owner key set)" : "");
      return finish({ ok: true, dry: true });
    }
    var headers = { "Content-Type": "application/json" };
    var key = ownerKey();
    if (key) headers["X-Feedback-Owner"] = key;
    fetch(API, { method: "POST", headers: headers, body: JSON.stringify(data), credentials: "omit" })
      .then(function (r) { return r.ok ? r.json().catch(function () { return { ok: true }; }) : { ok: false }; })
      .then(finish, function () { finish({ ok: false }); });
  });
  function finish(res) {
    send.disabled = false;
    status.textContent = "";
    if (res && res.ok) {
      fields.hidden = true; done.hidden = false;
      doneNote.textContent = res.dry ? t("fbDryRun") : res.labels ? t("fbSentLabels", { path: res.labels }) : "";
      textarea.value = ""; emailInput.value = ""; quote = ""; quoteBox.hidden = true;
      closeBtn.focus();
    } else {
      fail.hidden = false;     // the text stays in the fields
      textarea.focus();
    }
  }

  // ---------- "Comment on this" beside a selection (fine pointers only) ----------
  var selBtn = el("button", "fb-sel"); selBtn.type = "button"; selBtn.hidden = true;
  document.body.appendChild(selBtn);
  var finePointer = window.matchMedia && window.matchMedia("(pointer: fine)").matches;
  var selText = "", selEl = null, selTimer;
  function selection() {
    var s = window.getSelection();
    if (!s || s.isCollapsed || !s.rangeCount) return null;
    var range = s.getRangeAt(0), node = range.commonAncestorContainer;
    var e = node.nodeType === 1 ? node : node.parentElement;
    if (!e || e.closest(".fb-panel, .fb-sel, .series-bar, .foot, nav, input, textarea, button")) return null;
    var text = s.toString().replace(/\s+/g, " ").trim();
    if (text.length < MIN_SELECTION) return null;
    var startNode = range.startContainer;
    return { text: text, el: startNode.nodeType === 1 ? startNode : startNode.parentElement, rect: range.getBoundingClientRect() };
  }
  function showSelBtn() {
    var sel = finePointer && !dialog.open ? selection() : null;
    if (!sel) { selBtn.hidden = true; return; }
    selText = sel.text; selEl = sel.el;
    selBtn.hidden = false;
    var r = sel.rect, bw = selBtn.offsetWidth, bh = selBtn.offsetHeight;
    var left = Math.min(Math.max(8, r.right - bw), window.innerWidth - bw - 8) + window.scrollX;
    var top = r.bottom + 8 + window.scrollY;
    if (r.bottom + 8 + bh > window.innerHeight && r.top - bh - 8 >= 0) top = r.top - bh - 8 + window.scrollY;   // no room below: above
    selBtn.style.left = left + "px";
    selBtn.style.top = top + "px";
  }
  if (finePointer) {
    document.addEventListener("selectionchange", function () { clearTimeout(selTimer); selTimer = setTimeout(showSelBtn, 150); });
    document.addEventListener("mousedown", function (e) { if (e.target !== selBtn) selBtn.hidden = true; });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !dialog.open) selBtn.hidden = true; });
    selBtn.addEventListener("click", function () {
      var q = selText.slice(0, MAX_QUOTE);
      sectionAtOpen = sectionId(selEl);
      selBtn.hidden = true;
      open(selBtn, q);
    });
  }

  // ---------- owner setup (#owner-setup) ----------
  function saveOwner() {
    var v = setupInput.value.trim();
    if (!v) { forgetOwner(); return; }
    store(false, v);
    setupInput.value = "";
    setupStatus.textContent = t("fbOwnerSaved");
    ownerNote.hidden = !ownerKey();
  }
  function forgetOwner() {
    store(false, "");
    setupInput.value = "";
    setupStatus.textContent = t("fbOwnerCleared");
    ownerNote.hidden = true;
  }
  setupSave.addEventListener("click", saveOwner);
  setupForget.addEventListener("click", forgetOwner);
  function openSetup() {
    opener = trigger;
    setup.hidden = false; fields.hidden = true; done.hidden = true;
    setupStatus.textContent = "";
    ownerNote.hidden = !ownerKey();
    if (!dialog.open) dialog.showModal();
    setupInput.focus();
  }
  if (location.hash === "#owner-setup") {
    try { history.replaceState(null, "", location.pathname + location.search); } catch (e) { /* keep the hash */ }
    openSetup();
  }

  applyText();
  document.addEventListener("learnlangchange", applyText);
}());
