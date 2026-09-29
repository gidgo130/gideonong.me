import marimo

__generated_with = "0.25.0"
app = marimo.App(
    width="medium",
    app_title="Why R² Isn't Enough · play with the code",
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Why R² Isn't Enough — play with the code

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

    Trial 1 uses Anscombe's quartet (Anscombe 1973). Trials 2 and 3 are simulated from
    y = 1 + 2x + noise, so the true slope is 2.
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
    return FIT, GRID, INK, PT, mo, np, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The helpers every trial uses

    A straight-line least-squares fit, R², and the number that turns a standard error into a
    95% range (the t critical value; 1.96 for a huge sample, larger for a small one).
    """)
    return


@app.cell
def _(np):
    def ols(x, y):
        """Fit y = b0 + b1 * x. Returns b0, b1, fitted values, residuals, residual SD, slope SE."""
        n = len(x)
        b1, b0 = np.polyfit(x, y, 1)     # degree-1 polynomial = a straight line; slope first
        fitted = b0 + b1 * x
        residuals = y - fitted
        s = np.sqrt((residuals ** 2).sum() / (n - 2))              # residual SD (2 numbers fitted)
        se1 = s / np.sqrt(((x - x.mean()) ** 2).sum())             # standard error of the slope
        return b0, b1, fitted, residuals, s, se1


    def r2(y, fitted):
        """R²: the share of the spread in y that the fit explains (1 = perfect)."""
        unexplained = ((y - fitted) ** 2).sum()
        total = ((y - y.mean()) ** 2).sum()
        return 1 - unexplained / total


    def t_critical(df):
        """The 95% two-sided t value for df degrees of freedom (a close series formula)."""
        z = 1.959964
        return (z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)
                + (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / (384 * df ** 3))

    return ols, r2, t_critical


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Trial 1 · Four datasets, one R²

    These four small datasets were built by the statistician Francis Anscombe in 1973. Each
    has 11 points, and each gets the same fitted line and the same R². Pick one and look at
    the residuals.
    """)
    return


@app.cell
def _(np):
    # Anscombe's quartet: sets I, II and III share the same x values
    QUARTET_X = [
        np.array([10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5], float),
        np.array([10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5], float),
        np.array([10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5], float),
        np.array([8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8], float),
    ]
    QUARTET_Y = [
        np.array([8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68]),
        np.array([9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74]),
        np.array([7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73]),
        np.array([6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89]),
    ]
    QUARTET_NAMES = ["I", "II", "III", "IV"]
    return QUARTET_NAMES, QUARTET_X, QUARTET_Y


@app.cell
def _(mo):
    t1_set = mo.ui.radio(options={"I": 0, "II": 1, "III": 2, "IV": 3}, value="I", inline=True, label="Dataset")
    t1_set
    return (t1_set,)


@app.cell
def _(
    FIT,
    INK,
    PT,
    QUARTET_NAMES,
    QUARTET_X,
    QUARTET_Y,
    np,
    ols,
    plt,
    r2,
    t1_set,
):
    t1_x = QUARTET_X[t1_set.value]
    t1_y = QUARTET_Y[t1_set.value]
    t1_b0, t1_b1, t1_fitted, t1_residuals, t1_s, t1_se1 = ols(t1_x, t1_y)

    plt.close("all")                                   # throw away the previous figure
    t1_fig, (t1_left, t1_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t1_left.scatter(t1_x, t1_y, s=28, color=PT)
    t1_ends = np.array([2, 20])
    t1_left.plot(t1_ends, t1_b0 + t1_b1 * t1_ends, color=FIT, lw=2.2, label="fitted line")
    t1_left.set(title=f"Dataset {QUARTET_NAMES[t1_set.value]}: the data and the fit", xlabel="x", ylabel="y",
                xlim=(2, 20), ylim=(2, 14))
    t1_left.legend(loc="upper left", frameon=False, fontsize=10)
    t1_right.scatter(t1_fitted, t1_residuals, s=28, color=PT)
    t1_right.axhline(0, color=INK, lw=1)
    t1_right.set(title="Residual plot", xlabel="fitted y", ylabel="residual", ylim=(-4, 4))
    t1_fig.tight_layout()

    print(f"Slope {t1_b1:.3f}   Intercept {t1_b0:.2f}   R² {r2(t1_y, t1_fitted):.3f}   Residual SD {t1_s:.2f}")
    t1_fig                                             # the last line of a cell is what it shows
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** All four sets give slope 0.50, intercept 3.0 and R² 0.67. Only set I
    is a straight line plus noise. Set II is a curve (the residuals bend). Set III is a line
    with one outlier. Set IV is one lever point holding up the whole fit; without it there is
    no slope at all. R² can't tell them apart. The residual plot can.

    ### All four at once

    The figure from the slides: the four datasets side by side, fits on top, residuals below.
    """)
    return


@app.cell
def _(FIT, INK, PT, QUARTET_NAMES, QUARTET_X, QUARTET_Y, np, ols, plt, r2):
    plt.close("all")
    gallery_fig, gallery_axes = plt.subplots(2, 4, figsize=(13, 5.8))
    gallery_ends = np.array([2, 20])
    for column in range(4):
        gx, gy = QUARTET_X[column], QUARTET_Y[column]
        gb0, gb1, gfitted, gresiduals, gs, gse1 = ols(gx, gy)
        top = gallery_axes[0, column]
        top.scatter(gx, gy, s=24, color=PT)
        top.plot(gallery_ends, gb0 + gb1 * gallery_ends, color=FIT, lw=2)
        top.set(title=f"{QUARTET_NAMES[column]}:  R² = {r2(gy, gfitted):.2f}", xlim=(2, 20), ylim=(2, 14), xlabel="x")
        bottom = gallery_axes[1, column]
        bottom.scatter(gfitted, gresiduals, s=24, color=PT)
        bottom.axhline(0, color=INK, lw=1)
        bottom.set(xlabel="fitted y", ylim=(-4, 4))
    gallery_axes[0, 0].set_ylabel("y")
    gallery_axes[1, 0].set_ylabel("residual")
    gallery_fig.tight_layout()
    gallery_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Trial 2 · R² measures your test range

    Same sensor, same noise, same true slope. The only thing you change is how wide a range
    of x you test over. Thirty readings are spread evenly over the range.
    """)
    return


@app.cell
def _(mo):
    t2_span = mo.ui.slider(1, 30, step=1, value=5, show_value=True, label="Range of x tested: 0 to …")
    t2_sd = mo.ui.slider(0.5, 5, step=0.1, value=2.0, show_value=True, label="Sensor noise (SD, in y units)")
    t2_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t2_span, t2_sd, t2_new])
    return t2_new, t2_sd, t2_span


@app.cell
def _(np, t2_new):
    # The random numbers, reused while you move the sliders; the button draws new ones.
    # The noise draws are rescaled to mean 0 and SD 1, so the residual SD tracks the slider closely.
    t2_random = np.random.default_rng(11 + t2_new.value)
    t2_u = t2_random.uniform(0, 1, 30)                 # where each reading sits inside its slot
    t2_z = t2_random.standard_normal(30)
    t2_z = (t2_z - t2_z.mean()) / t2_z.std(ddof=1)
    return t2_u, t2_z


@app.cell
def _(FIT, INK, PT, np, ols, plt, r2, t2_sd, t2_span, t2_u, t2_z, t_critical):
    t2_x = t2_span.value * (np.arange(30) + t2_u) / 30            # 30 readings spread over 0 … span
    t2_y = 1 + 2 * t2_x + t2_sd.value * t2_z
    t2_b0, t2_b1, t2_fitted, t2_residuals, t2_s, t2_se1 = ols(t2_x, t2_y)

    # R² you'd get with unlimited data: signal variance over total variance, for x spread evenly over 0 … span
    def expected_r2(span, sd):
        signal = 2 ** 2 * span ** 2 / 12
        return signal / (signal + sd ** 2)

    t2_spans = np.linspace(0.01, 30, 300)

    plt.close("all")
    t2_fig, (t2_left, t2_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t2_left.scatter(t2_x, t2_y, s=16, color=PT, alpha=0.8)
    t2_left.plot([0, 30], [1, 1 + 2 * 30], "--", color=INK, lw=1.4, label="the truth")
    t2_left.plot([0, t2_span.value], [t2_b0, t2_b0 + t2_b1 * t2_span.value], color=FIT, lw=2.2, label="fitted line")
    t2_left.set(title="The data and the fit", xlabel="x", ylabel="y", xlim=(0, 30), ylim=(-15, 75))
    t2_left.legend(loc="upper left", frameon=False, fontsize=10)
    t2_right.plot(t2_spans, expected_r2(t2_spans, t2_sd.value), color=PT, lw=2.2)
    t2_right.plot(t2_span.value, expected_r2(t2_span.value, t2_sd.value), "o", color=FIT, ms=8)
    t2_right.set(title="R² with unlimited data, by test range", xlabel="range of x tested (0 to …)",
                 ylabel="expected R²", xlim=(0, 30), ylim=(0, 1))
    t2_fig.tight_layout()

    print(f"R² {r2(t2_y, t2_fitted):.3f}   (with unlimited data at this range: {expected_r2(t2_span.value, t2_sd.value):.3f})")
    print(f"Residual SD {t2_s:.2f}   (the sensor noise you set: {t2_sd.value:.1f})")
    print(f"Slope {t2_b1:.2f} ± {t_critical(28) * t2_se1:.2f} (95% range)   true slope 2.00")
    t2_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** Widen the range and R² climbs toward 1; narrow it and R² collapses,
    with the same sensor and the same noise. R² compares the fit's error with the spread of y,
    and a wider range means more spread. The residual SD, the number that describes the
    sensor, stays put. The dot on the right is your setting on the unlimited-data curve;
    small samples scatter around it.

    ## Trial 3 · More terms always raise R²

    Twelve readings from a straight line plus noise (SD 2). Add polynomial terms one at a
    time and watch R² and the curve. The second panel is the honest score: leave one reading
    out, fit the rest, predict it, repeat for every reading.
    """)
    return


@app.cell
def _(mo):
    t3_degree = mo.ui.slider(1, 9, step=1, value=1, show_value=True, label="Polynomial degree (1 = straight line)")
    t3_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t3_degree, t3_new])
    return t3_degree, t3_new


@app.cell
def _(np, t3_new):
    t3_random = np.random.default_rng(23 + t3_new.value)
    t3_x = np.sort(10 * (np.arange(12) + t3_random.uniform(0, 1, 12)) / 12)   # 12 readings over 0 … 10
    t3_y = 1 + 2 * t3_x + 2 * t3_random.standard_normal(12)
    return t3_x, t3_y


@app.cell
def _(FIT, GRID, INK, PT, np, plt, r2, t3_degree, t3_x, t3_y):
    def poly_fit(degree, x, y):
        # x is rescaled to -1 … 1 first, so high degrees stay numerically stable
        return np.polyfit((x - 5) / 5, y, degree)

    def poly_value(coefficients, x):
        return np.polyval(coefficients, (x - 5) / 5)

    # R² and the leave-one-out error for every degree, 1 to 9
    t3_r2_by_degree = []
    t3_loo_by_degree = []
    for degree in range(1, 10):
        coefficients = poly_fit(degree, t3_x, t3_y)
        t3_r2_by_degree.append(r2(t3_y, poly_value(coefficients, t3_x)))
        misses = []
        for k in range(12):                                # leave reading k out, fit the rest, predict it
            others = np.delete(np.arange(12), k)
            c_without = poly_fit(degree, t3_x[others], t3_y[others])
            misses.append(t3_y[k] - poly_value(c_without, t3_x[k]))
        t3_loo_by_degree.append(np.sqrt(np.mean(np.square(misses))))

    t3_d = t3_degree.value
    t3_coefficients = poly_fit(t3_d, t3_x, t3_y)
    t3_r2 = t3_r2_by_degree[t3_d - 1]
    t3_adjusted_r2 = 1 - (1 - t3_r2) * (12 - 1) / (12 - t3_d - 1)   # R² with a penalty for each term

    plt.close("all")
    t3_fig, (t3_left, t3_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t3_xx = np.linspace(-0.5, 13, 300)
    t3_left.axvspan(10, 13, color=GRID, alpha=0.6)         # beyond the last reading
    t3_left.plot(t3_xx, 1 + 2 * t3_xx, "--", color=INK, lw=1.4, label="the truth")
    t3_left.plot(t3_xx, poly_value(t3_coefficients, t3_xx), color=FIT, lw=2.2, label=f"degree {t3_d}: R² {t3_r2:.3f}")
    t3_left.scatter(t3_x, t3_y, s=30, color=PT, zorder=3)
    t3_left.set(title="The fit, and past the data", xlabel="x", ylabel="y", ylim=(-10, 45))
    t3_left.legend(loc="upper left", frameon=False, fontsize=10)
    t3_right.plot(range(1, 10), np.minimum(t3_loo_by_degree, 12), "o-", color=PT)
    t3_right.plot(t3_d, min(t3_loo_by_degree[t3_d - 1], 12), "o", color=FIT, ms=10)
    t3_right.axhline(2, ls="--", color=INK, lw=1)           # the sensor noise: the best any fit can do
    t3_right.set(title="Error on a point the fit hasn't seen", xlabel="polynomial degree",
                 ylabel="RMS error (capped at 12)", ylim=(0, 12))
    t3_fig.tight_layout()

    print(f"R² {t3_r2:.3f}   Adjusted R² {t3_adjusted_r2:.3f}")
    print(f"Error on a point it hasn't seen {t3_loo_by_degree[t3_d - 1]:.2f}   (sensor noise 2.00)")
    print(f"Prediction at x = 12: {poly_value(t3_coefficients, 12.0):.1f}   (truth 25)")
    t3_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** R² on the twelve points can only go up as you add terms; by degree 9
    the curve passes through every point and R² is 1. The error on an unseen point tells the
    truth: it is lowest for the straight line and grows with every extra term, while the
    prediction at x = 12 wanders off. The best any fit can do is the noise itself (the dashed
    line). Adjusted R² penalizes each term, but it is still built from the same twelve points.

    ## Make it your own

    - In Trial 2's data cell, change the 30 readings to 8 (three places) and see how far R²
      scatters around the unlimited-data curve.
    - In Trial 3's data cell, change the noise `2 *` to `0.5 *`: when does a higher degree
      start to win, if ever?
    - Add your own dataset to `QUARTET_X` / `QUARTET_Y` and a name to `QUARTET_NAMES`.
    """)
    return


if __name__ == "__main__":
    app.run()
