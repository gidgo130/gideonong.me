"""
Uneven Scatter -- companion script (Reading Your Fits, Module 3)
https://gideonong.me/learning/fits/uneven-scatter/

Reproduces the three trials from the interactive page with numpy, scipy and matplotlib,
and saves each figure as a PNG in ./figures (these are the figures used in the slides).

Run it:
  * Google Colab: upload this file (or paste it into a cell) and run. Everything needed is preinstalled.
  * Your own PC:  pip install numpy matplotlib scipy   then   python uneven-scatter.py

All data is simulated: y = 1 + 2x, sensor error SD = 0.5 + p% of the true reading.
"""
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

N, P = 40, 12          # readings per experiment, % of reading
X_LO, X_HI = 2, 9      # where the prediction band is checked


def sigma(x, p=P, pattern="high"):
    """Sensor error SD. 'high': 0.5 + p% of the reading. 'ends': worst at both ends of the range."""
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


# ---------------------------------------------------------------- Trial 1
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


# ---------------------------------------------------------------- Trial 2 and 3
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


def trial2_3(rng):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    labels = ["x=2 band", "x=9 band", "slope", "robust slope"]
    for ax, pattern, title in [(axes[0], "high", "Noise worst at high readings"), (axes[1], "ends", "Noise worst at both ends")]:
        c, bo, bw = simulate(rng, pattern)
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


if __name__ == "__main__":
    rng = np.random.default_rng(5)
    trial1(rng)
    trial2_3(rng)
    print(f"Figures saved in {OUT.resolve()}")
    plt.show()
