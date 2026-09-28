"""
Why R² Isn't Enough -- companion script (Reading Your Fits, Module 1)
https://gideonong.me/learning/fits/r-squared/

Reproduces the three trials from the interactive page with numpy and matplotlib,
and saves each figure as a PNG in ./figures (these are the figures used in the slides).

Run it:
  * Google Colab: upload this file (or paste it into a cell) and run. Everything needed is preinstalled.
  * Your own PC:  pip install numpy matplotlib   then   python r-squared.py

Trial 1 uses Anscombe's quartet (Anscombe 1973, The American Statistician 27(1)).
Trials 2 and 3 are simulated from y = 1 + 2x + noise.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT = Path("figures")
OUT.mkdir(exist_ok=True)

# One color meaning across the whole series
INK, FIT, FIX, PT, GRID = "#1c2420", "#c93a22", "#1d5ea6", "#6b7b70", "#dde5da"
plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "font.size": 12,
    "axes.edgecolor": "#c5d0c3", "axes.grid": True, "grid.color": GRID,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def r2(y, fitted):
    return 1 - ((y - fitted) ** 2).sum() / ((y - y.mean()) ** 2).sum()


# ---------------------------------------------------------------- Trial 1
X123 = np.array([10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5], float)
QUARTET = [
    (X123, [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68]),
    (X123, [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74]),
    (X123, [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73]),
    (np.array([8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8], float), [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89]),
]


def trial1():
    """Anscombe's quartet: same line, same R², four different stories."""
    fig, axes = plt.subplots(2, 4, figsize=(15, 6.8))
    for k, (x, y) in enumerate(QUARTET):
        y = np.array(y)
        b1, b0 = np.polyfit(x, y, 1)
        fitted = b0 + b1 * x
        ax = axes[0, k]
        ax.scatter(x, y, s=28, color=PT)
        xx = np.array([2, 20])
        ax.plot(xx, b0 + b1 * xx, color=FIT, lw=2.2)
        ax.set(title=f"{'I II III IV'.split()[k]}:  R² = {r2(y, fitted):.2f}", xlim=(2, 20), ylim=(2, 14), xlabel="x")
        ax = axes[1, k]
        ax.scatter(fitted, y - fitted, s=28, color=PT)
        ax.axhline(0, color=INK, lw=1)
        ax.set(xlabel="fitted y", ylim=(-4, 4))
        print(f"Trial 1 | set {k + 1}: slope {b1:.3f}  intercept {b0:.2f}  R² {r2(y, fitted):.3f}")
    axes[0, 0].set_ylabel("y")
    axes[1, 0].set_ylabel("residual")
    fig.tight_layout()
    fig.savefig(OUT / "t1_anscombe.png")


# ---------------------------------------------------------------- Trial 2
def trial2(rng, sd=2.0, n=30):
    """R² grows with the tested range; the residual SD doesn't."""
    spans = np.linspace(1, 30, 100)
    expected = (4 * spans ** 2 / 12) / (4 * spans ** 2 / 12 + sd ** 2)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    for span, color in [(3, PT), (30, FIT)]:
        x = np.sort(rng.uniform(0, span, n))
        y = 1 + 2 * x + sd * rng.standard_normal(n)
        b1, b0 = np.polyfit(x, y, 1)
        fitted = b0 + b1 * x
        s = np.sqrt(((y - fitted) ** 2).sum() / (n - 2))
        ax.scatter(x, y, s=16, color=color, alpha=0.8, label=f"0 to {span}: R² {r2(y, fitted):.2f}, residual SD {s:.2f}")
        print(f"Trial 2 | range 0 to {span:2d}: R² {r2(y, fitted):.3f}, residual SD {s:.2f}")
    ax.set(title="Same sensor, two test ranges", xlabel="x", ylabel="y")
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax = axes[1]
    ax.plot(spans, expected, color=PT, lw=2.4)
    ax.set(title="R² you'd expect, by test range (noise SD 2)", xlabel="range of x tested (0 to …)", ylabel="expected R²", ylim=(0, 1))
    fig.tight_layout()
    fig.savefig(OUT / "t2_range.png")


# ---------------------------------------------------------------- Trial 3
def trial3(rng, n=12, sd=2.0):
    """More polynomial terms: R² always rises, prediction gets worse."""
    x = np.sort(10 * (np.arange(n) + rng.uniform(0, 1, n)) / n)
    y = 1 + 2 * x + sd * rng.standard_normal(n)
    xs = (x - 5) / 5                               # scale to [-1, 1] so high degrees stay stable
    def fit(deg, xi, yi):
        return np.polyfit((xi - 5) / 5, yi, deg)
    loo, r2s = [], []
    for deg in range(1, 10):
        c = fit(deg, x, y)
        r2s.append(r2(y, np.polyval(c, xs)))
        errs = [y[k] - np.polyval(fit(deg, np.delete(x, k), np.delete(y, k)), xs[k]) for k in range(n)]
        loo.append(np.sqrt(np.mean(np.square(errs))))
        print(f"Trial 3 | degree {deg}: R² {r2s[-1]:.3f}  error on unseen point {loo[-1]:.2f}  prediction at x=12 {np.polyval(c, 1.4):.1f} (truth 25)")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    xx = np.linspace(-0.5, 13, 300)
    ax.axvspan(10, 13, color=GRID, alpha=0.6)
    ax.plot(xx, 1 + 2 * xx, "--", color=INK, lw=1.6)
    for deg, color in [(1, FIX), (6, FIT)]:
        ax.plot(xx, np.polyval(fit(deg, x, y), (xx - 5) / 5), color=color, lw=2.2, label=f"degree {deg}: R² {r2s[deg - 1]:.3f}")
    ax.scatter(x, y, s=30, color=PT, zorder=3)
    ax.set(title="Twelve readings, two fits", xlabel="x", ylabel="y", ylim=(-10, 45))
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax = axes[1]
    ax.plot(range(1, 10), np.minimum(loo, 12), "o-", color=PT)
    ax.axhline(sd, ls="--", color=INK, lw=1)
    ax.set(title="Error on a point the fit hasn't seen", xlabel="polynomial degree", ylabel="RMS error (capped at 12)", ylim=(0, 12))
    fig.tight_layout()
    fig.savefig(OUT / "t3_terms.png")


if __name__ == "__main__":
    rng = np.random.default_rng(11)
    trial1()
    trial2(rng)
    trial3(rng)
    print(f"Figures saved in {OUT.resolve()}")
    plt.show()
