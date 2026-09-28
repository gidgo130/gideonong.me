// main.js — Reading a residual plot (Reading Your Fits, Module 2). Page logic for the three
// trials and the "Name that pattern" quiz. Engine: ../../assets/learning.js (LF).
// Words: strings.js via LI18N.t. All data is simulated.
(function () {
  "use strict";
  var t = LI18N.t, num = LF.num;
  var $ = function (id) { return document.getElementById(id); };
  var radio = function (name) { return document.querySelector('input[name="' + name + '"]:checked').value; };
  var TRUE_B0 = 1, TRUE_B1 = 2;
  var PNAME = { none: "pNone", curve: "pCurve", fan: "pFan", drift: "pDrift", outlier: "pOutlier" };
  function fmtStatic() { document.querySelectorAll("[data-num]").forEach(function (el) { el.textContent = num(+el.getAttribute("data-num"), 2); }); }
  function flag(el, bad) { el.className = "v" + (bad ? " bad" : ""); }
  // Symmetric residual axis that always shows the whole band: at least ±min, in steps of `step`.
  function residRange(r, min, step) {
    min = min || 8; step = step || 4;
    var m = 0; for (var i = 0; i < r.length; i++) m = Math.max(m, Math.abs(r[i]));
    var lim = Math.max(min, Math.ceil(m * 1.15 / step) * step);
    return [-lim, lim];
  }
  function zeroLine(sX, sY, x0, x1) { return '<line class="zero" x1="' + sX(x0) + '" x2="' + sX(x1) + '" y1="' + sY(0) + '" y2="' + sY(0) + '"/>'; }

  // ---------- one simulated dataset with a hidden problem ----------
  // draws: { x, e, t } share random numbers across slider moves. Run order = array order;
  // x values are in random order, so time and x are unrelated.
  function makeDraws(n, seed) {
    var r = LF.mulberry32(seed), x = LF.uniforms(r, n, 0, 10), e = LF.normals(r, n), out = 0, best = 99;
    for (var i = 0; i < n; i++) if (Math.abs(x[i] - 8) < best) { best = Math.abs(x[i] - 8); out = i; }
    return { n: n, x: x, e: e, out: out };
  }
  function makeY(d, pattern, sev) {
    var y = new Float64Array(d.n);
    for (var k = 0; k < d.n; k++) {
      var x = d.x[k], tt = k / (d.n - 1), e = d.e[k];
      var v = TRUE_B0 + TRUE_B1 * x;
      if (pattern === "curve") v += 0.45 * sev * ((x - 5) * (x - 5) - 25 / 3);
      if (pattern === "fan") e *= 1 + sev * 0.6 * x;
      if (pattern === "drift") v += sev * 10 * tt;
      if (pattern === "outlier" && k === d.out) v += sev * 14;
      y[k] = v + e;
    }
    return y;
  }
  function residChart(svg, f, axis, n, small) {
    var yr = residRange(f.resid);
    if (axis === "order") {
      LF.chart(svg, { w: small ? 400 : 420, h: small ? 280 : 380, x: [0, n + 1], y: yr, xLabel: t("axRunNumber"), yLabel: t("axResidual"),
        draw: function (sX, sY) { var s = zeroLine(sX, sY, 0, n + 1); for (var k = 0; k < n; k++) s += '<circle class="pt" cx="' + sX(k + 1).toFixed(1) + '" cy="' + sY(f.resid[k]).toFixed(1) + '" r="4"/>'; return s; } });
    } else {
      // x axis fitted to the fitted values, in steps of 5, so the band fills the plot.
      var lo = Infinity, hi = -Infinity;
      for (var i = 0; i < n; i++) { lo = Math.min(lo, f.fitted[i]); hi = Math.max(hi, f.fitted[i]); }
      var x0 = Math.floor((lo - 1) / 5) * 5, x1 = Math.ceil((hi + 1) / 5) * 5;
      LF.chart(svg, { w: small ? 400 : 420, h: small ? 280 : 380, x: [x0, x1], y: yr, xLabel: t("axFittedY"), yLabel: t("axResidual"),
        draw: function (sX, sY) { return zeroLine(sX, sY, x0, x1) + LF.dots(f.fitted, f.resid, sX, sY); } });
    }
  }

  // ---------- Trial 1: pattern gallery ----------
  var T1 = {};
  function t1Draw() { T1.d = makeDraws(40, LF.newSeed()); }
  function t1() {
    var p = radio("t1p"), sev = +$("t1-sev").value, axis = radio("t1a");
    $("t1-sev-out").textContent = num(sev, 2);
    var y = makeY(T1.d, p, sev), x = T1.d.x, f = LF.ols(x, y);
    LF.chart($("t1-scatter"), { w: 420, h: 380, x: [-1, 11], y: [-8, 38], xLabel: t("axMeasuredX"), yLabel: t("axMeasuredY"),
      draw: function (sX, sY) { return LF.dots(x, y, sX, sY) + LF.line("truth", sX, sY, TRUE_B0, TRUE_B1, -1, 11) + LF.line("fit", sX, sY, f.b0, f.b1, -1, 11); } });
    residChart($("t1-resid"), f, axis, T1.d.n, false);
    $("t1-resid-cap").innerHTML = t(axis === "order" ? "t1ResidCapOrderHtml" : "t1ResidCapFittedHtml");
    $("t1-b").textContent = num(f.b1);
    $("t1-r2").textContent = num(LF.r2(y, f.fitted), 3);
    var key;
    if (p === "none") key = "t1NoteNoneHtml";
    else if (sev < 0.15) key = "t1NoteWeakHtml";
    else if (p === "drift") key = axis === "order" ? "t1NoteDriftOrderHtml" : "t1NoteDriftFittedHtml";
    else key = { curve: "t1NoteCurveHtml", fan: "t1NoteFanHtml", outlier: "t1NoteOutlierHtml" }[p];
    $("t1-note").innerHTML = t(key);
  }
  document.querySelectorAll('input[name="t1p"], input[name="t1a"]').forEach(function (el) { el.addEventListener("change", t1); });
  $("t1-sev").addEventListener("input", t1);
  $("t1-new").addEventListener("click", function () { t1Draw(); t1(); });

  // ---------- Quiz: name that pattern ----------
  var QZ = { right: 0, total: 0, answered: false, pattern: null };
  var PATTERNS = ["none", "curve", "fan", "drift", "outlier"];
  var QSEV = { none: 0, curve: 0.8, fan: 0.8, drift: 1, outlier: 1 };
  function qzNew() {
    var r = LF.mulberry32(LF.newSeed()), p;
    do { p = PATTERNS[Math.floor(r() * PATTERNS.length)]; } while (p === QZ.pattern);
    QZ.pattern = p; QZ.d = makeDraws(40, LF.newSeed()); QZ.answered = false;
    $("quiz").querySelectorAll(".opts button").forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
    $("quiz-answer").hidden = true;
    qzDraw();
  }
  function qzDraw() {
    var y = makeY(QZ.d, QZ.pattern, QSEV[QZ.pattern]), f = LF.ols(QZ.d.x, y);
    residChart($("qz-fitted"), f, "fitted", QZ.d.n, true);
    residChart($("qz-order"), f, "order", QZ.d.n, true);
    qzText();
  }
  function qzText() {
    $("quiz-score").textContent = QZ.total ? t("quizScore", { right: QZ.right, total: QZ.total }) : "";
    if (!QZ.answered) return;
    var name = t(PNAME[QZ.pattern]).toLowerCase();
    var why = t("quizWhy" + QZ.pattern.charAt(0).toUpperCase() + QZ.pattern.slice(1));
    var a = $("quiz-answer");
    a.hidden = false;
    a.innerHTML = t(QZ.lastRight ? "quizRightHtml" : "quizWrongHtml", { name: LF.esc(name) }) + LF.esc(why);
  }
  $("quiz").querySelectorAll(".opts button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (QZ.answered) return;
      $("quiz").querySelectorAll(".opts button").forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
      QZ.answered = true; QZ.total++;
      QZ.lastRight = btn.getAttribute("data-a") === QZ.pattern;
      if (QZ.lastRight) QZ.right++;
      qzText();
    });
  });
  $("quiz-new").addEventListener("click", qzNew);

  // ---------- Trial 2: cooling curve, line vs exponential ----------
  var T2 = { tInf: 22, t0: 80, tau: 4, dt: 0.25, max: 20 };
  function t2Draw() { var r = LF.mulberry32(LF.newSeed()); T2.z = LF.normals(r, Math.round(T2.max / T2.dt) + 1); }
  function truthT(tm) { return T2.tInf + (T2.t0 - T2.tInf) * Math.exp(-tm / T2.tau); }
  function t2() {
    var model = radio("t2m"), sd = +$("t2-noise").value, win = +$("t2-win").value;
    $("t2-noise-out").textContent = t("unitC", { v: num(sd, 1) });
    $("t2-win-out").textContent = t("unitMin", { v: num(win, 1) });
    var n = Math.round(win / T2.dt) + 1, tm = new Float64Array(n), y = new Float64Array(n);
    for (var i = 0; i < n; i++) { tm[i] = i * T2.dt; y[i] = truthT(tm[i]) + sd * T2.z[i]; }
    var f, p, curve;
    if (model === "exp") {
      f = LF.expFit(tm, y); p = 3;
      curve = function (x) { return f.B + f.A * Math.exp(-x / f.tau); };
    } else {
      var lf = LF.ols(tm, y); f = { fitted: lf.fitted, resid: lf.resid }; p = 2;
      curve = function (x) { return lf.b0 + lf.b1 * x; };
    }
    var sse = 0; for (i = 0; i < n; i++) sse += f.resid[i] * f.resid[i];
    var s = Math.sqrt(sse / (n - p)), r2 = LF.r2(y, f.fitted);
    // A smooth curve as an SVG path, sampled at 121 points across the recording window.
    function curvePath(sX, sY, fn, cls) {
      var d = "";
      for (var k = 0; k <= 120; k++) { var xv = win * k / 120; d += (k ? "L" : "M") + sX(xv).toFixed(1) + " " + sY(fn(xv)).toFixed(1); }
      return '<path class="' + cls + '" d="' + d + '"/>';
    }
    LF.chart($("t2-data"), { w: 420, h: 380, x: [0, win], y: [15, 85], xLabel: t("axTime"), yLabel: t("axTemp"),
      draw: function (sX, sY) {
        return LF.dots(tm, y, sX, sY, 3) + curvePath(sX, sY, truthT, "truth-curve") + curvePath(sX, sY, curve, model === "exp" ? "fix-curve" : "fit-curve");
      } });
    LF.chart($("t2-resid"), { w: 420, h: 380, x: [0, win], y: residRange(f.resid, 2, 1), xLabel: t("axTime"), yLabel: t("axResidC"),
      draw: function (sX, sY) { return zeroLine(sX, sY, 0, win) + LF.dots(tm, f.resid, sX, sY, 3); } });
    $("t2-r2").textContent = num(r2, 3);
    $("t2-s").textContent = t("unitC", { v: num(s, 2) });
    $("t2-tau").textContent = model === "exp" ? t("unitMin", { v: num(f.tau, 2) }) : t("dash");
    $("t2-truetau").textContent = t("unitMin", { v: num(T2.tau, 1) });
    $("t2-note").innerHTML = model === "exp"
      ? t(sd === 0 ? "t2NoteExpNoNoiseHtml" : "t2NoteExpHtml", { s: num(s, 2), tau: num(f.tau, 2) })
      : t("t2NoteLineHtml", { r2: num(r2, 3) });
  }
  document.querySelectorAll('input[name="t2m"]').forEach(function (el) { el.addEventListener("change", t2); });
  ["t2-noise", "t2-win"].forEach(function (id) { $(id).addEventListener("input", t2); });
  $("t2-new").addEventListener("click", function () { t2Draw(); t2(); });

  // ---------- Trial 3: one point steering the line ----------
  var T3 = { n0: 20 };
  function t3Draw() { var r = LF.mulberry32(LF.newSeed()); T3.x = LF.uniforms(r, T3.n0, 0, 10); T3.e = LF.normals(r, T3.n0); }
  function t3() {
    var xp = +$("t3-x").value, off = +$("t3-y").value;
    $("t3-x-out").textContent = num(xp, 1);
    $("t3-y-out").textContent = (off > 0 ? "+" : off < 0 ? "−" : "") + num(Math.abs(off), 1);
    var n = T3.n0 + 1, x = new Float64Array(n), y = new Float64Array(n);
    for (var i = 0; i < T3.n0; i++) { x[i] = T3.x[i]; y[i] = TRUE_B0 + TRUE_B1 * x[i] + T3.e[i]; }
    x[n - 1] = xp; y[n - 1] = TRUE_B0 + TRUE_B1 * xp + off;
    var inf = LF.influence(x, y), f = inf.fit, g = LF.ols(x.subarray(0, T3.n0), y.subarray(0, T3.n0));
    var P = n - 1, h = inf.h[P], r = inf.r[P], D = inf.D[P], hTyp = 2 * 2 / n, dTyp = 4 / n;
    LF.chart($("t3-data"), { w: 420, h: 380, x: [-1, 26], y: [-18, 58], xLabel: t("axMeasuredX"), yLabel: t("axMeasuredY"),
      draw: function (sX, sY) {
        return LF.dots(x.subarray(0, T3.n0), y.subarray(0, T3.n0), sX, sY) +
          LF.line("truth", sX, sY, TRUE_B0, TRUE_B1, -1, 26) + LF.line("fix", sX, sY, g.b0, g.b1, -1, 26) + LF.line("fit", sX, sY, f.b0, f.b1, -1, 26) +
          '<circle class="pt-mark" cx="' + sX(xp) + '" cy="' + sY(y[P]) + '" r="4.5"/><circle class="pt-ring" cx="' + sX(xp) + '" cy="' + sY(y[P]) + '" r="9"/>';
      } });
    var top = Math.max(0.5, Math.max.apply(null, Array.from(inf.D)) * 1.15);
    LF.chart($("t3-cook-chart"), { w: 420, h: 380, x: [0, n + 1], y: [0, top], xLabel: t("axPoint"), yLabel: t("axCook"), xt: 5,
      draw: function (sX, sY) {
        var s = "", bw = (sX(1) - sX(0)) * 0.7;
        for (var k = 0; k < n; k++) s += '<rect class="' + (k === P ? "bar-hi" : "bar") + '" x="' + (sX(k + 1) - bw / 2) + '" y="' + sY(inf.D[k]) + '" width="' + bw + '" height="' + (sY(0) - sY(inf.D[k])) + '"/>';
        return s + '<line class="thresh" x1="' + sX(0) + '" x2="' + sX(n + 1) + '" y1="' + sY(dTyp) + '" y2="' + sY(dTyp) + '"/>';
      } });
    $("t3-with").textContent = num(f.b1);
    $("t3-without").textContent = num(g.b1);
    $("t3-lev-lbl").textContent = t("roLev", { typ: num(hTyp, 2) });
    $("t3-lev").textContent = num(h, 2); flag($("t3-lev"), h > hTyp);
    $("t3-stud").textContent = (r < 0 ? "−" : "") + num(Math.abs(r), 2); flag($("t3-stud"), Math.abs(r) > 2.5);
    $("t3-cook").textContent = num(D, 2); flag($("t3-cook"), D > dTyp);
    var d = (Math.abs(f.b1 - g.b1) / Math.abs(g.b1) * 100).toFixed(0), key;
    if (h > hTyp && Math.abs(r) > 2) key = "t3NoteInfluentialHtml";
    else if (Math.abs(r) > 2.5) key = "t3NoteOutlierHtml";
    else if (h > hTyp) key = "t3NoteLeverHtml";
    else key = "t3NoteOrdinaryHtml";
    $("t3-note").innerHTML = t(key, { d: d });
  }
  ["t3-x", "t3-y"].forEach(function (id) { $(id).addEventListener("input", t3); });
  $("t3-new").addEventListener("click", function () { t3Draw(); t3(); });

  // ---------- start, and redraw on a language switch ----------
  function renderAll() { fmtStatic(); t1(); qzDraw(); t2(); t3(); LF.seriesNav($("series-nav"), "residual-plots"); }
  t1Draw(); t2Draw(); t3Draw();
  QZ.pattern = null; QZ.d = makeDraws(40, LF.newSeed());
  QZ.pattern = PATTERNS[1 + (LF.newSeed() % 4)];
  renderAll();
  document.addEventListener("learnlangchange", renderAll);
}());
