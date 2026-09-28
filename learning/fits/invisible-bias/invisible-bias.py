"""
The Invisible Bias -- companion script (Reading Your Fits, Module 5)
https://gideonong.me/learning/fits/invisible-bias/

Reproduces the four trials from the interactive page with numpy, matplotlib and scipy,
and saves each figure as a PNG in ./figures (these are the figures used in the slides).

Run it:
  * Google Colab: upload this file (or paste it into a cell) and run. Everything needed is preinstalled.
  * Your own PC:  pip install numpy matplotlib scipy   then   python invisible-bias.py

All data is simulated. True model: y = 1 + 2x + error, so the true slope is 2.00.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import odr, stats

TRUE_B0, TRUE_B1 = 1.0, 2.0
OUT = Path("figures")
OUT.mkdir(exist_ok=True)

# One color meaning across the whole module
INK, FIT, FIX, PT, GRID = "#1c2420", "#c93a22", "#1d5ea6", "#6b7b70", "#dde5da"
plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "font.size": 12,
    "axes.edgecolor": "#c5d0c3", "axes.grid": True, "grid.color": GRID,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
})


def ols(x, y):
    """Ordinary least squares for y = b0 + b1*x. Returns b0, b1, the slope's standard error, fitted, residuals."""
    n = len(x)
    b1, b0 = np.polyfit(x, y, 1)
    fitted = b0 + b1 * x
    resid = y - fitted
    s = np.sqrt(resid @ resid / (n - 2))
    se1 = s / np.sqrt(((x - x.mean()) ** 2).sum())
    return b0, b1, se1, fitted, resid


def odr_fit(x, y, sx, sy):
    """Orthogonal distance regression: allows error in x (sx) and y (sy)."""
    b1, b0 = np.polyfit(x, y, 1)
    model = odr.Model(lambda B, x: B[0] + B[1] * x)
    out = odr.ODR(odr.RealData(x, y, sx=sx, sy=sy), model, beta0=[b0, b1]).run()
    return out.beta[0], out.beta[1]


def draw_lines(ax, xlim, fits):
    xx = np.array(xlim)
    ax.plot(xx, TRUE_B0 + TRUE_B1 * xx, "--", color=INK, lw=1.8, label="truth (slope 2.00)")
    for (b0, b1), color, label in fits:
        ax.plot(xx, b0 + b1 * xx, color=color, lw=2.6, label=label)
    ax.set_xlim(xlim)


# ---------------------------------------------------------------- Trial 1
def trial1(rng):
    """Noise in y vs noise in x: only x-noise tilts the fitted line, and the residual plot stays healthy."""
    n = 50
    x_true = rng.uniform(0, 10, n)
    zx, zy = rng.standard_normal(n), rng.standard_normal(n)
    cases = [("Noisy y sensor (σ = 3), exact x", 0.0, 3.0), ("Noisy x sensor (σ = 2.5), good y", 2.5, 1.0)]

    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    for col, (title, sx, sy) in enumerate(cases):
        x = x_true + sx * zx
        y = TRUE_B0 + TRUE_B1 * x_true + sy * zy
        b0, b1, _, fitted, resid = ols(x, y)
        ax = axes[0, col]
        ax.scatter(x, y, s=22, color=PT, alpha=0.75)
        draw_lines(ax, (-6, 16), [((b0, b1), FIT, f"ordinary fit (slope {b1:.2f})")])
        ax.set(title=title, xlabel="measured x", ylabel="measured y", ylim=(-10, 32))
        ax.legend(loc="upper left", frameon=False, fontsize=10)
        ax = axes[1, col]
        ax.scatter(fitted, resid, s=22, color=PT, alpha=0.75)
        ax.axhline(0, color=INK, lw=1)
        ax.set(title="Its residual plot: looks healthy", xlabel="fitted y", ylabel="residual", ylim=(-12, 12))
        print(f"Trial 1 | {title:34s} fitted slope = {b1:.2f}")
    fig.tight_layout()
    fig.savefig(OUT / "t1_noise_y_vs_x.png")


# ---------------------------------------------------------------- Trial 2
def trial2(rng, sx=1.5, reps=400):
    """Repeat the experiment many times: x-noise shifts the whole pile, and more data doesn't move it back."""
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    for ax, n in zip(axes, (10, 100, 1000)):
        slopes, caught = np.empty(reps), 0
        t_crit = stats.t.ppf(0.975, n - 2)          # 95% two-sided, n - 2 degrees of freedom
        for k in range(reps):
            x_true = rng.uniform(0, 10, n)
            x = x_true + sx * rng.standard_normal(n)
            y = TRUE_B0 + TRUE_B1 * x_true + rng.standard_normal(n)
            _, b1, se1, _, _ = ols(x, y)
            slopes[k] = b1
            caught += abs(b1 - TRUE_B1) <= t_crit * se1
        ax.hist(slopes, bins=np.linspace(0.5, 2.5, 61), color=PT, alpha=0.6)
        ax.axvline(TRUE_B1, color=INK, ls="--", lw=1.8)
        ax.axvline(slopes.mean(), color=FIT, lw=2.4)
        ax.set(title=f"{n} points per experiment", xlabel="fitted slope")
        ax.text(0.03, 0.95, f"average {slopes.mean():.2f}\n95% error bars caught\nthe truth: {caught / reps:.0%}",
                transform=ax.transAxes, va="top", fontsize=10, color=FIT)
        print(f"Trial 2 | n = {n:4d}: mean slope {slopes.mean():.2f}, CI coverage {caught / reps:.0%}")
    axes[0].set_ylabel(f"number of repeats (of {reps})")
    fig.suptitle(f"x-noise σ = {sx}: the pile narrows around the wrong value", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "t2_more_data.png")


# ---------------------------------------------------------------- Trial 3
def trial3(rng, drift=6.0, n=40):
    """An unmeasured drift: sweeping x in order hides it in the slope; randomizing exposes it."""
    e = rng.standard_normal(n)
    perm = rng.permutation(n)
    t = np.arange(n) / (n - 1)                      # time: run 0 ... run n-1
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    for col, (title, levels) in enumerate([("Runs swept low to high x", np.arange(n)), ("Runs in random order", perm)]):
        x = 10 * levels / (n - 1)
        y = TRUE_B0 + TRUE_B1 * x + drift * t + e
        b0, b1, _, _, resid = ols(x, y)
        ax = axes[0, col]
        ax.scatter(x, y, c=t, cmap="Greys", vmin=-0.2, vmax=1.0, s=26, edgecolor="none")
        draw_lines(ax, (-1, 11), [((b0, b1), FIT, f"ordinary fit (slope {b1:.2f})")])
        ax.set(title=title, xlabel="x setting", ylabel="measured y")
        ax.legend(loc="upper left", frameon=False, fontsize=10)
        ax = axes[1, col]
        ax.scatter(np.arange(1, n + 1), resid, c=t, cmap="Greys", vmin=-0.2, vmax=1.0, s=26, edgecolor="none")
        ax.axhline(0, color=INK, lw=1)
        ax.set(title="Residuals in run order", xlabel="run number (time order)", ylabel="residual", ylim=(-8, 8))
        print(f"Trial 3 | {title:26s} fitted slope = {b1:.2f}")
    fig.tight_layout()
    fig.savefig(OUT / "t3_drift.png")


# ---------------------------------------------------------------- Trial 4
def trial4(rng, sx=2.0, sy=1.0, n=60):
    """Fixes: an errors-in-x fit (ODR), or a wider test range."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    x_true = rng.uniform(0, 10, n)
    x = x_true + sx * rng.standard_normal(n)
    y = TRUE_B0 + TRUE_B1 * x_true + sy * rng.standard_normal(n)
    b0, b1, *_ = ols(x, y)
    o0, o1 = odr_fit(x, y, sx, sy)
    ax = axes[0]
    ax.scatter(x, y, s=22, color=PT, alpha=0.75)
    draw_lines(ax, (-6, 16), [((b0, b1), FIT, f"ordinary fit ({b1:.2f})"), ((o0, o1), FIX, f"ODR fit ({o1:.2f})")])
    ax.set(title=f"Same data, x-noise σ = {sx}", xlabel="measured x", ylabel="measured y")
    ax.legend(loc="upper left", frameon=False, fontsize=10)
    print(f"Trial 4 | OLS slope {b1:.2f}   ODR slope {o1:.2f}")

    # One sample can mislead, so repeat it: ODR removes the bias but wobbles more from sample to sample
    reps_ols, reps_odr = [], []
    for _ in range(300):
        xt = rng.uniform(0, 10, n)
        xr = xt + sx * rng.standard_normal(n)
        yr = TRUE_B0 + TRUE_B1 * xt + sy * rng.standard_normal(n)
        reps_ols.append(ols(xr, yr)[1])
        reps_odr.append(odr_fit(xr, yr, sx, sy)[1])
    summary = (f"Over 300 repeats:\nordinary {np.mean(reps_ols):.2f} ± {np.std(reps_ols):.2f}\n"
               f"ODR {np.mean(reps_odr):.2f} ± {np.std(reps_odr):.2f}")
    ax.text(0.97, 0.05, summary, transform=ax.transAxes, ha="right", va="bottom", fontsize=10)
    print("Trial 4 | " + summary.replace("\n", "  "))

    # Expected ordinary-fit slope vs how wide a range of x you test (same noise)
    span = np.linspace(2, 30, 200)
    lam = (span ** 2 / 12) / (span ** 2 / 12 + sx ** 2)   # reliability ratio for x ~ uniform(0, span)
    ax = axes[1]
    ax.plot(span, TRUE_B1 * lam, color=FIT, lw=2.6)
    ax.axhline(TRUE_B1, color=INK, ls="--", lw=1.8)
    ax.set(title="Widen the range, shrink the bias", xlabel="range of x tested (0 to …)",
           ylabel="expected ordinary-fit slope", ylim=(0, 2.2))
    for s in (10, 30):
        v = TRUE_B1 * (s ** 2 / 12) / (s ** 2 / 12 + sx ** 2)
        ax.plot(s, v, "o", color=FIT)
        ax.annotate(f"0 to {s}: {v:.2f}", (s, v), textcoords="offset points", xytext=(-8, -18), ha="right", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "t4_fixes.png")


# ---------------------------------------------------------------- Attenuation curve
def attenuation_curve():
    r = np.linspace(0, 1.2, 200)
    lam = 1 / (1 + r ** 2)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(r, 100 * lam, color=FIT, lw=2.6)
    ax.axhline(100, color=INK, ls="--", lw=1.5)
    ax.plot(0.5, 80, "o", color=FIT)
    ax.annotate("x-noise at half the SD of x:\nslope comes out 20% low", (0.5, 80), xytext=(0.58, 88), fontsize=10)
    ax.set(title="How much the slope shrinks", xlabel="noise in x ÷ standard deviation of x   (σu / σx)",
           ylabel="fitted slope, % of true", ylim=(0, 108))
    fig.tight_layout()
    fig.savefig(OUT / "attenuation.png")


if __name__ == "__main__":
    rng = np.random.default_rng(3)
    trial1(rng)
    trial2(rng)
    trial3(rng)
    trial4(rng)
    attenuation_curve()
    print(f"Figures saved in {OUT.resolve()}")
    plt.show()
