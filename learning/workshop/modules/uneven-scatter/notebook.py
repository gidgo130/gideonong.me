import marimo

__generated_with = "0.25.0"
app = marimo.App(
    width="medium",
    app_title="Uneven Scatter · play with the code",
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Uneven Scatter — play with the code

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

    All data is simulated. True model y = 1 + 2x; the sensor's error SD is 0.5 + p% of the
    true reading.
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

    plt.rcParams.update({
        "figure.dpi": 100, "font.size": 11,
        "axes.edgecolor": "#c5d0c3", "axes.grid": True, "grid.color": "#dde5da",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    })
    return FIT, FIX, INK, PT, mo, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The helpers every trial uses

    `sigma` is the sensor's error SD at a reading. `ols` is the ordinary straight-line fit.
    `t_critical` turns a standard error into a 95% range. `hc3_se` is a *robust* standard
    error for the slope: it doesn't assume the scatter is even. `wls` is the weighted fit:
    each point counts in proportion to 1/σ², so precise readings matter more.

    The repeat-the-experiment trials fit hundreds of datasets at once: `ols_many` and
    `wls_many` do the same maths on a whole stack of experiments, one row each.
    """)
    return


@app.cell
def _(np):
    def sigma(x, p, pattern="high"):
        """Sensor error SD. 'high': 0.5 + p% of the reading. 'ends': worst at both ends of the range."""
        if pattern == "ends":
            return 0.5 + p / 100 * 21 * np.abs(x - 5.5) / 4.5
        return 0.5 + p / 100 * (1 + 2 * x)


    def ols(x, y):
        """Fit y = b0 + b1 * x. Returns b0, b1, fitted values, residuals, residual SD, slope SE."""
        n = len(x)
        b1, b0 = np.polyfit(x, y, 1)
        fitted = b0 + b1 * x
        residuals = y - fitted
        s = np.sqrt((residuals ** 2).sum() / (n - 2))
        se1 = s / np.sqrt(((x - x.mean()) ** 2).sum())
        return b0, b1, fitted, residuals, s, se1


    def t_critical(df):
        """The 95% two-sided t value for df degrees of freedom (a close series formula)."""
        z = 1.959964
        return (z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)
                + (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / (384 * df ** 3))


    def ols_many(X, Y):
        """Ordinary fits for a stack of experiments (one per row). Returns b0, b1, residuals, s, se1, sxx, mean x."""
        n = X.shape[1]
        mx = X.mean(axis=1, keepdims=True)
        my = Y.mean(axis=1, keepdims=True)
        sxx = ((X - mx) ** 2).sum(axis=1)
        b1 = ((X - mx) * (Y - my)).sum(axis=1) / sxx
        b0 = my[:, 0] - b1 * mx[:, 0]
        residuals = Y - (b0[:, None] + b1[:, None] * X)
        s = np.sqrt((residuals ** 2).sum(axis=1) / (n - 2))
        se1 = s / np.sqrt(sxx)
        return b0, b1, residuals, s, se1, sxx, mx[:, 0]


    def hc3_se_many(X, residuals, sxx, mx):
        """Robust (HC3) standard error of the slope, for a stack of experiments."""
        n = X.shape[1]
        leverage = 1 / n + (X - mx[:, None]) ** 2 / sxx[:, None]
        u = residuals / (1 - leverage)
        return np.sqrt(((X - mx[:, None]) ** 2 * u ** 2).sum(axis=1)) / sxx


    def wls_many(X, Y, W):
        """Weighted fits (weights W) for a stack of experiments. Returns b0, b1, s2, sum of weights, weighted mean x, weighted sxx."""
        n = X.shape[1]
        sw = W.sum(axis=1)
        mx = (W * X).sum(axis=1) / sw
        my = (W * Y).sum(axis=1) / sw
        sxx = (W * (X - mx[:, None]) ** 2).sum(axis=1)
        b1 = (W * (X - mx[:, None]) * (Y - my[:, None])).sum(axis=1) / sxx
        b0 = my - b1 * mx
        residuals = Y - (b0[:, None] + b1[:, None] * X)
        s2 = (W * residuals ** 2).sum(axis=1) / (n - 2)      # near 1 when the weights are right
        return b0, b1, s2, sw, mx, sxx

    return hc3_se_many, ols, ols_many, sigma, t_critical, wls_many


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Trial 1 · The fan

    Forty readings. Turn up the percentage part of the sensor's error and watch the residual
    plot. The spread is measured as the SD of the residuals in the lowest and highest third
    of fitted values.
    """)
    return


@app.cell
def _(mo):
    t1_p = mo.ui.slider(0, 25, step=1, value=12, show_value=True, label="Sensor error: 0.5 + this % of the reading")
    t1_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t1_p, t1_new])
    return t1_new, t1_p


@app.cell
def _(np, t1_new):
    t1_random = np.random.default_rng(5 + t1_new.value)
    t1_x = t1_random.uniform(1, 10, 40)
    t1_noise = t1_random.standard_normal(40)          # scaled by the sensor's error in the next cell
    return t1_noise, t1_x


@app.cell
def _(FIT, INK, PT, np, ols, plt, sigma, t1_noise, t1_p, t1_x):
    t1_y = 1 + 2 * t1_x + sigma(t1_x, t1_p.value) * t1_noise
    t1_b0, t1_b1, t1_fitted, t1_residuals, t1_s, t1_se1 = ols(t1_x, t1_y)

    # Spread in the lowest and highest third of fitted values
    t1_order = np.argsort(t1_fitted)
    t1_low = t1_residuals[t1_order[:13]].std(ddof=1)
    t1_high = t1_residuals[t1_order[-13:]].std(ddof=1)

    plt.close("all")
    t1_fig, (t1_left, t1_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t1_ends = np.array([0, 11])
    t1_left.scatter(t1_x, t1_y, s=18, color=PT, alpha=0.8)
    t1_left.plot(t1_ends, 1 + 2 * t1_ends, "--", color=INK, lw=1.4, label="the truth")
    t1_left.plot(t1_ends, t1_b0 + t1_b1 * t1_ends, color=FIT, lw=2.2, label="fitted line")
    t1_left.set(title=f"Sensor error 0.5 + {t1_p.value}% of reading", xlabel="x", ylabel="measured y", xlim=(0, 11))
    t1_left.legend(loc="upper left", frameon=False, fontsize=10)
    t1_right.scatter(t1_fitted, t1_residuals, s=18, color=PT, alpha=0.8)
    t1_right.axhline(0, color=INK, lw=1)
    t1_right.set(title="Residual plot", xlabel="fitted y", ylabel="residual")
    t1_fig.tight_layout()

    print(f"Fitted slope {t1_b1:.2f}   (true slope 2.00)")
    print(f"Residual spread, low third {t1_low:.2f}   high third {t1_high:.2f}   high ÷ low {t1_high / t1_low:.1f}")
    t1_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** With p at 0 the band is even. Turn p up and the residuals fan out
    toward high readings: the line itself is still fine (the slope stays near 2), but the
    error bars that assume even scatter are about to be wrong.

    ## Trial 2 · The error bars lie

    The experiment is repeated hundreds of times. Each time, the ordinary fit draws a 95%
    band where the next reading should land (checked at x = 2 and x = 9) and a 95% range for
    the slope, with the default standard error and with the robust one. The bars count how
    often each 95% promise held. Two noise patterns: worst at high readings, or worst at
    both ends of the range.
    """)
    return


@app.cell
def _(mo):
    t2_p = mo.ui.slider(0, 25, step=1, value=12, show_value=True, label="Sensor error: 0.5 + this % of the reading")
    t2_pattern = mo.ui.radio(options={"High readings": "high", "Both ends": "ends"}, value="High readings", inline=True,
                             label="Where the noise is worst")
    t2_reps = mo.ui.slider(100, 2000, step=100, value=400, show_value=True, label="Repeats of the experiment")
    t2_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t2_p, t2_pattern, t2_reps, t2_new])
    return t2_new, t2_p, t2_pattern, t2_reps


@app.cell
def _(hc3_se_many, np, ols_many, sigma, t_critical, wls_many):
    def simulate(random, reps, p, pattern):
        """Repeat the 40-reading experiment `reps` times; check every 95% promise. Returns a dict of percentages and the slopes."""
        n = 40
        X = random.uniform(1, 10, (reps, n))                       # one experiment per row
        Y = 1 + 2 * X + sigma(X, p, pattern) * random.standard_normal((reps, n))
        new_lo = 1 + 2 * 2 + sigma(2, p, pattern) * random.standard_normal(reps)     # a new reading at x = 2 …
        new_hi = 1 + 2 * 9 + sigma(9, p, pattern) * random.standard_normal(reps)     # … and one at x = 9
        tc = t_critical(n - 2)

        # Ordinary fit: prediction bands at x = 2 and 9, slope range with the default and the robust SE
        b0, b1, residuals, s, se1, sxx, mx = ols_many(X, Y)
        half_lo = tc * s * np.sqrt(1 + 1 / n + (2 - mx) ** 2 / sxx)
        half_hi = tc * s * np.sqrt(1 + 1 / n + (9 - mx) ** 2 / sxx)
        robust_se = hc3_se_many(X, residuals, sxx, mx)
        held = {
            "band_lo": np.abs(new_lo - (b0 + b1 * 2)) <= half_lo,
            "band_hi": np.abs(new_hi - (b0 + b1 * 9)) <= half_hi,
            "slope": np.abs(b1 - 2) <= tc * se1,
            "robust": np.abs(b1 - 2) <= tc * robust_se,
        }

        # Weighted fit (weights 1/σ²): its own prediction bands
        W = 1 / sigma(X, p, pattern) ** 2
        wb0, wb1, s2, sw, wmx, wsxx = wls_many(X, Y, W)
        whalf_lo = tc * np.sqrt(s2 * sigma(2, p, pattern) ** 2 + s2 * (1 / sw + (2 - wmx) ** 2 / wsxx))
        whalf_hi = tc * np.sqrt(s2 * sigma(9, p, pattern) ** 2 + s2 * (1 / sw + (9 - wmx) ** 2 / wsxx))
        held["w_band_lo"] = np.abs(new_lo - (wb0 + wb1 * 2)) <= whalf_lo
        held["w_band_hi"] = np.abs(new_hi - (wb0 + wb1 * 9)) <= whalf_hi

        percent = {key: 100 * value.mean() for key, value in held.items()}
        return percent, b1, wb1

    return (simulate,)


@app.cell
def _(
    FIT,
    INK,
    PT,
    np,
    ols,
    plt,
    sigma,
    simulate,
    t2_new,
    t2_p,
    t2_pattern,
    t2_reps,
    t_critical,
):
    t2_random = np.random.default_rng(17 + t2_new.value)
    t2_percent, t2_slopes, t2_wslopes = simulate(t2_random, t2_reps.value, t2_p.value, t2_pattern.value)

    # One fit and its band, with 200 new readings at x = 2 and x = 9
    t2_x = t2_random.uniform(1, 10, 40)
    t2_y = 1 + 2 * t2_x + sigma(t2_x, t2_p.value, t2_pattern.value) * t2_random.standard_normal(40)
    t2_b0, t2_b1, t2_fitted, t2_residuals, t2_s, t2_se1 = ols(t2_x, t2_y)
    t2_xx = np.linspace(0, 11, 200)
    t2_half = t_critical(38) * t2_s * np.sqrt(1 + 1 / 40 + (t2_xx - t2_x.mean()) ** 2 / ((t2_x - t2_x.mean()) ** 2).sum())

    plt.close("all")
    t2_fig, (t2_left, t2_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t2_left.fill_between(t2_xx, t2_b0 + t2_b1 * t2_xx - t2_half, t2_b0 + t2_b1 * t2_xx + t2_half, color=FIT, alpha=0.15,
                         label="95% band for the next reading")
    t2_left.plot(t2_xx, t2_b0 + t2_b1 * t2_xx, color=FIT, lw=2)
    t2_left.scatter(t2_x, t2_y, s=14, color=PT, alpha=0.8)
    for x_new in (2, 9):
        new_readings = 1 + 2 * x_new + sigma(x_new, t2_p.value, t2_pattern.value) * t2_random.standard_normal(200)
        half_here = t_critical(38) * t2_s * np.sqrt(1 + 1 / 40 + (x_new - t2_x.mean()) ** 2 / ((t2_x - t2_x.mean()) ** 2).sum())
        outside = np.abs(new_readings - (t2_b0 + t2_b1 * x_new)) > half_here
        jitter = x_new + t2_random.uniform(-0.15, 0.15, 200)
        t2_left.scatter(jitter[~outside], new_readings[~outside], s=6, color=PT, alpha=0.5)
        t2_left.scatter(jitter[outside], new_readings[outside], s=8, color=FIT, alpha=0.9)
    t2_left.set(title="One fit's band, 200 new readings at x = 2 and 9", xlabel="x", ylabel="y", xlim=(0, 11))
    t2_left.legend(loc="upper left", frameon=False, fontsize=9)

    t2_labels = ["band at x=2", "band at x=9", "slope, default", "slope, robust"]
    t2_values = [t2_percent["band_lo"], t2_percent["band_hi"], t2_percent["slope"], t2_percent["robust"]]
    t2_colors = [FIT if abs(v - 95) > 4 else PT for v in t2_values]
    t2_right.bar(t2_labels, t2_values, color=t2_colors, alpha=0.85)
    t2_right.axhline(95, ls="--", color=INK, lw=1)
    t2_right.set(title=f"How often each 95% promise held ({t2_reps.value} repeats)", ylim=(50, 100), ylabel="%")
    t2_right.tick_params(axis="x", labelsize=9)
    t2_fig.tight_layout()

    print(f"Band catches the new reading at x = 2: {t2_percent['band_lo']:.0f}%   at x = 9: {t2_percent['band_hi']:.0f}%")
    print(f"Slope range catches 2.00: default SE {t2_percent['slope']:.0f}%   robust SE {t2_percent['robust']:.0f}%")
    t2_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** With even scatter (p = 0) every bar sits near 95. With a fan, the band
    is too wide where the noise is small and too narrow where it is large: it catches far
    fewer than 95% of new readings at x = 9. The slope's default range is off too; the robust
    standard error fixes the slope's range but can't fix the bands. Red bars miss 95 by more
    than 4 points.

    ## Trial 3 · Weight each point by how much you trust it

    If you know each reading's uncertainty (from the datasheet or from repeat readings), a
    weighted fit gives each point a weight of 1/σ², so precise readings count more. Compare
    the two methods' bands and how tightly their slopes pile up over the repeats.
    """)
    return


@app.cell
def _(mo):
    t3_method = mo.ui.radio(options={"Ordinary": "ols", "Weighted (1/σ²)": "wls"}, value="Ordinary", inline=True, label="Fit")
    t3_p = mo.ui.slider(0, 25, step=1, value=12, show_value=True, label="Sensor error: 0.5 + this % of the reading")
    t3_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t3_method, t3_p, t3_new])
    return t3_method, t3_new, t3_p


@app.cell
def _(
    FIT,
    FIX,
    INK,
    PT,
    np,
    ols,
    plt,
    sigma,
    simulate,
    t3_method,
    t3_new,
    t3_p,
    t_critical,
):
    t3_random = np.random.default_rng(29 + t3_new.value)
    t3_percent, t3_slopes, t3_wslopes = simulate(t3_random, 400, t3_p.value, "high")

    # One dataset, fitted both ways
    t3_x = t3_random.uniform(1, 10, 40)
    t3_sigma = sigma(t3_x, t3_p.value)
    t3_y = 1 + 2 * t3_x + t3_sigma * t3_random.standard_normal(40)
    t3_xx = np.linspace(0, 11, 200)
    t3_tc = t_critical(38)
    if t3_method.value == "wls":
        t3_w = 1 / t3_sigma ** 2
        t3_sw = t3_w.sum()
        t3_mx = (t3_w * t3_x).sum() / t3_sw
        t3_my = (t3_w * t3_y).sum() / t3_sw
        t3_sxx = (t3_w * (t3_x - t3_mx) ** 2).sum()
        t3_b1 = (t3_w * (t3_x - t3_mx) * (t3_y - t3_my)).sum() / t3_sxx
        t3_b0 = t3_my - t3_b1 * t3_mx
        t3_s2 = (t3_w * (t3_y - t3_b0 - t3_b1 * t3_x) ** 2).sum() / 38
        t3_half = t3_tc * np.sqrt(t3_s2 * sigma(t3_xx, t3_p.value) ** 2 + t3_s2 * (1 / t3_sw + (t3_xx - t3_mx) ** 2 / t3_sxx))
        t3_color, t3_label = FIX, "weighted fit"
        t3_lo, t3_hi = t3_percent["w_band_lo"], t3_percent["w_band_hi"]
    else:
        t3_b0, t3_b1, t3_fitted, t3_residuals, t3_s, t3_se1 = ols(t3_x, t3_y)
        t3_half = t3_tc * t3_s * np.sqrt(1 + 1 / 40 + (t3_xx - t3_x.mean()) ** 2 / ((t3_x - t3_x.mean()) ** 2).sum())
        t3_color, t3_label = FIT, "ordinary fit"
        t3_lo, t3_hi = t3_percent["band_lo"], t3_percent["band_hi"]

    plt.close("all")
    t3_fig, (t3_left, t3_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t3_left.fill_between(t3_xx, t3_b0 + t3_b1 * t3_xx - t3_half, t3_b0 + t3_b1 * t3_xx + t3_half, color=t3_color, alpha=0.15)
    t3_left.plot(t3_xx, 1 + 2 * t3_xx, "--", color=INK, lw=1.4, label="the truth")
    t3_left.plot(t3_xx, t3_b0 + t3_b1 * t3_xx, color=t3_color, lw=2.2, label=t3_label)
    t3_left.scatter(t3_x, t3_y, s=16, color=PT, alpha=0.8)
    t3_left.set(title="The chosen fit and its 95% band for the next reading", xlabel="x", ylabel="y", xlim=(0, 11))
    t3_left.legend(loc="upper left", frameon=False, fontsize=10)
    t3_bins = np.linspace(1.4, 2.6, 37)
    t3_right.hist(t3_slopes, bins=t3_bins, histtype="step", color=FIT, lw=2, label=f"ordinary, SD {t3_slopes.std(ddof=1):.3f}")
    t3_right.hist(t3_wslopes, bins=t3_bins, histtype="step", color=FIX, lw=2, label=f"weighted, SD {t3_wslopes.std(ddof=1):.3f}")
    t3_right.axvline(2, ls="--", color=INK)
    t3_right.set(title="Fitted slopes from 400 repeats, both methods", xlabel="fitted slope", ylabel="repeats")
    t3_right.legend(frameon=False, fontsize=10)
    t3_fig.tight_layout()

    print(f"Fitted slope {t3_b1:.2f}   (true slope 2.00)")
    print(f"Band catches the new reading at x = 2: {t3_lo:.0f}%   at x = 9: {t3_hi:.0f}%")
    print(f"Slope scatter (SD) over 400 repeats: ordinary {t3_slopes.std(ddof=1):.3f}   weighted {t3_wslopes.std(ddof=1):.3f}")
    t3_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** The weighted band is narrow where the sensor is precise and wide
    where it isn't, so it keeps its 95% promise at both ends. Its slopes also pile up more
    tightly: giving the noisy points less say makes the estimate more precise, not just its
    error bar more honest. The weights only work if you know σ; with p at 0 both methods are
    the same fit.

    ## Make it your own

    - In `sigma`, try a different rule, for example a fixed error plus 1 unit above x = 6, and
      see which promises break.
    - In Trial 2's controls, push the repeats to 2000: the percentages settle down.
    - Give `wls_many` the *wrong* weights (in `simulate`, use `sigma(X, p / 2, pattern)`) and
      watch the weighted band stop keeping its promise.
    """)
    return


if __name__ == "__main__":
    app.run()
