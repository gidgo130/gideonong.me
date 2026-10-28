"""How big does n have to be? Reading skewness from the CLT (Marginalia 02, gideonong.me/learning/marginalia/)

Companion script: the rule, the coverage simulation, a reusable bootstrap-t function, and the exact
errors behind the page's second interactive. It runs top to bottom as a plain script and as a Colab
notebook (the "# %%" markers become cells). NumPy, SciPy and Matplotlib only.
Text, figures and code: CC BY-SA 4.0, Gideon A. Ong.
"""

# %% [markdown]
# ## 1. The rule
# Sugden, Smith & Jones (2000), eq. 4.3: trust the two-sided 95% interval x̄ ± 1.96·s/√n when
# n > 28 + 25·γ₁², where γ₁ is the skewness of the data.

# %%
import numpy as np
from scipy import stats
from fractions import Fraction
from math import comb, factorial, sqrt, pi, e
import matplotlib.pyplot as plt


def rule_n(g1):
    return 28 + 25 * g1 ** 2


models = {
    "normal": stats.norm(),
    "Poisson, mean 10": stats.poisson(10),
    "gamma, shape 4": stats.gamma(4),
    "Weibull, shape 1.5": stats.weibull_min(1.5),
    "lognormal, sigma 0.5": stats.lognorm(0.5),
    "exponential": stats.expon(),
    "lognormal, sigma 1": stats.lognorm(1.0),
}
for name, d in models.items():
    g1 = float(d.stats(moments="s"))
    print(f"{name:22s} skewness {g1:5.2f}   rule: n > {rule_n(g1):6.0f}")

# Estimating the skewness from data: scipy's bias=False matches Excel SKEW and MATLAB skewness(x, 0).
rng = np.random.default_rng(1)
x = rng.exponential(size=30)
print("\nsample skewness of 30 exponential values:", round(stats.skew(x, bias=False), 2), "(true value 2)")

# %% [markdown]
# ## 2. Coverage, one side at a time
# Simulate many samples, build the interval, and count how often the true mean falls above it
# (interval too low) or below it (interval too high). Each should be 2.5%.

# %%
SAMPLERS = {
    "uniform": (lambda r, s: r.random(s), 0.5),
    "exponential": (lambda r, s: r.exponential(size=s), 1.0),
    "lognormal, sigma 1": (lambda r, s: np.exp(r.standard_normal(s)), np.exp(0.5)),
}


def coverage(kind, n, reps=20000, crit="t", seed=0):
    draw, mu = SAMPLERS[kind]
    r = np.random.default_rng(seed)
    X = draw(r, (reps, n))
    m, s = X.mean(axis=1), X.std(axis=1, ddof=1)
    c = stats.t.ppf(0.975, n - 1) if crit == "t" else 1.96
    h = c * s / np.sqrt(n)
    return np.mean(mu > m + h), np.mean(mu < m - h)


for kind in SAMPLERS:
    print(kind)
    for n in [10, 30, 128, 500]:
        lo, hi = coverage(kind, n)
        lo_z, hi_z = coverage(kind, n, crit="z")
        print(f"  n = {n:4d}  t: too low {100 * lo:4.1f}%  too high {100 * hi:4.1f}%   "
              f"1.96: too low {100 * lo_z:4.1f}%  too high {100 * hi_z:4.1f}%")

# Where the 28 comes from: for exactly normal data, 1.96 with s covers 2·T_{n-1}(1.96) − 1.
for n in [10, 20, 29, 50]:
    print(f"normal data, 1.96·s, n = {n}: coverage {2 * stats.t.cdf(1.96, n - 1) - 1:.4f}")

# %% [markdown]
# ## 3. A bootstrap-t interval you can reuse
# Resample the data, studentize each resample, and use the 2.5% and 97.5% points of t* in place of
# ±1.96 (Hall 1992, Ch. 3). MATLAB equivalent: bootci(2000, {@mean, x}, 'Type', 'student').

# %%
def bootstrap_t(x, B=1999, level=0.95, seed=None):
    """Bootstrap-t confidence interval for the mean of x."""
    x = np.asarray(x, float)
    n = len(x)
    r = np.random.default_rng(seed)
    m, s = x.mean(), x.std(ddof=1)
    idx = r.integers(0, n, size=(B, n))
    xb = x[idx]
    tb = (xb.mean(axis=1) - m) / (xb.std(axis=1, ddof=1) / np.sqrt(n))
    # The order statistics at (B + 1)·a and (B + 1)·(1 − a), as the page does (choose B so that
    # these are whole numbers: 399, 999, 1999 for 95%).
    a = (1 - level) / 2
    tb.sort()
    t_lo, t_hi = tb[int(round((B + 1) * a)) - 1], tb[int(round((B + 1) * (1 - a))) - 1]
    return m - t_hi * s / np.sqrt(n), m - t_lo * s / np.sqrt(n)


x = rng.exponential(size=30)
print("t interval:          ", np.round(stats.t.interval(0.95, 29, loc=x.mean(), scale=x.std(ddof=1) / sqrt(30)), 3))
print("bootstrap-t interval:", np.round(bootstrap_t(x, seed=2), 3), "  (true mean 1)")

# Coverage check at n = 30, exponential data (1,000 samples, 399 resamples each: a minute or less).
r = np.random.default_rng(3)
lo = hi = 0
for i in range(1000):
    L, U = bootstrap_t(r.exponential(size=30), B=399, seed=i)
    lo += 1.0 > U
    hi += 1.0 < L
print(f"bootstrap-t, exponential, n = 30: too low {lo / 10:.1f}%, too high {hi / 10:.1f}%  (t interval: about 6.6% and 0.7%)")

# %% [markdown]
# ## 4. The exact error F_n − Φ and the Edgeworth expansion
# Y_n = (X̄ − μ)/(σ/√n). Exponential: ΣX ~ Gamma(n). Uniform: ΣX ~ Irwin–Hall(n), computed here
# exactly with Python's integers and fractions. Fair coin: ΣX ~ Binomial(n, ½).

# %%
def cdf_exp(n, x):
    return stats.gamma.cdf(n + x * np.sqrt(n), n)


def irwin_hall_cdf(n, t):
    """P(U1 + ... + Un <= t), exact for a rational t (a Fraction); returns a float."""
    t = Fraction(t)
    if t <= 0:
        return 0.0
    if t >= n:
        return 1.0
    s = sum((-1) ** k * comb(n, k) * (t - k) ** n for k in range(int(t) + 1))
    return float(s / factorial(n))


def cdf_uni(n, x):
    t = Fraction(n, 2) + Fraction(x).limit_denominator(10 ** 6) * Fraction(sqrt(n / 12)).limit_denominator(10 ** 9)
    return irwin_hall_cdf(n, t)


def cdf_coin(n, x):
    return stats.binom.cdf(np.floor((x * np.sqrt(n) + n) / 2 + 1e-12), n, 0.5)


phi = stats.norm.pdf
Phi = stats.norm.cdf


def edgeworth(g1, g2, n, x, terms=2):
    one = -phi(x) * g1 * (x ** 2 - 1) / (6 * np.sqrt(n))
    if terms == 1:
        return one
    return one - phi(x) * (g2 * (x ** 3 - 3 * x) / 24 + g1 ** 2 * (x ** 5 - 10 * x ** 3 + 15 * x) / 72) / n


n = 10
xs = np.linspace(-4, 4, 321)
err_exp = cdf_exp(n, xs) - Phi(xs)
err_uni = np.array([cdf_uni(n, v) for v in xs]) - Phi(xs)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
a1.plot(xs, 1000 * err_exp, label="exact")
a1.plot(xs, 1000 * edgeworth(2, 6, n, xs, 1), "--", label="one-term Edgeworth")
a1.plot(xs, 1000 * edgeworth(2, 6, n, xs, 2), ":", label="two-term Edgeworth")
a1.set(title=f"exponential parent, n = {n}", xlabel="x", ylabel="error × 1000")
a2.plot(xs, 1000 * err_uni, label="exact")
a2.plot(xs, 1000 * edgeworth(0, -1.2, n, xs, 2), ":", label="two-term Edgeworth")
a2.set(title=f"uniform parent, n = {n}", xlabel="x")
a1.legend()
a2.legend()
fig.tight_layout()
plt.show()

# %% [markdown]
# ## 5. Reading the parent from the speed
# Largest error times the predicted rate: it levels off at a constant that identifies the parent.

# %%
def sup_err_smooth(cdf, n):
    g = np.linspace(-5, 5, 2001)
    return np.max(np.abs(np.array([cdf(n, v) for v in g]) - Phi(g)))


def sup_err_coin(n):
    k = np.arange(n + 1)
    xk = (2 * k - n) / np.sqrt(n)
    F = stats.binom.cdf(k, n, 0.5)
    left = F - stats.binom.pmf(k, n, 0.5)
    return max(np.max(np.abs(F - Phi(xk))), np.max(np.abs(left - Phi(xk))))


print(" n    exp: err  ×√n     uniform: err  ×n      coin: err  ×√n")
for n in [5, 10, 20, 40, 80]:
    ee = sup_err_smooth(cdf_exp, n)
    eu = sup_err_smooth(lambda m, v: cdf_uni(m, v), n) if n <= 40 else float("nan")
    ec = sup_err_coin(n)
    print(f"{n:3d}  {ee:.5f}  {ee * sqrt(n):.4f}   {eu:.6f}  {eu * n:.4f}   {ec:.5f}  {ec * sqrt(n):.4f}")
print("theory: 2·φ(0)/6 = %.4f   (|γ2|/24)·max|He3·φ| = %.4f   lattice d·φ(0)/2 = %.4f"
      % (2 * phi(0) / 6, 1.2 / 24 * np.max(np.abs((xs ** 3 - 3 * xs) * phi(xs))), 2 * phi(0) / 2))

n = 128
g1_read = 6 * sqrt(2 * pi) * sqrt(n) * (cdf_exp(n, 0.0) - 0.5)
print(f"\nskewness read from the speed at n = {n}: {g1_read:.3f}  (true value 2)")

# %% [markdown]
# ## 6. Berry–Esseen: the guaranteed bound
# sup |F_n − Φ| ≤ 0.4748·ρ/√n with ρ = E|X − μ|³/σ³ (Shevtsova 2011). For Exp(1), ρ = 12/e − 2.

# %%
rho = 12 / e - 2
for n in [10, 128]:
    print(f"n = {n:3d}: guaranteed ≤ {0.4748 * rho / sqrt(n):.4f}, actual {sup_err_smooth(cdf_exp, n):.4f}")
