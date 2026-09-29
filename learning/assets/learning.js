// learning.js — shared engine for /learning pages: seeded random numbers, line fits,
// SVG charts, number formatting and the series navigation. No libraries.
// Exposes one global, LF. Loaded after learning-i18n.js (uses LI18N for words and language).
(function () {
  "use strict";
  var t = function (k, v) { return window.LI18N ? window.LI18N.t(k, v) : k; };

  // ---------- random numbers (seeded, so a slider can reuse the same draws) ----------
  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var r = Math.imul(a ^ a >>> 15, 1 | a);
      r = r + Math.imul(r ^ r >>> 7, 61 | r) ^ r;
      return ((r ^ r >>> 14) >>> 0) / 4294967296;
    };
  }
  function normals(rand, n) {
    var out = new Float64Array(n);
    for (var i = 0; i < n; i += 2) {
      var u = Math.max(rand(), 1e-12), v = rand(), r = Math.sqrt(-2 * Math.log(u));
      out[i] = r * Math.cos(2 * Math.PI * v);
      if (i + 1 < n) out[i + 1] = r * Math.sin(2 * Math.PI * v);
    }
    return out;
  }
  function uniforms(rand, n, a, b) {
    var out = new Float64Array(n);
    for (var i = 0; i < n; i++) out[i] = a + (b - a) * rand();
    return out;
  }
  var seedCounter = 20260928;
  function newSeed() { seedCounter = (Math.imul(seedCounter, 1103515245) + 12345) >>> 0; return seedCounter; }

  // ---------- fitting ----------
  // Ordinary least squares for y = b0 + b1 x. se1 = standard error of the slope.
  function ols(x, y) {
    var n = x.length, mx = 0, my = 0, i;
    for (i = 0; i < n; i++) { mx += x[i]; my += y[i]; }
    mx /= n; my /= n;
    var sxx = 0, sxy = 0;
    for (i = 0; i < n; i++) { var dx = x[i] - mx; sxx += dx * dx; sxy += dx * (y[i] - my); }
    var b1 = sxy / sxx, b0 = my - b1 * mx, sse = 0;
    var fitted = new Float64Array(n), resid = new Float64Array(n);
    for (i = 0; i < n; i++) { fitted[i] = b0 + b1 * x[i]; resid[i] = y[i] - fitted[i]; sse += resid[i] * resid[i]; }
    var s = Math.sqrt(sse / (n - 2));
    return { b0: b0, b1: b1, s: s, se1: s / Math.sqrt(sxx), fitted: fitted, resid: resid };
  }
  // Deming (errors-in-variables) regression. delta = (y error variance) / (x error variance).
  // delta = Infinity means x is exact, which is ordinary least squares.
  function deming(x, y, delta) {
    if (!isFinite(delta)) return ols(x, y);
    var n = x.length, mx = 0, my = 0, i;
    for (i = 0; i < n; i++) { mx += x[i]; my += y[i]; }
    mx /= n; my /= n;
    var sxx = 0, syy = 0, sxy = 0;
    for (i = 0; i < n; i++) { var dx = x[i] - mx, dy = y[i] - my; sxx += dx * dx; syy += dy * dy; sxy += dx * dy; }
    var d = syy - delta * sxx;
    var b1 = (d + Math.sqrt(d * d + 4 * delta * sxy * sxy)) / (2 * sxy);
    return { b0: my - b1 * mx, b1: b1 };
  }
  // Coefficient of determination for a fit (y, fitted).
  function r2(y, fitted) {
    var n = y.length, my = 0, i, sst = 0, sse = 0;
    for (i = 0; i < n; i++) my += y[i];
    my /= n;
    for (i = 0; i < n; i++) { sst += (y[i] - my) * (y[i] - my); sse += (y[i] - fitted[i]) * (y[i] - fitted[i]); }
    return 1 - sse / sst;
  }
  // Simple-regression influence measures for every point: leverage h, internally studentized
  // residual r, and Cook's distance D (k = 2 coefficients).
  function influence(x, y) {
    var f = ols(x, y), n = x.length, mx = 0, i, sxx = 0;
    for (i = 0; i < n; i++) mx += x[i];
    mx /= n;
    for (i = 0; i < n; i++) sxx += (x[i] - mx) * (x[i] - mx);
    var h = new Float64Array(n), r = new Float64Array(n), D = new Float64Array(n);
    for (i = 0; i < n; i++) {
      h[i] = 1 / n + (x[i] - mx) * (x[i] - mx) / sxx;
      r[i] = f.resid[i] / (f.s * Math.sqrt(1 - h[i]));
      D[i] = r[i] * r[i] * h[i] / (2 * (1 - h[i]));
    }
    return { fit: f, h: h, r: r, D: D };
  }
  // Least-squares fit of y = B + A·exp(−t/τ) (a first-order step response).
  // For a fixed τ the model is linear in A and B, so search τ on a log grid, then refine
  // with golden-section search.
  function expFit(t, y) {
    function at(tau) {
      var n = t.length, z = new Float64Array(n);
      for (var i = 0; i < n; i++) z[i] = Math.exp(-t[i] / tau);
      var f = ols(z, y), sse = 0;
      for (i = 0; i < n; i++) sse += f.resid[i] * f.resid[i];
      return { tau: tau, A: f.b1, B: f.b0, sse: sse, fitted: f.fitted, resid: f.resid };
    }
    var span = t[t.length - 1] - t[0], best = null, lo = Math.log(span / 50), hi = Math.log(span * 20);
    var steps = 40;   // coarse log grid; the golden-section search below recovers full precision
    for (var k = 0; k <= steps; k++) { var c = at(Math.exp(lo + (hi - lo) * k / steps)); if (!best || c.sse < best.sse) best = c; }
    // Golden-section search on log τ, reusing one evaluation per step.
    var g = (Math.sqrt(5) - 1) / 2, a = Math.log(best.tau) - (hi - lo) / steps, b = Math.log(best.tau) + (hi - lo) / steps;
    var m1 = b - g * (b - a), m2 = a + g * (b - a), f1 = at(Math.exp(m1)).sse, f2 = at(Math.exp(m2)).sse;
    for (k = 0; k < 28; k++) {
      if (f1 < f2) { b = m2; m2 = m1; f2 = f1; m1 = b - g * (b - a); f1 = at(Math.exp(m1)).sse; }
      else { a = m1; m1 = m2; f1 = f2; m2 = a + g * (b - a); f2 = at(Math.exp(m2)).sse; }
    }
    var fin = at(Math.exp((a + b) / 2));
    return fin.sse <= best.sse ? fin : best;
  }
  // ----- added with Modules 1, 3, 4, 6 -----
  // Solve A·c = b (small dense system) by Gaussian elimination with partial pivoting.
  function solve(A, b) {
    var n = b.length, M = A.map(function (row, i) { return row.slice().concat([b[i]]); }), i, j, k;
    for (k = 0; k < n; k++) {
      var piv = k;
      for (i = k + 1; i < n; i++) if (Math.abs(M[i][k]) > Math.abs(M[piv][k])) piv = i;
      var tmp = M[k]; M[k] = M[piv]; M[piv] = tmp;
      for (i = k + 1; i < n; i++) { var f = M[i][k] / M[k][k]; for (j = k; j <= n; j++) M[i][j] -= f * M[k][j]; }
    }
    var c = new Array(n);
    for (i = n - 1; i >= 0; i--) { var sum = M[i][n]; for (j = i + 1; j < n; j++) sum -= M[i][j] * c[j]; c[i] = sum / M[i][i]; }
    return c;
  }
  // Polynomial least squares of degree `deg`. x is centred and scaled to [-1, 1] internally so
  // high degrees stay well conditioned. Returns { predict(x), fitted, resid, sse, p }.
  function polyfit(x, y, deg) {
    var n = x.length, lo = Infinity, hi = -Infinity, i, j, k;
    for (i = 0; i < n; i++) { lo = Math.min(lo, x[i]); hi = Math.max(hi, x[i]); }
    var mid = (lo + hi) / 2, half = (hi - lo) / 2 || 1, p = deg + 1;
    var z = function (v) { return (v - mid) / half; };
    var A = [], b = new Array(p).fill(0);
    for (j = 0; j < p; j++) A.push(new Array(p).fill(0));
    for (i = 0; i < n; i++) {
      var pw = [1]; for (k = 1; k < p; k++) pw.push(pw[k - 1] * z(x[i]));
      for (j = 0; j < p; j++) { b[j] += pw[j] * y[i]; for (k = 0; k < p; k++) A[j][k] += pw[j] * pw[k]; }
    }
    var c = solve(A, b);
    var predict = function (v) { var zz = z(v), s = 0, pw = 1; for (var q = 0; q < p; q++) { s += c[q] * pw; pw *= zz; } return s; };
    var fitted = new Float64Array(n), resid = new Float64Array(n), sse = 0;
    for (i = 0; i < n; i++) { fitted[i] = predict(x[i]); resid[i] = y[i] - fitted[i]; sse += resid[i] * resid[i]; }
    return { predict: predict, fitted: fitted, resid: resid, sse: sse, p: p };
  }
  // Weighted least squares for y = b0 + b1 x with weights w (use 1/σ² when σ is known).
  // s2 = weighted residual variance (≈ 1 when the weights are exact 1/σ²).
  function wls(x, y, w) {
    var n = x.length, sw = 0, mx = 0, my = 0, i;
    for (i = 0; i < n; i++) { sw += w[i]; mx += w[i] * x[i]; my += w[i] * y[i]; }
    mx /= sw; my /= sw;
    var sxx = 0, sxy = 0;
    for (i = 0; i < n; i++) { sxx += w[i] * (x[i] - mx) * (x[i] - mx); sxy += w[i] * (x[i] - mx) * (y[i] - my); }
    var b1 = sxy / sxx, b0 = my - b1 * mx, chi = 0, resid = new Float64Array(n);
    for (i = 0; i < n; i++) { resid[i] = y[i] - b0 - b1 * x[i]; chi += w[i] * resid[i] * resid[i]; }
    var s2 = chi / (n - 2);
    return { b0: b0, b1: b1, resid: resid, s2: s2, se1: Math.sqrt(s2 / sxx), sw: sw, mx: mx, sxx: sxx };
  }
  // HC3 (heteroskedasticity-robust) standard error of the OLS slope.
  function hc3se(x, f) {
    var n = x.length, mx = 0, i, sxx = 0, num = 0;
    for (i = 0; i < n; i++) mx += x[i];
    mx /= n;
    for (i = 0; i < n; i++) sxx += (x[i] - mx) * (x[i] - mx);
    for (i = 0; i < n; i++) {
      var h = 1 / n + (x[i] - mx) * (x[i] - mx) / sxx, u = f.resid[i] / (1 - h);
      num += (x[i] - mx) * (x[i] - mx) * u * u;
    }
    return Math.sqrt(num) / sxx;
  }
  // 95% confidence (mean line) and prediction (next reading) half-widths for an OLS fit at x0.
  function bands(x, f, x0) {
    var n = x.length, mx = 0, i, sxx = 0;
    for (i = 0; i < n; i++) mx += x[i];
    mx /= n;
    for (i = 0; i < n; i++) sxx += (x[i] - mx) * (x[i] - mx);
    var tc = tcrit(n - 2), lev = 1 / n + (x0 - mx) * (x0 - mx) / sxx;
    return { y: f.b0 + f.b1 * x0, ci: tc * f.s * Math.sqrt(lev), pi: tc * f.s * Math.sqrt(1 + lev) };
  }
  // AR(1) noise: each value = rho·previous + fresh noise, scaled so the SD stays `sd`.
  function ar1(z, rho, sd) {
    var n = z.length, e = new Float64Array(n), k = Math.sqrt(1 - rho * rho);
    e[0] = z[0];
    for (var i = 1; i < n; i++) e[i] = rho * e[i - 1] + k * z[i];
    for (i = 0; i < n; i++) e[i] *= sd;
    return e;
  }
  // Autocorrelation of a series at lags 1..maxLag.
  function acf(r, maxLag) {
    var n = r.length, m = 0, i, c0 = 0, out = [];
    for (i = 0; i < n; i++) m += r[i];
    m /= n;
    for (i = 0; i < n; i++) c0 += (r[i] - m) * (r[i] - m);
    for (var L = 1; L <= maxLag; L++) { var c = 0; for (i = L; i < n; i++) c += (r[i] - m) * (r[i - L] - m); out.push(c / c0); }
    return out;
  }
  // Durbin–Watson statistic of residuals in time order (≈ 2 when uncorrelated).
  function durbinWatson(r) {
    var num = 0, den = r[0] * r[0];
    for (var i = 1; i < r.length; i++) { num += (r[i] - r[i - 1]) * (r[i] - r[i - 1]); den += r[i] * r[i]; }
    return num / den;
  }
  // Two-sided 95% t critical value (Cornish-Fisher expansion; good to 3 decimals for df >= 8).
  function tcrit(df) {
    var z = 1.959964;
    return z + (Math.pow(z, 3) + z) / (4 * df) + (5 * Math.pow(z, 5) + 16 * Math.pow(z, 3) + 3 * z) / (96 * df * df)
      + (3 * Math.pow(z, 7) + 19 * Math.pow(z, 5) + 17 * Math.pow(z, 3) - 15 * z) / (384 * Math.pow(df, 3));
  }

  // ---------- numbers ----------
  // Fixed decimals in the page's language (ES uses a decimal comma).
  function num(v, d) {
    var s = Number(v).toFixed(d === undefined ? 2 : d);
    return (window.LI18N && window.LI18N.lang === "es") ? s.replace(".", ",") : s;
  }

  // ---------- charts ----------
  function niceTicks(a, b, count) {
    var span = b - a, step0 = span / count, mag = Math.pow(10, Math.floor(Math.log10(step0)));
    var err = step0 / mag, step = mag * (err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1);
    var out = [];
    for (var v = Math.ceil(a / step) * step; v <= b + 1e-9; v += step) out.push(+v.toFixed(10));
    return out;
  }
  function tickText(v) { return Math.abs(v) < 1e-9 ? "0" : Number.isInteger(v) ? String(v) : num(v, 1); }
  var clipId = 0;
  // o: { x:[min,max], y:[min,max], w?, h?, xLabel, yLabel, noY?, xt?, yt?, xticks?: [values], xfmt?(v) → label,
  //      draw(sx,sy) → svg string,
  //      over?(sx,sy,geom) → svg string drawn unclipped }
  function chart(svg, o) {
    var W = o.w || 560, H = o.h || 360, m = { l: 50, r: 14, t: 14, b: 46 };
    var pw = W - m.l - m.r, ph = H - m.t - m.b;
    var sx = function (v) { return m.l + (v - o.x[0]) / (o.x[1] - o.x[0]) * pw; };
    var sy = function (v) { return m.t + ph - (v - o.y[0]) / (o.y[1] - o.y[0]) * ph; };
    var id = "lfclip" + (++clipId), g = "";
    g += '<defs><clipPath id="' + id + '"><rect x="' + m.l + '" y="' + m.t + '" width="' + pw + '" height="' + ph + '"/></clipPath></defs>';
    (o.xticks || niceTicks(o.x[0], o.x[1], o.xt || 6)).forEach(function (tk) {
      g += '<line class="gridline" x1="' + sx(tk) + '" x2="' + sx(tk) + '" y1="' + m.t + '" y2="' + (m.t + ph) + '"/>' +
        '<text class="tick" x="' + sx(tk) + '" y="' + (m.t + ph + 16) + '" text-anchor="middle">' + (o.xfmt ? esc(o.xfmt(tk)) : tickText(tk)) + '</text>';
    });
    if (!o.noY) niceTicks(o.y[0], o.y[1], o.yt || 5).forEach(function (tk) {
      g += '<line class="gridline" x1="' + m.l + '" x2="' + (m.l + pw) + '" y1="' + sy(tk) + '" y2="' + sy(tk) + '"/>' +
        '<text class="tick" x="' + (m.l - 7) + '" y="' + (sy(tk) + 4) + '" text-anchor="end">' + tickText(tk) + '</text>';
    });
    g += '<line class="axis" x1="' + m.l + '" x2="' + (m.l + pw) + '" y1="' + (m.t + ph) + '" y2="' + (m.t + ph) + '"/>' +
      '<line class="axis" x1="' + m.l + '" x2="' + m.l + '" y1="' + m.t + '" y2="' + (m.t + ph) + '"/>';
    g += '<text class="axlabel" x="' + (m.l + pw / 2) + '" y="' + (H - 8) + '" text-anchor="middle">' + esc(o.xLabel) + '</text>';
    g += '<text class="axlabel" transform="translate(13 ' + (m.t + ph / 2) + ') rotate(-90)" text-anchor="middle">' + esc(o.yLabel) + '</text>';
    g += '<g clip-path="url(#' + id + ')">' + o.draw(sx, sy) + '</g>';
    if (o.over) g += o.over(sx, sy, { m: m, pw: pw, ph: ph });
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.innerHTML = g;
  }
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
  function line(cls, sx, sy, b0, b1, x0, x1) {
    return '<line class="' + cls + '" x1="' + sx(x0) + '" y1="' + sy(b0 + b1 * x0) + '" x2="' + sx(x1) + '" y2="' + sy(b0 + b1 * x1) + '"/>';
  }
  function dots(xs, ys, sx, sy, r) {
    var s = "";
    for (var i = 0; i < xs.length; i++) s += '<circle class="pt" cx="' + sx(xs[i]).toFixed(1) + '" cy="' + sy(ys[i]).toFixed(1) + '" r="' + (r || 4) + '"/>';
    return s;
  }

  // ---------- offline app (the installed copy) ----------
  // The Windows installer (learning/workshop/offline/) appends window.LEARN_OFFLINE to the
  // installed copy of modules.js: { version, missing: ["fits/<slug>/", "fits/<slug>/slides.html", …] },
  // the paths (relative to learning/) the reader chose not to install; a trailing "/" means the
  // whole folder. It never exists on the site or in the repo, so none of this runs there.
  var OFFLINE = window.LEARN_OFFLINE || null;
  // learning/ as an absolute URL, from this script's own address (…/learning/assets/learning.js).
  var ROOT = (function () {
    var s = document.currentScript && document.currentScript.src;
    return s ? s.replace(/assets\/learning\.js(?:[?#].*)?$/, "") : "";
  }());
  function isMissing(path) {
    return !!OFFLINE && (OFFLINE.missing || []).some(function (p) {
      return p.slice(-1) === "/" ? path.indexOf(p) === 0 : path === p;
    });
  }
  function moduleMissing(m) { return isMissing("fits/" + m.slug + "/"); }
  var RELEASES = "https://github.com/gidgo130/gideonong.me/releases/latest";
  // Hub footer in the installed copy only: which version this is, and where newer ones are.
  // The app never checks for updates by itself.
  function offlineNote(el) {
    if (!OFFLINE || !el) return;
    var span = el.querySelector(".offline-copy");
    if (!span) { span = document.createElement("span"); span.className = "offline-copy"; el.appendChild(span); }
    span.innerHTML = esc(t("offlineCopy", { v: OFFLINE.version || "?", c: OFFLINE.commit || "?" })) +
      ' · <a href="' + RELEASES + '" target="_blank" rel="noopener">' + esc(t("offlineUpdates")) + '</a>';
  }

  // ---------- series navigation ----------
  // Paths are relative so pages work on the site AND opened from disk (offline app).
  // From a module page (learning/fits/<slug>/): hub = "../../", sibling = "../<slug>/".
  function moduleTitle(m) { return t("mod" + m.key + "Title"); }
  function seriesNav(el, currentSlug) {
    var mods = window.LEARN_MODULES || [];
    var i = mods.findIndex(function (m) { return m.slug === currentSlug; });
    if (i < 0 || !el) return;
    function cell(m, n, cls, labelKey) {
      if (!m) return '<span></span>';
      var head = '<small>' + esc(t(labelKey)) + " · " + esc(t("moduleN", { n: n })) + '</small>';
      if (!m.ready || moduleMissing(m)) {
        return '<span class="soon ' + cls + '">' + head + esc(moduleTitle(m)) + ' <small>' + esc(t(m.ready ? "statusMissing" : "statusSoon")) + '</small></span>';
      }
      return '<a class="' + cls + '" href="../' + m.slug + '/">' + head + esc(moduleTitle(m)) + '</a>';
    }
    el.innerHTML = cell(mods[i - 1], i, "prev", "navPrev") +
      '<a class="all" href="../../"><small>' + esc(t("seriesName")) + '</small>' + esc(t("navAll")) + '</a>' +
      cell(mods[i + 1], i + 2, "next", "navNext");
    fixFileLinks(el);
  }
  // Hub list (learning/index.html): module rows, numbered by position in the registry.
  function moduleList(el) {
    var mods = window.LEARN_MODULES || [];
    el.innerHTML = mods.map(function (m, i) {
      var open = m.ready && !moduleMissing(m);
      var inner = '<span class="m-num">' + String(i + 1).padStart(2, "0") + '</span>' +
        '<span class="m-title">' + esc(moduleTitle(m)) + '</span>' +
        '<span class="m-status' + (open ? " ready" : "") + '">' + esc(t(open ? "statusReady" : m.ready ? "statusMissing" : "statusSoon")) + '</span>' +
        '<span class="m-desc">' + esc(t("mod" + m.key + "Desc")) + '</span>';
      return '<li>' + (open
        ? '<a class="module-row" href="fits/' + m.slug + '/">' + inner + '</a>'
        : '<div class="module-row is-soon">' + inner + '</div>') + '</li>';
    }).join("");
    fixFileLinks(el);
  }

  // Opened from disk (offline app), a folder link like "../../" shows a directory listing
  // instead of the page, so point relative folder links at their index.html.
  // In the installed copy (LEARN_OFFLINE) two more fixes: a link that leaves learning/ (the
  // "gideonong.me" crumb) goes to the live site, and a link to a file the reader chose not to
  // install (a module's slides or script) is hidden.
  function fixFileLinks(scope) {
    if (location.protocol !== "file:") return;
    (scope || document).querySelectorAll("a[href]").forEach(function (a) {
      var h = a.getAttribute("href");
      if (/^[a-z]+:/i.test(h) || h.charAt(0) === "#" || h.charAt(0) === "/") return;
      if (OFFLINE && ROOT) {
        var abs = a.href.replace(/[?#].*$/, ""), up = ROOT.replace(/[^\/]+\/$/, "");
        if (abs.indexOf(ROOT) !== 0) {
          if (abs.indexOf(up) === 0) a.setAttribute("href", "https://gideonong.me/" + abs.slice(up.length));
          return;
        }
        if (isMissing(abs.slice(ROOT.length))) { a.hidden = true; return; }
      }
      if (/\/$/.test(h) || h === "." || h === "..") a.setAttribute("href", h.replace(/\/?$/, "/") + "index.html");
    });
  }
  // Some links only work over HTTP (the "Play with the code" notebook runs Python from a CDN).
  // Mark them data-http-only and they disappear when the page is opened from disk.
  function hideHttpOnly() {
    if (location.protocol !== "file:") return;
    document.querySelectorAll("[data-http-only]").forEach(function (el) { el.hidden = true; });
  }
  // "Lite" devices (phones, save-data, little memory) get the Colab link as the primary way to
  // run the code and the in-browser notebook second; everything else the other way round. Both
  // stay visible; learning.css reads data-lite on <html> to reorder and style the pair. Decided
  // once, at script load (the script sits at the end of <body>), so the row never visibly reorders.
  function isLiteDevice() {
    var c = navigator.connection || {};
    return (window.matchMedia && window.matchMedia("(max-width: 640px), (pointer: coarse)").matches) ||
      c.saveData === true ||
      (typeof navigator.deviceMemory === "number" && navigator.deviceMemory <= 4);
  }
  if (isLiteDevice()) document.documentElement.setAttribute("data-lite", "");

  // ---------- offline downloads (live site only) ----------
  // The GitHub release assets have version-free names (learning/workshop/offline/build.ps1
  // -Release), so these links never change between releases. Windows visitors get the hub's
  // full installer and each module page's own installer; everyone else gets the zip on the
  // hub. Nothing is shown from disk or in the offline copy itself.
  var DOWNLOAD = RELEASES + "/download/";
  function isWindows() {
    var d = navigator.userAgentData;
    return d && d.platform ? d.platform === "Windows" : /Windows/.test(navigator.userAgent);
  }
  function offlineLinks() {
    if (location.protocol === "file:" || OFFLINE) return;
    var win = isWindows();
    var hub = document.getElementById("offline-get");
    if (hub) {
      hub.innerHTML = '<span>' + esc(t("offlineGetLabel")) + '</span>' +
        (win ? '<a href="' + DOWNLOAD + 'ReadingYourFits-Setup.exe">' + esc(t("offlineGetWin")) + '</a>' : "") +
        '<a href="' + DOWNLOAD + 'ReadingYourFits.zip">' + esc(t(win ? "offlineGetZip" : "offlineGetZipOnly")) + '</a>' +
        (win ? '<small>' + esc(t("offlineGetNote")) + ' <a href="' + RELEASES + '" target="_blank" rel="noopener">' +
          esc(t("offlineGetNotes")) + '</a></small>' : "");
      hub.hidden = false;
    }
    // A module page (learning/fits/<slug>/): its own installer in the "Take it with you" row.
    var row = document.querySelector(".takeaway-links");
    var rel = ROOT && location.href.indexOf(ROOT) === 0 ? location.href.slice(ROOT.length) : "";
    var hit = /^fits\/([a-z0-9-]+)\//.exec(rel);
    var mod = hit && (window.LEARN_MODULES || []).filter(function (m) { return m.slug === hit[1] && m.ready; })[0];
    if (row && mod && win) {
      var a = row.querySelector(".take-offline");
      if (!a) {
        a = document.createElement("a");
        a.className = "take-offline";
        a.href = DOWNLOAD + "ReadingYourFits-" + mod.slug + "-Setup.exe";
        row.appendChild(a);
      }
      a.textContent = t("takeOffline");
      a.title = t("takeOfflineTitle");
    }
  }
  document.addEventListener("DOMContentLoaded", function () { fixFileLinks(); hideHttpOnly(); offlineLinks(); });
  document.addEventListener("learnlangchange", offlineLinks);

  window.LF = {
    mulberry32: mulberry32, normals: normals, uniforms: uniforms, newSeed: newSeed,
    ols: ols, deming: deming, tcrit: tcrit, num: num, r2: r2, influence: influence, expFit: expFit,
    solve: solve, polyfit: polyfit, wls: wls, hc3se: hc3se, bands: bands, ar1: ar1, acf: acf, durbinWatson: durbinWatson,
    chart: chart, line: line, dots: dots, esc: esc,
    seriesNav: seriesNav, moduleList: moduleList, fixFileLinks: fixFileLinks, isLiteDevice: isLiteDevice,
    offlineNote: offlineNote, isWindows: isWindows
  };
}());
