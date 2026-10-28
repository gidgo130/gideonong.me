// main.js — "Does a Markov chain forget where it started?" (Marginalia 01). Everything is exact:
// p_n = P(up at step n) from the recursion p_{n+1} = λ p_n + b, which is P^n row by row. Charts use
// the series tokens --s1..--s3 (marginalia.css), never --fit / --fix, and each line in a shared
// chart has its own form (solid / dashed / dotted). The plotter is ../plot.js (window.MP).
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const N = 30;                                   // steps shown
  const state = { a: 0.05, b: 0.30 };

  // p_n for n = 0..N from a start (1 = up, 0 = down), by the exact recursion.
  function path(p0, a, b) { const lam = 1 - a - b, out = [p0]; for (let n = 1; n <= N; n++) out.push(lam * out[n - 1] + b); return out; }
  const f2 = (v) => v.toFixed(2), f3 = (v) => v.toFixed(3);

  /* ---------- the diagram ---------- */
  // Hand-drawn SVG (not the plotter): two states, the two crossing arrows with a and b, and the two
  // self-loops with 1 − a and 1 − b. An arrow with probability 0 is drawn faint and dashed.
  function diagram(a, b) {
    const svg = $("mg"), W = 420, H = 220, cx1 = 120, cx2 = 300, cy = 120, r = 38;
    // Text stays 13 px on screen (15 px for the state names) whatever width the diagram renders at.
    const k = Math.max(1, W / (svg.getBoundingClientRect().width || W)), fs = (v) => `font-size:${(v * k).toFixed(1)}px`;
    const arrow = (p) => p > 0 ? "var(--ink)" : "var(--rule)";
    const dash = (p) => p > 0 ? "" : "stroke-dasharray:6 5;";
    let s = `<defs><marker id="mgar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" style="fill:var(--ink)"/></marker></defs>`;
    // a: up → down (upper arc), b: down → up (lower arc)
    s += `<path d="M${cx1 + 30},${cy - 24} Q210,${cy - 80} ${cx2 - 30},${cy - 24}" style="fill:none;stroke:${arrow(a)};stroke-width:1.6;${dash(a)}" marker-end="url(#mgar)"/>`;
    s += `<path d="M${cx2 - 30},${cy + 24} Q210,${cy + 80} ${cx1 + 30},${cy + 24}" style="fill:none;stroke:${arrow(b)};stroke-width:1.6;${dash(b)}" marker-end="url(#mgar)"/>`;
    // self-loops
    s += `<path d="M${cx1 - 22},${cy - 30} C${cx1 - 80},${cy - 100} ${cx1 + 10},${cy - 110} ${cx1 + 4},${cy - r - 2}" style="fill:none;stroke:${arrow(1 - a)};stroke-width:1.6;${dash(1 - a)}" marker-end="url(#mgar)"/>`;
    s += `<path d="M${cx2 + 22},${cy - 30} C${cx2 + 80},${cy - 100} ${cx2 - 10},${cy - 110} ${cx2 - 4},${cy - r - 2}" style="fill:none;stroke:${arrow(1 - b)};stroke-width:1.6;${dash(1 - b)}" marker-end="url(#mgar)"/>`;
    s += `<circle cx="${cx1}" cy="${cy}" r="${r}" style="fill:var(--paper);stroke:var(--s1);stroke-width:2"/><circle cx="${cx2}" cy="${cy}" r="${r}" style="fill:var(--paper);stroke:var(--s2);stroke-width:2"/>`;
    s += `<text x="${cx1}" y="${cy + 5}" text-anchor="middle" style="fill:var(--ink);${fs(15)}">up</text><text x="${cx2}" y="${cy + 5}" text-anchor="middle" style="fill:var(--ink);${fs(15)}">down</text>`;
    s += `<text x="210" y="${cy - 62}" text-anchor="middle" style="fill:var(--ink);${fs(13)}">a = ${f2(a)}</text>`;
    s += `<text x="210" y="${cy + 80}" text-anchor="middle" style="fill:var(--ink);${fs(13)}">b = ${f2(b)}</text>`;
    s += `<text x="${cx1 - 30}" y="20" text-anchor="middle" style="${fs(13)}">1 − a = ${f2(1 - a)}</text><text x="${cx2 + 30}" y="20" text-anchor="middle" style="${fs(13)}">1 − b = ${f2(1 - b)}</text>`;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.innerHTML = s;
  }

  /* ---------- λ on [−1, 1] ---------- */
  function lambdaLine(lam) {
    const svg = $("ml"), W = 420, x0 = 30, x1 = 390, y = 34, sx = (v) => x0 + (v + 1) / 2 * (x1 - x0);
    const k = Math.max(1, W / (svg.getBoundingClientRect().width || W)), fs = `font-size:${(13 * k).toFixed(1)}px`;
    let s = `<line x1="${x0}" x2="${x1}" y1="${y}" y2="${y}" style="stroke:var(--rule);stroke-width:2"/>`;
    [-1, 0, 1].forEach((v) => { s += `<line x1="${sx(v)}" x2="${sx(v)}" y1="${y - 6}" y2="${y + 6}" style="stroke:var(--muted);stroke-width:1.5"/><text x="${sx(v)}" y="${y + 22}" text-anchor="middle" style="${fs}">${v === -1 ? "−1" : v}</text>`; });
    s += `<text x="${sx(-1) - 10}" y="${y + 42}" text-anchor="start" style="${fs}">flips</text><text x="${sx(0)}" y="${y + 42}" text-anchor="middle" style="${fs}">forgets</text><text x="${sx(1) + 10}" y="${y + 42}" text-anchor="end" style="${fs}">stuck</text>`;
    s += `<circle cx="${sx(lam)}" cy="${y}" r="7" style="fill:var(--accent);stroke:var(--paper);stroke-width:2"/><text x="${Math.min(Math.max(sx(lam), 70), 350)}" y="${y - 13}" text-anchor="middle" style="fill:var(--ink);${fs}">λ = ${f2(lam)}</text>`;
    svg.setAttribute("viewBox", `0 0 ${W} 80`);
    svg.innerHTML = s;
  }

  /* ---------- the charts ---------- */
  function draw() {
    const { a, b } = state, lam = 1 - a - b, still = a + b === 0, pi = still ? NaN : b / (a + b);
    $("mAo").textContent = f2(a); $("mBo").textContent = f2(b);
    diagram(a, b); lambdaLine(lam);
    const ns = Array.from({ length: N + 1 }, (_, i) => i);
    const up = path(1, a, b), dn = path(0, a, b);

    const ser1 = [{ pts: ns.map((n) => [n, up[n]]), c: "var(--s1)" }, { pts: ns.map((n) => [n, dn[n]]), c: "var(--s2)", dash: "dashed" }];
    MP.plot($("mc1"), { x: [0, N], y: [0, 1], xl: "step n (shifts)", yl: "P(up at step n)", yticks: [0, .25, .5, .75, 1], series: ser1,
      hlines: still ? [] : [{ y: pi, c: "var(--muted)", dash: "dotted" }] });

    // log chart: exact gap from the "down" start (gap₀ = π) against |λ|ⁿ · gap₀
    const g0 = still ? 0 : pi, gap = dn.map((p) => Math.abs(p - pi));
    const pts = ns.map((n) => [n, gap[n]]).filter((p) => p[1] > 1e-7);
    const ser2 = [];
    if (!still && Math.abs(lam) > 1e-9) ser2.push({ pts: ns.map((n) => [n, g0 * Math.pow(Math.abs(lam), n)]), c: "var(--s1)", dash: "dashed" });
    ser2.push({ pts, c: "var(--s2)", dots: true, r: 3.5 });
    MP.plot($("mc2"), { x: [0, N], y: [1e-6, 1], ylog: true, xl: "step n (shifts)", yl: "|P(up) − π(up)|, start down", yticks: [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 0.1, 1],
      yf: (v) => v >= 0.01 ? String(v) : "1e" + Math.round(Math.log10(v)), series: ser2, hlines: [{ y: 0.01, c: "var(--rule)", w: 1 }] });

    // readouts
    let out;
    if (still) out = `<span>λ = <b>1</b>: the chain never moves</span><span>Every distribution is stationary; it stays where it started</span>`;
    else {
      const gw = Math.max(pi, 1 - pi), al = Math.abs(lam);
      const steps = al < 1e-12 ? 1 : al >= 1 - 1e-12 ? Infinity : Math.max(0, Math.ceil(Math.log(0.01 / gw) / Math.log(al)));
      const tau = al < 1e-12 ? 0 : al >= 1 - 1e-12 ? Infinity : -1 / Math.log(al);
      out = `<span>Availability π<sub>up</sub> = b/(a+b) = <b>${f3(pi)}</b></span><span>λ = 1 − a − b = <b>${f2(lam)}</b></span>` +
        `<span>MTBF = 1/a = <b>${a > 0 ? (1 / a).toFixed(1) : "∞"}</b> shifts, MTTR = 1/b = <b>${b > 0 ? (1 / b).toFixed(1) : "∞"}</b> shifts</span>` +
        (isFinite(steps) ? `<span>Within 0.01 of π<sub>up</sub> from either start after <b>${steps}</b> step${steps === 1 ? "" : "s"}</span>` : `<span class="flag">Never settles: |λ| = 1</span>`) +
        (isFinite(tau) && tau > 0 ? `<span>Time constant τ = <b>${tau.toFixed(2)}</b> steps</span>` : "") +
        (lam < 0 && al < 1 ? `<span>λ &lt; 0: overshoots and alternates as it settles</span>` : "");
    }
    $("mRead").innerHTML = out;
    drawFraction();
  }

  // §4: P(up at n) from "up" against its running average over steps 0..n (the expected fraction of
  // time up so far), for the same chain.
  function drawFraction() {
    const { a, b } = state, still = a + b === 0, pi = still ? NaN : b / (a + b);
    const M = 40, up = [1]; for (let n = 1; n <= M; n++) up.push((1 - a - b) * up[n - 1] + b);
    let acc = 0; const avg = up.map((p, n) => (acc += p) / (n + 1));
    const ns = Array.from({ length: M + 1 }, (_, i) => i);
    MP.plot($("mc3"), { x: [0, M], y: [0, 1], xl: "step n", yl: "probability / fraction", yticks: [0, .25, .5, .75, 1],
      series: [{ pts: ns.map((n) => [n, up[n]]), c: "var(--s1)" }, { pts: ns.map((n) => [n, avg[n]]), c: "var(--s2)", dash: "dashed" }],
      hlines: still ? [] : [{ y: pi, c: "var(--muted)", dash: "dotted" }] });
    $("m4now").textContent = `now: a = ${f2(a)}, b = ${f2(b)}`;
  }

  function set(a, b) { state.a = a; state.b = b; $("mA").value = a; $("mB").value = b; draw(); }
  $("mA").addEventListener("input", () => set(+$("mA").value, state.b));
  $("mB").addEventListener("input", () => set(state.a, +$("mB").value));
  document.querySelectorAll("button[data-a]").forEach((btn) => btn.addEventListener("click", () => set(+btn.dataset.a, +btn.dataset.b)));
  draw();
  // The two hand-drawn SVGs size their text from their rendered width, so redraw them on resize
  // (the plotter redraws its own charts).
  let rsz; window.addEventListener("resize", () => { clearTimeout(rsz); rsz = setTimeout(() => { diagram(state.a, state.b); lambdaLine(1 - state.a - state.b); }, 160); });
}());
