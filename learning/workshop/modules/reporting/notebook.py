import marimo

__generated_with = "0.25.0"
app = marimo.App(
    width="medium",
    app_title="Using and Reporting a Fit · play with the code",
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Using and Reporting a Fit — play with the code

    This is the module's Python, running in your browser. Nothing is installed on your
    computer and nothing is sent anywhere: the page downloads a Python runtime once (about
    the size of a short video), then everything runs here.

    - Move a slider and the figure below it redraws.
    - Every cell is editable. Change a number or a formula, then run the cell (the ▶ button on
      its right, or Ctrl+Enter). Cells that use its results rerun by themselves.
    - Broke something? Reload the page and you're back to the original.

    **Reading the code.** Lines starting with `#` are comments. Names starting with `t1_`
    and `t2_` belong to Trials 1 and 2; every name in the notebook is unique because marimo
    tracks which cell defines what (that's how it knows what to rerun). `mo.` is marimo
    itself: sliders, buttons and layout. `np.` is NumPy (arrays and maths) and `plt.` is
    Matplotlib (figures).

    All data is simulated. Trial 1: y = 1 + 2x, noise SD 2, 15 readings. Trial 2:
    y = 2(x − c) with c the left edge of the data, noise SD 1, 12 readings.
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

    `fit` is the straight-line fit with everything the error bars need: the residual SD, the
    mean of x and the spread of x. `t_critical` turns a standard error into a 95% range.
    `bands` gives, at any x, the fitted y and two 95% half-widths: for the true line
    (confidence) and for a single new reading (prediction).
    """)
    return


@app.cell
def _(np):
    def fit(x, y):
        """Fit y = b0 + b1 * x. Returns b0, b1, residual SD, mean of x, sum of squared x deviations."""
        n = len(x)
        b1, b0 = np.polyfit(x, y, 1)
        residuals = y - (b0 + b1 * x)
        s = np.sqrt((residuals ** 2).sum() / (n - 2))
        return b0, b1, s, x.mean(), ((x - x.mean()) ** 2).sum()


    def t_critical(df):
        """The 95% two-sided t value for df degrees of freedom (a close series formula)."""
        z = 1.959964
        return (z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)
                + (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / (384 * df ** 3))


    def bands(x0, b0, b1, s, mean_x, sxx, n):
        """At x0: the fitted y, the 95% half-width for the true line, and for a single new reading."""
        leverage = 1 / n + (x0 - mean_x) ** 2 / sxx      # grows away from the middle of the data
        tc = t_critical(n - 2)
        return b0 + b1 * x0, tc * s * np.sqrt(leverage), tc * s * np.sqrt(1 + leverage)

    return bands, fit, t_critical


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Trial 1 · Two bands: the line, and the next reading

    Fifteen readings over x = 0 to 10. Slide the point where you want an answer, including
    past the data.
    """)
    return


@app.cell
def _(mo):
    t1_at = mo.ui.slider(-5, 20, step=0.5, value=5.0, show_value=True, label="Where you want an answer (x)")
    t1_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t1_at, t1_new])
    return t1_at, t1_new


@app.cell
def _(np, t1_new):
    t1_random = np.random.default_rng(9 + t1_new.value)
    t1_x = np.sort(10 * (np.arange(15) + t1_random.uniform(0, 1, 15)) / 15)     # 15 readings over 0 … 10
    t1_y = 1 + 2 * t1_x + 2 * t1_random.standard_normal(15)
    return t1_x, t1_y


@app.cell
def _(FIT, GRID, INK, PT, bands, fit, np, plt, t1_at, t1_x, t1_y, t_critical):
    t1_b0, t1_b1, t1_s, t1_mean_x, t1_sxx = fit(t1_x, t1_y)
    t1_xx = np.linspace(-5, 20, 300)
    t1_yhat, t1_ci, t1_pi = bands(t1_xx, t1_b0, t1_b1, t1_s, t1_mean_x, t1_sxx, 15)
    t1_y_at, t1_ci_at, t1_pi_at = bands(t1_at.value, t1_b0, t1_b1, t1_s, t1_mean_x, t1_sxx, 15)
    t1_inside = t1_x.min() <= t1_at.value <= t1_x.max()

    plt.close("all")
    t1_fig, (t1_left, t1_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t1_left.axvspan(-5, t1_x.min(), color=GRID, alpha=0.6)            # outside the tested range
    t1_left.axvspan(t1_x.max(), 20, color=GRID, alpha=0.6)
    t1_left.fill_between(t1_xx, t1_yhat - t1_pi, t1_yhat + t1_pi, color=PT, alpha=0.18, label="next reading (prediction)")
    t1_left.fill_between(t1_xx, t1_yhat - t1_ci, t1_yhat + t1_ci, color=FIT, alpha=0.2, label="true line (confidence)")
    t1_left.plot(t1_xx, t1_yhat, color=FIT, lw=2)
    t1_left.plot(t1_xx, 1 + 2 * t1_xx, "--", color=INK, lw=1.4)
    t1_left.scatter(t1_x, t1_y, s=22, color=PT, zorder=3)
    t1_left.axvline(t1_at.value, color=INK, lw=1)
    t1_left.set(title="Two 95% bands", xlabel="x", ylabel="y", xlim=(-5, 20))
    t1_left.legend(frameon=False, fontsize=10, loc="upper left")
    t1_right.plot(t1_xx, t1_pi, color=PT, lw=2.2, label="next reading")
    t1_right.plot(t1_xx, t1_ci, color=FIT, lw=2.2, label="true line")
    t1_right.plot([t1_at.value, t1_at.value], [t1_ci_at, t1_pi_at], "o", color=INK)
    t1_right.set(title="Band half-width along x", xlabel="x", ylabel="half-width", xlim=(-5, 20), ylim=(0, None))
    t1_right.legend(frameon=False, fontsize=10)
    t1_fig.tight_layout()

    print(f"Fitted y at x = {t1_at.value:.1f}: {t1_y_at:.1f}")
    print(f"Where the true line is (95%): ± {t1_ci_at:.1f}      Where the next reading will land (95%): ± {t1_pi_at:.1f}")
    print(f"Inside the tested range? {'yes' if t1_inside else 'NO: this is extrapolation'}")
    print()
    print("Report line (Trial 3 of the page), built from this data:")
    print(f"  Linear least-squares fit, n = 15 readings over x = {t1_x.min():.1f} to {t1_x.max():.1f}.")
    print(f"  Slope b1 = {t1_b1:.2f} ± {t_critical(13) * t1_s / np.sqrt(t1_sxx):.2f} (95%); "
          f"intercept b0 = {t1_b0:.2f} ± {t_critical(13) * t1_s * np.sqrt(1 / 15 + t1_mean_x ** 2 / t1_sxx):.2f}.")
    print(f"  Residual SD s = {t1_s:.2f} (in y's units).")
    print(f"  Prediction at x = {t1_at.value:.1f}: {t1_y_at:.1f} ± {t1_pi_at:.1f} for a single new reading (95%).")
    t1_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** The narrow band is where the true line is; the wide band is where
    the next single reading will land, and it never gets narrower than the sensor's own
    scatter. Both are narrowest in the middle of the data and flare outward. Past the
    data, the bands keep flaring but the model itself is untested there: the number the
    fit gives you is a guess dressed up with an error bar.

    ## Trial 2 · Carrying the uncertainty into a result

    Often the answer isn't a coefficient but something computed from both: here, the x where
    the line crosses zero (like the temperature where a sensor's output crosses 0 V). Twelve
    readings over a span of 5, starting at distance c from x = 0; the true crossing is c. The
    intercept b0 is the fit's value at x = 0, which may be far from where the data are.
    """)
    return


@app.cell
def _(mo):
    t2_distance = mo.ui.slider(0, 20, step=1, value=10, show_value=True, label="How far the data sit from x = 0")
    t2_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t2_distance, t2_new])
    return t2_distance, t2_new


@app.cell
def _(np, t_critical):
    def crossing_many(random, c, reps, n=12):
        """`reps` experiments at distance c: the crossing estimate and its two 95% half-widths, one per row."""
        X = c + 5 * (np.arange(n) + random.uniform(0, 1, (reps, n))) / n
        Y = 2 * (X - c) + random.standard_normal((reps, n))
        mx = X.mean(axis=1)
        my = Y.mean(axis=1)
        sxx = ((X - mx[:, None]) ** 2).sum(axis=1)
        b1 = ((X - mx[:, None]) * (Y - my[:, None])).sum(axis=1) / sxx
        b0 = my - b1 * mx
        s2 = ((Y - (b0[:, None] + b1[:, None] * X)) ** 2).sum(axis=1) / (n - 2)
        var_b1 = s2 / sxx                                  # how uncertain the slope is
        var_b0 = s2 * (1 / n + mx ** 2 / sxx)              # how uncertain the intercept is
        cov = -s2 * mx / sxx                               # how the two move together (large when the data sit far from 0)
        x0 = -b0 / b1
        naive = np.sqrt(var_b0 + x0 ** 2 * var_b1) / np.abs(b1)                 # ignoring the correlation
        delta = np.sqrt(var_b0 + 2 * x0 * cov + x0 ** 2 * var_b1) / np.abs(b1)   # with it (the delta method)
        tc = t_critical(n - 2)
        return x0, tc * naive, tc * delta, b0, b1, X, Y

    return (crossing_many,)


@app.cell
def _(FIT, FIX, INK, PT, crossing_many, np, plt, t2_distance, t2_new):
    t2_random = np.random.default_rng(29 + t2_new.value)
    t2_c = t2_distance.value
    t2_x0, t2_naive, t2_delta, t2_b0, t2_b1, t2_X, t2_Y = crossing_many(t2_random, t2_c, 400)   # the first row is shown
    t2_actual = 1.96 * t2_x0.std(ddof=1)                 # the spread the ranges should match

    # The same three numbers at every distance, for the curve
    t2_distances = np.arange(0, 21, 2)
    t2_curve_naive, t2_curve_delta, t2_curve_actual = [], [], []
    for distance in t2_distances:
        x0_d, naive_d, delta_d = crossing_many(t2_random, distance, 400)[:3]
        t2_curve_naive.append(naive_d.mean())
        t2_curve_delta.append(delta_d.mean())
        t2_curve_actual.append(1.96 * x0_d.std(ddof=1))

    plt.close("all")
    t2_fig, (t2_left, t2_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t2_xx = np.array([t2_c - 8, t2_c + 6])
    t2_left.plot(t2_xx, 2 * (t2_xx - t2_c), "--", color=INK, lw=1.4, label="the truth")
    t2_left.plot(t2_xx, t2_b0[0] + t2_b1[0] * t2_xx, color=FIT, lw=2, label="fitted line, extended")
    t2_left.scatter(t2_X[0], t2_Y[0], s=22, color=PT, zorder=3)
    t2_left.axhline(0, color=INK, lw=1)
    t2_left.plot([t2_x0[0] - t2_naive[0], t2_x0[0] + t2_naive[0]], [-1.2, -1.2], color=FIT, lw=4, label="range ignoring correlation")
    t2_left.plot([t2_x0[0] - t2_delta[0], t2_x0[0] + t2_delta[0]], [-2.0, -2.0], color=FIX, lw=4, label="range with correlation")
    t2_left.set(title="The fit, extended back to where it crosses zero", xlabel="x", ylabel="y")
    t2_left.legend(frameon=False, fontsize=9, loc="upper left")
    t2_right.plot(t2_distances, t2_curve_naive, "o-", color=FIT, label="ignoring correlation")
    t2_right.plot(t2_distances, t2_curve_delta, "o-", color=FIX, label="with correlation (delta method)")
    t2_right.plot(t2_distances, t2_curve_actual, "s--", color=INK, label="actual spread over 400 repeats")
    t2_right.axvline(t2_c, color=PT, lw=1)
    t2_right.set(title="95% range on the crossing, by distance", xlabel="how far the data sit from x = 0", ylabel="± half-width")
    t2_right.legend(frameon=False, fontsize=9)
    t2_fig.tight_layout()

    print(f"True crossing {t2_c:.1f}   Estimated crossing {t2_x0[0]:.2f}")
    print(f"95% range: ± {t2_naive[0]:.2f} ignoring correlation   ± {t2_delta[0]:.2f} with correlation")
    print(f"Actual spread of the estimate over 400 repeats: ± {t2_actual:.2f}")
    t2_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** With the data sitting at x = 0 the two ranges agree. Move the data
    away and the intercept's uncertainty balloons, but so does its correlation with the
    slope: a steeper fitted slope comes with a lower intercept, and the two errors partly
    cancel at the crossing. Add them as if they were independent and the range is far too
    wide; include the correlation (the delta method) and it matches the actual spread.

    ## Make it your own

    - In Trial 1's data cell, change the noise `2 *` to `0.5 *` and watch which band shrinks
      and which doesn't.
    - In Trial 2, change the span of the data (`5 *` in `crossing_many`) to 1: a short span
      makes the extrapolation to the crossing far worse.
    - Reuse `bands` on your own fit: it only needs the five numbers `fit` returns.
    """)
    return


if __name__ == "__main__":
    app.run()
