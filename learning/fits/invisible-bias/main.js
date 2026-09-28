// main.js — The Invisible Bias (Reading Your Fits, Module 5). Page logic for the four trials.
// Engine: ../../assets/learning.js (LF). Words: strings.js via LI18N.t. All data is simulated:
// true model y = 1 + 2x + error.
(function () {
  "use strict";
  var t = LI18N.t, num = LF.num;
  var $ = function (id) { return document.getElementById(id); };
  var TRUE_B0 = 1, TRUE_B1 = 2;

  function offBy(b) {
    var p = (b - TRUE_B1) / TRUE_B1 * 100;
    if (Math.abs(p) < 2) return t("offSmall");
    return t(p < 0 ? "offFlat" : "offSteep", { p: Math.abs(p).toFixed(0) });
  }
  function flag(el, bad, good) { el.className = "v" + (bad ? " bad" : good ? " good" : ""); }
  function fmtStatic() { document.querySelectorAll("[data-num]").forEach(function (el) { el.textContent = num(+el.getAttribute("data-num"), 2); }); }

  // ---------- quiz ----------
  var quizPick = null;
  function quizRender() {
    if (!quizPick) return;
    var a = $("quiz1-answer");
    a.hidden = false;
    a.innerHTML = t(quizPick === "flatter" ? "quizRightHtml" : "quizWrongHtml") + LF.esc(t("quizExplain"));
  }
  $("quiz1").querySelectorAll(".opts button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      $("quiz1").querySelectorAll(".opts button").forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      quizPick = btn.getAttribute("data-a");
      quizRender();
    });
  });

  // ---------- Trial 1: noise in y vs noise in x ----------
  var T1 = { n: 50 };
  function t1Draw() { var r = LF.mulberry32(LF.newSeed()); T1.xt = LF.uniforms(r, T1.n, 0, 10); T1.zx = LF.normals(r, T1.n); T1.zy = LF.normals(r, T1.n); }
  function t1() {
    var sy = +$("t1-sy").value, sx = +$("t1-sx").value;
    $("t1-sy-out").textContent = num(sy, 1); $("t1-sx-out").textContent = num(sx, 1);
    var x = new Float64Array(T1.n), y = new Float64Array(T1.n);
    for (var i = 0; i < T1.n; i++) { x[i] = T1.xt[i] + sx * T1.zx[i]; y[i] = TRUE_B0 + TRUE_B1 * T1.xt[i] + sy * T1.zy[i]; }
    var f = LF.ols(x, y);
    LF.chart($("t1-scatter"), { w: 420, h: 380, x: [-6, 16], y: [-10, 32], xLabel: t("axMeasuredX"), yLabel: t("axMeasuredY"),
      draw: function (sX, sY) { return LF.dots(x, y, sX, sY) + LF.line("truth", sX, sY, TRUE_B0, TRUE_B1, -6, 16) + LF.line("fit", sX, sY, f.b0, f.b1, -6, 16); } });
    LF.chart($("t1-resid"), { w: 420, h: 380, x: [-6, 32], y: [-12, 12], xLabel: t("axFittedY"), yLabel: t("axResidual"),
      draw: function (sX, sY) { return '<line class="zero" x1="' + sX(-6) + '" x2="' + sX(32) + '" y1="' + sY(0) + '" y2="' + sY(0) + '"/>' + LF.dots(f.fitted, f.resid, sX, sY); } });
    $("t1-b").textContent = num(f.b1);
    $("t1-err").textContent = offBy(f.b1); flag($("t1-err"), Math.abs(f.b1 - TRUE_B1) / TRUE_B1 > 0.08);
    var lam = 8.333 / (8.333 + sx * sx);   // variance of uniform(0,10) = 100/12
    $("t1-note").innerHTML = sx < 0.3 ? t("t1NoteExactHtml") : t("t1NoteNoisyHtml", { sx: num(sx, 1), pct: (lam * 100).toFixed(0) });
  }
  ["t1-sy", "t1-sx"].forEach(function (id) { $(id).addEventListener("input", t1); });
  $("t1-new").addEventListener("click", function () { t1Draw(); t1(); });

  // ---------- Trial 2: repeat the experiment 400 times ----------
  var T2 = { reps: 400 };
  function t2Seed() { T2.seed = LF.newSeed(); }
  function t2() {
    var sx = +$("t2-sx").value, n = +document.querySelector('input[name="t2n"]:checked').value;
    $("t2-sx-out").textContent = num(sx, 1);
    var r = LF.mulberry32(T2.seed), slopes = new Float64Array(T2.reps), caught = 0, tc = LF.tcrit(n - 2);
    var x = new Float64Array(n), y = new Float64Array(n);
    for (var k = 0; k < T2.reps; k++) {
      for (var i = 0; i < n; i++) { var xt = 10 * r(), z = LF.normals(r, 2); x[i] = xt + sx * z[0]; y[i] = TRUE_B0 + TRUE_B1 * xt + z[1]; }
      var f = LF.ols(x, y); slopes[k] = f.b1;
      if (Math.abs(f.b1 - TRUE_B1) <= tc * f.se1) caught++;
    }
    var sorted = Array.from(slopes).sort(function (a, b) { return a - b; });
    var mean = sorted.reduce(function (a, b) { return a + b; }, 0) / sorted.length;
    var lo = sorted[Math.floor(0.025 * sorted.length)], hi = sorted[Math.ceil(0.975 * sorted.length) - 1];
    // Axis covers every slope: at least 0.5 to 2.5, widened in 0.5 steps when the pile spills over.
    var b0 = Math.min(0.5, Math.floor(sorted[0] * 2) / 2), b1 = Math.max(2.5, Math.ceil(sorted[sorted.length - 1] * 2) / 2);
    var w = 1 / 30, bins = Math.round((b1 - b0) / w), counts = new Array(bins).fill(0);
    sorted.forEach(function (s) { var j = Math.min(bins - 1, Math.floor((s - b0) / w)); if (j >= 0) counts[j]++; });
    var top = Math.max.apply(null, counts.concat([1])) * 1.15;
    LF.chart($("t2-hist"), { h: 320, x: [b0, b1], y: [0, top], xLabel: t("axFittedSlope"), yLabel: t("axRepeats"), noY: true,
      draw: function (sX, sY) {
        var s = "";
        counts.forEach(function (c, j) { if (c) s += '<rect class="bar" x="' + (sX(b0 + j * w) + 0.5) + '" y="' + sY(c) + '" width="' + (sX(b0 + w) - sX(b0) - 1) + '" height="' + (sY(0) - sY(c)) + '"/>'; });
        return s + '<line class="vline-truth" x1="' + sX(TRUE_B1) + '" x2="' + sX(TRUE_B1) + '" y1="' + sY(0) + '" y2="' + sY(top) + '"/>' +
          '<line class="vline-fit" x1="' + sX(mean) + '" x2="' + sX(mean) + '" y1="' + sY(0) + '" y2="' + sY(top) + '"/>';
      },
      over: function (sX, sY, g) {
        var near = Math.abs(sX(mean) - sX(TRUE_B1)) < 60;
        return '<text class="lbl-truth" x="' + (sX(TRUE_B1) + 6) + '" y="' + (g.m.t + 16) + '">' + LF.esc(t("lblTruth", { v: num(TRUE_B1) })) + '</text>' +
          (near ? "" : '<text class="lbl-fit" x="' + (sX(mean) - 6) + '" y="' + (g.m.t + 16) + '" text-anchor="end">' + LF.esc(t("lblAvg", { v: num(mean) })) + '</text>');
      } });
    var cover = caught / T2.reps * 100;
    $("t2-mean").textContent = num(mean); flag($("t2-mean"), Math.abs(mean - TRUE_B1) > 0.1);
    $("t2-range").textContent = t("rangeFmt", { lo: num(lo), hi: num(hi) });
    $("t2-cover").textContent = t("coverFmt", { p: cover.toFixed(0) }); flag($("t2-cover"), cover < 85);
    $("t2-note").innerHTML = sx < 0.3 ? t("t2NoteExactHtml")
      : t("t2NoteNoisyHtml", { mean: num(mean) }) + t(cover < 85 ? "t2NoteLowCoverHtml" : "t2NoteOkCoverHtml", { n: n, cover: cover.toFixed(0) });
  }
  $("t2-sx").addEventListener("input", t2);
  document.querySelectorAll('input[name="t2n"]').forEach(function (el) { el.addEventListener("change", t2); });
  $("t2-new").addEventListener("click", function () { t2Seed(); t2(); });

  // ---------- Trial 3: unmeasured drift and run order ----------
  var T3 = { n: 40 };
  function t3Draw() {
    var r = LF.mulberry32(LF.newSeed());
    T3.ze = LF.normals(r, T3.n);
    T3.perm = Array.from({ length: T3.n }, function (_, i) { return i; });
    for (var i = T3.n - 1; i > 0; i--) { var j = Math.floor(r() * (i + 1)), tmp = T3.perm[i]; T3.perm[i] = T3.perm[j]; T3.perm[j] = tmp; }
  }
  function t3() {
    var D = +$("t3-d").value, order = document.querySelector('input[name="t3o"]:checked').value;
    $("t3-d-out").textContent = num(D, 1);
    var n = T3.n, x = new Float64Array(n), y = new Float64Array(n), tt = new Float64Array(n);
    for (var k = 0; k < n; k++) {                 // k = run number (time order)
      var level = order === "sweep" ? k : T3.perm[k];
      x[k] = 10 * level / (n - 1);
      tt[k] = k / (n - 1);
      y[k] = TRUE_B0 + TRUE_B1 * x[k] + D * tt[k] + T3.ze[k];
    }
    var f = LF.ols(x, y);
    var shade = function (k) { return (0.15 + 0.8 * tt[k]).toFixed(2); };
    LF.chart($("t3-scatter"), { w: 420, h: 380, x: [-1, 11], y: [-4, 34], xLabel: t("axXSetting"), yLabel: t("axMeasuredY"),
      draw: function (sX, sY) {
        var s = "";
        for (var k = 0; k < n; k++) s += '<circle class="pt-time" cx="' + sX(x[k]).toFixed(1) + '" cy="' + sY(y[k]).toFixed(1) + '" r="4.5" fill-opacity="' + shade(k) + '"/>';
        return s + LF.line("truth", sX, sY, TRUE_B0, TRUE_B1, -1, 11) + LF.line("fit", sX, sY, f.b0, f.b1, -1, 11);
      } });
    LF.chart($("t3-resid"), { w: 420, h: 380, x: [0, n + 1], y: [-8, 8], xLabel: t("axRunNumber"), yLabel: t("axResidual"),
      draw: function (sX, sY) {
        var s = '<line class="zero" x1="' + sX(0) + '" x2="' + sX(n + 1) + '" y1="' + sY(0) + '" y2="' + sY(0) + '"/>';
        for (var k = 0; k < n; k++) s += '<circle class="pt-time" cx="' + sX(k + 1).toFixed(1) + '" cy="' + sY(f.resid[k]).toFixed(1) + '" r="4.5" fill-opacity="' + shade(k) + '"/>';
        return s;
      } });
    $("t3-b").textContent = num(f.b1);
    $("t3-err").textContent = offBy(f.b1); flag($("t3-err"), Math.abs(f.b1 - TRUE_B1) / TRUE_B1 > 0.08);
    $("t3-note").innerHTML = D < 0.5 ? t("t3NoteNoneHtml") : t(order === "sweep" ? "t3NoteSweepHtml" : "t3NoteRandomHtml");
  }
  $("t3-d").addEventListener("input", t3);
  document.querySelectorAll('input[name="t3o"]').forEach(function (el) { el.addEventListener("change", t3); });
  $("t3-new").addEventListener("click", function () { t3Draw(); t3(); });

  // ---------- Trial 4: what fixes noise in x ----------
  var T4 = { n: 60 };
  function t4Draw() { var r = LF.mulberry32(LF.newSeed()); T4.u = LF.uniforms(r, T4.n, 0, 1); T4.zx = LF.normals(r, T4.n); T4.zy = LF.normals(r, T4.n); }
  function t4() {
    var sx = +$("t4-sx").value, span = +$("t4-span").value;
    $("t4-sx-out").textContent = num(sx, 1); $("t4-span-out").textContent = t("spanFmt", { s: span });
    var n = T4.n, x = new Float64Array(n), y = new Float64Array(n);
    for (var i = 0; i < n; i++) { var xt = span * T4.u[i]; x[i] = xt + sx * T4.zx[i]; y[i] = TRUE_B0 + TRUE_B1 * xt + T4.zy[i]; }
    var f = LF.ols(x, y), d = LF.deming(x, y, sx > 0 ? 1 / (sx * sx) : Infinity);
    var varX = span * span / 12, lam = varX / (varX + sx * sx);
    var X0 = -6, X1 = span + 6;
    LF.chart($("t4-scatter"), { h: 380, x: [X0, X1], y: [TRUE_B0 + TRUE_B1 * X0, TRUE_B0 + TRUE_B1 * X1], xLabel: t("axMeasuredX"), yLabel: t("axMeasuredY"),
      draw: function (sX, sY) { return LF.dots(x, y, sX, sY) + LF.line("truth", sX, sY, TRUE_B0, TRUE_B1, X0, X1) + LF.line("fit", sX, sY, f.b0, f.b1, X0, X1) + LF.line("fix", sX, sY, d.b0, d.b1, X0, X1); } });
    $("t4-ols").textContent = num(f.b1); flag($("t4-ols"), Math.abs(f.b1 - TRUE_B1) / TRUE_B1 > 0.08);
    // Left neutral on purpose: the errors-in-x fit is unbiased but noisier, so any one sample can miss by more
    // than the 8% used for the other readouts. The note below warns when the correction itself is unreliable.
    $("t4-dem").textContent = num(d.b1); flag($("t4-dem"), false, false);
    $("t4-lam").textContent = t("expectedFmt", { v: num(TRUE_B1 * lam), p: (lam * 100).toFixed(0) });
    $("t4-note").innerHTML = sx < 0.3 ? t("t4NoteExactHtml")
      : t("t4NoteNoisyHtml", { exp: num(TRUE_B1 * lam) }) + (lam < 0.3 ? t("t4NoteUnreliableHtml") : "");
  }
  ["t4-sx", "t4-span"].forEach(function (id) { $(id).addEventListener("input", t4); });
  $("t4-new").addEventListener("click", function () { t4Draw(); t4(); });

  // ---------- start, and redraw on a language switch ----------
  function renderAll() { fmtStatic(); t1(); t2(); t3(); t4(); quizRender(); LF.seriesNav($("series-nav"), "invisible-bias"); }
  t1Draw(); t2Seed(); t3Draw(); t4Draw();
  renderAll();
  document.addEventListener("learnlangchange", renderAll);
}());
