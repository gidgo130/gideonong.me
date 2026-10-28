// codetip.js — the Marginalia "other code" tooltips. Excel stays in the text; each
// <button class="codetip" data-tip="ID"> opens a popup built from <template id="ID">, with one
// tab per language (MATLAB · Python · R · Julia) and a copy button per snippet.
//
// Behaviour (like a strategy-game tooltip that locks):
//   mouse hover   shows a preview at once; a thin bar fills for 1 s, then the tip LOCKS: it stays
//                 put when the mouse leaves, so you can switch tabs, select and copy. Moving the
//                 mouse into the preview locks it at once; going anywhere else first closes it.
//   click / tap / Enter / Space   opens it locked straight away (the only way on touch screens).
//                 Clicking a tip's chip again closes it, unless the tip was opened by hovering.
//   Several tips can be open at once; the one opened (or clicked into) last is on top. Only one
//                 unlocked preview exists at a time; locked tips never block another chip.
//   Esc closes the top tip; × closes its own tip; a click / tap outside every tip closes them all.
//                 Focus returns to the chip. Scrolling never closes anything (outside taps count on
//                 "click", which a scroll gesture never fires).
// The chosen language is shared by every tip on every Marginalia page (localStorage
// "margCodeLang", wrapped in try/catch: a blocked store just means MATLAB first each time).
//
// Template markup: <template id="ID"><div data-lang="matlab" data-label="MATLAB"><pre><code>…
// </code></pre><p class="ct-note">optional note</p></div> … one div per language …</template>
(function () {
  "use strict";
  const LOCK_MS = 1000, BRIDGE_MS = 160, KEY = "margCodeLang", Z0 = 30;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)");
  const tips = [];            // open tips, bottom to top: { chip, pop, locked, lockT, leaveT, byClick }
  let uid = 0;
  const top = () => tips[tips.length - 1];
  const of = (el) => tips.find((t) => t.chip === el || t.pop === el);

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
    const t = of(pop); if (t) place(t);
  }

  function wire(pop) {
    pop.addEventListener("click", (e) => {
      const tab = e.target.closest('[role="tab"]');
      const t = of(pop);
      if (tab) { if (t) lock(t); select(pop, tab.dataset.lang, true); return; }
      if (e.target.closest(".ct-x")) { if (t) close(t, true); return; }
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
    pop.addEventListener("pointerenter", (e) => { const t = of(pop); if (e.pointerType === "mouse" && t) { clearTimeout(t.leaveT); lock(t); } });
    pop.addEventListener("pointerdown", () => { const t = of(pop); if (t) raise(t); });
  }
  function fallback(cp, done) {
    const r = document.createRange(); r.selectNodeContents(cp.closest(".ct-pane").querySelector("pre code") || cp.closest(".ct-pane").querySelector("pre"));
    const s = getSelection(); s.removeAllRanges(); s.addRange(r); cp.textContent = "Selected: press Ctrl+C"; setTimeout(() => { cp.textContent = "Copy"; }, 2200);
  }

  // Below the chip, flipped above when there is no room; kept 16 px inside the viewport.
  function place(t) {
    const { chip, pop } = t, r = chip.getBoundingClientRect(), vw = document.documentElement.clientWidth, vh = innerHeight;
    pop.style.maxWidth = Math.min(560, vw - 32) + "px";
    const w = pop.offsetWidth, h = pop.offsetHeight;
    const left = Math.min(Math.max(16, r.left), vw - 16 - w);
    let y = r.bottom + 6;
    if (y + h > vh - 8 && r.top - 6 - h > 8) y = r.top - 6 - h;
    pop.style.left = (left + scrollX) + "px"; pop.style.top = (y + scrollY) + "px";
  }
  const placeAll = () => tips.forEach(place);

  // Newest on top: move the tip to the end of the stack and renumber z-indexes.
  function raise(t) {
    const i = tips.indexOf(t);
    if (i >= 0 && i !== tips.length - 1) { tips.splice(i, 1); tips.push(t); }
    tips.forEach((x, k) => { x.pop.style.zIndex = Z0 + k; });
  }

  function show(chip, locked) {
    let t = of(chip);
    if (t) {
      clearTimeout(t.leaveT); raise(t);
      if (locked && !t.locked) { t.byClick = true; lock(t); }
      return t;
    }
    tips.filter((x) => !x.locked).forEach((x) => close(x, false));   // one preview at a time
    const pop = chip._pop || (chip._pop = build(chip));
    if (!pop) return null;
    t = { chip, pop, locked: false, lockT: null, leaveT: null, byClick: !!locked };
    tips.push(t); raise(t);
    pop.classList.add("is-open"); pop.classList.remove("is-locked", "is-filling");
    chip.setAttribute("aria-expanded", "true"); chip.setAttribute("aria-controls", pop.id);
    place(t);
    if (locked) lock(t);
    else {
      void pop.offsetWidth;                       // restart the fill transition
      if (!reduce.matches) pop.classList.add("is-filling");
      t.lockT = setTimeout(() => lock(t), LOCK_MS);
    }
    return t;
  }
  function lock(t) {
    if (!t || t.locked || tips.indexOf(t) < 0) return;
    clearTimeout(t.lockT); t.locked = true;
    t.pop.classList.remove("is-filling"); t.pop.classList.add("is-locked");
    t.pop.querySelector(".ct-state").textContent = "locked · Esc to close";
  }
  // Mouse left the chip. A locked tip stays; a preview gets a moment for the mouse to cross the
  // 6 px gap into it (which locks it), then closes.
  function chipLeft(t) {
    if (t.locked) return;
    clearTimeout(t.leaveT);
    t.leaveT = setTimeout(() => { if (!t.locked) close(t, false); }, BRIDGE_MS);
  }
  function close(t, refocus) {
    const i = tips.indexOf(t);
    if (i < 0) return;
    tips.splice(i, 1);
    clearTimeout(t.lockT); clearTimeout(t.leaveT);
    t.pop.classList.remove("is-open", "is-locked", "is-filling");
    t.pop.querySelector(".ct-state").textContent = "";
    t.chip.setAttribute("aria-expanded", "false");
    if (refocus || t.pop.contains(document.activeElement)) t.chip.focus();
  }

  document.querySelectorAll("button.codetip").forEach((chip) => {
    chip.setAttribute("aria-expanded", "false");
    chip.setAttribute("aria-haspopup", "dialog");
    chip.addEventListener("pointerenter", (e) => {
      if (e.pointerType !== "mouse") return;
      const t = of(chip);
      if (t) clearTimeout(t.leaveT);              // came straight back, or already open: keep it
      else show(chip, false);
    });
    chip.addEventListener("pointerleave", (e) => { const t = of(chip); if (e.pointerType === "mouse" && t) chipLeft(t); });
    chip.addEventListener("click", () => {
      const t = of(chip);
      if (t && t.locked && t.byClick) { close(t, true); return; }
      const n = show(chip, true);
      const tab = n && n.pop.querySelector('[role="tab"][aria-selected="true"]');
      if (tab) tab.focus();
    });
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && tips.length) close(top(), true); });
  // Outside clicks close every tip. A mouse closes on pointerdown (so a text selection dragged out
  // of a tip doesn't count); touch and pen close on "click", which fires for a tap, never a scroll.
  const outside = (el) => !tips.some((t) => t.pop.contains(el)) && !(el.closest && el.closest("button.codetip"));
  const closeAll = () => tips.slice().forEach((t) => close(t, false));
  let lastPointer = "mouse";
  document.addEventListener("pointerdown", (e) => { lastPointer = e.pointerType; if (e.pointerType === "mouse" && tips.length && outside(e.target)) closeAll(); });
  document.addEventListener("click", (e) => { if (lastPointer !== "mouse" && tips.length && outside(e.target)) closeAll(); });
  addEventListener("resize", placeAll);
  addEventListener("scroll", placeAll, { passive: true });
}());
