/* Shared by every editor page: the per-launch token, the api() wrapper, tiny
   DOM helpers, toasts, banners and the diff renderer. Loaded before app.js /
   cv.js; exposes window.Editor. */
(function () {
  "use strict";

  // ---------------------------------------------------------------- token
  const params = new URLSearchParams(location.search);
  let token = params.get("token");
  if (token) {
    try { sessionStorage.setItem("editorToken", token); } catch (e) { /* ignore */ }
    history.replaceState(null, "", location.pathname + location.hash);
  } else {
    try { token = sessionStorage.getItem("editorToken"); } catch (e) { token = null; }
  }

  const $ = (sel, root) => (root || document).querySelector(sel);
  const el = (tag, attrs, ...children) => {
    const n = document.createElement(tag);
    if (attrs) for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") n.className = v;
      else if (k === "html") n.innerHTML = v;
      else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
      else if (v !== null && v !== undefined) n.setAttribute(k, v);
    }
    for (const c of children) if (c !== null && c !== undefined) n.append(c);
    return n;
  };

  // ---------------------------------------------------------------- api
  async function api(path, opts) {
    const o = Object.assign({ headers: {} }, opts || {});
    o.headers["X-Editor-Token"] = token || "";
    if (o.body && typeof o.body !== "string" && !(o.body instanceof FormData)) {
      o.body = JSON.stringify(o.body);
      o.headers["Content-Type"] = "application/json";
    }
    const r = await fetch(path, o);
    let j = null;
    try { j = await r.json(); } catch (e) { /* not json */ }
    if (!r.ok && !(j && (j.error || j.gate || j.plan))) throw new Error((j && j.error) || (r.status + " " + r.statusText));
    return j;
  }

  // ---------------------------------------------------------------- toast
  let toastTimer = null;
  function toast(msg, ms) {
    const t = $("#toast");
    if (!t) return;
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.hidden = true; }, ms || 3500);
  }

  // ---------------------------------------------------------------- banners
  const banners = {};
  function setBanner(id, kind, content, actions) {
    clearBanner(id);
    if (!content) return;
    const b = el("div", { class: "banner " + (kind || ""), "data-id": id });
    const text = el("div", { class: "text" });
    if (typeof content === "string") text.textContent = content; else text.append(content);
    b.append(text);
    for (const a of actions || []) b.append(el("button", { type: "button", class: a.primary ? "primary" : "ghost", onclick: a.onclick }, a.label));
    $("#banners").append(b);
    banners[id] = b;
  }
  function clearBanner(id) { if (banners[id]) { banners[id].remove(); delete banners[id]; } }

  // ---------------------------------------------------------------- helpers
  const fold = (s) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

  function renderDiff(text) {
    const pre = el("pre", { class: "diff" });
    for (const line of text.split("\n")) {
      let cls = "";
      if (line.startsWith("+++") || line.startsWith("---")) cls = "meta";
      else if (line.startsWith("@@")) cls = "hunk";
      else if (line.startsWith("+")) cls = "add";
      else if (line.startsWith("-")) cls = "del";
      pre.append(el("span", { class: cls }, line + "\n"));
    }
    return pre;
  }

  function fmtTime(unixSeconds) {
    if (!unixSeconds) return "—";
    const d = new Date(unixSeconds * 1000);
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
  }

  // Tab strip: mark the current page. Tab clicks are in-app navigation, so the
  // "unsaved drafts" prompt (drafts live on the server anyway) is skipped.
  function initTabs() {
    for (const a of document.querySelectorAll(".tabs a")) {
      a.classList.toggle("active", a.getAttribute("href") === location.pathname);
      a.addEventListener("click", () => { window.__navigating = true; });
    }
  }

  function noToken() {
    setBanner("token", "err", "No access token. Open the editor from its desktop shortcut (or the URL the launcher printed) — a bare URL is refused on purpose.");
  }

  window.Editor = { token, $, el, api, toast, setBanner, clearBanner, banners, fold, renderDiff, fmtTime, initTabs, noToken };
})();
