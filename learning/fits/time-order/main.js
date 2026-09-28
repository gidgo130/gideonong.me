// main.js — Time-ordered data (Reading Your Fits, Module 4). Page logic for the three trials.
// Engine: ../../assets/learning.js (LF). Words: strings.js via LI18N.t. All data is simulated.
(function () {
  "use strict";
  var t = LI18N.t, num = LF.num;
  var $ = function (id) { return document.getElementById(id); };
  var radio = function (name) { return document.querySelector('input[name="' + name + '"]:checked').value; };
  function zeroLine(sX, sY, x0, x1) { return '<line class="zero" x1="' + sX(x0) + '" x2="' + sX(x1) + '" y1="' + sY(0) + '" y2="' + sY(0) + '"/>'; }
  function hline(sX, sY, x0, x1, y, cls) { return '<line class="' + cls + '" x1="' + sX(x0) + '" x2="' + sX(x1) + '" y1="' + sY(y) + '" y2="' + sY(y) + '"/>'; }
  function pct(v) { return t("pctOf", { p: num(v, 0) }); }
  function flagCov(el, v) { el.className = "v" + (Math.abs(v - 95) > 4 ? " bad" : ""); }
  function mean(a) { var s = 0; for (var i = 0; i < a.length; i++) s += a[i]; return s / a.length; }
  function sdev(a) { var m = mean(a), v = 0; for (var i = 0; i < a.length; i++) v += (a[i] - m) * (a[i] - m); return Math.sqrt(v / (a.length - 1)); }

  // ---------- Trial 1: autocorrelated residuals ----------
  var T1 = { n: 100, reps: 400, b0: 1, b1: 0.2 };
  function t1Draw() { T1.seed = LF.newSeed(); T1.simSeed = LF.newSeed(); }
  function t1Sample(r, rho) {
    var n = T1.n, x = new Float64Array(n), y = new Float64Array(n), e = LF.ar1(LF.normals(r, n), rho, 1);
    for (var i = 0; i < n; i++) { x[i] = i / 10; y[i] = T1.b0 + T1.b1 * x[i] + e[i]; }
    return { x: x, y: y };
  }
  function t1() {
    var rho = +$("t1-rho").value, n = T1.n;
    $("t1-rho-out").textContent = num(rho, 2);
    var d = t1Sample(LF.mulberry32(T1.seed), rho), f = LF.ols(d.x, d.y), ac = LF.acf(f.resid, 15), dw = LF.durbinWatson(f.resid);
    var r1 = Math.max(0, ac[0]), neff = Math.max(2, Math.round(n * (1 - r1) / (1 + r1)));
    var rs = LF.mulberry32(T1.simSeed), tc = LF.tcrit(n - 2), hit = 0;
    for (var k = 0; k < T1.reps; k++) { var dd = t1Sample(rs, rho), ff = LF.ols(dd.x, dd.y); if (Math.abs(ff.b1 - T1.b1) <= tc * ff.se1) hit++; }
    var cov = hit / T1.reps * 100;
    var yl = Math.max(4, Math.ceil(Math.max.apply(null, Array.from(f.resid).map(Math.abs)) * 1.15));
    LF.chart($("t1-resid"), { w: 420, h: 380, x: [0, n + 1], y: [-yl, yl], xLabel: t("axSample"), yLabel: t("axResidual"),
      draw: function (sX, sY) {
        var s = zeroLine(sX, sY, 0, n + 1), dd = "";
        for (var i = 0; i < n; i++) dd += (i ? "L" : "M") + sX(i + 1).toFixed(1) + " " + sY(f.resid[i]).toFixed(1);
        s += '<path class="ln-muted" d="' + dd + '" stroke-width="1"/>';
        for (i = 0; i < n; i++) s += '<circle class="pt" cx="' + sX(i + 1).toFixed(1) + '" cy="' + sY(f.resid[i]).toFixed(1) + '" r="2.5"/>';
        return s;
      } });
    var band = 2 / Math.sqrt(n);
    LF.chart($("t1-acf"), { w: 420, h: 380, x: [0.3, 15.7], y: [-0.4, 1], xLabel: t("axLag"), yLabel: t("axAcf"), xticks: [1, 3, 5, 7, 9, 11, 13, 15],
      draw: function (sX, sY) {
        var s = zeroLine(sX, sY, 0.3, 15.7) + hline(sX, sY, 0.3, 15.7, band, "thresh") + hline(sX, sY, 0.3, 15.7, -band, "thresh"), bw = (sX(1) - sX(0)) * 0.55;
        ac.forEach(function (v, i) {
          var y0 = sY(Math.max(v, 0)), h = Math.abs(sY(v) - sY(0));
          s += '<rect class="' + (Math.abs(v) > band ? "bar-hi" : "bar") + '" x="' + (sX(i + 1) - bw / 2) + '" y="' + y0 + '" width="' + bw + '" height="' + h + '"/>';
        });
        return s;
      } });
    $("t1-lag1").textContent = num(ac[0], 2); $("t1-lag1").className = "v" + (ac[0] > band ? " bad" : "");
    $("t1-dw").textContent = num(dw, 2); $("t1-dw").className = "v" + (dw < 1.5 ? " bad" : "");
    $("t1-neff").textContent = t("neffFmt", { e: neff, n: n });
    $("t1-cov").textContent = pct(cov); flagCov($("t1-cov"), cov);
    $("t1-note").innerHTML = t(cov >= 91 ? "t1NoteLowHtml" : "t1NoteHighHtml", { c: num(cov, 0), n: n, e: neff });
  }
  $("t1-rho").addEventListener("input", t1);
  $("t1-new").addEventListener("click", function () { t1Draw(); t1(); });

  // ---------- Trial 2: the cooling-curve log trap ----------
  var T2 = { tInf: 22, t0: 80, tau: 4, dt: 0.25, win: 20, reps: 200 };
  T2.n = Math.round(T2.win / T2.dt) + 1;
  function t2Draw() { T2.seed = LF.newSeed(); T2.simSeed = LF.newSeed(); }
  function truthT(tm) { return T2.tInf + (T2.t0 - T2.tInf) * Math.exp(-tm / T2.tau); }
  function t2Sample(r, sd) {
    var tm = new Float64Array(T2.n), y = new Float64Array(T2.n), z = LF.normals(r, T2.n);
    for (var i = 0; i < T2.n; i++) { tm[i] = i * T2.dt; y[i] = truthT(tm[i]) + sd * z[i]; }
    return { t: tm, y: y };
  }
  // Log method: keep T − T∞ > 0, fit ln(T − T∞) = a − t/τ, τ = −1/slope.
  function logFit(d, tInfAssumed) {
    var xs = [], ls = [], kept = [];
    for (var i = 0; i < d.t.length; i++) { var dT = d.y[i] - tInfAssumed; kept.push(dT > 0); if (dT > 0) { xs.push(d.t[i]); ls.push(Math.log(dT)); } }
    var f = LF.ols(xs, ls);
    return { tau: -1 / f.b1, a: f.b0, b1: f.b1, kept: kept, dropped: d.t.length - xs.length };
  }
  function t2() {
    var sd = +$("t2-noise").value, dR = +$("t2-room").value, m = radio("t2m"), tA = T2.tInf + dR;
    $("t2-noise-out").textContent = t("unitC", { v: num(sd, 1) });
    $("t2-room-out").textContent = t("unitCSigned", { s: dR > 0 ? "+" : dR < 0 ? "−" : "", v: num(Math.abs(dR), 1) });
    var d = t2Sample(LF.mulberry32(T2.seed), sd), lg = logFit(d, tA), ex = LF.expFit(d.t, d.y);
    var rs = LF.mulberry32(T2.simSeed), aL = [], aD = [];
    for (var k = 0; k < T2.reps; k++) { var dd = t2Sample(rs, sd), l = logFit(dd, tA); if (isFinite(l.tau) && l.tau > 0) aL.push(l.tau); aD.push(LF.expFit(dd.t, dd.y).tau); }
    var avgL = mean(aL), avgD = mean(aD);
    LF.chart($("t2-log"), { w: 420, h: 380, x: [0, T2.win], y: [-4, 5], xLabel: t("axTime"), yLabel: t("axLn"),
      draw: function (sX, sY) {
        var s = LF.line("truth", sX, sY, Math.log(T2.t0 - T2.tInf), -1 / T2.tau, 0, T2.win) + LF.line("fit", sX, sY, lg.a, lg.b1, 0, T2.win);
        for (var i = 0; i < T2.n; i++) {
          var dT = d.y[i] - tA;
          if (lg.kept[i]) s += '<circle class="pt" cx="' + sX(d.t[i]).toFixed(1) + '" cy="' + sY(Math.max(-4, Math.log(dT))).toFixed(1) + '" r="3"/>';
          else s += '<circle class="pt-ring" cx="' + sX(d.t[i]).toFixed(1) + '" cy="' + sY(-3.8).toFixed(1) + '" r="3"/>';
        }
        return s;
      } });
    var isD = m === "direct";
    LF.chart($("t2-curve"), { w: 420, h: 380, x: [0, T2.win], y: [15, 85], xLabel: t("axTime"), yLabel: t("axTemp"),
      draw: function (sX, sY) {
        var path = function (fn, cls) { var p = ""; for (var k2 = 0; k2 <= 160; k2++) { var xv = T2.win * k2 / 160; p += (k2 ? "L" : "M") + sX(xv).toFixed(1) + " " + sY(fn(xv)).toFixed(1); } return '<path class="' + cls + '" d="' + p + '"/>'; };
        var fit = isD ? function (x) { return ex.B + ex.A * Math.exp(-x / ex.tau); } : function (x) { return tA + Math.exp(lg.a + lg.b1 * x); };
        return LF.dots(d.t, d.y, sX, sY, 3) + path(truthT, "truth-curve") + path(fit, isD ? "fix-curve" : "fit-curve");
      } });
    $("t2-tlog").textContent = t("unitMin", { v: num(lg.tau, 2) }); $("t2-tlog").className = "v" + (Math.abs(lg.tau - T2.tau) / T2.tau > 0.08 ? " bad" : "");
    $("t2-tdir").textContent = t("unitMin", { v: num(ex.tau, 2) });
    $("t2-drop").textContent = t("droppedFmt", { d: lg.dropped, n: T2.n }); $("t2-drop").className = "v" + (lg.dropped ? " bad" : "");
    $("t2-alog").textContent = t("unitMin", { v: num(avgL, 2) }); $("t2-alog").className = "v" + (Math.abs(avgL - T2.tau) / T2.tau > 0.05 ? " bad" : "");
    $("t2-adir").textContent = t("unitMin", { v: num(avgD, 2) }); $("t2-adir").className = "v" + (Math.abs(avgD - T2.tau) / T2.tau > 0.05 ? " bad" : "");
    $("t2-true").textContent = t("unitMin", { v: num(T2.tau, 1) });
    var v = { tau: num(isD ? ex.tau : lg.tau, 2), avg: num(isD ? avgD : avgL, 2), tlog: num(lg.tau, 2), alog: num(avgL, 2) };
    $("t2-note").innerHTML = t(sd === 0 && dR === 0 ? "t2NoteCleanHtml" : isD ? "t2NoteDirHtml" : "t2NoteLogHtml", v);
  }
  document.querySelectorAll('input[name="t2m"]').forEach(function (el) { el.addEventListener("change", t2); });
  ["t2-noise", "t2-room"].forEach(function (id) { $(id).addEventListener("input", t2); });
  $("t2-new").addEventListener("click", function () { t2Draw(); t2(); });

  // ---------- Trial 3: count runs, not samples ----------
  var T3 = { runs: 5, per: 60, mu: 50, reps: 400, show: 20 };
  function t3Draw() { T3.seed = LF.newSeed(); T3.simSeed = LF.newSeed(); }
  function t3Sample(r, runSd, rho) {
    var all = [], means = [], off = LF.normals(r, T3.runs);
    for (var j = 0; j < T3.runs; j++) {
      var e = LF.ar1(LF.normals(r, T3.per), rho, 1), run = [];
      for (var i = 0; i < T3.per; i++) { var v = T3.mu + runSd * off[j] + e[i]; run.push(v); all.push(v); }
      means.push(mean(run));
    }
    return { all: all, means: means };
  }
  function ranges(d) {
    var N = d.all.length;
    return {
      sample: { m: mean(d.all), h: LF.tcrit(N - 1) * sdev(d.all) / Math.sqrt(N) },
      run: { m: mean(d.means), h: 2.776445 * sdev(d.means) / Math.sqrt(T3.runs) }   // t(0.975, 4)
    };
  }
  function t3() {
    var runSd = +$("t3-run").value, rho = +$("t3-rho").value, c = radio("t3c");
    $("t3-run-out").textContent = num(runSd, 2); $("t3-rho-out").textContent = num(rho, 2);
    var d = t3Sample(LF.mulberry32(T3.seed), runSd, rho), R = ranges(d)[c];
    var rs = LF.mulberry32(T3.simSeed), hs = 0, hr = 0, shown = [];
    for (var k = 0; k < T3.reps; k++) {
      var g = ranges(t3Sample(rs, runSd, rho));
      if (Math.abs(g.sample.m - T3.mu) <= g.sample.h) hs++;
      if (Math.abs(g.run.m - T3.mu) <= g.run.h) hr++;
      if (k < T3.show) shown.push(g[c]);
    }
    var cs = hs / T3.reps * 100, cr = hr / T3.reps * 100, total = T3.runs * T3.per;
    var lo = Math.floor(Math.min.apply(null, d.all) - 0.5), hi = Math.ceil(Math.max.apply(null, d.all) + 0.5);
    LF.chart($("t3-data"), { w: 420, h: 380, x: [0, total + 1], y: [lo, hi], xLabel: t("axSample"), yLabel: t("axValue"), xticks: [0, 60, 120, 180, 240, 300],
      draw: function (sX, sY) {
        var s = hline(sX, sY, 0, total + 1, T3.mu, "vline-truth");
        for (var j = 0; j < T3.runs; j++) {
          if (j % 2) s += '<rect class="shade" x="' + sX(j * T3.per + 0.5) + '" y="' + sY(hi) + '" width="' + (sX(T3.per) - sX(0)) + '" height="' + (sY(lo) - sY(hi)) + '"/>';
          for (var i = 0; i < T3.per; i++) { var q = j * T3.per + i; s += '<circle class="pt" cx="' + sX(q + 1).toFixed(1) + '" cy="' + sY(d.all[q]).toFixed(1) + '" r="2"/>'; }
          s += '<line class="vline-fit" x1="' + sX(j * T3.per + 4) + '" x2="' + sX((j + 1) * T3.per - 3) + '" y1="' + sY(d.means[j]) + '" y2="' + sY(d.means[j]) + '"/>';
        }
        return s;
      } });
    var span = Math.max(1, Math.ceil(Math.max.apply(null, shown.map(function (g) { return Math.abs(g.m - T3.mu) + g.h; })) * 1.1 * 2) / 2);
    LF.chart($("t3-ci"), { w: 420, h: 380, x: [0, T3.show + 1], y: [T3.mu - span, T3.mu + span], xLabel: t("axRepeat"), yLabel: t("axValue"), xticks: [1, 5, 10, 15, 20],
      draw: function (sX, sY) {
        var s = hline(sX, sY, 0, T3.show + 1, T3.mu, "vline-truth");
        shown.forEach(function (g, i) {
          var miss = Math.abs(g.m - T3.mu) > g.h;
          s += '<line class="' + (miss ? "ci-bar" : "ci-bar-fix") + '" x1="' + sX(i + 1) + '" x2="' + sX(i + 1) + '" y1="' + sY(g.m - g.h) + '" y2="' + sY(g.m + g.h) + '"/>' +
            '<circle class="' + (miss ? "pt-hi" : "pt-fix") + '" cx="' + sX(i + 1) + '" cy="' + sY(g.m) + '" r="3.5"/>';
        });
        return s;
      } });
    $("t3-est").textContent = num(R.m, 2);
    $("t3-range").textContent = t("rangeFmt", { m: num(R.m, 2), h: num(R.h, 2) });
    $("t3-cs").textContent = pct(cs); flagCov($("t3-cs"), cs);
    $("t3-cr").textContent = pct(cr); flagCov($("t3-cr"), cr);
    var v = { h: num(R.h, 2), c: num(c === "run" ? cr : cs, 0), cs: num(cs, 0) };
    $("t3-note").innerHTML = t(runSd === 0 && rho === 0 ? "t3NoteSameHtml" : c === "run" ? "t3NoteRunHtml" : "t3NoteSampleHtml", runSd === 0 && rho === 0 ? { cs: num(cs, 0), c: num(cr, 0) } : v);
  }
  document.querySelectorAll('input[name="t3c"]').forEach(function (el) { el.addEventListener("change", t3); });
  ["t3-run", "t3-rho"].forEach(function (id) { $(id).addEventListener("input", t3); });
  $("t3-new").addEventListener("click", function () { t3Draw(); t3(); });

  // ---------- start, and redraw on a language switch ----------
  function renderAll() { t1(); t2(); t3(); LF.seriesNav($("series-nav"), "time-order"); }
  t1Draw(); t2Draw(); t3Draw();
  renderAll();
  document.addEventListener("learnlangchange", renderAll);
}());
