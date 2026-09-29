import marimo

__generated_with = "0.25.0"
app = marimo.App(
    width="medium",
    app_title="Time-Ordered Data · play with the code",
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Time-Ordered Data — play with the code

    This is the module's Python, running in your browser. Nothing is installed on your
    computer and nothing is sent anywhere: the page downloads a Python runtime once (about
    the size of a short video), then everything runs here.

    - Move a slider and the figure below it redraws.
    - Every cell is editable. Change a number or a formula, then run the cell (the ▶ button on
      its right, or Ctrl+Enter). Cells that use its results rerun by themselves.
    - Broke something? Reload the page and you're back to the original.

    **Reading the code.** Lines starting with `#` are comments. Names starting with `t1_`,
    `t2_`, `t3_` belong to Trials 1, 2 and 3; every name in the notebook is unique because
    marimo tracks which cell defines what (that's how it knows what to rerun). `mo.` is
    marimo itself: sliders, buttons and layout. `np.` is NumPy (arrays and maths) and `plt.`
    is Matplotlib (figures).

    All data is simulated. Trial 1: y = 1 + 0.2t + carry-over noise, SD 1. Trial 2:
    T = 22 + 58·e^(−t/4) + noise, every 15 s for 20 min. Trial 3: steady value 50, run
    offsets and carry-over noise with SD 1.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Setup

    Two libraries: NumPy for the numbers and Matplotlib for the figures. The colors mean the
    same thing on every plot in this series: dashed ink is the truth, red is what an ordinary
    fit reports, blue is a corrected or better fit, grey dots are measured points.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np

    # One color, one meaning, on every plot
    INK = "#1c2420"    # the truth
    FIT = "#c93a22"    # what an ordinary fit reports
    FIX = "#1d5ea6"    # a corrected or better fit
    PT = "#6b7b70"     # measured points
    GRID = "#dde5da"   # grid lines and shaded strips

    plt.rcParams.update({
        "figure.dpi": 100, "font.size": 11,
        "axes.edgecolor": "#c5d0c3", "axes.grid": True, "grid.color": GRID,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    })
    return FIT, FIX, GRID, INK, PT, mo, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The helpers every trial uses

    `carry_over_noise` makes noise where each sample's error is partly the previous sample's
    error (the fraction `rho`) plus something fresh, scaled so the SD stays 1. It makes a
    whole stack of recordings at once, one per row. `acf` measures the carry-over in a
    residual series, lag by lag. `ols_many` fits a straight line to every row of a stack.
    `t_critical` turns a standard error into a 95% range.
    """)
    return


@app.cell
def _(np):
    def carry_over_noise(random, reps, n, rho):
        """`reps` recordings of `n` samples of AR(1) noise with carry-over `rho`, SD 1. One recording per row."""
        fresh = random.standard_normal((reps, n))
        e = np.empty((reps, n))
        e[:, 0] = fresh[:, 0]
        for i in range(1, n):                          # each sample leans on the previous one
            e[:, i] = rho * e[:, i - 1] + np.sqrt(1 - rho ** 2) * fresh[:, i]
        return e


    def acf(r, lags=15):
        """Autocorrelation of a series at lags 1 … lags: how alike values are that far apart."""
        r = r - r.mean()
        return np.array([(r[L:] * r[:-L]).sum() / (r * r).sum() for L in range(1, lags + 1)])


    def durbin_watson(r):
        """Durbin-Watson statistic: 2 means no carry-over, 0 means strong positive carry-over."""
        return (np.diff(r) ** 2).sum() / (r ** 2).sum()


    def ols_many(X, Y):
        """Ordinary fits for a stack of experiments (one per row). Returns b0, b1, residuals, s, se1."""
        n = X.shape[1]
        mx = X.mean(axis=1, keepdims=True)
        my = Y.mean(axis=1, keepdims=True)
        sxx = ((X - mx) ** 2).sum(axis=1)
        b1 = ((X - mx) * (Y - my)).sum(axis=1) / sxx
        b0 = my[:, 0] - b1 * mx[:, 0]
        residuals = Y - (b0[:, None] + b1[:, None] * X)
        s = np.sqrt((residuals ** 2).sum(axis=1) / (n - 2))
        return b0, b1, residuals, s, s / np.sqrt(sxx)


    def t_critical(df):
        """The 95% two-sided t value for df degrees of freedom (a close series formula)."""
        z = 1.959964
        return (z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)
                + (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / (384 * df ** 3))

    return acf, carry_over_noise, durbin_watson, ols_many, t_critical


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Trial 1 · Sampling faster than the noise changes

    A slow drift, y = 1 + 0.2t, fitted with a line from 100 samples. The slider sets how
    strongly each sample's error carries over into the next one. The repeats count how often
    the slope's 95% range catches the true slope 0.2.
    """)
    return


@app.cell
def _(mo):
    t1_rho = mo.ui.slider(0, 0.95, step=0.05, value=0.8, show_value=True, label="Carry-over from one sample to the next")
    t1_reps = mo.ui.slider(100, 2000, step=100, value=400, show_value=True, label="Repeats of the recording")
    t1_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t1_rho, t1_reps, t1_new])
    return t1_new, t1_reps, t1_rho


@app.cell
def _(
    FIT,
    INK,
    PT,
    acf,
    carry_over_noise,
    durbin_watson,
    np,
    ols_many,
    plt,
    t1_new,
    t1_reps,
    t1_rho,
    t_critical,
):
    t1_random = np.random.default_rng(3 + t1_new.value)
    t1_n = 100
    t1_t = np.arange(t1_n) / 10                                  # time, 10 samples per unit
    t1_T = np.tile(t1_t, (t1_reps.value, 1))                    # the same times for every repeat
    t1_Y = 1 + 0.2 * t1_T + carry_over_noise(t1_random, t1_reps.value, t1_n, t1_rho.value)
    t1_b0, t1_b1, t1_residuals, t1_s, t1_se1 = ols_many(t1_T, t1_Y)
    t1_caught = 100 * np.mean(np.abs(t1_b1 - 0.2) <= t_critical(t1_n - 2) * t1_se1)

    # The first recording is the one shown
    t1_r = t1_residuals[0]
    t1_lag1 = acf(t1_r)[0]
    t1_effective = t1_n * (1 - t1_lag1) / (1 + t1_lag1)         # roughly how many independent samples this is worth
    t1_band = 2 / np.sqrt(t1_n)                                 # chance alone stays inside ±2/√n

    plt.close("all")
    t1_fig, (t1_left, t1_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t1_left.plot(np.arange(1, t1_n + 1), t1_r, "-o", ms=3, lw=0.8, color=PT)
    t1_left.axhline(0, color=INK, lw=1)
    t1_left.set(title="Residuals in time order", xlabel="sample number", ylabel="residual")
    t1_acf = acf(t1_r)
    t1_bar_colors = [FIT if abs(v) > t1_band else PT for v in t1_acf]
    t1_right.bar(np.arange(1, 16), t1_acf, color=t1_bar_colors, alpha=0.85)
    t1_right.axhline(t1_band, ls="--", color=INK, lw=1)
    t1_right.axhline(-t1_band, ls="--", color=INK, lw=1)
    t1_right.set(title="Autocorrelation of the residuals, lags 1–15", xlabel="lag (samples)", ylabel="autocorrelation",
                 ylim=(-1, 1))
    t1_fig.tight_layout()

    print(f"Lag-1 autocorrelation of residuals {t1_lag1:.2f}   Durbin–Watson {durbin_watson(t1_r):.2f} (2 = none)")
    print(f"Samples' worth of evidence, roughly {max(t1_effective, 1):.0f} of {t1_n}")
    print(f"Slope range catches the truth in {t1_caught:.0f}% of {t1_reps.value} repeats (should be 95%)")
    t1_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** With no carry-over the residuals are a jittery band, the bars stay
    inside the dashed lines, and the slope's range catches the truth about 95% of the time.
    Turn the carry-over up: the residuals wander in slow waves, the first bars stick out
    (red), and the same 95% range catches the truth far less often. A hundred samples taken
    faster than the noise changes are worth far fewer than a hundred independent readings,
    and the error bars don't know it.

    ## Trial 2 · The cooling-curve log trap

    A thermocouple cools from 80 °C toward a 22 °C room with time constant τ = 4 min, logged
    every 15 s for 20 min. The textbook shortcut: plot ln(T − T∞) against time and read
    −1/τ from the slope. Compare it with fitting the exponential directly. The averages over
    200 recordings show which method is biased.
    """)
    return


@app.cell
def _(mo):
    t2_method = mo.ui.radio(options={"Log, then line": "log", "Fit the exponential": "direct"}, value="Log, then line",
                            inline=True, label="Method")
    t2_noise = mo.ui.slider(0, 2, step=0.1, value=0.5, show_value=True, label="Sensor noise (°C)")
    t2_room = mo.ui.slider(-2, 2, step=0.1, value=0.0, show_value=True, label="Room temperature you assume, minus the true 22 °C")
    t2_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t2_method, t2_noise, t2_room, t2_new])
    return t2_method, t2_new, t2_noise, t2_room


@app.cell
def _(np):
    def cooling(t, t_inf, a, tau):
        """The cooling model: room temperature t_inf, drop a, time constant tau (minutes)."""
        return t_inf + a * np.exp(-t / tau)


    def log_method(t, y, t_inf):
        """Plot ln(y - t_inf) against t and read tau from the slope. Returns tau and how many points were dropped."""
        keep = y - t_inf > 0                              # the log of a negative number doesn't exist
        slope = np.polyfit(t[keep], np.log(y[keep] - t_inf), 1)[0]
        return -1 / slope, int((~keep).sum())


    def fit_exponential_many(t, Y, taus):
        """Direct least-squares fit of the cooling model to every row of Y. Returns the best tau per row.

        For a fixed tau the model is a straight line in z = exp(-t/tau), so each tau costs one
        line fit per row; try every tau in `taus` and keep the one with the smallest error.
        """
        best_error = np.full(Y.shape[0], np.inf)
        best_tau = np.zeros(Y.shape[0])
        Y_mean = Y.mean(axis=1)
        Y_centered = Y - Y_mean[:, None]
        for tau in taus:
            z = np.exp(-t / tau)
            z_centered = z - z.mean()
            a = Y_centered @ z_centered / (z_centered ** 2).sum()          # slope of y against z, per row
            t_inf = Y_mean - a * z.mean()
            error = ((Y - (t_inf[:, None] + a[:, None] * z)) ** 2).sum(axis=1)
            better = error < best_error
            best_error[better] = error[better]
            best_tau[better] = tau
        return best_tau


    TAU_GRID = np.geomspace(0.5, 50, 1200)                # 0.4% steps on a log scale, fine enough for 2 decimals
    return TAU_GRID, cooling, fit_exponential_many, log_method


@app.cell
def _(
    FIT,
    FIX,
    INK,
    PT,
    TAU_GRID,
    cooling,
    fit_exponential_many,
    log_method,
    np,
    plt,
    t2_method,
    t2_new,
    t2_noise,
    t2_room,
):
    t2_random = np.random.default_rng(13 + t2_new.value)
    t2_t = np.arange(0, 20.001, 0.25)
    t2_truth = cooling(t2_t, 22, 58, 4.0)
    t2_Y = t2_truth + t2_noise.value * t2_random.standard_normal((200, len(t2_t)))    # 200 recordings; the first is shown
    t2_y = t2_Y[0]
    t2_assumed_room = 22 + t2_room.value

    # Both methods on the recording shown
    t2_tau_log, t2_dropped = log_method(t2_t, t2_y, t2_assumed_room)
    t2_tau_direct = fit_exponential_many(t2_t, t2_y[None, :], TAU_GRID)[0]
    # Both methods averaged over all 200 recordings
    t2_avg_log = np.mean([log_method(t2_t, row, t2_assumed_room)[0] for row in t2_Y])
    t2_avg_direct = np.mean(fit_exponential_many(t2_t, t2_Y, TAU_GRID))

    if t2_method.value == "log":
        t2_tau, t2_color, t2_label = t2_tau_log, FIT, "log, then line"
        t2_intercept = np.polyfit(t2_t[t2_y - t2_assumed_room > 0], np.log(t2_y[t2_y - t2_assumed_room > 0] - t2_assumed_room), 1)[1]
        t2_curve = t2_assumed_room + np.exp(t2_intercept) * np.exp(-t2_t / t2_tau)
    else:
        t2_tau, t2_color, t2_label = t2_tau_direct, FIX, "fit the exponential"
        t2_z = np.exp(-t2_t / t2_tau)
        t2_a, t2_t_inf = np.polyfit(t2_z, t2_y, 1)
        t2_curve = cooling(t2_t, t2_t_inf, t2_a, t2_tau)

    plt.close("all")
    t2_fig, (t2_left, t2_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t2_kept = t2_y - t2_assumed_room > 0
    t2_left.scatter(t2_t[t2_kept], np.log(t2_y[t2_kept] - t2_assumed_room), s=12, color=PT)
    t2_left.scatter(t2_t[~t2_kept], np.zeros((~t2_kept).sum()) - 3.8, s=18, facecolors="none", edgecolors=FIT)   # dropped
    t2_left.plot(t2_t, np.log(58) - t2_t / 4, "--", color=INK, lw=1.4, label="the truth")
    t2_left.set(title="ln(T − T∞) against time", xlabel="time (min)", ylabel="ln(T − T∞)", ylim=(-4, 5))
    t2_left.legend(loc="upper right", frameon=False, fontsize=10)
    t2_right.scatter(t2_t, t2_y, s=10, color=PT, alpha=0.8)
    t2_right.plot(t2_t, t2_truth, "--", color=INK, lw=1.4, label="the truth")
    t2_right.plot(t2_t, t2_curve, color=t2_color, lw=2.2, label=t2_label)
    t2_right.set(title="The cooling curve and the chosen fit", xlabel="time (min)", ylabel="temperature (°C)", ylim=(15, 85))
    t2_right.legend(loc="upper right", frameon=False, fontsize=10)
    t2_fig.tight_layout()

    print(f"τ from the log method {t2_tau_log:.2f} min   τ from the direct fit {t2_tau_direct:.2f} min   (true 4.00)")
    print(f"Points the log method had to drop: {t2_dropped}")
    print(f"Average τ over 200 recordings: log method {t2_avg_log:.2f} min   direct fit {t2_avg_direct:.2f} min")
    t2_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** Near room temperature T − T∞ is tiny, so its logarithm swings wildly
    and readings below T∞ can't be logged at all: the tail, where the noise is worst, gets
    the most say in the log-method line. Add a little sensor noise, or misjudge the room
    temperature by a degree, and the log method's τ drifts away from 4.0 on average. The
    direct fit weights every reading fairly and stays near 4.0.

    ## Trial 3 · Every sample, or every run?

    You log a steady reading for 60 samples, reset the rig, and repeat for 5 runs. Each run
    settles a little differently (a run-to-run offset) and its samples carry over. Count
    every sample as evidence, or count the five run averages: which 95% range is honest?
    """)
    return


@app.cell
def _(mo):
    t3_counting = mo.ui.radio(options={"Each sample (300)": "sample", "Each run (5)": "run"}, value="Each sample (300)",
                              inline=True, label="What counts as one piece of evidence")
    t3_run_sd = mo.ui.slider(0, 1.5, step=0.05, value=0.5, show_value=True, label="Run-to-run offset (SD)")
    t3_rho = mo.ui.slider(0, 0.95, step=0.05, value=0.8, show_value=True, label="Carry-over within a run")
    t3_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t3_counting, t3_run_sd, t3_rho, t3_new])
    return t3_counting, t3_new, t3_rho, t3_run_sd


@app.cell
def _(
    FIT,
    FIX,
    GRID,
    INK,
    PT,
    carry_over_noise,
    np,
    plt,
    t3_counting,
    t3_new,
    t3_rho,
    t3_run_sd,
    t_critical,
):
    t3_random = np.random.default_rng(31 + t3_new.value)
    t3_runs, t3_per, t3_reps = 5, 60, 400

    # 400 repeats of the whole experiment, each 5 runs of 60 samples: shape (repeat, run, sample)
    t3_offsets = t3_run_sd.value * t3_random.standard_normal((t3_reps, t3_runs, 1))
    t3_noise = carry_over_noise(t3_random, t3_reps * t3_runs, t3_per, t3_rho.value).reshape(t3_reps, t3_runs, t3_per)
    t3_data = 50 + t3_offsets + t3_noise

    # Counting every sample: 300 values, 299 degrees of freedom
    t3_all = t3_data.reshape(t3_reps, -1)
    t3_est_sample = t3_all.mean(axis=1)
    t3_half_sample = t_critical(t3_all.shape[1] - 1) * t3_all.std(axis=1, ddof=1) / np.sqrt(t3_all.shape[1])
    # Counting runs: 5 run averages, 4 degrees of freedom
    t3_means = t3_data.mean(axis=2)
    t3_est_run = t3_means.mean(axis=1)
    t3_half_run = t_critical(t3_runs - 1) * t3_means.std(axis=1, ddof=1) / np.sqrt(t3_runs)
    t3_caught_sample = 100 * np.mean(np.abs(t3_est_sample - 50) <= t3_half_sample)
    t3_caught_run = 100 * np.mean(np.abs(t3_est_run - 50) <= t3_half_run)

    if t3_counting.value == "sample":
        t3_est, t3_half = t3_est_sample, t3_half_sample
    else:
        t3_est, t3_half = t3_est_run, t3_half_run

    plt.close("all")
    t3_fig, (t3_left, t3_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    for j in range(t3_runs):                                       # the first repeat is the one shown
        index = np.arange(j * t3_per, (j + 1) * t3_per)
        if j % 2:
            t3_left.axvspan(index[0], index[-1], color=GRID, alpha=0.6)
        t3_left.scatter(index, t3_data[0, j], s=6, color=PT)
        t3_left.plot([index[0] + 3, index[-1] - 3], [t3_data[0, j].mean()] * 2, color=INK, lw=2.4)
    t3_left.axhline(50, ls="--", color=INK, lw=1)
    t3_left.set(title="Five runs of 60 samples (ticks: each run's mean)", xlabel="sample number", ylabel="steady value")
    for repeat in range(20):                                       # the 95% range from 20 repeats
        hit = abs(t3_est[repeat] - 50) <= t3_half[repeat]
        t3_right.plot([repeat, repeat], [t3_est[repeat] - t3_half[repeat], t3_est[repeat] + t3_half[repeat]],
                      color=FIX if hit else FIT, lw=2)
    t3_right.axhline(50, ls="--", color=INK, lw=1)
    t3_right.set(title="The 95% range from 20 repeats", xlabel="repeat", ylabel="steady value")
    t3_fig.tight_layout()

    print(f"Estimated steady value {t3_est[0]:.2f} ± {t3_half[0]:.2f} (95% range)   truth 50")
    print(f"Range catches 50, counting samples: {t3_caught_sample:.0f}%   counting runs: {t3_caught_run:.0f}%   (of {t3_reps} repeats)")
    t3_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** Counting every sample gives a tiny error bar that misses the true
    value most of the time: the 300 samples share their run's offset and carry over, so they
    are nowhere near 300 independent readings. Counting the five run averages gives a wider
    range that keeps its 95% promise. Set the offset and the carry-over to 0 and the two agree.

    ## Make it your own

    - In Trial 1, change `1 + 0.2 * t1_T` to a curve and see whether the autocorrelation
      bars can tell carry-over from a wrong shape (they can't; the residual plot can).
    - In Trial 2, shorten the recording (`np.arange(0, 8.001, 0.25)`): which method suffers?
    - In Trial 3, change the 5 runs to 10 and the 60 samples to 30.
    """)
    return


if __name__ == "__main__":
    app.run()
