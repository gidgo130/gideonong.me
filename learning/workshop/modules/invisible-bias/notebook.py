import marimo

__generated_with = "0.25.0"
app = marimo.App(
    width="medium",
    app_title="The Invisible Bias · play with the code",
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # The Invisible Bias — play with the code

    This is the module's Python, running in your browser. Nothing is installed on your
    computer and nothing is sent anywhere: the page downloads a Python runtime once (about
    the size of a short video), then everything runs here.

    - Move a slider and the figure below it redraws.
    - Every cell is editable. Change a number or a formula, then run the cell (the ▶ button on
      its right, or Ctrl+Enter). Cells that use its results rerun by themselves.
    - Broke something? Reload the page and you're back to the original.

    **Reading the code.** Lines starting with `#` are comments. Names starting with `t1_`
    … `t4_` belong to Trials 1 to 4; every name in the notebook is unique because marimo
    tracks which cell defines what (that's how it knows what to rerun). `mo.` is marimo
    itself: sliders, buttons and layout. `np.` is NumPy (arrays and maths) and `plt.` is
    Matplotlib (figures).

    All data is simulated. True model: y = 1 + 2x + error, so the true slope is 2.00.
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

    `ols` is the ordinary straight-line fit. `ols_many` does the same for a whole stack of
    experiments at once, one per row. `t_critical` turns a standard error into a 95% range.
    `deming` is the errors-in-x fit: it needs the ratio of the two noise variances, y over
    x, and the module's script uses SciPy's orthogonal distance regression for the same job.
    """)
    return


@app.cell
def _(np):
    def ols(x, y):
        """Fit y = b0 + b1 * x. Returns b0, b1, fitted values, residuals, residual SD, slope SE."""
        n = len(x)
        b1, b0 = np.polyfit(x, y, 1)
        fitted = b0 + b1 * x
        residuals = y - fitted
        s = np.sqrt((residuals ** 2).sum() / (n - 2))
        se1 = s / np.sqrt(((x - x.mean()) ** 2).sum())
        return b0, b1, fitted, residuals, s, se1


    def ols_many(X, Y):
        """Ordinary fits for a stack of experiments (one per row). Returns b1 and the slope's SE, one per row."""
        n = X.shape[1]
        mx = X.mean(axis=1, keepdims=True)
        my = Y.mean(axis=1, keepdims=True)
        sxx = ((X - mx) ** 2).sum(axis=1)
        b1 = ((X - mx) * (Y - my)).sum(axis=1) / sxx
        b0 = my[:, 0] - b1 * mx[:, 0]
        residuals = Y - (b0[:, None] + b1[:, None] * X)
        s = np.sqrt((residuals ** 2).sum(axis=1) / (n - 2))
        return b1, s / np.sqrt(sxx)


    def t_critical(df):
        """The 95% two-sided t value for df degrees of freedom (a close series formula)."""
        z = 1.959964
        return (z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)
                + (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / (384 * df ** 3))


    def deming(x, y, ratio):
        """Errors-in-x fit of y = b0 + b1 * x. `ratio` = (y noise variance) / (x noise variance). Returns b0, b1."""
        if not np.isfinite(ratio):                        # no noise in x: the ordinary fit is right
            b1, b0 = np.polyfit(x, y, 1)
            return b0, b1
        dx, dy = x - x.mean(), y - y.mean()
        sxx, syy, sxy = (dx ** 2).sum(), (dy ** 2).sum(), (dx * dy).sum()
        d = syy - ratio * sxx
        b1 = (d + np.sqrt(d ** 2 + 4 * ratio * sxy ** 2)) / (2 * sxy)
        return y.mean() - b1 * x.mean(), b1

    return deming, ols, ols_many, t_critical


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Trial 1 · Noise in y versus noise in x

    Fifty readings. Both sliders add random error to a sensor. Only one of them tilts the
    line. The x values are read off an instrument too, so they can be noisy just like y.
    """)
    return


@app.cell
def _(mo):
    t1_sy = mo.ui.slider(0, 4, step=0.1, value=1.0, show_value=True, label="Noise in the y sensor (SD)")
    t1_sx = mo.ui.slider(0, 3, step=0.1, value=0.0, show_value=True, label="Noise in the x sensor (SD)")
    t1_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t1_sy, t1_sx, t1_new])
    return t1_new, t1_sx, t1_sy


@app.cell
def _(np, t1_new):
    t1_random = np.random.default_rng(3 + t1_new.value)
    t1_x_true = t1_random.uniform(0, 10, 50)           # where x really was
    t1_zx = t1_random.standard_normal(50)              # the x sensor's error, before scaling
    t1_zy = t1_random.standard_normal(50)              # the y sensor's error, before scaling
    return t1_x_true, t1_zx, t1_zy


@app.cell
def _(FIT, INK, PT, np, ols, plt, t1_sx, t1_sy, t1_x_true, t1_zx, t1_zy):
    t1_x = t1_x_true + t1_sx.value * t1_zx             # what the x sensor reported
    t1_y = 1 + 2 * t1_x_true + t1_sy.value * t1_zy     # y depends on the TRUE x
    t1_b0, t1_b1, t1_fitted, t1_residuals, t1_s, t1_se1 = ols(t1_x, t1_y)

    plt.close("all")
    t1_fig, (t1_left, t1_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t1_ends = np.array([-6, 16])
    t1_left.scatter(t1_x, t1_y, s=20, color=PT, alpha=0.75)
    t1_left.plot(t1_ends, 1 + 2 * t1_ends, "--", color=INK, lw=1.4, label="the truth (slope 2.00)")
    t1_left.plot(t1_ends, t1_b0 + t1_b1 * t1_ends, color=FIT, lw=2.2, label=f"ordinary fit (slope {t1_b1:.2f})")
    t1_left.set(title="The data and the fit", xlabel="measured x", ylabel="measured y", xlim=(-6, 16), ylim=(-10, 32))
    t1_left.legend(loc="upper left", frameon=False, fontsize=10)
    t1_right.scatter(t1_fitted, t1_residuals, s=20, color=PT, alpha=0.75)
    t1_right.axhline(0, color=INK, lw=1)
    t1_right.set(title="Residual plot", xlabel="fitted y", ylabel="residual", ylim=(-12, 12))
    t1_fig.tight_layout()

    print(f"Fitted slope {t1_b1:.2f}   (true slope 2.00)   off by {t1_b1 - 2:+.2f}")
    t1_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** Noise in y scatters the points but the slope stays near 2.00 on
    average. Noise in x pulls the slope down, and the residual plot under it still looks
    perfectly healthy. That's the invisible bias: the leftovers can't show it.

    ## Trial 2 · Will more data fix it?

    The same experiment is repeated 400 times. Each bar counts how many repeats got a given
    slope. The software's 95% error bars should contain the true slope in 95% of repeats.
    """)
    return


@app.cell
def _(mo):
    t2_sx = mo.ui.slider(0, 3, step=0.1, value=1.5, show_value=True, label="Noise in the x sensor (SD)")
    t2_n = mo.ui.radio(options={"10": 10, "30": 30, "100": 100, "300": 300, "1000": 1000}, value="30", inline=True,
                       label="Readings per experiment")
    t2_new = mo.ui.button(label="Repeat all 400 again", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t2_sx, t2_n, t2_new])
    return t2_n, t2_new, t2_sx


@app.cell
def _(FIT, INK, PT, np, ols_many, plt, t2_n, t2_new, t2_sx, t_critical):
    t2_random = np.random.default_rng(7 + t2_new.value)
    t2_reps = 400
    t2_X_true = t2_random.uniform(0, 10, (t2_reps, t2_n.value))              # one experiment per row
    t2_X = t2_X_true + t2_sx.value * t2_random.standard_normal((t2_reps, t2_n.value))
    t2_Y = 1 + 2 * t2_X_true + t2_random.standard_normal((t2_reps, t2_n.value))
    t2_b1, t2_se1 = ols_many(t2_X, t2_Y)
    t2_caught = 100 * np.mean(np.abs(t2_b1 - 2) <= t_critical(t2_n.value - 2) * t2_se1)
    t2_low, t2_high = np.percentile(t2_b1, [2.5, 97.5])

    plt.close("all")
    t2_fig, t2_ax = plt.subplots(figsize=(10, 4.2))
    t2_ax.hist(t2_b1, bins=np.linspace(0.5, 2.5, 61), color=PT, alpha=0.6)
    t2_ax.axvline(2, color=INK, ls="--", lw=1.8, label="the truth")
    t2_ax.axvline(t2_b1.mean(), color=FIT, lw=2.4, label=f"average fit {t2_b1.mean():.2f}")
    t2_ax.set(title=f"Fitted slopes from 400 repeats, {t2_n.value} readings each", xlabel="fitted slope", ylabel="repeats",
              xlim=(0.5, 2.5))
    t2_ax.legend(loc="upper left", frameon=False, fontsize=10)
    t2_fig.tight_layout()

    print(f"Average fitted slope {t2_b1.mean():.2f}   (true slope 2.00)")
    print(f"Middle 95% of fits: {t2_low:.2f} to {t2_high:.2f}")
    print(f"Error bars that caught 2.00: {t2_caught:.0f}%   (should be 95%)")
    t2_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** More readings make the pile narrower, but it narrows around the
    wrong value: the average slope doesn't move back toward 2, and the error bars catch the
    truth less and less often. More data makes you more confident in the wrong answer. Set
    the x noise to 0 and everything behaves.

    ## Trial 3 · Something you didn't measure

    During the session, something drifts upward: the room warms, a battery sags, a bearing
    heats up. It nudges every y reading a little more as time goes on. You never measured it.
    Forty runs; the order you take them in is the only thing you control.
    """)
    return


@app.cell
def _(mo):
    t3_drift = mo.ui.slider(0, 10, step=0.5, value=6.0, show_value=True, label="Total drift in y over the session")
    t3_order = mo.ui.radio(options={"Low to high x": "sweep", "Randomized": "random"}, value="Low to high x", inline=True,
                           label="Order of the runs")
    t3_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t3_drift, t3_order, t3_new])
    return t3_drift, t3_new, t3_order


@app.cell
def _(np, t3_new):
    t3_random = np.random.default_rng(19 + t3_new.value)
    t3_noise = t3_random.standard_normal(40)
    t3_shuffle = t3_random.permutation(40)             # a random order of the 40 x settings
    return t3_noise, t3_shuffle


@app.cell
def _(FIT, INK, np, ols, plt, t3_drift, t3_noise, t3_order, t3_shuffle):
    t3_n = 40
    t3_time = np.arange(t3_n) / (t3_n - 1)             # 0 at the first run, 1 at the last
    if t3_order.value == "sweep":
        t3_levels = np.arange(t3_n)                    # run k uses the k-th x setting: low to high
    else:
        t3_levels = t3_shuffle
    t3_x = 10 * t3_levels / (t3_n - 1)
    t3_y = 1 + 2 * t3_x + t3_drift.value * t3_time + t3_noise
    t3_b0, t3_b1, t3_fitted, t3_residuals, t3_s, t3_se1 = ols(t3_x, t3_y)

    plt.close("all")
    t3_fig, (t3_left, t3_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t3_ends = np.array([-1, 11])
    t3_left.scatter(t3_x, t3_y, c=t3_time, cmap="Greys", vmin=-0.2, vmax=1.0, s=26, edgecolor="none")   # darker = later
    t3_left.plot(t3_ends, 1 + 2 * t3_ends, "--", color=INK, lw=1.4, label="the truth (slope 2.00)")
    t3_left.plot(t3_ends, t3_b0 + t3_b1 * t3_ends, color=FIT, lw=2.2, label=f"ordinary fit (slope {t3_b1:.2f})")
    t3_left.set(title="The data and the fit (darker = later)", xlabel="x setting", ylabel="measured y", xlim=(-1, 11))
    t3_left.legend(loc="upper left", frameon=False, fontsize=10)
    t3_right.scatter(np.arange(1, t3_n + 1), t3_residuals, c=t3_time, cmap="Greys", vmin=-0.2, vmax=1.0, s=26, edgecolor="none")
    t3_right.axhline(0, color=INK, lw=1)
    t3_right.set(title="Residuals in run order", xlabel="run number (time order)", ylabel="residual", ylim=(-8, 8))
    t3_fig.tight_layout()

    print(f"Fitted slope {t3_b1:.2f}   (true slope 2.00)   off by {t3_b1 - 2:+.2f}")
    t3_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** Sweeping x from low to high lines the drift up with x, so it hides
    inside the slope and the residuals look fine. Randomize the order and the drift shows in
    the residuals plotted in run order, while the slope comes out right. Randomizing the
    order is what exposes it.

    ## Trial 4 · What actually fixes noise in x

    Two remedies. One is a fitting method that allows for error in both x and y (the
    errors-in-x fit, called Deming or orthogonal distance regression), which needs the size
    of both errors. The other is a design choice: test over a wider range of x, so the noise
    is small compared with how much x varies. Sixty readings; the y noise SD is 1.
    """)
    return


@app.cell
def _(mo):
    t4_sx = mo.ui.slider(0, 3, step=0.1, value=2.0, show_value=True, label="Noise in the x sensor (SD)")
    t4_span = mo.ui.slider(4, 30, step=1, value=10, show_value=True, label="Range of x tested: 0 to …")
    t4_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t4_sx, t4_span, t4_new])
    return t4_new, t4_span, t4_sx


@app.cell
def _(np, t4_new):
    t4_random = np.random.default_rng(23 + t4_new.value)
    t4_u = t4_random.uniform(0, 1, 60)                 # where each true x sits in 0 … 1 (scaled by the span)
    t4_zx = t4_random.standard_normal(60)
    t4_zy = t4_random.standard_normal(60)
    return t4_u, t4_zx, t4_zy


@app.cell
def _(
    FIT,
    FIX,
    INK,
    PT,
    deming,
    np,
    ols,
    plt,
    t4_span,
    t4_sx,
    t4_u,
    t4_zx,
    t4_zy,
):
    t4_x_true = t4_span.value * t4_u
    t4_x = t4_x_true + t4_sx.value * t4_zx
    t4_y = 1 + 2 * t4_x_true + 1.0 * t4_zy
    t4_b0, t4_b1, t4_fitted, t4_residuals, t4_s, t4_se1 = ols(t4_x, t4_y)
    t4_ratio = 1.0 ** 2 / t4_sx.value ** 2 if t4_sx.value > 0 else np.inf     # y noise variance over x noise variance
    t4_d0, t4_d1 = deming(t4_x, t4_y, t4_ratio)

    # The slope an ordinary fit gives on average, by test range: the attenuation factor λ
    def expected_slope(span, sx):
        spread = span ** 2 / 12                        # variance of x spread evenly over 0 … span
        return 2 * spread / (spread + sx ** 2)

    t4_spans = np.linspace(2, 30, 200)

    plt.close("all")
    t4_fig, (t4_left, t4_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t4_ends = np.array([-6, 36])
    t4_left.scatter(t4_x, t4_y, s=20, color=PT, alpha=0.75)
    t4_left.plot(t4_ends, 1 + 2 * t4_ends, "--", color=INK, lw=1.4, label="the truth (slope 2.00)")
    t4_left.plot(t4_ends, t4_b0 + t4_b1 * t4_ends, color=FIT, lw=2.2, label=f"ordinary fit ({t4_b1:.2f})")
    t4_left.plot(t4_ends, t4_d0 + t4_d1 * t4_ends, color=FIX, lw=2.2, label=f"errors-in-x fit ({t4_d1:.2f})")
    t4_left.set(title="Three lines, one dataset", xlabel="measured x", ylabel="measured y",
                xlim=(-6, t4_span.value + 6), ylim=(-10, 2 * t4_span.value + 12))
    t4_left.legend(loc="upper left", frameon=False, fontsize=10)
    t4_right.plot(t4_spans, expected_slope(t4_spans, t4_sx.value), color=FIT, lw=2.2)
    t4_right.plot(t4_span.value, expected_slope(t4_span.value, t4_sx.value), "o", color=FIT, ms=8)
    t4_right.axhline(2, color=INK, ls="--", lw=1.4)
    t4_right.set(title="Widen the range, shrink the bias", xlabel="range of x tested (0 to …)",
                 ylabel="expected ordinary-fit slope", ylim=(0, 2.2))
    t4_fig.tight_layout()

    print(f"Ordinary fit {t4_b1:.2f}   Errors-in-x fit {t4_d1:.2f}   (true slope 2.00)")
    print(f"Ordinary fit expected at {expected_slope(t4_span.value, t4_sx.value):.2f} for this range and x noise")
    t4_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** The errors-in-x fit lands near 2.00 on average but wobbles more from
    sample to sample, and it only works if you know how noisy x is. Widening the range costs
    nothing you don't already have: with x spread over 0 to 30 and the same noise, the
    ordinary fit's expected slope is almost back at 2. The rule of thumb is the curve below.

    ### The rule of thumb

    How much the ordinary slope shrinks, as a function of the x noise divided by the spread
    (standard deviation) of x. At half the spread, the slope comes out 20% low.
    """)
    return


@app.cell
def _(FIT, INK, np, plt):
    plt.close("all")
    rule_ratio = np.linspace(0, 1.2, 200)
    rule_factor = 1 / (1 + rule_ratio ** 2)
    rule_fig, rule_ax = plt.subplots(figsize=(8, 3.8))
    rule_ax.plot(rule_ratio, 100 * rule_factor, color=FIT, lw=2.4)
    rule_ax.axhline(100, color=INK, ls="--", lw=1.4)
    rule_ax.plot(0.5, 80, "o", color=FIT)
    rule_ax.annotate("x noise at half the SD of x:\nslope comes out 20% low", (0.5, 80), xytext=(0.58, 88), fontsize=10)
    rule_ax.set(title="How much the slope shrinks", xlabel="noise in x ÷ standard deviation of x",
                ylabel="fitted slope, % of true", ylim=(0, 108))
    rule_fig.tight_layout()
    rule_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Make it your own

    - In Trial 1's data cell, make y depend on the *measured* x (`1 + 2 * t1_x`) instead of
      the true one: that's the case where x is a setting you dialed in (setpoint error), and
      the slope stays honest.
    - In Trial 2, change the 400 repeats to 2000 and watch the "caught" percentage settle.
    - In Trial 4, give `deming` the wrong ratio (try `t4_ratio * 4`) and see what a wrong
      guess about the noise does to the "fixed" slope.
    """)
    return


if __name__ == "__main__":
    app.run()
