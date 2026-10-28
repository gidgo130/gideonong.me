// plot.js — the Marginalia series' small SVG plotter, shared by every entry's main.js.
// Started from the Reflections plotter (learning/reflections/the-goal/balanced-plant/main.js) and
// kept to the same hub-wide rules (learning/README.md → Hub-wide rules): one user unit = one CSS
// pixel at every width, so chart text is 13 px (12 px when a title has to fit) on a phone and on a
// desktop; strokes, dashes and markers keep their on-screen size; at most three line forms per
// chart (solid, "dashed" 10/6 px, "dotted" 3.25 px dots every 6 px), told apart by shape.
// Additions over the Reflections version: log axes (xlog / ylog), horizontal reference lines
// (hlines) and a debounced resize handler that redraws every chart from its stored options.
(function () {
  "use strict";
  function nice(lo, hi, n) {
    const span = hi - lo || 1, raw = span / n, p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p;
    const st = (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p, out = [];
    for (let v = Math.ceil(lo / st - 1e-9) * st; v <= hi + 1e-9; v += st) out.push(+v.toFixed(10));
    return out;
  }
  function fmt(v) {
    const a = Math.abs(v);
    if (a >= 1000) return Math.round(v).toLocaleString("en-US");
    if (a >= 10 || v === 0) return String(Math.round(v * 10) / 10);
    return String(+v.toFixed(3)).replace("-", "−");
  }
  function chartSize(svg) {
    if (!svg.dataset.vb) svg.dataset.vb = svg.getAttribute("viewBox");
    const [, , w0, h0] = svg.dataset.vb.split(/\s+/).map(Number);
    const cw = svg.getBoundingClientRect().width || svg.parentNode.clientWidth;
    if (!cw) return { w: w0, h: h0 };
    const w = Math.max(Math.round(cw), 300);
    return { w, h: Math.min(Math.max(Math.round(h0 * w / w0), 220), Math.round(h0 * 1.25)) };
  }
  const L10 = (v) => Math.log10(v);
  // o: { x:[lo,hi], y:[lo,hi], xl, yl, xticks, yticks, xf, yf, xlog, ylog, series:[...], areas,
  //      vlines:[{x,c,label}], hlines:[{y,c,dash}] }
  // A series: { pts:[[x,y]...], c, dash: "dashed"|"dotted"|undefined, w, dots, r, ring, label }
  function plot(svg, o) {
    svg._plot = o;
    const VB = chartSize(svg), W = VB.w, H = VB.h, m = { l: 62, r: 18, t: 14, b: 46 };
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const k = W / (svg.getBoundingClientRect().width || W), px = (v) => +(v * k).toFixed(2);
    const title = (txt, room) => {
      txt = txt || ""; const u = Math.max(1, k), est = (f) => 0.62 * f * u * txt.length;
      if (est(13) <= room) return { fs: 13 * u, lines: [txt] };
      if (est(12) <= room) return { fs: 12 * u, lines: [txt] };
      const w = txt.split(" "), mid = Math.ceil(w.length / 2);
      return { fs: 12 * u, lines: [w.slice(0, mid).join(" "), w.slice(mid).join(" ")] };
    };
    const lineH = (f) => Math.round(f * 1.15);
    const xT = title(o.xl, W - m.l - m.r), yT = title(o.yl, H - m.t - m.b);
    if (xT.lines.length > 1) m.b += lineH(xT.fs);
    if (yT.lines.length > 1) m.l += lineH(yT.fs);
    const fsL = 13 * Math.max(1, k), labeled = (o.series || []).filter((se) => se.label && !se.dots);
    let useLabels = labeled.length > 0;
    if (useLabels) { const mr = 18 + Math.ceil(Math.max(...labeled.map((se) => 0.62 * fsL * se.label.length))) + 8; if (W - m.l - mr < 200) useLabels = false; else m.r = mr; }
    const tx = o.xlog ? L10 : (v) => v, ty = o.ylog ? L10 : (v) => v;
    const X0 = tx(o.x[0]), X1 = tx(o.x[1]), Y0 = ty(o.y[0]), Y1 = ty(o.y[1]);
    const sx = (x) => m.l + (tx(x) - X0) / (X1 - X0) * (W - m.l - m.r);
    const sy = (y) => H - m.b - (ty(y) - Y0) / (Y1 - Y0) * (H - m.t - m.b);
    let s = `<rect class="plot-bg" x="${m.l}" y="${m.t}" width="${W - m.l - m.r}" height="${H - m.t - m.b}"/>`;
    const xt = o.xticks || nice(o.x[0], o.x[1], 6), yt = o.yticks || nice(o.y[0], o.y[1], 5);
    yt.forEach((v) => { const y = sy(v); s += `<line class="gridl" x1="${m.l}" x2="${W - m.r}" y1="${y}" y2="${y}"/><text x="${m.l - 8}" y="${y + 4}" text-anchor="end">${(o.yf || fmt)(v)}</text>`; });
    // x tick labels: drop the ones that would touch their left neighbour (narrow charts, log axes).
    let lastRight = -Infinity;
    xt.forEach((v) => {
      const x = sx(v), lab = (o.xf || fmt)(v), half = 0.62 * 13 * Math.max(1, k) * String(lab).length / 2;
      if (x - half < lastRight + 6 * k) return;
      lastRight = x + half;
      s += `<text x="${x}" y="${H - m.b + 18}" text-anchor="middle">${lab}</text>`;
    });
    s += `<line class="axis" x1="${m.l}" x2="${W - m.r}" y1="${H - m.b}" y2="${H - m.b}"/><line class="axis" x1="${m.l}" x2="${m.l}" y1="${m.t}" y2="${H - m.b}"/>`;
    s += `<text x="${(m.l + W - m.r) / 2}" y="${H - 8 - (xT.lines.length - 1) * lineH(xT.fs)}" text-anchor="middle" style="font-size:${xT.fs.toFixed(1)}px">` + xT.lines.map((l, i) => `<tspan x="${(m.l + W - m.r) / 2}" dy="${i ? lineH(xT.fs) : 0}">${l}</tspan>`).join("") + `</text>`;
    s += `<text transform="translate(14 ${(m.t + H - m.b) / 2}) rotate(-90)" text-anchor="middle" style="font-size:${yT.fs.toFixed(1)}px">` + yT.lines.map((l, i) => `<tspan x="0" dy="${i ? lineH(yT.fs) : 0}">${l}</tspan>`).join("") + `</text>`;
    s += `<clipPath id="${svg.id}cp"><rect x="${m.l}" y="${m.t - 2}" width="${W - m.l - m.r}" height="${H - m.t - m.b + 4}"/></clipPath><g clip-path="url(#${svg.id}cp)">`;
    (o.areas || []).forEach((a) => { s += `<path d="M${a.pts.map((p) => sx(p[0]) + "," + sy(p[1])).join(" L")} Z" style="fill:${a.c};opacity:${a.op || .2}"/>`; });
    const dashOf = (d) => d === "dotted" ? `stroke-dasharray:0 ${px(6)};` : d ? `stroke-dasharray:${px(10)} ${px(6)};` : "";
    (o.hlines || []).forEach((h) => { const y = sy(h.y), dot = h.dash === "dotted"; s += `<line x1="${m.l}" x2="${W - m.r}" y1="${y}" y2="${y}" style="stroke:${h.c};stroke-width:${px(dot ? 3.25 : (h.w || 1.5))};${dashOf(h.dash)}stroke-linecap:round"/>`; });
    (o.vlines || []).forEach((v) => { const x = sx(v.x); s += `<line x1="${x}" x2="${x}" y1="${m.t}" y2="${H - m.b}" style="stroke:${v.c};stroke-width:${px(1.5)};${v.solid ? "" : `stroke-dasharray:${px(10)} ${px(6)}`}"/>`; });
    const labels = [];
    (o.series || []).forEach((se) => {
      if (se.dots) {
        const r = px(se.r || 4);
        se.pts.forEach((p) => {
          if (!isFinite(p[1]) || (o.ylog && p[1] <= 0)) return; const cx = sx(p[0]), cy = sy(p[1]);
          s += `<circle cx="${cx}" cy="${cy}" r="${r}" style="${se.ring ? `fill:var(--paper);stroke:${se.c};stroke-width:${px(2.5)}` : `fill:${se.c};stroke:var(--paper);stroke-width:${px(1.5)}`}"/>`;
        });
        return;
      }
      let d = "", pen = false, last = null;
      se.pts.forEach((p) => { if (!isFinite(p[1]) || (o.ylog && p[1] <= 0)) { pen = false; return; } d += (pen ? " L" : " M") + sx(p[0]).toFixed(1) + "," + sy(p[1]).toFixed(1); pen = true; last = p; });
      const dotted = se.dash === "dotted", w = px(dotted ? 3.25 : (se.w || 2.2));
      s += `<path d="${d}" style="fill:none;stroke:${se.c};stroke-width:${w};${dashOf(se.dash)}stroke-linejoin:round;stroke-linecap:round"/>`;
      if (useLabels && se.label && last) labels.push({ y: sy(last[1]), c: se.c, text: se.label });
    });
    s += "</g>";
    (o.vlines || []).forEach((v) => { if (v.label) { const x = sx(v.x), right = x + 8 + 0.62 * 13 * k * v.label.length < W - m.r; s += `<text x="${right ? x + 5 : x - 5}" y="${m.t + 13}" text-anchor="${right ? "start" : "end"}">${v.label}</text>`; } });
    if (labels.length) {
      const gap = fsL * 1.6, top = m.t + fsL * 0.7, bot = H - m.b - fsL * 0.7; labels.sort((p, q) => p.y - q.y);
      for (let i = 0; i < labels.length; i++) labels[i].y = Math.max(labels[i].y, i ? labels[i - 1].y + gap : top);
      for (let i = labels.length - 1; i >= 0; i--) labels[i].y = Math.min(labels[i].y, i < labels.length - 1 ? labels[i + 1].y - gap : bot);
      labels.forEach((l) => { s += `<text x="${(W - m.r + 8).toFixed(1)}" y="${(l.y + fsL * 0.35).toFixed(1)}" style="fill:${l.c};font-size:${fsL}px;font-weight:500">${l.text}</text>`; });
    }
    svg.innerHTML = s;
  }
  let rsz;
  window.addEventListener("resize", () => {
    clearTimeout(rsz);
    rsz = setTimeout(() => { document.querySelectorAll("svg[id]").forEach((s) => { if (s._plot) plot(s, s._plot); }); }, 150);
  });
  window.MP = { plot, nice, fmt };
}());
