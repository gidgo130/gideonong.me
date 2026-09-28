"""
Using and Reporting a Fit -- companion script (Reading Your Fits, Module 6)
https://gideonong.me/learning/fits/reporting/

Reproduces the first two trials from the interactive page with numpy, scipy and matplotlib,
prints a report line like Trial 3, and saves figures in ./figures (used in the slides).

Run it:
  * Google Colab: upload this file (or paste it into a cell) and run. Everything needed is preinstalled.
  * Your own PC:  pip install numpy matplotlib scipy   then   python reporting.py

All data is simulated. Trial 1: y = 1 + 2x, noise SD 2. Trial 2: y = 2(x - c), noise SD 1.
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


def fit(x, y):
    """Straight-line fit with its covariance matrix (intercept, slope) and residual SD."""
    n = len(x)
    X = np.c_[np.ones(n), x]
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ X.T @ y
    e = y - X @ b
    s = np.sqrt(e @ e / (n - 2))
    return b, s, XtXi, s ** 2 * XtXi


def bands(x0, b, s, XtXi, n):
    """95% half-widths at x0: for the true line (confidence) and for a new reading (prediction)."""
    v = np.c_[np.ones_like(x0), x0]
    lev = np.einsum("ij,jk,ik->i", v, XtXi, v)
    tc = stats.t.ppf(0.975, n - 2)
    return v @ b, tc * s * np.sqrt(lev), tc * s * np.sqrt(1 + lev)


# ---------------------------------------------------------------- Trial 1
def trial1(rng, n=15):
    x = np.sort(10 * (np.arange(n) + rng.uniform(0, 1, n)) / n)
    y = 1 + 2 * x + 2 * rng.standard_normal(n)
    b, s, XtXi, V = fit(x, y)
    xx = np.linspace(-5, 20, 300)
    yh, ci, pi = bands(xx, b, s, XtXi, n)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    ax.axvspan(-5, x.min(), color=GRID, alpha=0.6)
    ax.axvspan(x.max(), 20, color=GRID, alpha=0.6)
    ax.fill_between(xx, yh - pi, yh + pi, color=PT, alpha=0.18, label="next reading (prediction)")
    ax.fill_between(xx, yh - ci, yh + ci, color=FIT, alpha=0.2, label="true line (confidence)")
    ax.plot(xx, yh, color=FIT, lw=2)
    ax.plot(xx, 1 + 2 * xx, "--", color=INK, lw=1.4)
    ax.scatter(x, y, s=22, color=PT, zorder=3)
    ax.set(title="Two 95% bands", xlabel="x", ylabel="y")
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax = axes[1]
    ax.plot(xx, pi, color=PT, lw=2.2, label="next reading")
    ax.plot(xx, ci, color=FIT, lw=2.2, label="true line")
    ax.set(title="Band half-width along x", xlabel="x", ylabel="half-width", ylim=(0, None))
    ax.legend(frameon=False, fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "t1_bands.png")
    # The report line (Trial 3)
    tc = stats.t.ppf(0.975, n - 2)
    y5, _, p5 = bands(np.array([5.0]), b, s, XtXi, n)
    print("Trial 3 | report line:")
    print(f"  Linear least-squares fit, n = {n} readings over x = {x.min():.1f} to {x.max():.1f}.")
    print(f"  Slope b1 = {b[1]:.2f} ± {tc * np.sqrt(V[1, 1]):.2f} (95%); intercept b0 = {b[0]:.2f} ± {tc * np.sqrt(V[0, 0]):.2f}.")
    print(f"  Residual SD s = {s:.2f} (in y's units).")
    print(f"  Prediction at x = 5.0: {y5[0]:.1f} ± {p5[0]:.1f} for a single new reading (95%).")


# ---------------------------------------------------------------- Trial 2
def crossing(b, V):
    """x where the line crosses zero, with its SE ignoring and including the slope-intercept covariance."""
    x0 = -b[0] / b[1]
    naive = np.sqrt(V[0, 0] + x0 ** 2 * V[1, 1]) / abs(b[1])
    delta = np.sqrt(V[0, 0] + 2 * x0 * V[0, 1] + x0 ** 2 * V[1, 1]) / abs(b[1])
    return x0, naive, delta


def trial2(rng, n=12, reps=2000):
    rows = []
    for c in [0, 5, 10, 20]:
        tc = stats.t.ppf(0.975, n - 2)
        crosses, naive, delta = [], [], []
        for _ in range(reps):
            x = c + 5 * (np.arange(n) + rng.uniform(0, 1, n)) / n
            y = 2 * (x - c) + rng.standard_normal(n)
            b, s, XtXi, V = fit(x, y)
            x0, sn, sd = crossing(b, V)
            crosses.append(x0); naive.append(tc * sn); delta.append(tc * sd)
        rows.append((c, np.mean(naive), np.mean(delta), 1.96 * np.std(crosses, ddof=1)))
        print(f"Trial 2 | data {c:2d} from x=0: ±{rows[-1][1]:.2f} ignoring correlation, ±{rows[-1][2]:.2f} with it, actual ±{rows[-1][3]:.2f}")
    fig, ax = plt.subplots(figsize=(8, 4.4))
    cs = [r[0] for r in rows]
    ax.plot(cs, [r[1] for r in rows], "o-", color=FIT, label="ignoring correlation")
    ax.plot(cs, [r[2] for r in rows], "o-", color=FIX, label="with correlation (delta method)")
    ax.plot(cs, [r[3] for r in rows], "s--", color=INK, label="actual spread over repeats")
    ax.set(title="95% range on the zero crossing", xlabel="how far the data sit from x = 0", ylabel="± half-width")
    ax.legend(frameon=False, fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "t2_crossing.png")


if __name__ == "__main__":
    rng = np.random.default_rng(9)
    trial1(rng)
    trial2(rng)
    print(f"Figures saved in {OUT.resolve()}")
    plt.show()
