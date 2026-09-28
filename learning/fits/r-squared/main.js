// main.js — Why R² isn't enough (Reading Your Fits, Module 1). Page logic for the three trials.
// Engine: ../../assets/learning.js (LF). Words: strings.js via LI18N.t.
// Trial 1 uses Anscombe's (1973) published quartet; trials 2 and 3 are simulated, y = 1 + 2x + error.
(function () {
  "use strict";
  var t = LI18N.t, num = LF.num;
  var $ = function (id) { return document.getElementById(id); };
  var radio = function (name) { return document.querySelector('input[name="' + name + '"]:checked').value; };
  var TRUE_B0 = 1, TRUE_B1 = 2;
  function zeroLine(sX, sY, x0, x1) { return '<line class="zero" x1="' + sX(x0) + '" x2="' + sX(x1) + '" y1="' + sY(0) + '" y2="' + sY(0) + '"/>'; }
  function curvePath(sX, sY, fn, x0, x1, cls) {
    var d = "";
    for (var k = 0; k <= 160; k++) { var xv = x0 + (x1 - x0) * k / 160; d += (k ? "L" : "M") + sX(xv).toFixed(1) + " " + sY(fn(xv)).toFixed(1); }
    return '<path class="' + cls + '" d="' + d + '"/>';
  }

  // ---------- Trial 1: Anscombe's quartet ----------
  var X123 = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5];
  var SETS = [
    { x: X123, y: [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68] },
    { x: X123, y: [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74] },
    { x: X123, y: [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73] },
    { x: [8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8], y: [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89] }
  ];
  function t1() {
    var k = +radio("t1s"), d = SETS[k], f = LF.ols(d.x, d.y);
    LF.chart($("t1-data"), { w: 420, h: 380, x: [2, 20], y: [2, 14], xLabel: t("axX"), yLabel: t("axY"),
      draw: function (sX, sY) { return LF.line("fit", sX, sY, f.b0, f.b1, 2, 20) + LF.dots(d.x, d.y, sX, sY, 5); } });
    LF.chart($("t1-resid"), { w: 420, h: 380, x: [4, 14], y: [-4, 4], xLabel: t("axFittedY"), yLabel: t("axResidual"),
      draw: function (sX, sY) { return zeroLine(sX, sY, 4, 14) + LF.dots(f.fitted, f.resid, sX, sY, 5); } });
    $("t1-b1").textContent = num(f.b1, 3);
    $("t1-b0").textContent = num(f.b0, 2);
    $("t1-r2").textContent = num(LF.r2(d.y, f.fitted), 3);
    $("t1-s").textContent = num(f.s, 2);
    $("t1-note").innerHTML = t("t1Note" + (k + 1) + "Html");
  }
  document.querySelectorAll('input[name="t1s"]').forEach(function (el) { el.addEventListener("change", t1); });

  var quizPick = null;
  function quizRender() {
    if (quizPick === null) return;
    $("quiz1-answer").innerHTML = t(quizPick === "0" ? "quizRightHtml" : "quizWrongHtml") + LF.esc(t("quizExplain"));
  }
  $("quiz1").querySelectorAll(".opts button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      $("quiz1").querySelectorAll(".opts button").forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      quizPick = btn.getAttribute("data-a");
      quizRender();
    });
  });

  // ---------- Trial 2: R² grows with the test range ----------
  var T2 = { n: 30 };
  function t2Draw() {
    var r = LF.mulberry32(LF.newSeed()), z = LF.normals(r, T2.n), m = 0, v = 0, i;
    T2.u = LF.uniforms(r, T2.n, 0, 1);
    // Rescale the draws to mean 0, SD 1 so the residual SD tracks the noise slider closely.
    for (i = 0; i < T2.n; i++) m += z[i];
    m /= T2.n;
    for (i = 0; i < T2.n; i++) v += (z[i] - m) * (z[i] - m);
    v = Math.sqrt(v / (T2.n - 1));
    for (i = 0; i < T2.n; i++) z[i] = (z[i] - m) / v;
    T2.z = z;
  }
  // Expected R² for x spread evenly over 0..span with noise sd: signal variance / total variance.
  function expectedR2(span, sd) { var v = TRUE_B1 * TRUE_B1 * span * span / 12; return v / (v + sd * sd); }
  function t2() {
    var span = +$("t2-span").value, sd = +$("t2-sd").value, n = T2.n;
    $("t2-span-out").textContent = t("spanFmt", { s: span });
    $("t2-sd-out").textContent = num(sd, 1);
    var x = new Float64Array(n), y = new Float64Array(n);
    for (var i = 0; i < n; i++) { x[i] = span * (i + T2.u[i]) / n; y[i] = TRUE_B0 + TRUE_B1 * x[i] + sd * T2.z[i]; }
    var f = LF.ols(x, y), r2 = LF.r2(y, f.fitted);
    LF.chart($("t2-data"), { w: 420, h: 380, x: [0, 30], y: [-15, 75], xLabel: t("axX"), yLabel: t("axY"),
      draw: function (sX, sY) { return LF.line("truth", sX, sY, TRUE_B0, TRUE_B1, 0, 30) + LF.line("fit", sX, sY, f.b0, f.b1, 0, span) + LF.dots(x, y, sX, sY); } });
    LF.chart($("t2-curve"), { w: 420, h: 380, x: [0, 30], y: [0, 1], xLabel: t("axXRange"), yLabel: t("axExpectedR2"),
      draw: function (sX, sY) {
        return curvePath(sX, sY, function (s) { return expectedR2(Math.max(s, 0.01), sd); }, 0, 30, "ln-muted") +
          '<circle class="pt-hi" cx="' + sX(span) + '" cy="' + sY(expectedR2(span, sd)) + '" r="6"/>';
      } });
    $("t2-r2").textContent = num(r2, 3);
    $("t2-exp").textContent = num(expectedR2(span, sd), 3);
    $("t2-s").textContent = num(f.s, 2);
    $("t2-b").textContent = t("ciFmt", { b: num(f.b1, 2), h: num(LF.tcrit(n - 2) * f.se1, 2) });
    $("t2-note").innerHTML = t("t2NoteHtml", { r2: num(r2, 3), s: num(f.s, 2), sd: num(sd, 1) });
  }
  ["t2-span", "t2-sd"].forEach(function (id) { $(id).addEventListener("input", t2); });
  $("t2-new").addEventListener("click", function () { t2Draw(); t2(); });

  // ---------- Trial 3: more terms always raise R² ----------
  var T3 = { n: 12, sd: 2, maxDeg: 9 };
  function t3Draw() {
    var r = LF.mulberry32(LF.newSeed()), u = LF.uniforms(r, T3.n, 0, 1);
    T3.x = new Float64Array(T3.n); T3.y = new Float64Array(T3.n);
    var z = LF.normals(r, T3.n);
    for (var i = 0; i < T3.n; i++) { T3.x[i] = 10 * (i + u[i]) / T3.n; T3.y[i] = TRUE_B0 + TRUE_B1 * T3.x[i] + T3.sd * z[i]; }
    // Leave-one-out error for every degree, computed once per sample.
    T3.loo = [];
    for (var deg = 1; deg <= T3.maxDeg; deg++) {
      var ss = 0;
      for (var k = 0; k < T3.n; k++) {
        var xs = [], ys = [];
        for (i = 0; i < T3.n; i++) if (i !== k) { xs.push(T3.x[i]); ys.push(T3.y[i]); }
        var e = T3.y[k] - LF.polyfit(xs, ys, deg).predict(T3.x[k]);
        ss += e * e;
      }
      T3.loo.push(Math.sqrt(ss / T3.n));
    }
  }
  function t3() {
    var deg = +$("t3-deg").value, n = T3.n;
    $("t3-deg-out").textContent = deg;
    var f = LF.polyfit(T3.x, T3.y, deg), r2 = LF.r2(T3.y, f.fitted), adj = 1 - (1 - r2) * (n - 1) / (n - f.p);
    var pred = f.predict(12), loo = T3.loo[deg - 1];
    LF.chart($("t3-data"), { w: 420, h: 380, x: [-0.5, 13], y: [-10, 45], xLabel: t("axX"), yLabel: t("axY"),
      draw: function (sX, sY) {
        return '<rect class="shade" x="' + sX(10) + '" y="' + sY(45) + '" width="' + (sX(13) - sX(10)) + '" height="' + (sY(-10) - sY(45)) + '"/>' +
          LF.line("truth", sX, sY, TRUE_B0, TRUE_B1, -0.5, 13) + curvePath(sX, sY, f.predict, -0.5, 13, "fit-curve") + LF.dots(T3.x, T3.y, sX, sY, 5) +
          '<circle class="pt-hi" cx="' + sX(12) + '" cy="' + sY(Math.max(-10, Math.min(45, pred))) + '" r="5"/>';
      },
      over: function (sX, sY, g) { return '<text class="lbl-muted" x="' + (sX(11.5)) + '" y="' + (g.m.t + 16) + '" text-anchor="middle">' + LF.esc(t("lblBeyond")) + '</text>'; } });
    var top = 12;   // fixed, so the high-degree blow-up doesn't flatten the rest
    LF.chart($("t3-loo-chart"), { w: 420, h: 380, x: [0.5, 9.5], y: [0, top], xLabel: t("axDegree"), yLabel: t("axLoo"), xt: 9,
      draw: function (sX, sY) {
        var d = "", s = "";
        T3.loo.forEach(function (v, i) { d += (i ? "L" : "M") + sX(i + 1).toFixed(1) + " " + sY(Math.min(v, top)).toFixed(1); });
        s += '<line class="thresh" x1="' + sX(0.5) + '" x2="' + sX(9.5) + '" y1="' + sY(T3.sd) + '" y2="' + sY(T3.sd) + '"/>';
        s += '<path class="ln-muted" d="' + d + '"/>';
        T3.loo.forEach(function (v, i) { s += '<circle class="' + (i + 1 === deg ? "pt-hi" : "pt") + '" cx="' + sX(i + 1) + '" cy="' + sY(Math.min(v, top)) + '" r="' + (i + 1 === deg ? 6 : 4) + '"/>'; });
        return s;
      },
      over: function (sX, sY) { return '<text class="lbl-muted" x="' + (sX(9.4)) + '" y="' + (sY(T3.sd) - 6) + '" text-anchor="end">' + LF.esc(t("lblNoise")) + '</text>'; } });
    $("t3-r2").textContent = num(r2, 3);
    $("t3-adj").textContent = num(adj, 3);
    $("t3-loo").textContent = num(loo, 2);
    $("t3-pred").textContent = num(pred, 1);
    $("t3-pred").className = "v" + (Math.abs(pred - 25) > 5 ? " bad" : "");
    var vars = { r2: num(r2, 3), adj: num(adj, 3), loo: num(loo, 2), loo1: num(T3.loo[0], 2), pred: num(pred, 1) };
    $("t3-note").innerHTML = t(deg === 1 ? "t3Note1Html" : deg <= 4 ? "t3NoteSomeHtml" : "t3NoteManyHtml", vars);
  }
  $("t3-deg").addEventListener("input", t3);
  $("t3-new").addEventListener("click", function () { t3Draw(); t3(); });

  // ---------- start, and redraw on a language switch ----------
  function renderAll() { t1(); quizRender(); t2(); t3(); LF.seriesNav($("series-nav"), "r-squared"); }
  t2Draw(); t3Draw();
  renderAll();
  document.addEventListener("learnlangchange", renderAll);
}());
