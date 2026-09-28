// main.js — Uneven scatter (Reading Your Fits, Module 3). Page logic for the three trials.
// Engine: ../../assets/learning.js (LF). Words: strings.js via LI18N.t.
// Simulated data: y = 1 + 2x, sensor error SD = 0.5 + p% of the true reading.
(function () {
  "use strict";
  var t = LI18N.t, num = LF.num;
  var $ = function (id) { return document.getElementById(id); };
  var radio = function (name) { return document.querySelector('input[name="' + name + '"]:checked').value; };
  var TRUE_B0 = 1, TRUE_B1 = 2, N = 40, REPS = 400, X_LO = 2, X_HI = 9;
  var truth = function (x) { return TRUE_B0 + TRUE_B1 * x; };
  // Sensor error SD. "high": 0.5 + p% of the true reading. "ends": 0.5 in the middle, growing
  // linearly toward both ends to the same size the "high" case reaches at the top (x = 10).
  var sigma = function (x, p, pat) {
    return pat === "ends" ? 0.5 + p / 100 * truth(10) * Math.abs(x - 5.5) / 4.5 : 0.5 + p / 100 * truth(x);
  };
  function fmtStatic() { document.querySelectorAll("[data-num]").forEach(function (el) { el.textContent = num(+el.getAttribute("data-num"), 2); }); }
  function zeroLine(sX, sY, x0, x1) { return '<line class="zero" x1="' + sX(x0) + '" x2="' + sX(x1) + '" y1="' + sY(0) + '" y2="' + sY(0) + '"/>'; }
  function pctOut(id, p) { $(id).textContent = t("pctFmt", { p: p }); }
  // A shaded band between lo(x) and hi(x), sampled across [x0, x1].
  function bandPath(sX, sY, lo, hi, x0, x1, cls) {
    var top = "", bot = "", k, xv;
    for (k = 0; k <= 60; k++) { xv = x0 + (x1 - x0) * k / 60; top += (k ? "L" : "M") + sX(xv).toFixed(1) + " " + sY(hi(xv)).toFixed(1); }
    for (k = 60; k >= 0; k--) { xv = x0 + (x1 - x0) * k / 60; bot += "L" + sX(xv).toFixed(1) + " " + sY(lo(xv)).toFixed(1); }
    return '<path class="' + cls + '" d="' + top + bot + 'Z"/>';
  }
  function sampleXY(r, p, pat) {
    var x = LF.uniforms(r, N, 1, 10), z = LF.normals(r, N), y = new Float64Array(N);
    for (var i = 0; i < N; i++) y[i] = truth(x[i]) + sigma(x[i], p, pat) * z[i];
    return { x: x, y: y };
  }
  function weights(x, p, pat) { var w = new Float64Array(x.length); for (var i = 0; i < x.length; i++) { var s = sigma(x[i], p, pat); w[i] = 1 / (s * s); } return w; }
  // 95% prediction half-width for a weighted fit at x0 (σ known up to the fitted scale s2).
  function wlsPi(f, x0, p, pat) {
    var s0 = sigma(x0, p, pat), varMean = f.s2 * (1 / f.sw + (x0 - f.mx) * (x0 - f.mx) / f.sxx);
    return LF.tcrit(N - 2) * Math.sqrt(f.s2 * s0 * s0 + varMean);
  }
  // Repeat the experiment REPS times and count how often each 95% promise holds.
  function simulate(seed, p, pat) {
    var r = LF.mulberry32(seed), tc = LF.tcrit(N - 2), c = { piLo: 0, piHi: 0, def: 0, rob: 0, wLo: 0, wHi: 0 };
    var bo = [], bw = [];
    for (var k = 0; k < REPS; k++) {
      var d = sampleXY(r, p, pat), f = LF.ols(d.x, d.y), w = LF.wls(d.x, d.y, weights(d.x, p, pat)), z = LF.normals(r, 2);
      var yLo = truth(X_LO) + sigma(X_LO, p, pat) * z[0], yHi = truth(X_HI) + sigma(X_HI, p, pat) * z[1];
      var bLo = LF.bands(d.x, f, X_LO), bHi = LF.bands(d.x, f, X_HI);
      if (Math.abs(yLo - bLo.y) <= bLo.pi) c.piLo++;
      if (Math.abs(yHi - bHi.y) <= bHi.pi) c.piHi++;
      if (Math.abs(f.b1 - TRUE_B1) <= tc * f.se1) c.def++;
      if (Math.abs(f.b1 - TRUE_B1) <= tc * LF.hc3se(d.x, f)) c.rob++;
      if (Math.abs(yLo - (w.b0 + w.b1 * X_LO)) <= wlsPi(w, X_LO, p, pat)) c.wLo++;
      if (Math.abs(yHi - (w.b0 + w.b1 * X_HI)) <= wlsPi(w, X_HI, p, pat)) c.wHi++;
      bo.push(f.b1); bw.push(w.b1);
    }
    Object.keys(c).forEach(function (key) { c[key] = c[key] / REPS * 100; });
    c.bo = bo; c.bw = bw;
    return c;
  }
  function sd(a) { var m = 0, v = 0; a.forEach(function (q) { m += q; }); m /= a.length; a.forEach(function (q) { v += (q - m) * (q - m); }); return Math.sqrt(v / (a.length - 1)); }
  function pct(v) { return t("pctOf", { p: num(v, 0) }); }
  function flagCov(el, v) { el.className = "v" + (Math.abs(v - 95) > 4 ? " bad" : ""); }

  // ---------- Trial 1: the fan ----------
  var T1 = {};
  function t1Draw() { T1.seed = LF.newSeed(); }
  function t1() {
    var p = +$("t1-p").value; pctOut("t1-p-out", p);
    var d = sampleXY(LF.mulberry32(T1.seed), p, "high"), f = LF.ols(d.x, d.y);
    // Residual spread in the lowest and highest third of fitted values.
    var idx = Array.from(f.fitted.keys()).sort(function (a, b) { return f.fitted[a] - f.fitted[b]; });
    var third = Math.floor(N / 3);
    var rs = function (ids) { return sd(ids.map(function (i) { return f.resid[i]; })); };
    var lo = rs(idx.slice(0, third)), hi = rs(idx.slice(N - third)), ratio = hi / lo;
    LF.chart($("t1-data"), { w: 420, h: 380, x: [0, 11], y: [-5, 35], xLabel: t("axX"), yLabel: t("axY"),
      draw: function (sX, sY) { return LF.dots(d.x, d.y, sX, sY) + LF.line("truth", sX, sY, TRUE_B0, TRUE_B1, 0, 11) + LF.line("fit", sX, sY, f.b0, f.b1, 0, 11); } });
    LF.chart($("t1-resid"), { w: 420, h: 380, x: [0, 25], y: [-12, 12], xLabel: t("axFittedY"), yLabel: t("axResidual"),
      draw: function (sX, sY) { return zeroLine(sX, sY, 0, 25) + LF.dots(f.fitted, f.resid, sX, sY); } });
    $("t1-b").textContent = num(f.b1);
    $("t1-lo").textContent = num(lo, 2);
    $("t1-hi").textContent = num(hi, 2);
    $("t1-ratio").textContent = t("ratioFmt", { r: num(ratio, 1) });
    $("t1-ratio").className = "v" + (ratio > 2 ? " bad" : "");
    $("t1-note").innerHTML = t(ratio > 2 ? "t1NoteFanHtml" : "t1NoteEvenHtml", { r: num(ratio, 1), b: num(f.b1) });
  }
  $("t1-p").addEventListener("input", t1);
  $("t1-new").addEventListener("click", function () { t1Draw(); t1(); });

  // ---------- Trial 2: the error bars lie ----------
  var T2 = {};
  function t2Draw() { T2.seed = LF.newSeed(); T2.simSeed = LF.newSeed(); }
  function t2() {
    var p = +$("t2-p").value, pat = radio("t2pat"); pctOut("t2-p-out", p);
    var d = sampleXY(LF.mulberry32(T2.seed), p, pat), f = LF.ols(d.x, d.y), c = simulate(T2.simSeed, p, pat);
    var rz = LF.mulberry32(T2.seed + 1), zl = LF.normals(rz, 200), zh = LF.normals(rz, 200), jit = LF.uniforms(rz, 200, -0.25, 0.25);
    var bl = LF.bands(d.x, f, X_LO), bh = LF.bands(d.x, f, X_HI);
    LF.chart($("t2-band"), { w: 420, h: 380, x: [0, 11], y: [-5, 35], xLabel: t("axX"), yLabel: t("axY"),
      draw: function (sX, sY) {
        var s = bandPath(sX, sY, function (x) { var b = LF.bands(d.x, f, x); return b.y - b.pi; }, function (x) { var b = LF.bands(d.x, f, x); return b.y + b.pi; }, 0, 11, "band-pi");
        s += LF.line("fit", sX, sY, f.b0, f.b1, 0, 11);
        for (var i = 0; i < 200; i++) {
          var yl = truth(X_LO) + sigma(X_LO, p, pat) * zl[i], yh = truth(X_HI) + sigma(X_HI, p, pat) * zh[i];
          s += '<circle class="' + (Math.abs(yl - bl.y) <= bl.pi ? "pt" : "pt-hi") + '" cx="' + sX(X_LO + jit[i]).toFixed(1) + '" cy="' + sY(yl).toFixed(1) + '" r="2.5"/>';
          s += '<circle class="' + (Math.abs(yh - bh.y) <= bh.pi ? "pt" : "pt-hi") + '" cx="' + sX(X_HI + jit[i]).toFixed(1) + '" cy="' + sY(yh).toFixed(1) + '" r="2.5"/>';
        }
        return s;
      } });
    var vals = [c.piLo, c.piHi, c.def, c.rob], labs = [t("barLow"), t("barHigh"), t("barSlopeDef"), t("barSlopeRob")];
    LF.chart($("t2-bars"), { w: 420, h: 380, x: [0.4, 4.6], y: [50, 100], xLabel: "", yLabel: t("axCaught"),
      xticks: [1, 2, 3, 4], xfmt: function (v) { return labs[v - 1]; },
      draw: function (sX, sY) {
        var s = "", bw = (sX(1) - sX(0)) * 0.55;
        vals.forEach(function (v, i) { s += '<rect class="' + (Math.abs(v - 95) > 4 ? "bar-hi" : "bar") + '" x="' + (sX(i + 1) - bw / 2) + '" y="' + sY(Math.max(v, 50)) + '" width="' + bw + '" height="' + (sY(50) - sY(Math.max(v, 50))) + '"/>'; });
        return s + '<line class="thresh" x1="' + sX(0.4) + '" x2="' + sX(4.6) + '" y1="' + sY(95) + '" y2="' + sY(95) + '"/>';
      } });
    [["t2-lo", c.piLo], ["t2-hi", c.piHi], ["t2-def", c.def], ["t2-rob", c.rob]].forEach(function (a) { $(a[0]).textContent = pct(a[1]); flagCov($(a[0]), a[1]); });
    var v = { lo: num(c.piLo, 0), hi: num(c.piHi, 0), def: num(c.def, 0), rob: num(c.rob, 0) };
    var uneven = Math.abs(c.piLo - 95) > 3 || Math.abs(c.piHi - 95) > 3;
    $("t2-note").innerHTML = uneven ? t("t2NoteFanHtml", v) + t(c.def < 91 ? "t2NoteSlopeBadHtml" : "t2NoteSlopeOkHtml", v) : t("t2NoteEvenHtml", v);
  }
  $("t2-p").addEventListener("input", t2);
  document.querySelectorAll('input[name="t2pat"]').forEach(function (el) { el.addEventListener("change", t2); });
  $("t2-new").addEventListener("click", function () { t2Draw(); t2(); });

  // ---------- Trial 3: weighted fit ----------
  var T3 = {};
  function t3Draw() { T3.seed = LF.newSeed(); T3.simSeed = LF.newSeed(); }
  function t3() {
    var p = +$("t3-p").value, m = radio("t3m"); pctOut("t3-p-out", p);
    var d = sampleXY(LF.mulberry32(T3.seed), p, "high"), c = simulate(T3.simSeed, p, "high");
    var f = LF.ols(d.x, d.y), w = LF.wls(d.x, d.y, weights(d.x, p, "high")), isW = m === "wls";
    var yhat = function (x) { return isW ? w.b0 + w.b1 * x : f.b0 + f.b1 * x; };
    var half = function (x) { return isW ? wlsPi(w, x, p, "high") : LF.bands(d.x, f, x).pi; };
    LF.chart($("t3-data"), { w: 420, h: 380, x: [0, 11], y: [-5, 35], xLabel: t("axX"), yLabel: t("axY"),
      draw: function (sX, sY) {
        return bandPath(sX, sY, function (x) { return yhat(x) - half(x); }, function (x) { return yhat(x) + half(x); }, 0, 11, isW ? "band-pi-fix" : "band-pi") +
          LF.dots(d.x, d.y, sX, sY) + LF.line("truth", sX, sY, TRUE_B0, TRUE_B1, 0, 11) +
          LF.line(isW ? "fix" : "fit", sX, sY, isW ? w.b0 : f.b0, isW ? w.b1 : f.b1, 0, 11);
      } });
    // Two histograms of fitted slopes on one axis: ordinary (red outline) and weighted (blue).
    var lo = 1.4, hi = 2.6, nb = 36, bwid = (hi - lo) / nb;
    var hist = function (a) { var h = new Array(nb).fill(0); a.forEach(function (v) { var j = Math.floor((v - lo) / bwid); if (j >= 0 && j < nb) h[j]++; }); return h; };
    var ho = hist(c.bo), hw = hist(c.bw), top = Math.max.apply(null, ho.concat(hw)) * 1.15 || 1;
    LF.chart($("t3-spread"), { w: 420, h: 380, x: [lo, hi], y: [0, top], xLabel: t("axFittedSlope"), yLabel: t("axRepeats"), noY: true,
      draw: function (sX, sY) {
        var step = function (h, cls) {
          var dd = "M" + sX(lo) + " " + sY(0);
          h.forEach(function (v, j) { dd += "L" + sX(lo + j * bwid) + " " + sY(v) + "L" + sX(lo + (j + 1) * bwid) + " " + sY(v); });
          return '<path class="' + cls + '" d="' + dd + "L" + sX(hi) + " " + sY(0) + '"/>';
        };
        return step(ho, "fit-curve") + step(hw, "fix-curve") + '<line class="vline-truth" x1="' + sX(2) + '" x2="' + sX(2) + '" y1="' + sY(0) + '" y2="' + sY(top) + '"/>';
      },
      over: function (sX, sY, g) {
        return '<text class="lbl-fit" x="' + (g.m.l + 8) + '" y="' + (g.m.t + 16) + '">' + LF.esc(t("lblOls")) + " " + num(sd(c.bo), 3) + '</text>' +
          '<text class="lbl-truth" x="' + (g.m.l + 8) + '" y="' + (g.m.t + 34) + '" style="fill: var(--fix)">' + LF.esc(t("lblWls")) + " " + num(sd(c.bw), 3) + '</text>';
      } });
    $("t3-b").textContent = num(isW ? w.b1 : f.b1);
    var cl = isW ? c.wLo : c.piLo, ch = isW ? c.wHi : c.piHi;
    $("t3-lo").textContent = pct(cl); flagCov($("t3-lo"), cl);
    $("t3-hi").textContent = pct(ch); flagCov($("t3-hi"), ch);
    $("t3-osd").textContent = num(sd(c.bo), 3);
    $("t3-wsd").textContent = num(sd(c.bw), 3);
    var key = p < 3 ? "t3NoteEvenHtml" : isW ? "t3NoteWlsHtml" : "t3NoteOlsHtml";
    $("t3-note").innerHTML = t(key, { lo: num(cl, 0), hi: num(ch, 0), w: num(sd(c.bw), 3), o: num(sd(c.bo), 3) });
  }
  document.querySelectorAll('input[name="t3m"]').forEach(function (el) { el.addEventListener("change", t3); });
  $("t3-p").addEventListener("input", t3);
  $("t3-new").addEventListener("click", function () { t3Draw(); t3(); });

  // ---------- start, and redraw on a language switch ----------
  function renderAll() { fmtStatic(); t1(); t2(); t3(); LF.seriesNav($("series-nav"), "uneven-scatter"); }
  t1Draw(); t2Draw(); t3Draw();
  renderAll();
  document.addEventListener("learnlangchange", renderAll);
}());
