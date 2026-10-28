// Checks for learning/marginalia/clt-sample-size/clt-math.js (the exact distributions behind
// "How big does n have to be?"). Node built-ins only:
//   node --test "scripts/tests/*.test.mjs"
// The reference values were computed independently with SciPy (gamma, binomial) and with mpmath at
// 80 digits (Irwin–Hall), not with this file's code (2026-10-27; the script is in the Python
// companion, learning/marginalia/clt-sample-size/clt-sample-size.py, §5).
import { test } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
createRequire(import.meta.url)(path.join(ROOT, "learning/marginalia/clt-sample-size/clt-math.js"));
const M = globalThis.CLTM;
const near = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b} (tol ${tol})`);

// sup_x |F_n(x) − Φ(x)| for the three parents, rounded as printed by the reference run.
const REF = {
  exp: { 20: 0.02976, 40: 0.02103, 80: 0.01487, 320: 0.00743 },
  uni: { 5: 0.005713, 10: 0.002813, 20: 0.001391, 40: 0.000692, 80: 0.000345 },
  coin: { 5: 0.17264, 10: 0.12305, 20: 0.0881, 40: 0.06269, 80: 0.04446, 320: 0.02228 }
};

test("largest error matches the independent reference for every parent and n", () => {
  for (const [key, rows] of Object.entries(REF)) {
    for (const [n, v] of Object.entries(rows)) near(M.supErr(key, +n).err, v, key === "uni" ? 6e-7 : 6e-6, `${key} n=${n}`);
  }
});

test("the uniform's two methods agree where they meet (exact sum vs characteristic function, n = 16)", () => {
  let worst = 0;
  for (let x = -4; x <= 4; x += 0.05) worst = Math.max(worst, Math.abs(M.cdfUniGP(16, x) - M.ihExact(16, 8 + x * Math.sqrt(16 / 12))));
  assert.ok(worst < 1e-9, `max difference ${worst}`);
});

test("the rates the page claims: ×√n → γ₁φ(0)/6 (exponential), ×n → 0.0275 (uniform), ×√n → φ(0) (coin)", () => {
  near(M.supErr("exp", 400).err * 20, 2 * M.phi(0) / 6, 5e-4, "exponential");
  near(M.supErr("uni", 200).err * 200, 0.0275, 3e-4, "uniform");
  near(M.supErr("coin", 400).err * 20, M.phi(0), 3e-3, "coin");
});

test("skewness read from the speed recovers γ₁ = 2 for the exponential", () => {
  const n = 400;
  near(6 * Math.sqrt(2 * Math.PI) * Math.sqrt(n) * (M.cdfExp(n, 0) - 0.5), 2, 0.03, "6√(2π)√n(F(0) − ½)");
});

test("normal and Student t helpers", () => {
  near(M.Phi(1.959963984540054), 0.975, 1e-12, "Φ(1.96)");
  near(M.Phi(-3), 0.0013498980316301, 1e-15, "Φ(−3)");
  near(M.tQuantile(0.975, 9), 2.2621571627409915, 1e-9, "t(0.975, 9)");
  near(2 * M.tCdf(1.96, 9) - 1, 0.9184, 1e-4, "normal data, n = 10, 1.96·s coverage (the page's 91.8%)");
  near(2 * M.tCdf(1.96, 28) - 1, 0.93998, 1e-5, "n = 29: still just under 94% (the page's claim)");
  near(2 * M.tCdf(1.96, 29) - 1, 0.94033, 1e-5, "n = 30: just over 94%");
  assert.equal(M.sugdenN(2), 128);
});

test("Edgeworth: the one-term correction peaks at 0.0665·γ₁/√n at x = 0", () => {
  near(M.edge1(M.PARENTS.exp, 1, 0), 2 * M.phi(0) / 6, 1e-12, "edge1 at 0");
  near(M.phi(0) / 6, 0.0665, 5e-5, "the 0.0665 constant");
});

test("seeded generator: same stream for the same seed, uniform mean ≈ ½", () => {
  const a = M.rng(42), b = M.rng(42);
  for (let i = 0; i < 5; i++) assert.equal(a(), b());
  const r = M.rng(7); let s = 0; for (let i = 0; i < 200000; i++) s += r();
  near(s / 200000, 0.5, 3e-3, "mean");
});
