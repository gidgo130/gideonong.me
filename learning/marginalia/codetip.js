// codetip.js — the Marginalia "other code" tooltips. Excel stays in the text; each
// <button class="codetip" data-tip="ID"> opens a popup built from <template id="ID">, with one
// tab per language (MATLAB · Python · R · Julia) and a copy button per snippet.
//
// Behaviour (like a strategy-game tooltip that locks):
//   mouse hover   shows a preview at once; a thin bar fills for 1 s, then the tip LOCKS and you can
//                 move into it, switch tabs, select and copy. Leaving before it locks closes it;
//                 leaving a locked tip closes it after a short grace period.
//   click / tap / Enter / Space   opens it locked straight away (the only way on touch screens).
//   Esc, the × button or a click outside   closes it; focus returns to the chip.
// The chosen language is shared by every tip on every Marginalia page (localStorage
// "margCodeLang", wrapped in try/catch: a blocked store just means MATLAB first each time).
//
// Template markup: <template id="ID"><div data-lang="matlab" data-label="MATLAB"><pre><code>…
// </code></pre><p class="ct-note">optional note</p></div> … one div per language …</template>
(function () {
  "use strict";
  const LOCK_MS = 1000, GRACE_MS = 280, KEY = "margCodeLang";
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");
  let open = null;            // { chip, pop, locked, timers }
  let uid = 0;

  const getLang = () => { try { return localStorage.getItem(KEY); } catch (e) { return null; } };
  const setLang = (v) => { try { localStorage.setItem(KEY, v); } catch (e) { /* blocked: fine */ } };

  function build(chip) {
    const tpl = document.getElementById(chip.dataset.tip);
    if (!tpl) return null;
    const id = "ct-" + (++uid), pop = document.createElement("div");
    pop.className = "ctip"; pop.id = id; pop.setAttribute("role", "dialog");
    pop.setAttribute("aria-label", chip.getAttribute("aria-label") || "Code in other languages");
    const panes = Array.from(tpl.content.querySelectorAll("[data-lang]"));
    const want = getLang(), first = panes.some((p) => p.dataset.lang === want) ? want : panes[0].dataset.lang;
    let html = `<div class="ct-bar" aria-hidden="true"><span></span></div><div class="ct-head"><div class="ct-tabs" role="tablist">`;
    panes.forEach((p) => {
      const on = p.dataset.lang === first;
      html += `<button type="button" role="tab" id="${id}-t-${p.dataset.lang}" aria-controls="${id}-p-${p.dataset.lang}" aria-selected="${on}" tabindex="${on ? 0 : -1}" data-lang="${p.dataset.lang}">${p.dataset.label}</button>`;
    });
    html += `</div><span class="ct-state"></span><button type="button" class="ct-x" aria-label="Close">×</button></div>`;
    pop.innerHTML = html;
    panes.forEach((p) => {
      const pane = document.createElement("div");
      pane.className = "ct-pane"; pane.id = `${id}-p-${p.dataset.lang}`; pane.setAttribute("role", "tabpanel");
      pane.setAttribute("aria-labelledby", `${id}-t-${p.dataset.lang}`); pane.dataset.lang = p.dataset.lang;
      pane.hidden = p.dataset.lang !== first;
      pane.append(...Array.from(p.cloneNode(true).childNodes));
      const copy = document.createElement("button");
      copy.type = "button"; copy.className = "ct-copy"; copy.textContent = "Copy";
      pane.querySelector("pre") && pane.querySelector("pre").after(copy);
      pane.tabIndex = 0;
      pop.appendChild(pane);
    });
    document.body.appendChild(pop);
    wire(pop);
    return pop;
  }

  function select(pop, lang, focus) {
    pop.querySelectorAll('[role="tab"]').forEach((t) => {
      const on = t.dataset.lang === lang; t.setAttribute("aria-selected", on); t.tabIndex = on ? 0 : -1; if (on && focus) t.focus();
    });
    pop.querySelectorAll(".ct-pane").forEach((p) => { p.hidden = p.dataset.lang !== lang; });
    setLang(lang);
    place();
  }

  function wire(pop) {
    pop.addEventListener("click", (e) => {
      const tab = e.target.closest('[role="tab"]');
      if (tab) { lock(); select(pop, tab.dataset.lang, true); return; }
      if (e.target.closest(".ct-x")) { close(true); return; }
      const cp = e.target.closest(".ct-copy");
      if (cp) {
        const text = cp.closest(".ct-pane").querySelector("pre").innerText.replace(/\n$/, "");
        const done = () => { cp.textContent = "Copied"; setTimeout(() => { cp.textContent = "Copy"; }, 1400); };
        if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, () => fallback(cp, done));
        else fallback(cp, done);
      }
    });
    pop.addEventListener("keydown", (e) => {
      const tabs = Array.from(pop.querySelectorAll('[role="tab"]')), i = tabs.indexOf(document.activeElement);
      if (i < 0) return;
      let j = null;
      if (e.key === "ArrowRight") j = (i + 1) % tabs.length; else if (e.key === "ArrowLeft") j = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") j = 0; else if (e.key === "End") j = tabs.length - 1;
      if (j !== null) { e.preventDefault(); select(pop, tabs[j].dataset.lang, true); }
    });
    pop.addEventListener("pointerenter", () => { if (open && open.pop === pop) clearTimeout(open.leave); });
    pop.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse") scheduleClose(); });
  }
  function fallback(cp, done) {
    const r = document.createRange(); r.selectNodeContents(cp.closest(".ct-pane").querySelector("pre code") || cp.closest(".ct-pane").querySelector("pre"));
    const s = getSelection(); s.removeAllRanges(); s.addRange(r); cp.textContent = "Selected: press Ctrl+C"; setTimeout(() => { cp.textContent = "Copy"; }, 2200);
  }

  // Below the chip, flipped above when there is no room; kept 16 px inside the viewport.
  function place() {
    if (!open) return;
    const { chip, pop } = open, r = chip.getBoundingClientRect(), vw = document.documentElement.clientWidth, vh = innerHeight;
    pop.style.maxWidth = Math.min(560, vw - 32) + "px";
    const w = pop.offsetWidth, h = pop.offsetHeight;
    let left = Math.min(Math.max(16, r.left), vw - 16 - w);
    let top = r.bottom + 6;
    if (top + h > vh - 8 && r.top - 6 - h > 8) top = r.top - 6 - h;
    pop.style.left = (left + scrollX) + "px"; pop.style.top = (top + scrollY) + "px";
  }

  function show(chip, locked) {
    if (open && open.chip === chip) { if (locked) lock(); return; }
    close(false);
    const pop = chip._pop || (chip._pop = build(chip));
    if (!pop) return;
    open = { chip, pop, locked: false, lockT: null, leave: null };
    pop.classList.add("is-open"); pop.classList.remove("is-locked", "is-filling");
    chip.setAttribute("aria-expanded", "true"); chip.setAttribute("aria-controls", pop.id);
    place();
    if (locked) lock();
    else {
      void pop.offsetWidth;                       // restart the fill transition
      if (!reduce.matches) pop.classList.add("is-filling");
      open.lockT = setTimeout(lock, LOCK_MS);
    }
  }
  function lock() {
    if (!open || open.locked) return;
    clearTimeout(open.lockT); open.locked = true;
    open.pop.classList.remove("is-filling"); open.pop.classList.add("is-locked");
    open.pop.querySelector(".ct-state").textContent = "locked · Esc to close";
  }
  function scheduleClose() {
    if (!open) return;
    clearTimeout(open.leave);
    if (!open.locked) { close(false); return; }
    open.leave = setTimeout(() => close(false), GRACE_MS);
  }
  function close(refocus) {
    if (!open) return;
    const { chip, pop } = open;
    clearTimeout(open.lockT); clearTimeout(open.leave);
    pop.classList.remove("is-open", "is-locked", "is-filling");
    pop.querySelector(".ct-state").textContent = "";
    chip.setAttribute("aria-expanded", "false");
    const hadFocus = pop.contains(document.activeElement);
    open = null;
    if (refocus || hadFocus) chip.focus();
  }

  document.querySelectorAll("button.codetip").forEach((chip) => {
    chip.setAttribute("aria-expanded", "false");
    chip.setAttribute("aria-haspopup", "dialog");
    chip.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") { if (open && open.chip === chip) clearTimeout(open.leave); else show(chip, false); } });
    chip.addEventListener("pointerleave", (e) => { if (e.pointerType === "mouse" && open && open.chip === chip) scheduleClose(); });
    chip.addEventListener("click", () => {
      if (open && open.chip === chip && open.locked) { close(true); return; }
      show(chip, true);
      const t = open && open.pop.querySelector('[role="tab"][aria-selected="true"]');
      if (t) t.focus();
    });
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && open) close(true); });
  document.addEventListener("pointerdown", (e) => { if (open && !open.pop.contains(e.target) && e.target !== open.chip && !open.chip.contains(e.target)) close(false); });
  addEventListener("resize", place);
  addEventListener("scroll", place, { passive: true });
}());
