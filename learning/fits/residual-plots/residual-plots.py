"""
Reading a Residual Plot -- companion script (Reading Your Fits, Module 2)
https://gideonong.me/learning/fits/residual-plots/

Reproduces the three trials from the interactive page with numpy, scipy and matplotlib,
and saves each figure as a PNG in ./figures (these are the figures used in the slides).

Run it:
  * Google Colab: upload this file (or paste it into a cell) and run. Everything needed is preinstalled.
  * Your own PC:  pip install numpy matplotlib scipy   then   python residual-plots.py

All data is simulated. Trials 1 and 3: y = 1 + 2x + error. Trial 2: T = 22 + 58*exp(-t/4) + error.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

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


def ols(x, y):
    """Straight-line least squares. Returns intercept, slope, fitted values, residuals."""
    b1, b0 = np.polyfit(x, y, 1)
    fitted = b0 + b1 * x
    return b0, b1, fitted, y - fitted


def make_y(x, e, pattern, sev, out_idx):
    """y = 1 + 2x + error, with one hidden problem. Array order = run order."""
    n = len(x)
    t = np.arange(n) / (n - 1)
    y = 1 + 2 * x
    if pattern == "curve":
        y = y + 0.45 * sev * ((x - 5) ** 2 - 25 / 3)
    if pattern == "fan":
        e = e * (1 + sev * 0.6 * x)
    if pattern == "drift":
        y = y + sev * 10 * t
    y = y + e
    if pattern == "outlier":
        y[out_idx] += sev * 14
    return y


# ---------------------------------------------------------------- Trial 1
def trial1(rng, n=40, sev=0.8):
    """The pattern gallery: each hidden problem, as residuals vs fitted and vs run order."""
    x = rng.uniform(0, 10, n)            # random x order, so time and x are unrelated
    e = rng.standard_normal(n)
    out_idx = int(np.argmin(abs(x - 8)))
    patterns = [("none", "None"), ("curve", "Curve"), ("fan", "Fan"), ("drift", "Drift"), ("outlier", "Outlier")]
    fig, axes = plt.subplots(2, 5, figsize=(17, 6.4), sharey="row")
    for col, (key, name) in enumerate(patterns):
        y = make_y(x, e, key, 0 if key == "none" else sev, out_idx)
        _, b1, fitted, resid = ols(x, y)
        ax = axes[0, col]
        ax.scatter(fitted, resid, s=16, color=PT, alpha=0.8)
        ax.axhline(0, color=INK, lw=1)
        ax.set(title=name, xlabel="fitted y")
        ax = axes[1, col]
        ax.scatter(np.arange(1, n + 1), resid, s=16, color=PT, alpha=0.8)
        ax.axhline(0, color=INK, lw=1)
        ax.set(xlabel="run number")
        print(f"Trial 1 | {name:8s} fitted slope {b1:.2f}")
    axes[0, 0].set_ylabel("residual\n(vs fitted value)")
    axes[1, 0].set_ylabel("residual\n(in run order)")
    fig.tight_layout()
    fig.savefig(OUT / "t1_patterns.png")


# ---------------------------------------------------------------- Trial 2
def cooling(t, t_inf, a, tau):
    return t_inf + a * np.exp(-t / tau)


def trial2(rng, noise=0.5, window=15.0):
    """A cooling curve: a straight line leaves a U in the residuals; the exponential doesn't."""
    t = np.arange(0, window + 1e-9, 0.25)                 # every 15 s, in minutes
    y = cooling(t, 22, 58, 4.0) + noise * rng.standard_normal(len(t))
    _, _, fit_line, res_line = ols(t, y)
    p, _ = curve_fit(cooling, t, y, p0=[y[-1], y[0] - y[-1], window / 4])
    fit_exp = cooling(t, *p)
    res_exp = y - fit_exp

    def r2(fitted):
        return 1 - ((y - fitted) ** 2).sum() / ((y - y.mean()) ** 2).sum()

    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), sharex=True)
    for col, (name, fitted, resid, color) in enumerate(
            [("Straight line", fit_line, res_line, FIT), ("Exponential (the physics)", fit_exp, res_exp, FIX)]):
        ax = axes[0, col]
        ax.scatter(t, y, s=10, color=PT, alpha=0.8)
        ax.plot(t, fitted, color=color, lw=2.4)
        ax.set(title=f"{name}: R² = {r2(fitted):.3f}", ylabel="temperature (°C)")
        ax = axes[1, col]
        ax.scatter(t, resid, s=10, color=PT, alpha=0.8)
        ax.axhline(0, color=INK, lw=1)
        ax.set(xlabel="time (min)", ylabel="residual (°C)")
    fig.tight_layout()
    fig.savefig(OUT / "t2_cooling.png")
    print(f"Trial 2 | line R² {r2(fit_line):.3f}   exponential R² {r2(fit_exp):.3f}   fitted tau {p[2]:.2f} min (true 4.0)")

    # A short recording hides the curve
    for w in (3, 15):
        m = t <= w
        _, _, f, _ = ols(t[m], y[m])
        rr = 1 - ((y[m] - f) ** 2).sum() / ((y[m] - y[m].mean()) ** 2).sum()
        print(f"Trial 2 | straight line over the first {w:2d} min: R² {rr:.3f}")


# ---------------------------------------------------------------- Trial 3
def influence(x, y):
    """Leverage h, studentized residual r and Cook's distance D for each point (straight-line fit)."""
    n = len(x)
    _, _, fitted, resid = ols(x, y)
    s = np.sqrt((resid ** 2).sum() / (n - 2))
    h = 1 / n + (x - x.mean()) ** 2 / ((x - x.mean()) ** 2).sum()
    r = resid / (s * np.sqrt(1 - h))
    D = r ** 2 * h / (2 * (1 - h))
    return h, r, D


def trial3(rng, n0=20):
    """One extra point: a lever point on the line, an outlier in the middle, an influential point."""
    x0 = rng.uniform(0, 10, n0)
    y0 = 1 + 2 * x0 + rng.standard_normal(n0)
    cases = [("Lever point on the line", 20, 0), ("Outlier in the middle", 5, 12), ("Influential point", 20, -10)]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    for ax, (title, xp, off) in zip(axes, cases):
        x = np.append(x0, xp)
        y = np.append(y0, 1 + 2 * xp + off)
        h, r, D = influence(x, y)
        b0, b1, _, _ = ols(x, y)
        c0, c1, _, _ = ols(x0, y0)
        xx = np.array([-1, 26])
        ax.scatter(x0, y0, s=18, color=PT, alpha=0.8)
        ax.scatter([xp], [y[-1]], s=140, facecolors="none", edgecolors=INK, lw=2)
        ax.plot(xx, 1 + 2 * xx, "--", color=INK, lw=1.6)
        ax.plot(xx, c0 + c1 * xx, color=FIX, lw=2.2, label=f"without it: {c1:.2f}")
        ax.plot(xx, b0 + b1 * xx, color=FIT, lw=2.2, label=f"with it: {b1:.2f}")
        ax.set(title=title, xlabel="x", xlim=(-1, 26))
        ax.text(0.97, 0.05, f"leverage {h[-1]:.2f}\nstudentized r {r[-1]:.2f}\nCook's D {D[-1]:.2f}",
                transform=ax.transAxes, ha="right", va="bottom", fontsize=10)
        ax.legend(loc="upper left", frameon=False, fontsize=10)
        print(f"Trial 3 | {title:24s} slope {b1:.2f} (without {c1:.2f})  h {h[-1]:.2f}  r {r[-1]:.2f}  D {D[-1]:.2f}")
    axes[0].set_ylabel("y")
    fig.tight_layout()
    fig.savefig(OUT / "t3_influence.png")


if __name__ == "__main__":
    rng = np.random.default_rng(7)
    trial1(rng)
    trial2(rng)
    trial3(rng)
    print(f"Figures saved in {OUT.resolve()}")
    plt.show()
