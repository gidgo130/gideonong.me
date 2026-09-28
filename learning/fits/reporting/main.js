// main.js — Using and reporting a fit (Reading Your Fits, Module 6). Page logic for the three trials.
// Engine: ../../assets/learning.js (LF). Words: strings.js via LI18N.t. All data is simulated.
(function () {
  "use strict";
  var t = LI18N.t, num = LF.num;
  var $ = function (id) { return document.getElementById(id); };
  function curvePath(sX, sY, fn, x0, x1, cls) {
    var d = "";
    for (var k = 0; k <= 120; k++) { var xv = x0 + (x1 - x0) * k / 120; d += (k ? "L" : "M") + sX(xv).toFixed(1) + " " + sY(fn(xv)).toFixed(1); }
    return '<path class="' + cls + '" d="' + d + '"/>';
  }
  function bandPath(sX, sY, lo, hi, x0, x1, cls) {
    var top = "", bot = "", k, xv;
    for (k = 0; k <= 80; k++) { xv = x0 + (x1 - x0) * k / 80; top += (k ? "L" : "M") + sX(xv).toFixed(1) + " " + sY(hi(xv)).toFixed(1); }
    for (k = 80; k >= 0; k--) { xv = x0 + (x1 - x0) * k / 80; bot += "L" + sX(xv).toFixed(1) + " " + sY(lo(xv)).toFixed(1); }
    return '<path class="' + cls + '" d="' + top + bot + 'Z"/>';
  }
  function sdev(a) { var m = 0, v = 0, i; for (i = 0; i < a.length; i++) m += a[i]; m /= a.length; for (i = 0; i < a.length; i++) v += (a[i] - m) * (a[i] - m); return Math.sqrt(v / (a.length - 1)); }
  function pm(h, d) { return t("pmFmt", { h: num(h, d === undefined ? 2 : d) }); }

  // ---------- Trial 1: confidence vs prediction band ----------
  var T1 = { n: 15, sd: 2, b0: 1, b1: 2, X0: -5, X1: 20 };
  function t1Draw() {
    var r = LF.mulberry32(LF.newSeed()), u = LF.uniforms(r, T1.n, 0, 1), z = LF.normals(r, T1.n);
    T1.x = new Float64Array(T1.n); T1.y = new Float64Array(T1.n);
    for (var i = 0; i < T1.n; i++) { T1.x[i] = 10 * (i + u[i]) / T1.n; T1.y[i] = T1.b0 + T1.b1 * T1.x[i] + T1.sd * z[i]; }
    T1.f = LF.ols(T1.x, T1.y);
  }
  function t1() {
    var x0 = +$("t1-x").value, f = T1.f, b = LF.bands(T1.x, f, x0);
    var xlo = Math.min.apply(null, T1.x), xhi = Math.max.apply(null, T1.x), inside = x0 >= xlo && x0 <= xhi;
    $("t1-x-out").textContent = num(x0, 1);
    var ci = function (x) { return LF.bands(T1.x, f, x).ci; }, pi = function (x) { return LF.bands(T1.x, f, x).pi; }, yh = function (x) { return f.b0 + f.b1 * x; };
    // Shaded strip from x = a to c, spanning y = lo to hi.
    var shadeY = function (sX, sY, a, c, lo, hi) { return '<rect class="shade" x="' + sX(a) + '" y="' + sY(hi) + '" width="' + (sX(c) - sX(a)) + '" height="' + (sY(lo) - sY(hi)) + '"/>'; };
    var shade = function (sX, sY, a, c) { return shadeY(sX, sY, a, c, -25, 55); };
    LF.chart($("t1-data"), { w: 420, h: 380, x: [T1.X0, T1.X1], y: [-25, 55], xLabel: t("axX"), yLabel: t("axY"),
      draw: function (sX, sY) {
        return shade(sX, sY, T1.X0, xlo) + shade(sX, sY, xhi, T1.X1) +
          bandPath(sX, sY, function (x) { return yh(x) - pi(x); }, function (x) { return yh(x) + pi(x); }, T1.X0, T1.X1, "band-pi") +
          bandPath(sX, sY, function (x) { return yh(x) - ci(x); }, function (x) { return yh(x) + ci(x); }, T1.X0, T1.X1, "band-ci") +
          LF.line("truth", sX, sY, T1.b0, T1.b1, T1.X0, T1.X1) + LF.line("fit", sX, sY, f.b0, f.b1, T1.X0, T1.X1) + LF.dots(T1.x, T1.y, sX, sY) +
          '<line class="thresh" x1="' + sX(x0) + '" x2="' + sX(x0) + '" y1="' + sY(-25) + '" y2="' + sY(55) + '"/>' +
          '<line class="ci-bar" x1="' + sX(x0) + '" x2="' + sX(x0) + '" y1="' + sY(b.y - b.pi) + '" y2="' + sY(b.y + b.pi) + '" style="stroke: var(--pt)"/>' +
          '<line class="ci-bar" x1="' + sX(x0) + '" x2="' + sX(x0) + '" y1="' + sY(b.y - b.ci) + '" y2="' + sY(b.y + b.ci) + '"/>';
      },
      over: function (sX, sY, g) { return '<text class="lbl-muted" x="' + (g.m.l + 6) + '" y="' + (g.m.t + 16) + '">' + LF.esc(t("lblOutside")) + '</text>'; } });
    var top = Math.ceil(pi(T1.X1) * 1.1);
    LF.chart($("t1-width"), { w: 420, h: 380, x: [T1.X0, T1.X1], y: [0, top], xLabel: t("axX"), yLabel: t("axHalf"),
      draw: function (sX, sY) {
        return shadeY(sX, sY, T1.X0, xlo, 0, top) + shadeY(sX, sY, xhi, T1.X1, 0, top) +
          curvePath(sX, sY, pi, T1.X0, T1.X1, "ln-muted") + curvePath(sX, sY, ci, T1.X0, T1.X1, "fit-curve") +
          '<line class="thresh" x1="' + sX(x0) + '" x2="' + sX(x0) + '" y1="' + sY(0) + '" y2="' + sY(top) + '"/>';
      },
      over: function (sX, sY) {
        return '<text class="lbl-muted" x="' + sX(T1.X1 - 0.3) + '" y="' + (sY(pi(T1.X1)) + 16) + '" text-anchor="end">' + LF.esc(t("lblPi")) + '</text>' +
          '<text class="lbl-fit" x="' + sX(T1.X1 - 0.3) + '" y="' + (sY(ci(T1.X1)) + 16) + '" text-anchor="end">' + LF.esc(t("lblCi")) + '</text>';
      } });
    $("t1-y").textContent = num(b.y, 1);
    $("t1-ci").textContent = pm(b.ci, 1);
    $("t1-pi").textContent = pm(b.pi, 1);
    $("t1-in").textContent = t(inside ? "yes" : "no"); $("t1-in").className = "v" + (inside ? "" : " bad");
    var d = inside ? 0 : x0 < xlo ? xlo - x0 : x0 - xhi;
    $("t1-note").innerHTML = t(inside ? "t1NoteInHtml" : "t1NoteOutHtml", { ci: num(b.ci, 1), pi: num(b.pi, 1), y: num(b.y, 1), d: num(d, 1) });
    t3();
  }
  $("t1-x").addEventListener("input", t1);
  $("t1-new").addEventListener("click", function () { t1Draw(); t1(); });

  // ---------- Trial 2: uncertainty of the zero crossing ----------
  var T2 = { n: 12, sd: 1, slope: 2, reps: 400, boots: 400 };
  function t2Draw() { T2.seed = LF.newSeed(); T2.simSeed = LF.newSeed(); T2.bootSeed = LF.newSeed(); }
  // Data span [c, c + 5]; the true line y = 2(x − c) crosses zero at x = c, the data's left edge.
  function t2Sample(r, c) {
    var u = LF.uniforms(r, T2.n, 0, 1), z = LF.normals(r, T2.n), x = new Float64Array(T2.n), y = new Float64Array(T2.n);
    for (var i = 0; i < T2.n; i++) { x[i] = c + 5 * (i + u[i]) / T2.n; y[i] = T2.slope * (x[i] - c) + T2.sd * z[i]; }
    return { x: x, y: y };
  }
  // Crossing x0 = −b0/b1 and its standard error with and without the slope–intercept covariance.
  function crossing(x, f) {
    var n = x.length, mx = 0, i, sxx = 0;
    for (i = 0; i < n; i++) mx += x[i];
    mx /= n;
    for (i = 0; i < n; i++) sxx += (x[i] - mx) * (x[i] - mx);
    var s2 = f.s * f.s, v0 = s2 * (1 / n + mx * mx / sxx), v1 = s2 / sxx, c01 = -mx * s2 / sxx, x0 = -f.b0 / f.b1;
    return { x0: x0, naive: Math.sqrt(v0 + x0 * x0 * v1) / Math.abs(f.b1), delta: Math.sqrt(v0 + 2 * x0 * c01 + x0 * x0 * v1) / Math.abs(f.b1) };
  }
  function t2() {
    var d = +$("t2-d").value, tc = LF.tcrit(T2.n - 2);
    $("t2-d-out").textContent = num(d, 0);
    var s = t2Sample(LF.mulberry32(T2.seed), d), f = LF.ols(s.x, s.y), c = crossing(s.x, f);
    var rs = LF.mulberry32(T2.simSeed), reps = [];
    for (var k = 0; k < T2.reps; k++) { var ss = t2Sample(rs, d); reps.push(crossing(ss.x, LF.ols(ss.x, ss.y)).x0); }
    var rb = LF.mulberry32(T2.bootSeed), boots = [], bx = new Float64Array(T2.n), by = new Float64Array(T2.n);
    for (k = 0; k < T2.boots; k++) {
      for (var i = 0; i < T2.n; i++) { var j = Math.floor(rb() * T2.n); bx[i] = s.x[j]; by[i] = s.y[j]; }
      var fb = LF.ols(bx, by); if (isFinite(fb.b1) && fb.b1 !== 0) boots.push(-fb.b0 / fb.b1);
    }
    var hN = tc * c.naive, hD = tc * c.delta, hB = 1.96 * sdev(boots), hA = 1.96 * sdev(reps);
    var xl = Math.min(0, d - hN - 1), xr = d + 6;
    LF.chart($("t2-data"), { w: 420, h: 380, x: [xl, xr], y: [-8, 14], xLabel: t("axX"), yLabel: t("axY"),
      draw: function (sX, sY) {
        var y0 = sY(0);
        return '<line class="zero" x1="' + sX(xl) + '" x2="' + sX(xr) + '" y1="' + y0 + '" y2="' + y0 + '"/>' +
          LF.line("truth", sX, sY, -T2.slope * d, T2.slope, xl, xr) + LF.line("fit", sX, sY, f.b0, f.b1, xl, xr) + LF.dots(s.x, s.y, sX, sY) +
          '<line class="ci-bar" x1="' + sX(c.x0 - hN) + '" x2="' + sX(c.x0 + hN) + '" y1="' + (y0 - 10) + '" y2="' + (y0 - 10) + '"/>' +
          '<line class="ci-bar-fix" x1="' + sX(c.x0 - hD) + '" x2="' + sX(c.x0 + hD) + '" y1="' + (y0 + 10) + '" y2="' + (y0 + 10) + '"/>' +
          '<circle class="pt-mark" cx="' + sX(c.x0) + '" cy="' + y0 + '" r="4.5"/>';
      } });
    var lo = d - Math.max(hN, hA) * 1.3, hi = d + Math.max(hN, hA) * 1.3, nb = 40, bw = (hi - lo) / nb, counts = new Array(nb).fill(0);
    reps.forEach(function (v) { var q = Math.floor((v - lo) / bw); if (q >= 0 && q < nb) counts[q]++; });
    var top = Math.max.apply(null, counts) * 1.35 || 1;
    LF.chart($("t2-hist"), { w: 420, h: 380, x: [lo, hi], y: [0, top], xLabel: t("axCross"), yLabel: t("axRepeats"), noY: true,
      draw: function (sX, sY) {
        var out = "";
        counts.forEach(function (v, q) { if (v) out += '<rect class="bar" x="' + (sX(lo + q * bw) + 0.5) + '" y="' + sY(v) + '" width="' + Math.max(1, sX(lo + bw) - sX(lo) - 1) + '" height="' + (sY(0) - sY(v)) + '"/>'; });
        var yN = sY(top * 0.92), yD = sY(top * 0.84);
        out += '<line class="ci-bar" x1="' + sX(Math.max(lo, d - hN)) + '" x2="' + sX(Math.min(hi, d + hN)) + '" y1="' + yN + '" y2="' + yN + '"/>';
        out += '<line class="ci-bar-fix" x1="' + sX(d - hD) + '" x2="' + sX(d + hD) + '" y1="' + yD + '" y2="' + yD + '"/>';
        return out + '<line class="vline-truth" x1="' + sX(d) + '" x2="' + sX(d) + '" y1="' + sY(0) + '" y2="' + sY(top * 0.78) + '"/>';
      },
      over: function (sX, sY, g) {
        return '<text class="lbl-fit" x="' + (g.m.l + 6) + '" y="' + (g.m.t + 14) + '">' + LF.esc(t("lblNaive")) + '</text>' +
          '<text class="lbl-truth" x="' + (g.m.l + g.pw - 6) + '" y="' + (g.m.t + 14) + '" text-anchor="end" style="fill: var(--fix)">' + LF.esc(t("lblDelta")) + '</text>';
      } });
    $("t2-x0").textContent = num(c.x0, 2);
    $("t2-true").textContent = num(d, 2);
    $("t2-naive").textContent = pm(hN); $("t2-naive").className = "v" + (Math.abs(hN - hA) / hA > 0.3 ? " bad" : "");
    $("t2-delta").textContent = pm(hD); $("t2-delta").className = "v good";
    $("t2-boot").textContent = pm(hB);
    $("t2-act").textContent = pm(hA);
    var v = { n: num(hN, 2), d: num(hD, 2), a: num(hA, 2), b: num(hB, 2) };
    $("t2-note").innerHTML = t(d < 1 ? "t2NoteNearHtml" : "t2NoteHtml", v);
  }
  $("t2-d").addEventListener("input", t2);
  $("t2-new").addEventListener("click", function () { t2Draw(); t2(); });

  // ---------- Trial 3: the report line (from Trial 1's data) ----------
  function t3() {
    var f = T1.f, n = T1.n, tc = LF.tcrit(n - 2), mx = 0, sxx = 0, i, x0 = +$("t1-x").value, b = LF.bands(T1.x, f, x0);
    for (i = 0; i < n; i++) mx += T1.x[i];
    mx /= n;
    for (i = 0; i < n; i++) sxx += (T1.x[i] - mx) * (T1.x[i] - mx);
    var se0 = f.s * Math.sqrt(1 / n + mx * mx / sxx);
    $("t3-report").textContent = t("reportTpl", {
      n: n, xlo: num(Math.min.apply(null, T1.x), 1), xhi: num(Math.max.apply(null, T1.x), 1),
      b1: num(f.b1, 2), b1h: num(tc * f.se1, 2), b0: num(f.b0, 2), b0h: num(tc * se0, 2), s: num(f.s, 2),
      x0: num(x0, 1), yhat: num(b.y, 1), pih: num(b.pi, 1),
      outside: x0 < Math.min.apply(null, T1.x) || x0 > Math.max.apply(null, T1.x) ? t("reportOutside") : ""
    });
  }
  $("t3-copy").addEventListener("click", function () {
    var txt = $("t3-report").textContent, st = $("t3-copy-status");
    function fallback() {
      var r = document.createRange(); r.selectNodeContents($("t3-report"));
      var sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
      st.textContent = t("copyFail");
    }
    try {
      navigator.clipboard.writeText(txt).then(function () { st.textContent = t("copied"); }, fallback);
    } catch (e) { fallback(); }
  });

  // ---------- start, and redraw on a language switch ----------
  function renderAll() { t1(); t2(); LF.seriesNav($("series-nav"), "reporting"); }
  t1Draw(); t2Draw();
  renderAll();
  document.addEventListener("learnlangchange", function () { $("t3-copy-status").textContent = ""; renderAll(); });
}());
