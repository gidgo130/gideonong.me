"""
# Uneven Scatter — Reading Your Fits, Module 3

The module's Python: https://gideonong.me/learning/fits/uneven-scatter/

It rebuilds the three trials from the interactive page with numpy, scipy and matplotlib,
and saves each figure as a PNG in ./figures (these are the figures used in the slides).

Run it:
  * Google Colab: use "Open in Colab" on the module page (or upload this file). Everything
    needed is preinstalled. Run the cells top to bottom; then change a number in the
    "knobs" cell and run the cells below it again.
  * Your own PC:  pip install numpy matplotlib scipy   then   python uneven-scatter.py

All data is simulated: y = 1 + 2x, sensor error SD = 0.5 + p% of the true reading.
"""
# %% [markdown]
# ## Setup
#
# Imports, where the figures go, and one color meaning for the whole series: dashed ink is
# the truth, red is what an ordinary fit reports, blue is a corrected or better fit, grey
# dots are measured points. The random numbers get a fixed seed, so every run gives the
# same data; change the seed to draw a new sample.

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

OUT = Path("figures")
OUT.mkdir(exist_ok=True)

INK, FIT, FIX, PT, GRID = "#1c2420", "#c93a22", "#1d5ea6", "#6b7b70", "#dde5da"
plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "font.size": 12,
    "axes.edgecolor": "#c5d0c3", "axes.grid": True, "grid.color": GRID,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
})

SEED = 5                 # change it to draw a new sample everywhere
rng = np.random.default_rng(SEED)

# %% [markdown]
# ## Knobs for the whole module
#
# Many sensors are rated as a percentage of the reading, so big readings carry big errors.
# `P` is that percentage: the sensor's error SD is 0.5 + P% of the true reading. Change a
# number here, then run the cells below again.

# %% Module knobs
N = 40                   # readings per experiment
P = 12                   # sensor error, % of the reading (page slider 0 to 25)
X_LO, X_HI = 2, 9        # where the prediction band is checked
REPS = 2000              # how many times Trials 2 and 3 repeat the experiment (the page uses 400)

# %% [markdown]
# ## The fitting helpers
#
# `sigma` is the sensor's error at a reading. `ols` is the ordinary straight-line fit, with
# the pieces the error bars need. `pred_half` is the 95% half-width of the band where the
# next reading should land. `hc3_se` is a robust standard error for the slope (it doesn't
# assume the scatter is even). `wls` is the weighted fit: each point weighted by 1/σ², so
# precise readings count more.

# %%
def sigma(x, p=None, pattern="high"):
    """Sensor error SD. 'high': 0.5 + p% of the reading. 'ends': worst at both ends of the range."""
    if p is None:
        p = P
    if pattern == "ends":
        return 0.5 + p / 100 * 21 * np.abs(x - 5.5) / 4.5
    return 0.5 + p / 100 * (1 + 2 * x)


def sample(rng, pattern="high"):
    x = rng.uniform(1, 10, N)
    return x, 1 + 2 * x + sigma(x, pattern=pattern) * rng.standard_normal(N)


def ols(x, y):
    """Slope, intercept, fitted, residuals, residual SD, and the pieces for bands and HC3."""
    X = np.c_[np.ones_like(x), x]
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ X.T @ y
    e = y - X @ b
    s = np.sqrt(e @ e / (len(x) - 2))
    return b, e, s, X, XtXi


def pred_half(x0, s, XtXi, n):
    """95% prediction half-width at x0 for an ordinary fit."""
    v = np.array([1, x0])
    return stats.t.ppf(0.975, n - 2) * s * np.sqrt(1 + v @ XtXi @ v)


def hc3_se(X, XtXi, e):
    h = np.einsum("ij,jk,ik->i", X, XtXi, X)
    V = XtXi @ X.T @ np.diag((e / (1 - h)) ** 2) @ X @ XtXi
    return np.sqrt(V[1, 1])


def wls(x, y, w):
    X = np.c_[np.ones_like(x), x]
    W = np.diag(w)
    A = np.linalg.inv(X.T @ W @ X)
    b = A @ X.T @ W @ y
    e = y - X @ b
    s2 = (w * e ** 2).sum() / (len(x) - 2)
    return b, A, s2


# %% [markdown]
# ## Trial 1 · The fan
#
# One experiment. Left: the data, the truth (dashed) and the ordinary fit (red). Right: the
# residuals fan out as the fitted value grows. The line itself is fine; it's the error bars
# that will be wrong.

# %%
def trial1(rng):
    x, y = sample(rng)
    b, e, *_ = ols(x, y)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    xx = np.array([0, 11])
    axes[0].scatter(x, y, s=18, color=PT)
    axes[0].plot(xx, 1 + 2 * xx, "--", color=INK, lw=1.6)
    axes[0].plot(xx, b[0] + b[1] * xx, color=FIT, lw=2.4)
    axes[0].set(title=f"Sensor error 0.5 + {P}% of reading", xlabel="x", ylabel="measured y")
    fitted = y - e
    axes[1].scatter(fitted, e, s=18, color=PT)
    axes[1].axhline(0, color=INK, lw=1)
    axes[1].set(title="Residuals fan out", xlabel="fitted y", ylabel="residual")
    fig.tight_layout()
    fig.savefig(OUT / "t1_fan.png")
    print(f"Trial 1 | fitted slope {b[1]:.2f} (true 2.00)")


trial1(rng)

# %% [markdown]
# ## Trials 2 and 3 · The error bars lie, and the weighted fix
#
# The experiment is repeated `REPS` times. Each time, the ordinary fit draws a 95% band where
# the next reading should land (checked at x = 2 and x = 9) and a 95% range for the slope,
# with and without the robust standard error. The bars show how often each promise held;
# red bars miss 95% by more than 4 points. Two noise patterns: worst at high readings, and
# worst at both ends of the range.
#
# Trial 3 repeats the same runs with a weighted fit (weights 1/σ²). Its slopes are tighter
# and its bands keep their promise. The histogram compares the two fits' slopes.

# %%
def simulate(rng, pattern, reps=2000):
    tc = stats.t.ppf(0.975, N - 2)
    c = dict(lo=0, hi=0, slope=0, robust=0, wlo=0, whi=0)
    b_ols, b_wls = [], []
    for _ in range(reps):
        x, y = sample(rng, pattern)
        b, e, s, X, XtXi = ols(x, y)
        new_lo = 1 + 2 * X_LO + sigma(X_LO, pattern=pattern) * rng.standard_normal()
        new_hi = 1 + 2 * X_HI + sigma(X_HI, pattern=pattern) * rng.standard_normal()
        c["lo"] += abs(new_lo - (b[0] + b[1] * X_LO)) <= pred_half(X_LO, s, XtXi, N)
        c["hi"] += abs(new_hi - (b[0] + b[1] * X_HI)) <= pred_half(X_HI, s, XtXi, N)
        c["slope"] += abs(b[1] - 2) <= tc * s * np.sqrt(XtXi[1, 1])
        c["robust"] += abs(b[1] - 2) <= tc * hc3_se(X, XtXi, e)
        w = 1 / sigma(x, pattern=pattern) ** 2
        bw, A, s2 = wls(x, y, w)
        for x0, ynew, key in [(X_LO, new_lo, "wlo"), (X_HI, new_hi, "whi")]:
            v = np.array([1, x0])
            half = tc * np.sqrt(s2 * sigma(x0, pattern=pattern) ** 2 + s2 * v @ A @ v)
            c[key] += abs(ynew - v @ bw) <= half
        b_ols.append(b[1])
        b_wls.append(bw[1])
    return {k: 100 * v / reps for k, v in c.items()}, np.array(b_ols), np.array(b_wls)


def trial2_3(rng, reps=2000):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    labels = ["x=2 band", "x=9 band", "slope", "robust slope"]
    for ax, pattern, title in [(axes[0], "high", "Noise worst at high readings"), (axes[1], "ends", "Noise worst at both ends")]:
        c, bo, bw = simulate(rng, pattern, reps)
        vals = [c["lo"], c["hi"], c["slope"], c["robust"]]
        ax.bar(labels, vals, color=[FIT if abs(v - 95) > 4 else PT for v in vals], alpha=0.8)
        ax.axhline(95, ls="--", color=INK, lw=1)
        ax.set(title=title, ylim=(50, 100), ylabel="how often the 95% promise held (%)")
        print(f"Trial 2 | {pattern:4s}: band x=2 {vals[0]:.0f}%  band x=9 {vals[1]:.0f}%  slope {vals[2]:.0f}%  robust {vals[3]:.0f}%")
        if pattern == "high":
            print(f"Trial 3 | weighted band x=2 {c['wlo']:.0f}%  x=9 {c['whi']:.0f}%  |  slope SD ordinary {bo.std(ddof=1):.3f}  weighted {bw.std(ddof=1):.3f}")
            f3, a3 = plt.subplots(figsize=(7, 4.4))
            bins = np.linspace(1.4, 2.6, 37)
            a3.hist(bo, bins=bins, histtype="step", color=FIT, lw=2, label=f"ordinary, SD {bo.std(ddof=1):.3f}")
            a3.hist(bw, bins=bins, histtype="step", color=FIX, lw=2, label=f"weighted, SD {bw.std(ddof=1):.3f}")
            a3.axvline(2, ls="--", color=INK)
            a3.set(title="Weighted fit: tighter slopes", xlabel="fitted slope", ylabel="repeats")
            a3.legend(frameon=False, fontsize=10)
            f3.tight_layout()
            f3.savefig(OUT / "t3_weighted.png")
    fig.tight_layout()
    fig.savefig(OUT / "t2_coverage.png")


trial2_3(rng, reps=REPS)

# %% [markdown]
# ## Done
#
# The figures are also saved as PNG files in the `figures` folder (in Colab: the folder
# icon on the left). Copy any function above into your own script: `wls` is the weighted
# fit you'd use with real datasheet uncertainties.

# %%
print(f"Figures saved in {OUT.resolve()}")
plt.show()
