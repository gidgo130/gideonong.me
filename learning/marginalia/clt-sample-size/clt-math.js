// clt-math.js — the exact distributions and expansions behind "How big does n have to be?"
// (Marginalia). Pure functions, no DOM: main.js draws with them, and the Node check in
// learning/marginalia/README.md ("Checks") compares them with an independent Python/mpmath run.
//
// Y_n = (X̄_n − μ)/(σ/√n) for three parents, computed exactly (no simulation):
//   exponential  ΣX ~ Gamma(n, 1)           regularized incomplete gamma, as a Poisson tail
//   uniform      ΣX ~ Irwin–Hall(n)          exact alternating sum for n ≤ 16; above that the
//                                            characteristic function inverted numerically
//                                            (Gil-Pelaez), because the alternating sum loses
//                                            every digit to cancellation in double precision
//   fair coin    ΣX ~ Binomial(n, ½)         exact pmf from log-gamma
// Plus the one- and two-term Edgeworth corrections, Esseen's lattice term, Berry–Esseen, the
// Student-t quantile, and a seeded random number generator for the coverage simulation.
(function (root) {
  "use strict";
  const SQ2PI = Math.sqrt(2 * Math.PI);

  /* ---------- normal ---------- */
  const phi = (x) => Math.exp(-0.5 * x * x) / SQ2PI;
  // erf from its all-positive series erf(x) = 2/√π e^{−x²} Σ 2^k x^{2k+1} / (1·3·…·(2k+1)):
  // no cancellation, about 1e-16 for |x| ≤ 6. Φ(x) = (1 + erf(x/√2)) / 2.
  function erfPos(x) {
    if (x > 6) return 1;
    let term = x, sum = x, k = 0;
    while (term > 1e-17 * sum) { k++; term *= 2 * x * x / (2 * k + 1); sum += term; }
    return 2 / Math.sqrt(Math.PI) * Math.exp(-x * x) * sum;
  }
  function Phi(x) {
    const z = Math.abs(x) / Math.SQRT2;
    if (z > 6) return x > 0 ? 1 : 0;
    const e = erfPos(z);
    return x >= 0 ? 0.5 + 0.5 * e : 0.5 - 0.5 * e;
  }

  /* ---------- log-gamma (Lanczos, g = 7) ---------- */
  const LG = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
  function lgamma(z) {
    if (z < 0.5) return Math.log(Math.PI / Math.abs(Math.sin(Math.PI * z))) - lgamma(1 - z);
    z -= 1; let a = LG[0]; const t = z + 7.5;
    for (let i = 1; i < 9; i++) a += LG[i] / (z + i);
    return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(a);
  }

  /* ---------- exponential parent: Gamma(n, 1) CDF ---------- */
  // For integer n, P(ΣX ≤ s) = 1 − Σ_{k<n} e^{−s} s^k / k!. Terms are built in log space from
  // the largest one outward, so nothing underflows for n up to a few thousand.
  function gammaCdfInt(n, s) {
    if (s <= 0) return 0;
    const m = Math.min(n - 1, Math.floor(s));          // index of the largest Poisson term
    const lm = -s + m * Math.log(s) - lgamma(m + 1);
    let sum = 0, t = 1;
    for (let k = m; k >= 0; k--) { sum += t; t *= k / s; if (t < 1e-18) break; }
    t = 1;
    for (let k = m + 1; k <= n - 1; k++) { t *= s / k; sum += t; if (t < 1e-18 * sum) break; }
    return Math.max(0, Math.min(1, 1 - Math.exp(lm) * sum));
  }
  const cdfExp = (n, x) => gammaCdfInt(n, n + x * Math.sqrt(n));

  /* ---------- uniform parent: Irwin–Hall ---------- */
  function ihExact(n, t) {             // P(U1+…+Un ≤ t), exact sum; fine in doubles for n ≤ 16
    if (t <= 0) return 0;
    if (t >= n) return 1;
    if (t > n / 2) return 1 - ihExact(n, n - t);
    let s = 0, c = 1;                   // c = C(n, k)
    for (let k = 0; k <= Math.floor(t); k++) {
      s += (k % 2 ? -1 : 1) * c * Math.pow(t - k, n);
      c = c * (n - k) / (k + 1);
    }
    return s / Math.exp(lgamma(n + 1));
  }
  // Gil-Pelaez: F(x) = ½ + (1/π) ∫₀^∞ sin(tx) ψ(t)/t dt with ψ(t) = (sin(ct)/(ct))^n, c = √(3/n)
  // (the standardized uniform has variance 1). ψ is real and even. Past the first zero t = π/c,
  // |ψ| ≤ (1/π)^n < 1e-8 at n = 17 and its side lobes are smaller still, so [0, π/c] suffices.
  // Simpson with 2,400 panels; the nodes and weights are cached per n.
  const gpCache = {};
  function gpNodes(n) {
    if (gpCache[n]) return gpCache[n];
    const c = Math.sqrt(3 / n), T = Math.PI / c, N = 2400, h = T / N, t = new Float64Array(N + 1), w = new Float64Array(N + 1);
    for (let i = 0; i <= N; i++) {
      const ti = i * h; t[i] = ti;
      const simp = (i === 0 || i === N) ? 1 : (i % 2 ? 4 : 2);
      const psi = ti === 0 ? 1 : Math.pow(Math.sin(c * ti) / (c * ti), n);
      w[i] = simp * h / 3 * (ti === 0 ? 0 : psi / ti);   // the t = 0 node is handled below
    }
    return (gpCache[n] = { t, w, h });
  }
  function cdfUniGP(n, x) {
    const g = gpNodes(n);
    let s = g.h / 3 * x;                // t = 0 node: lim sin(tx)ψ(t)/t = x, Simpson weight 1
    for (let i = 1; i < g.t.length; i++) s += Math.sin(g.t[i] * x) * g.w[i];
    return Math.max(0, Math.min(1, 0.5 + s / Math.PI));
  }
  const cdfUni = (n, x) => n <= 16 ? ihExact(n, n / 2 + x * Math.sqrt(n / 12)) : cdfUniGP(n, x);

  /* ---------- coin parent: Binomial(n, ½), W = ±1 ---------- */
  const binCache = {};
  function binCdfTable(n) {            // cdf[k] = P(S ≤ k), pmf[k]
    if (binCache[n]) return binCache[n];
    const pmf = new Float64Array(n + 1), cdf = new Float64Array(n + 1), lf = lgamma(n + 1) - n * Math.LN2;
    let acc = 0;
    for (let k = 0; k <= n; k++) { pmf[k] = Math.exp(lf - lgamma(k + 1) - lgamma(n - k + 1)); acc += pmf[k]; cdf[k] = Math.min(1, acc); }
    return (binCache[n] = { pmf, cdf });
  }
  // Y = (S − n/2)/(√n/2): the lattice points are x_k = (2k − n)/√n, spacing 2/√n.
  function cdfCoin(n, x) {
    const k = Math.floor((x * Math.sqrt(n) + n) / 2 + 1e-12);
    if (k < 0) return 0;
    if (k >= n) return 1;
    return binCdfTable(n).cdf[k];
  }
  const coinPoint = (n, k) => (2 * k - n) / Math.sqrt(n);

  /* ---------- the parents ---------- */
  // γ₁ skewness, γ₂ excess kurtosis, ρ = E|W|³ of the standardized parent (Berry–Esseen).
  const PARENTS = {
    exp: { name: "exponential", g1: 2, g2: 6, rho: 12 / Math.E - 2, cdf: cdfExp },
    uni: { name: "uniform", g1: 0, g2: -1.2, rho: 9 / (4 * Math.sqrt(3)), cdf: cdfUni },
    coin: { name: "fair coin", g1: 0, g2: -2, rho: 1, cdf: cdfCoin, lattice: 2 }
  };

  /* ---------- Edgeworth ---------- */
  // F_n(x) ≈ Φ(x) − φ(x)[ γ₁ He₂(x) / (6√n) + ( γ₂ He₃(x)/24 + γ₁² He₅(x)/72 ) / n ]
  // He₂ = x² − 1, He₃ = x³ − 3x, He₅ = x⁵ − 10x³ + 15x (Feller 1971 §XVI.4; Hall 1992 Ch. 2).
  const edge1 = (p, n, x) => -phi(x) * p.g1 * (x * x - 1) / (6 * Math.sqrt(n));
  const edge2 = (p, n, x) => edge1(p, n, x) - phi(x) * (p.g2 * (x * x * x - 3 * x) / 24 + p.g1 * p.g1 * (Math.pow(x, 5) - 10 * x * x * x + 15 * x) / 72) / n;
  // Esseen's lattice term (Esseen 1945; Feller 1971 §XVI.4) for the coin: W ∈ −1 + 2ℤ (span d = 2),
  // F_n(x) ≈ Φ(x) + (d/√n) φ(x) g(u), u = (x√n + n)/2, g(u) = ⌊u⌋ − u + ½ (the sawtooth).
  function lattice(n, x) { const u = (x * Math.sqrt(n) + n) / 2 + 1e-12; return 2 / Math.sqrt(n) * phi(x) * (Math.floor(u) - u + 0.5); }

  /* ---------- the largest error, sup_x |F_n(x) − Φ(x)| ---------- */
  // Smooth parents: a grid on [−5, 5] plus a golden-section polish around the best grid point.
  // Coin: the sup is at a jump, so check F and its left limit at every lattice point.
  function supErr(key, n) {
    const p = PARENTS[key];
    if (key === "coin") {
      const t = binCdfTable(n); let m = 0, at = 0;
      for (let k = 0; k <= n; k++) {
        const x = coinPoint(n, k), P = Phi(x);
        const a = Math.abs(t.cdf[k] - P), b = Math.abs(t.cdf[k] - t.pmf[k] - P);
        if (a > m) { m = a; at = x; } if (b > m) { m = b; at = x; }
      }
      return { err: m, at };
    }
    const f = (x) => Math.abs(p.cdf(n, x) - Phi(x));
    let best = 0, bx = 0;
    for (let i = 0; i <= 200; i++) { const x = -5 + i * 0.05, v = f(x); if (v > best) { best = v; bx = x; } }
    let a = bx - 0.05, b = bx + 0.05;
    for (let i = 0; i < 40; i++) { const m1 = b - (b - a) / 1.618034, m2 = a + (b - a) / 1.618034; if (f(m1) > f(m2)) b = m2; else a = m1; }
    const xm = (a + b) / 2, v = f(xm);
    return v > best ? { err: v, at: xm } : { err: best, at: bx };
  }
  const BE_C = 0.4748;                          // Shevtsova (2011), iid case
  const berryEsseen = (key, n) => BE_C * PARENTS[key].rho / Math.sqrt(n);
  const sugdenN = (g1) => 28 + 25 * g1 * g1;    // Sugden, Smith & Jones (2000), eq. (4.3)

  /* ---------- Student t ---------- */
  // Regularized incomplete beta by Lentz's continued fraction (the standard algorithm), then
  // P(T ≤ t) and its quantile by bisection. Only a few calls per redraw, so speed is no issue.
  function betacf(a, b, x) {
    const TINY = 1e-300; let qab = a + b, qap = a + 1, qam = a - 1, c = 1, d = 1 - qab * x / qap;
    if (Math.abs(d) < TINY) d = TINY; d = 1 / d; let h = d;
    for (let m = 1; m <= 300; m++) {
      const m2 = 2 * m; let aa = m * (b - m) * x / ((qam + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY; c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY; d = 1 / d; h *= d * c;
      aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2));
      d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY; c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY; d = 1 / d;
      const del = d * c; h *= del; if (Math.abs(del - 1) < 1e-15) break;
    }
    return h;
  }
  function ibeta(a, b, x) {
    if (x <= 0) return 0; if (x >= 1) return 1;
    const bt = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    return x < (a + 1) / (a + b + 2) ? bt * betacf(a, b, x) / a : 1 - bt * betacf(b, a, 1 - x) / b;
  }
  function tCdf(t, v) { const ib = ibeta(v / 2, 0.5, v / (v + t * t)); return t >= 0 ? 1 - ib / 2 : ib / 2; }
  function tQuantile(p, v) {
    let lo = -50, hi = 50;
    for (let i = 0; i < 100; i++) { const m = (lo + hi) / 2; if (tCdf(m, v) < p) lo = m; else hi = m; }
    return (lo + hi) / 2;
  }

  /* ---------- seeded random numbers ---------- */
  // xoshiro128** (Blackman & Vigna): fast, good quality, and the same stream in every browser.
  function rng(seed) {
    let a = seed >>> 0 || 1, b = 0x9e3779b9, c = 0x243f6a88, d = 0xb7e15162;
    const next = () => {
      const r = Math.imul(rotl(Math.imul(b, 5), 7), 9) >>> 0, t = b << 9;
      c ^= a; d ^= b; b ^= c; a ^= d; c ^= t; d = rotl(d, 11);
      return (r + 0.5) / 4294967296;
    };
    for (let i = 0; i < 16; i++) next();
    let spare = null;
    next.normal = () => {              // Marsaglia's polar method
      if (spare !== null) { const s = spare; spare = null; return s; }
      let u, v, s; do { u = 2 * next() - 1; v = 2 * next() - 1; s = u * u + v * v; } while (s >= 1 || s === 0);
      const m = Math.sqrt(-2 * Math.log(s) / s); spare = v * m; return u * m;
    };
    return next;
  }
  function rotl(x, k) { return (x << k) | (x >>> (32 - k)); }

  root.CLTM = { phi, Phi, lgamma, gammaCdfInt, ihExact, cdfUniGP, cdfExp, cdfUni, cdfCoin, coinPoint,
    binCdfTable, PARENTS, edge1, edge2, lattice, supErr, berryEsseen, BE_C, sugdenN, tCdf, tQuantile, rng };
}(typeof window !== "undefined" ? window : globalThis));
