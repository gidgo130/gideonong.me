// main.js — "How big does n have to be?" (Marginalia 02). Two figures:
//   §2 coverage checker: seeded simulation of the 95% interval's misses on each side, against n,
//      with an optional bootstrap-t run at one n.
//   §3 fingerprint: the exact error F_n − Φ for three parents against the Edgeworth predictions,
//      and the largest error against n on log–log axes.
// The numerics live in clt-math.js (window.CLTM); the plotter is ../plot.js (window.MP). Charts
// use --s1..--s3 (marginalia.css), never --fit / --fix, one line form per series.
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id), M = window.CLTM;
  const pct = (v) => (100 * v).toFixed(1) + "%";

  /* ================================================================ §2 coverage checker */
  const DATA = {
    uni:  { g1: 0,      mu: 0.5,                              draw: (r) => r() },
    wb:   { g1: 1.0720, mu: Math.exp(M.lgamma(1 + 1 / 1.5)),  draw: (r) => Math.pow(-Math.log(r()), 1 / 1.5) },
    ln05: { g1: 1.7502, mu: Math.exp(0.125),                  draw: (r) => Math.exp(0.5 * r.normal()) },
    exp:  { g1: 2,      mu: 1,                                draw: (r) => -Math.log(r()) },
    ln1:  { g1: 6.1849, mu: Math.exp(0.5),                    draw: (r) => Math.exp(r.normal()) }
  };
  const GRID = [5, 8, 12, 20, 30, 50, 80, 128, 200, 300, 500, 1000];
  const CN = [5, 8, 10, 12, 15, 20, 30, 40, 50, 60, 80, 100, 128, 150, 200, 300, 500, 1000];
  const REPS = 4000, BOOT_REPS = 2000, BOOT_B = 399, BOOT_MAX_N = 300;
  const cache = {}, bootCache = {};
  const tcrit = {};
  const crit = (kind, n) => kind === "z" ? 1.96 : (tcrit[n] || (tcrit[n] = M.tQuantile(0.975, n - 1)));
  const seedOf = (s) => { let h = 2166136261; for (const ch of s) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); } return h >>> 0; };

  // One coverage estimate: REPS samples of size n; count true mean above / below the interval.
  function cover(key, kind, n) {
    const id = key + "|" + kind + "|" + n;
    if (cache[id]) return cache[id];
    const d = DATA[key], r = M.rng(seedOf(id)), c = crit(kind, n), x = new Float64Array(n);
    let lo = 0, hi = 0;
    for (let i = 0; i < REPS; i++) {
      let m = 0; for (let j = 0; j < n; j++) { x[j] = d.draw(r); m += x[j]; } m /= n;
      let q = 0; for (let j = 0; j < n; j++) q += (x[j] - m) * (x[j] - m);
      const h = c * Math.sqrt(q / (n - 1) / n);
      if (d.mu > m + h) lo++; else if (d.mu < m - h) hi++;
    }
    return (cache[id] = { lo: lo / REPS, hi: hi / REPS });
  }

  // Bootstrap-t (Hall 1992, Ch. 3): resample, studentize each resample, read the 2.5% and 97.5%
  // points of t* and turn them into the interval [m − t*₉₇.₅ s/√n, m − t*₂.₅ s/√n].
  function bootChunk(job, count) {
    const { d, r, n, x, ts, xb } = job, k1 = Math.round(0.025 * (BOOT_B + 1)) - 1, k2 = Math.round(0.975 * (BOOT_B + 1)) - 1, rn = Math.sqrt(n);
    for (let i = 0; i < count && job.done < BOOT_REPS; i++, job.done++) {
      let m = 0; for (let j = 0; j < n; j++) { x[j] = d.draw(r); m += x[j]; } m /= n;
      let q = 0; for (let j = 0; j < n; j++) q += (x[j] - m) * (x[j] - m);
      const s = Math.sqrt(q / (n - 1));
      for (let b = 0; b < BOOT_B; b++) {
        let mb = 0; for (let j = 0; j < n; j++) { const v = x[(r() * n) | 0]; xb[j] = v; mb += v; } mb /= n;
        let qb = 0; for (let j = 0; j < n; j++) qb += (xb[j] - mb) * (xb[j] - mb);
        ts[b] = (mb - m) / (Math.sqrt(qb / (n - 1)) / rn || 1e-300);
      }
      ts.sort();
      const U = m - ts[k1] * s / rn, L = m - ts[k2] * s / rn;
      if (d.mu > U) job.lo++; else if (d.mu < L) job.hi++;
    }
  }

  let runToken = 0, bootToken = 0;
  const cState = () => ({ key: $("cP").value, kind: document.querySelector('input[name="cC"]:checked').value, n: CN[+$("cN").value] });

  function drawCover() {
    const { key, kind, n } = cState(), d = DATA[key], rule = M.sugdenN(d.g1);
    $("cNo").textContent = n;
    const pts = GRID.filter((g) => cache[key + "|" + kind + "|" + g]).map((g) => [g, cache[key + "|" + kind + "|" + g]]);
    const ymax = Math.max(8, ...pts.map((p) => 100 * Math.max(p[1].lo, p[1].hi))) * 1.08;
    const lo = pts.map((p) => [p[0], 100 * p[1].lo]), hi = pts.map((p) => [p[0], 100 * p[1].hi]);
    const series = [{ pts: lo, c: "var(--s1)" }, { pts: lo, c: "var(--s1)", dots: true, r: 3 },
      { pts: hi, c: "var(--s2)", dash: "dashed" }, { pts: hi, c: "var(--s2)", dots: true, r: 3 }];
    const bk = bootCache[key + "|" + n];
    if (bk && bk.done >= BOOT_REPS) series.push({ pts: [[n, 100 * bk.lo / BOOT_REPS]], c: "var(--s1)", dots: true, ring: true, r: 6 }, { pts: [[n, 100 * bk.hi / BOOT_REPS]], c: "var(--s2)", dots: true, ring: true, r: 6 });
    const vl = [{ x: n, c: "var(--ink)", solid: true }];
    if (rule <= 1000) vl.push({ x: rule, c: "var(--muted)", label: "rule: n > " + Math.round(rule) });
    MP.plot($("cc"), { x: [4, 1200], xlog: true, xticks: [5, 10, 20, 50, 100, 200, 500, 1000], y: [0, ymax],
      xl: "sample size n (log scale)", yl: "% of intervals missing, each side", yf: (v) => String(v), series, vlines: vl,
      hlines: [{ y: 2.5, c: "var(--muted)", dash: "dotted" }] });

    const at = cache[key + "|" + kind + "|" + n];
    let txt = `<span>Rule for this data: n &gt; <b>${Math.round(rule)}</b> (γ₁ = ${d.g1.toFixed(2)})</span>`;
    if (at) {
      txt += `<span>At n = ${n}: too low <b class="${at.lo > 0.035 ? "flag" : ""}">${pct(at.lo)}</b>, too high <b class="${at.hi > 0.035 ? "flag" : ""}">${pct(at.hi)}</b> (target 2.5% each)</span>` +
        `<span>Total coverage <b>${pct(1 - at.lo - at.hi)}</b>${1 - at.lo - at.hi < 0.94 ? ' <span class="flag">below 94%</span>' : ""}</span>` +
        `<span>${n >= Math.floor(rule + 1e-9) + 1 ? "Meets the rule" : `Short of the rule by <b>${Math.floor(rule + 1e-9) + 1 - n}</b>`}</span>`;
    } else txt += `<span>Simulating…</span>`;
    if (bk && bk.done >= BOOT_REPS) txt += `<span>Bootstrap-t at n = ${n}: too low <b>${pct(bk.lo / BOOT_REPS)}</b>, too high <b>${pct(bk.hi / BOOT_REPS)}</b></span>`;
    else if (bk) txt += `<span>Bootstrap-t: ${Math.round(100 * bk.done / BOOT_REPS)}%…</span>`;
    $("cRead").innerHTML = txt;
    const btn = $("cBoot");
    btn.disabled = n > BOOT_MAX_N || !!(bk && bk.done < BOOT_REPS);
    btn.title = n > BOOT_MAX_N ? `Bootstrap-t runs for n up to ${BOOT_MAX_N} here (it is slow in a browser)` : "";
  }

  // Simulate the grid (and the chosen n) one size at a time, redrawing as each lands, so the page
  // stays responsive. A newer request cancels an older one.
  function runCover() {
    const tok = ++runToken, { key, kind, n } = cState();
    const todo = GRID.concat(GRID.includes(n) ? [] : [n]).filter((g) => !cache[key + "|" + kind + "|" + g]);
    drawCover();
    (function step() {
      if (tok !== runToken || !todo.length) return;
      cover(key, kind, todo.shift()); drawCover();
      setTimeout(step, 0);
    })();
  }
  function runBoot() {
    const { key, n } = cState(), id = key + "|" + n;
    if (n > BOOT_MAX_N || bootCache[id]) { drawCover(); return; }
    const job = bootCache[id] = { d: DATA[key], r: M.rng(seedOf("boot|" + id)), n, x: new Float64Array(n), xb: new Float64Array(n), ts: new Float64Array(BOOT_B), lo: 0, hi: 0, done: 0 };
    const tok = ++bootToken;
    (function step() {
      if (tok !== bootToken) { delete bootCache[id]; drawCover(); return; }
      bootChunk(job, Math.max(5, Math.round(20000 / n)));
      drawCover();
      if (job.done < BOOT_REPS) setTimeout(step, 0);
    })();
  }
  $("cP").addEventListener("change", () => { bootToken++; runCover(); });
  document.querySelectorAll('input[name="cC"]').forEach((el) => el.addEventListener("change", runCover));
  $("cN").addEventListener("input", () => { bootToken++; runCover(); });
  $("cBoot").addEventListener("click", runBoot);

  /* ================================================================ §3 fingerprint */
  const EN = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100, 128, 160, 200, 250, 300, 400];
  const supCache = { exp: {}, uni: {}, coin: {} };
  const sup = (key, n) => supCache[key][n] || (supCache[key][n] = M.supErr(key, n));
  const eState = () => ({ key: document.querySelector('input[name="eP"]:checked').value, n: EN[+$("eN").value] });

  function errorCurves(key, n) {
    const p = M.PARENTS[key], exact = [], one = [], two = [];
    if (key === "coin") {
      // the staircase: each step from one lattice point to the next, Φ curving underneath
      const sq = Math.sqrt(n), t = M.binCdfTable(n);
      const kmin = Math.max(0, Math.floor((-4.4 * sq + n) / 2)), kmax = Math.min(n, Math.ceil((4.4 * sq + n) / 2));
      if (kmin > 0) for (let i = 0; i <= 10; i++) { const x = -4.4 + i * (M.coinPoint(n, kmin) + 4.4) / 10; exact.push([x, 1000 * (t.cdf[kmin - 1] - M.Phi(x))]); }
      for (let k = kmin; k <= kmax; k++) {
        const x0 = M.coinPoint(n, k), x1 = Math.min(k < n ? M.coinPoint(n, k + 1) : 4.4, 4.4);
        for (let i = 0; i <= 10; i++) { const x = x0 + i * (x1 - x0) / 10 - (i === 10 ? 1e-9 : 0); exact.push([x, 1000 * (t.cdf[k] - M.Phi(x))]); }
      }
      for (let i = 0; i <= 1600; i++) { const x = -4 + i * 0.005; one.push([x, 1000 * M.edge1(p, n, x)]); two.push([x, 1000 * (M.edge2(p, n, x) + M.lattice(n, x))]); }
    } else {
      for (let i = 0; i <= 320; i++) {
        const x = -4 + i * 0.025;
        exact.push([x, 1000 * (p.cdf(n, x) - M.Phi(x))]); one.push([x, 1000 * M.edge1(p, n, x)]); two.push([x, 1000 * M.edge2(p, n, x)]);
      }
    }
    return { exact, one, two };
  }

  function drawFinger() {
    const { key, n } = eState(), p = M.PARENTS[key];
    $("eNo").textContent = n;
    $("eLeg3").textContent = key === "coin" ? "with Esseen's lattice term" : "two-term Edgeworth";
    const c = errorCurves(key, n);
    const mx = Math.max(...c.exact.filter((q) => Math.abs(q[0]) <= 4).map((q) => Math.abs(q[1])), 1e-6);
    const lim = Math.max(mx, Math.min(1.5 * mx, Math.max(...c.one.map((q) => Math.abs(q[1])), ...c.two.map((q) => Math.abs(q[1]))))) * 1.12;
    const yt = MP.nice(-lim, lim, 4);
    MP.plot($("ec1"), { x: [-4, 4], y: [-lim, lim], xl: "x (standardized mean)", yl: "error × 1000", xticks: [-4, -3, -2, -1, 0, 1, 2, 3, 4], yticks: yt,
      series: [{ pts: c.exact, c: "var(--s1)" }, { pts: c.one, c: "var(--s2)", dash: "dashed" }, { pts: c.two, c: "var(--s3)", dash: "dotted" }],
      hlines: [{ y: 0, c: "var(--rule)", w: 1 }] });

    const s = sup(key, n), F0 = p.cdf(n, 0), g1read = 6 * Math.sqrt(2 * Math.PI) * Math.sqrt(n) * (F0 - 0.5), be = M.berryEsseen(key, n);
    let txt = `<span>Largest error <b>${s.err.toExponential(2)}</b></span><span>× √n = <b>${(s.err * Math.sqrt(n)).toFixed(4)}</b></span><span>× n = <b>${(s.err * n).toFixed(4)}</b></span>` +
      `<span>Skewness read from the speed, 6√(2π)·√n·(F<sub>n</sub>(0) − ½) = <b>${g1read.toFixed(2)}</b> (true γ₁ = ${p.g1})</span>` +
      `<span>Berry–Esseen guarantee ≤ <b>${be.toFixed(4)}</b>, ${(be / s.err).toFixed(1)}× the actual error</span>`;
    if (key === "coin") txt += `<span>${n % 2 ? "Odd n: x = 0 falls between two steps, so F<sub>n</sub>(0) = ½ exactly" : "Even n: x = 0 is a step, so F<sub>n</sub>(0) includes half a jump and the readout sits near 6, not 0"}</span>`;
    $("eRead").innerHTML = txt;
    drawRate();
  }

  // Log–log chart: largest error against n for the three parents. Computed once, lazily.
  let rateReady = false;
  function drawRate() {
    const { key, n } = eState();
    const line = (k) => EN.filter((m) => supCache[k][m]).map((m) => [m, supCache[k][m].err]);
    MP.plot($("ec2"), { x: [1, 400], xlog: true, y: [1e-5, 1], ylog: true, xticks: [1, 2, 5, 10, 20, 50, 100, 200, 400],
      yticks: [1e-5, 1e-4, 1e-3, 0.01, 0.1, 1], yf: (v) => v >= 0.01 ? String(v) : "1e" + Math.round(Math.log10(v)),
      xl: "n (log scale)", yl: "largest error (log scale)",
      series: [{ pts: line("exp"), c: "var(--s1)" }, { pts: line("uni"), c: "var(--s2)", dash: "dashed" }, { pts: line("coin"), c: "var(--s3)", dash: "dotted" },
        { pts: [[n, sup(key, n).err]], c: "var(--ink)", dots: true, ring: true, r: 6 }] });
    if (!rateReady) {
      rateReady = true;
      const todo = []; ["exp", "uni", "coin"].forEach((k) => EN.forEach((m) => todo.push([k, m])));
      (function step() { for (let i = 0; i < 6 && todo.length; i++) { const [k, m] = todo.shift(); sup(k, m); } drawRate(); if (todo.length) setTimeout(step, 0); })();
    }
  }
  document.querySelectorAll('input[name="eP"]').forEach((el) => el.addEventListener("change", drawFinger));
  $("eN").addEventListener("input", drawFinger);

  /* ================================================================ §1 check your data */
  // Rule verdict and the one-term prediction of each tail's miss rate for the t interval:
  // 2.5% ± 8.5·γ₁/√n percentage points (§4; Hall 1992, Ch. 2). For γ₁ > 0 the "too low" side
  // (true mean above the interval: an upper bound fails) gets the plus sign.
  function sampleSkew(x) {                 // Excel SKEW / MATLAB skewness(x, 0): adjusted G1
    const n = x.length, m = x.reduce((a, b) => a + b, 0) / n;
    let s2 = 0, s3 = 0; x.forEach((v) => { const d = v - m; s2 += d * d; s3 += d * d * d; });
    const s = Math.sqrt(s2 / (n - 1));
    return s > 0 ? n / ((n - 1) * (n - 2)) * s3 / (s * s * s) : NaN;
  }
  function yourData(n, g) {
    const rule = M.sugdenN(g), sh = 8.5 * g / Math.sqrt(n);
    const lo = Math.max(0, 2.5 + sh), hi = Math.max(0, 2.5 - sh);
    const risky = Math.abs(g) < 0.25 ? "Close to symmetric: neither side is much worse than the other."
      : g > 0 ? "Right-skewed: an <b>upper</b> bound on the mean (\"at most…\") is the risky claim; a lower bound is conservative."
      : "Left-skewed: a <b>lower</b> bound on the mean (\"at least…\") is the risky claim; an upper bound is conservative.";
    const need = Math.floor(rule + 1e-9) + 1;   // the smallest whole n that is > rule
    $("ydOut").innerHTML = `<span>Rule: n &gt; <b>${Math.round(rule)}</b> → ${n >= need ? "<b>meets it</b>" : `<b class="flag">short by ${need - n}</b>`}</span>` +
      `<span>Predicted: too low <b class="${lo > 3.5 ? "flag" : ""}">${lo.toFixed(1)}%</b>, too high <b class="${hi > 3.5 ? "flag" : ""}">${hi.toFixed(1)}%</b> (target 2.5% each)</span>` +
      `<span>${risky}</span>` + (n < 20 ? `<span>With n under about 20 the prediction is rough.</span>` : "");
  }
  function ydErr(msg) { $("ydErr").textContent = msg; }
  $("yd").addEventListener("submit", (e) => {
    e.preventDefault();
    const n = Number($("ydN").value), g = Number($("ydG").value);
    if (!Number.isInteger(n) || n < 3) { ydErr("Enter a whole-number sample size of 3 or more."); return; }
    if ($("ydG").value.trim() === "" || !isFinite(g)) { ydErr("Enter a skewness, for example 1 or −0.5."); return; }
    ydErr(""); yourData(n, g);
  });
  $("ydUse").addEventListener("click", () => {
    const x = $("ydX").value.split(/[\s,;]+/).filter(Boolean).map(Number);
    if (x.some((v) => !isFinite(v))) { ydErr("Only numbers, separated by spaces, commas or new lines."); return; }
    if (x.length < 3) { ydErr("Paste at least 3 numbers."); return; }
    const g = sampleSkew(x);
    if (!isFinite(g)) { ydErr("All the values are the same, so the skewness is undefined."); return; }
    $("ydN").value = x.length; $("ydG").value = g.toFixed(2); ydErr(""); yourData(x.length, g);
  });
  ["ydN", "ydG", "ydX"].forEach((id) => $(id).addEventListener("input", () => ydErr("")));
  yourData(40, 1);

  drawFinger();
  runCover();
}());
