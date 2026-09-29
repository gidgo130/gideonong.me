"""
# Time-Ordered Data — Reading Your Fits, Module 4

The module's Python: https://gideonong.me/learning/fits/time-order/

It rebuilds the three trials from the interactive page with numpy, scipy and matplotlib,
and saves each figure as a PNG in ./figures (these are the figures used in the slides).

Run it:
  * Google Colab: use "Open in Colab" on the module page (or upload this file). Everything
    needed is preinstalled. Run the cells top to bottom; then change a number in any
    "knobs" cell and run that cell again.
  * Your own PC:  pip install numpy matplotlib scipy   then   python time-order.py

All data is simulated. Trial 1: y = 1 + 0.2t + AR(1) noise. Trial 2: T = 22 + 58·exp(-t/4) + noise.
Trial 3: steady value 50 with run-to-run offsets and AR(1) noise.
"""
# %% [markdown]
# ## Setup
#
# Imports, where the figures go, and one color meaning for the whole series: dashed ink is
# the truth, red is what an ordinary fit reports, blue is a corrected or better fit, grey
# dots are measured points. The random numbers get a fixed seed, so every run gives the
# same data; change the seed to draw a new sample.
#
# `ar1` makes "carry-over" noise: each sample's error is partly the previous sample's error
# (the fraction `rho`) plus something fresh. `acf` measures that carry-over in a residual
# series, lag by lag.

# %%
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit

# Windows consoles default to cp1252; print Greek letters and symbols safely.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

OUT = Path("figures")
OUT.mkdir(exist_ok=True)

INK, FIT, FIX, PT, GRID = "#1c2420", "#c93a22", "#1d5ea6", "#6b7b70", "#dde5da"
plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "font.size": 12,
    "axes.edgecolor": "#c5d0c3", "axes.grid": True, "grid.color": GRID,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
})

SEED = 3                 # change it to draw a new sample everywhere
rng = np.random.default_rng(SEED)


def ar1(rng, n, rho, sd=1.0):
    """AR(1) noise: each value = rho * previous + fresh noise, scaled to keep SD = sd."""
    z = rng.standard_normal(n)
    e = np.empty(n)
    e[0] = z[0]
    for i in range(1, n):
        e[i] = rho * e[i - 1] + np.sqrt(1 - rho ** 2) * z[i]
    return sd * e


def acf(r, lags=15):
    r = r - r.mean()
    return np.array([(r[L:] * r[:-L]).sum() / (r * r).sum() for L in range(1, lags + 1)])


# %% [markdown]
# ## Trial 1 · Sampling faster than the noise changes
#
# A slow drift, y = 1 + 0.2t, fitted with a line from 100 samples. With no carry-over the
# residuals are a jittery band and the slope's 95% range catches the true slope about 95% of
# the time. With carry-over 0.9 the residuals wander in slow waves, the autocorrelation bars
# stick out past the ±2/√n lines, and the same 95% range catches the truth far less often:
# 100 samples are not 100 independent pieces of evidence, and the error bars don't know it.

# %%
def trial1(rng, n=100, reps=2000, carryovers=(0.0, 0.9)):
    t = np.arange(n) / 10
    tc = stats.t.ppf(0.975, n - 2)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for rho, color in zip(carryovers, (PT, FIT)):
        y = 1 + 0.2 * t + ar1(rng, n, rho)
        b1, b0 = np.polyfit(t, y, 1)
        r = y - (b0 + b1 * t)
        axes[0].plot(np.arange(1, n + 1), r, "-o", ms=3, lw=0.8, color=color, label=f"carry-over {rho}")
        axes[1].bar(np.arange(1, 16) + (0.2 if rho else -0.2), acf(r), width=0.4, color=color, alpha=0.8)
        hit = 0
        for _ in range(reps):
            yy = 1 + 0.2 * t + ar1(rng, n, rho)
            X = np.c_[np.ones(n), t]
            b = np.linalg.lstsq(X, yy, rcond=None)[0]
            e = yy - X @ b
            se = np.sqrt(e @ e / (n - 2) / ((t - t.mean()) ** 2).sum())
            hit += abs(b[1] - 0.2) <= tc * se
        dw = (np.diff(r) ** 2).sum() / (r ** 2).sum()
        print(f"Trial 1 | carry-over {rho}: lag-1 {acf(r)[0]:.2f}, Durbin-Watson {dw:.2f}, slope range catches truth {100 * hit / reps:.0f}%")
    axes[0].axhline(0, color=INK, lw=1)
    axes[0].set(title="Residuals in time order", xlabel="sample number", ylabel="residual")
    axes[0].legend(frameon=False, fontsize=10)
    band = 2 / np.sqrt(n)
    for v in (band, -band):
        axes[1].axhline(v, ls="--", color=INK, lw=1)
    axes[1].set(title="Autocorrelation of the residuals", xlabel="lag (samples)", ylabel="autocorrelation")
    fig.tight_layout()
    fig.savefig(OUT / "t1_autocorr.png")


# %% Trial 1 knobs
T1_SAMPLES = 100             # samples in the recording
T1_REPS = 2000               # repeats used to count how often the slope's 95% range holds (the page uses 400)
T1_CARRYOVERS = (0.0, 0.9)   # the two carry-over strengths to compare (page slider 0 to 0.95)

trial1(rng, n=T1_SAMPLES, reps=T1_REPS, carryovers=T1_CARRYOVERS)

# %% [markdown]
# ## Trial 2 · The cooling-curve log trap
#
# A thermocouple cools from 80 °C toward a 22 °C room with time constant 4 min. The textbook
# shortcut: plot ln(T − T∞) against time and read −1/τ from the slope. Left: what that plot
# looks like once the tail is near room temperature; the noise explodes, and readings below
# T∞ can't even be logged. Right: the average time constant from many recordings, by the log
# method and by fitting the exponential directly, for three cases: normal noise, room
# temperature misjudged by 1 °C, and a noisier sensor. The direct fit stays near 4.0.

# %%
def cooling(t, t_inf, a, tau):
    return t_inf + a * np.exp(-t / tau)


def log_tau(t, y, t_inf):
    keep = y - t_inf > 0
    slope = np.polyfit(t[keep], np.log(y[keep] - t_inf), 1)[0]
    return -1 / slope, (~keep).sum()


def trial2(rng, reps=500, cases=(("noise 0.5 °C", 0.5, 0.0), ("noise 0.5, T_inf off by +1 °C", 0.5, 1.0), ("noise 2 °C", 2.0, 0.0))):
    t = np.arange(0, 20.001, 0.25)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    y = cooling(t, 22, 58, 4) + 0.5 * rng.standard_normal(len(t))
    keep = y - 22 > 0
    axes[0].scatter(t[keep], np.log(y[keep] - 22), s=12, color=PT)
    axes[0].plot(t, np.log(58) - t / 4, "--", color=INK, lw=1.6)
    axes[0].set(title="ln(T − T∞): the tail's noise explodes", xlabel="time (min)", ylabel="ln(T − T∞)", ylim=(-4, 5))
    results = {}
    for label, noise, room_err in cases:
        tl, td = [], []
        for _ in range(reps):
            yy = cooling(t, 22, 58, 4) + noise * rng.standard_normal(len(t))
            tau, _ = log_tau(t, yy, 22 + room_err)
            tl.append(tau)
            td.append(curve_fit(cooling, t, yy, p0=[yy[-1], yy[0] - yy[-1], 5])[0][2])
        results[label] = (np.mean(tl), np.mean(td))
        print(f"Trial 2 | {label:28s}: average tau, log method {np.mean(tl):.2f} min, direct fit {np.mean(td):.2f} min (true 4.0)")
    names = list(results)
    xs = np.arange(len(names))
    axes[1].bar(xs - 0.18, [results[k][0] for k in names], width=0.36, color=FIT, label="log, then line")
    axes[1].bar(xs + 0.18, [results[k][1] for k in names], width=0.36, color=FIX, label="fit the exponential")
    axes[1].axhline(4, ls="--", color=INK, lw=1)
    axes[1].set_xticks(xs, names, fontsize=9)
    axes[1].set(title=f"Average fitted τ over {reps} recordings", ylabel="τ (min)")
    axes[1].legend(frameon=False, fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "t2_logtrap.png")


# %% Trial 2 knobs
T2_REPS = 500            # recordings averaged per case (the page shows one at a time)
# Each case: (label, sensor noise in °C, how far the assumed room temperature is off, in °C)
T2_CASES = (
    ("noise 0.5 °C", 0.5, 0.0),
    ("noise 0.5, T_inf off by +1 °C", 0.5, 1.0),
    ("noise 2 °C", 2.0, 0.0),
)

trial2(rng, reps=T2_REPS, cases=T2_CASES)

# %% [markdown]
# ## Trial 3 · Every sample, or every run?
#
# You log a steady reading for 60 samples, reset the rig, and repeat for 5 runs. Each run
# settles a little differently (a run-to-run offset) and its samples carry over. Counting
# every sample as independent evidence gives a tiny error bar that misses the true value
# most of the time; counting the five run averages gives an honest one. The figure shows one
# set of five runs with each run's mean in red.

# %%
def trial3(rng, runs=5, per=60, run_sd=0.5, rho=0.8, reps=2000):
    hs = hr = 0
    for _ in range(reps):
        offsets = run_sd * rng.standard_normal(runs)
        data = np.array([50 + offsets[j] + ar1(rng, per, rho) for j in range(runs)])
        allv, means = data.ravel(), data.mean(axis=1)
        h_s = stats.t.ppf(0.975, allv.size - 1) * allv.std(ddof=1) / np.sqrt(allv.size)
        h_r = stats.t.ppf(0.975, runs - 1) * means.std(ddof=1) / np.sqrt(runs)
        hs += abs(allv.mean() - 50) <= h_s
        hr += abs(means.mean() - 50) <= h_r
    print(f"Trial 3 | 95% range catches 50: counting samples {100 * hs / reps:.0f}%, counting runs {100 * hr / reps:.0f}%")
    offsets = run_sd * rng.standard_normal(runs)
    data = np.array([50 + offsets[j] + ar1(rng, per, rho) for j in range(runs)])
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for j in range(runs):
        idx = np.arange(j * per, (j + 1) * per)
        if j % 2:
            ax.axvspan(idx[0], idx[-1], color=GRID, alpha=0.6)
        ax.scatter(idx, data[j], s=6, color=PT)
        ax.plot([idx[0] + 3, idx[-1] - 3], [data[j].mean()] * 2, color=FIT, lw=2.4)
    ax.axhline(50, ls="--", color=INK, lw=1)
    ax.set(title=f"Five runs: ranges catch 50 in {100 * hs / reps:.0f}% (samples) vs {100 * hr / reps:.0f}% (runs)",
           xlabel="sample number", ylabel="steady value")
    fig.tight_layout()
    fig.savefig(OUT / "t3_runs.png")


# %% Trial 3 knobs
T3_RUNS = 5              # runs (rig reset between them)
T3_SAMPLES_PER_RUN = 60  # samples logged per run
T3_RUN_SD = 0.5          # run-to-run offset, SD (page slider 0 to 1.5)
T3_CARRYOVER = 0.8       # carry-over within a run (page slider 0 to 0.95)
T3_REPS = 2000           # repeats used to count how often each 95% range holds

trial3(rng, runs=T3_RUNS, per=T3_SAMPLES_PER_RUN, run_sd=T3_RUN_SD, rho=T3_CARRYOVER, reps=T3_REPS)

# %% [markdown]
# ## Done
#
# The figures are also saved as PNG files in the `figures` folder (in Colab: the folder
# icon on the left). Copy `acf` into your own script to check any residual series for
# carry-over.

# %%
print(f"Figures saved in {OUT.resolve()}")
plt.show()
