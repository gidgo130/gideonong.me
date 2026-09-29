import marimo

__generated_with = "0.25.0"
app = marimo.App(
    width="medium",
    app_title="Reading a Residual Plot · play with the code",
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Reading a Residual Plot — play with the code

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

    All data is simulated, so the true model is known. Trials 1 and 3: y = 1 + 2x + error.
    Trial 2: T = 22 + 58·e^(−t/4) + error, in °C and minutes.
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

    # Figure style (grid on, no box around the plot, bold titles at the left)
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
    ## The two helpers every trial uses

    A straight-line least-squares fit, and R². The **residual** is measured y minus fitted y:
    the vertical gap between a point and the line.
    """)
    return


@app.cell
def _(np):
    def ols(x, y):
        """Fit the straight line y = b0 + b1 * x. Returns b0, b1, fitted values, residuals."""
        b1, b0 = np.polyfit(x, y, 1)     # degree-1 polynomial = a straight line; slope first
        fitted = b0 + b1 * x
        residuals = y - fitted
        return b0, b1, fitted, residuals


    def r2(y, fitted):
        """R²: the share of the spread in y that the fit explains (1 = perfect)."""
        unexplained = ((y - fitted) ** 2).sum()
        total = ((y - y.mean()) ** 2).sum()
        return 1 - unexplained / total

    return ols, r2


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Trial 1 · The pattern gallery

    Forty readings of y = 1 + 2x + noise, taken in random x order, with one hidden problem
    mixed in. `make_y` is where each problem is added; the order of the array is the order
    the readings were taken. Pick a problem, turn it up, and look at the residuals both ways.
    """)
    return


@app.cell
def _(np):
    def make_y(x, noise, problem, strength, outlier_index):
        """y = 1 + 2x + noise, plus one hidden problem. Array order = run order."""
        n = len(x)
        time = np.arange(n) / (n - 1)         # 0 at the first reading, 1 at the last
        y = 1 + 2 * x                          # the true straight line
        if problem == "curve":                 # the real shape bends, so a line is wrong
            y = y + 0.45 * strength * ((x - 5) ** 2 - 25 / 3)
        if problem == "fan":                   # the noise grows with x
            noise = noise * (1 + strength * 0.6 * x)
        if problem == "drift":                 # something changed during the session
            y = y + strength * 10 * time
        y = y + noise
        if problem == "outlier":               # one bad reading, near x = 8
            y[outlier_index] = y[outlier_index] + strength * 14
        return y

    return (make_y,)


@app.cell
def _(mo):
    # The controls. options = {label shown: value used in the code}
    t1_problem = mo.ui.radio(
        options={"None": "none", "Curve": "curve", "Fan": "fan", "Drift": "drift", "Outlier": "outlier"},
        value="Curve", inline=True, label="Hidden problem",
    )
    t1_strength = mo.ui.slider(0, 1, step=0.05, value=0.7, show_value=True,
                               label="How strong (0 = none, 1 = hard to miss)")
    t1_axis = mo.ui.radio(options={"Fitted value": "fitted", "Run order": "order"},
                          value="Fitted value", inline=True, label="Plot residuals against")
    # Each click adds 1 to the button's value; the data cell below uses it as part of the seed
    t1_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t1_problem, t1_strength, t1_axis, t1_new])   # show them stacked
    return t1_axis, t1_new, t1_problem, t1_strength


@app.cell
def _(np, t1_new):
    # The random numbers. The seed fixes them, so moving a slider reuses the same readings;
    # the button changes the seed and draws new ones.
    t1_random = np.random.default_rng(7 + t1_new.value)
    t1_x = t1_random.uniform(0, 10, 40)            # 40 x values between 0 and 10, random order
    t1_noise = t1_random.standard_normal(40)       # 40 noise values, standard deviation 1
    t1_outlier_index = int(np.argmin(abs(t1_x - 8)))   # which reading is closest to x = 8
    return t1_noise, t1_outlier_index, t1_x


@app.cell
def _(
    FIT,
    INK,
    PT,
    make_y,
    np,
    ols,
    plt,
    r2,
    t1_axis,
    t1_noise,
    t1_outlier_index,
    t1_problem,
    t1_strength,
    t1_x,
):
    # Make the data with the chosen problem, then fit a straight line to it
    t1_y = make_y(t1_x, t1_noise, t1_problem.value, t1_strength.value, t1_outlier_index)
    t1_b0, t1_b1, t1_fitted, t1_residuals = ols(t1_x, t1_y)

    plt.close("all")                                   # throw away the previous figure
    t1_fig, (t1_left, t1_right) = plt.subplots(1, 2, figsize=(10, 4.2))

    # Left: the data, the truth (dashed) and the fitted line (red)
    t1_left.scatter(t1_x, t1_y, s=18, color=PT, alpha=0.8)
    t1_ends = np.array([-1, 11])                       # draw the lines from x = -1 to x = 11
    t1_left.plot(t1_ends, 1 + 2 * t1_ends, "--", color=INK, lw=1.4, label="the truth")
    t1_left.plot(t1_ends, t1_b0 + t1_b1 * t1_ends, color=FIT, lw=2.2, label="fitted line")
    t1_left.set(title="The data and the fit", xlabel="measured x", ylabel="measured y", xlim=(-1, 11))
    t1_left.legend(loc="upper left", frameon=False, fontsize=10)

    # Right: the residuals, against the fitted value or in run order
    if t1_axis.value == "order":
        t1_run_number = np.arange(1, 41)               # 1, 2, ..., 40
        t1_right.scatter(t1_run_number, t1_residuals, s=18, color=PT, alpha=0.8)
        t1_right.set(title="Residuals in run order", xlabel="run number (time order)", ylabel="residual")
    else:
        t1_right.scatter(t1_fitted, t1_residuals, s=18, color=PT, alpha=0.8)
        t1_right.set(title="Residuals against the fitted value", xlabel="fitted y", ylabel="residual")
    t1_right.axhline(0, color=INK, lw=1)              # the zero line
    t1_fig.tight_layout()

    print(f"Fitted slope {t1_b1:.2f}   (true slope 2.00)")
    print(f"R² {r2(t1_y, t1_fitted):.3f}")
    t1_fig                                             # the last line of a cell is what it shows
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** Healthy residuals are a flat, even band around zero with no shape,
    whichever way you plot them. A **bend** means the line is the wrong shape. A **fan** means
    the scatter isn't the same everywhere. **Drift** looks almost healthy against the fitted
    value and only shows in run order, which is why you make both plots. **One point** far from
    the band is a run to check in your notes before anything else.

    ### All five at once

    The same forty readings with each problem in turn, at strength 0.8: the figure from the
    slides. Top row against the fitted value, bottom row in run order.
    """)
    return


@app.cell
def _(INK, PT, make_y, np, ols, plt, t1_noise, t1_outlier_index, t1_x):
    plt.close("all")
    gallery_fig, gallery_axes = plt.subplots(2, 5, figsize=(13, 5), sharey="row")
    gallery_run_number = np.arange(1, 41)

    # One column per problem. enumerate gives the column number (0, 1, 2, ...) and the problem.
    for column, problem in enumerate(["none", "curve", "fan", "drift", "outlier"]):
        if problem == "none":
            strength = 0
        else:
            strength = 0.8
        y = make_y(t1_x, t1_noise, problem, strength, t1_outlier_index)
        b0, b1, fitted, residuals = ols(t1_x, y)

        top = gallery_axes[0, column]                  # row 0: against the fitted value
        top.scatter(fitted, residuals, s=12, color=PT, alpha=0.8)
        top.axhline(0, color=INK, lw=1)
        top.set(title=problem.capitalize(), xlabel="fitted y")

        bottom = gallery_axes[1, column]               # row 1: in run order
        bottom.scatter(gallery_run_number, residuals, s=12, color=PT, alpha=0.8)
        bottom.axhline(0, color=INK, lw=1)
        bottom.set(xlabel="run number")

    gallery_axes[0, 0].set_ylabel("residual\n(vs fitted value)")
    gallery_axes[1, 0].set_ylabel("residual\n(in run order)")
    gallery_fig.tight_layout()
    gallery_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Trial 2 · When the shape is wrong

    A thermocouple at 80 °C is dropped into a 22 °C room and logged every 15 seconds. Physics
    says it cools exponentially toward room temperature: T = 22 + 58·e^(−t/τ) with τ = 4 min.
    Fit a straight line anyway and read the residuals; then fit the exponential.

    The exponential fit below is written out in plain NumPy so you can see how it works: for
    any guess of τ the model is a straight line in z = e^(−t/τ), so `np.polyfit` finds the
    other two numbers, and we simply try many values of τ and keep the best. On your own
    computer `scipy.optimize.curve_fit` does the same job in one call (the module's script
    uses it); it isn't used here because SciPy is a 14 MB download for the browser.
    """)
    return


@app.cell
def _(np):
    def cooling(t, t_inf, a, tau):
        """The cooling model: room temperature t_inf, drop a, time constant tau (minutes)."""
        return t_inf + a * np.exp(-t / tau)


    def fit_exponential(t, y):
        """Fit T = t_inf + a * exp(-t / tau) to the data. Returns t_inf, a, tau."""

        def error_for(tau):
            # With tau fixed, the model is a straight line in z, so polyfit finds a and t_inf.
            z = np.exp(-t / tau)
            a, t_inf = np.polyfit(z, y, 1)
            error = ((y - (t_inf + a * z)) ** 2).sum()     # total squared miss
            return error, t_inf, a

        def best_tau_in(taus):
            # Try every tau in the list and keep the one with the smallest error
            best_tau, best_error = None, None
            for tau in taus:
                error = error_for(tau)[0]
                if best_error is None or error < best_error:
                    best_tau, best_error = tau, error
            return best_tau

        # Pass 1: a coarse sweep from 0.05 min to 200 min (evenly spaced on a log scale).
        # Pass 2: a fine sweep within 3% of the best one from pass 1.
        rough = best_tau_in(np.geomspace(0.05, 200, 400))
        tau = best_tau_in(np.linspace(0.97 * rough, 1.03 * rough, 400))
        error, t_inf, a = error_for(tau)
        return t_inf, a, tau

    return cooling, fit_exponential


@app.cell
def _(mo):
    t2_model = mo.ui.radio(options={"Straight line": "line", "Exponential": "exp"},
                           value="Straight line", inline=True, label="Model")
    t2_noise = mo.ui.slider(0, 2, step=0.1, value=0.5, show_value=True, label="Sensor noise (°C)")
    t2_window = mo.ui.slider(3, 20, step=0.5, value=15, show_value=True,
                             label="Stop recording after (min) — a short recording hides the curve")
    t2_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t2_model, t2_noise, t2_window, t2_new])
    return t2_model, t2_new, t2_noise, t2_window


@app.cell
def _(np, t2_new):
    # 81 noise values: enough for a 20-minute recording at one reading every 15 s
    t2_random = np.random.default_rng(11 + t2_new.value)
    t2_noise_values = t2_random.standard_normal(81)
    return (t2_noise_values,)


@app.cell
def _(
    FIT,
    FIX,
    INK,
    PT,
    cooling,
    fit_exponential,
    np,
    ols,
    plt,
    r2,
    t2_model,
    t2_noise,
    t2_noise_values,
    t2_window,
):
    # The readings: every 15 s (0.25 min) until the recording stops
    t2_t = np.arange(0, t2_window.value + 0.001, 0.25)
    t2_truth = cooling(t2_t, 22, 58, 4.0)
    t2_y = t2_truth + t2_noise.value * t2_noise_values[: len(t2_t)]

    if t2_model.value == "exp":
        t2_t_inf, t2_a, t2_tau = fit_exponential(t2_t, t2_y)
        t2_fitted = cooling(t2_t, t2_t_inf, t2_a, t2_tau)
        t2_parameters = 3                              # the model has three fitted numbers
        t2_color = FIX
    else:
        t2_b0, t2_b1, t2_fitted, t2_line_residuals = ols(t2_t, t2_y)
        t2_tau = None                                  # a straight line has no time constant
        t2_parameters = 2
        t2_color = FIT
    t2_residuals = t2_y - t2_fitted
    # Residual SD: the typical size of a residual, allowing for the numbers the fit used up
    t2_sd = np.sqrt((t2_residuals ** 2).sum() / (len(t2_t) - t2_parameters))

    plt.close("all")
    t2_fig, (t2_left, t2_right) = plt.subplots(1, 2, figsize=(10, 4.2))
    t2_left.scatter(t2_t, t2_y, s=12, color=PT, alpha=0.8)
    t2_left.plot(t2_t, t2_truth, "--", color=INK, lw=1.4, label="the truth")
    t2_left.plot(t2_t, t2_fitted, color=t2_color, lw=2.2, label="fitted")
    t2_left.set(title="Cooling curve and the fit", xlabel="time (min)", ylabel="temperature (°C)", ylim=(15, 85))
    t2_left.legend(loc="upper right", frameon=False, fontsize=10)
    t2_right.scatter(t2_t, t2_residuals, s=12, color=PT, alpha=0.8)
    t2_right.axhline(0, color=INK, lw=1)
    t2_right.set(title="Residuals in time order", xlabel="time (min)", ylabel="residual (°C)")
    t2_fig.tight_layout()

    print(f"R² {r2(t2_y, t2_fitted):.3f}")
    print(f"Residual SD {t2_sd:.2f} °C   (the sensor noise you set: {t2_noise.value:.1f} °C)")
    if t2_tau is None:
        print("Fitted time constant: none (a straight line has no time constant)   true: 4.0 min")
    else:
        print(f"Fitted time constant {t2_tau:.2f} min   true: 4.0 min")
    t2_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** The straight line scores a high R² and still leaves a clear U: above
    the data in the middle, below at the ends, every time. A high R² doesn't mean the shape is
    right. Shorten the recording to 3 min and raise the noise to 2 °C and the U shrinks until
    the noise hides it; the model is still wrong, the data just can't show it. The exponential
    leaves a flat band, and its residual SD matches the sensor noise.

    ## Trial 3 · One point steering the line

    Twenty well-behaved readings plus one you control. Three numbers describe what that point
    can do: **leverage** (how far out in x it sits; it *could* move the line), the
    **studentized residual** (how far off the line it sits, measured fairly) and **Cook's
    distance** (how much the whole fit changes without it). The formulas below are the
    straight-line special case.
    """)
    return


@app.cell
def _(np, ols):
    def influence(x, y):
        """Leverage, studentized residual and Cook's distance for every point (straight-line fit)."""
        n = len(x)
        b0, b1, fitted, residuals = ols(x, y)
        s = np.sqrt((residuals ** 2).sum() / (n - 2))          # residual SD (2 numbers fitted)
        # Leverage: 1/n for everyone, plus more the farther the point is from the mean x
        leverage = 1 / n + (x - x.mean()) ** 2 / ((x - x.mean()) ** 2).sum()
        # Studentized residual: the residual in units of its own expected size
        studentized = residuals / (s * np.sqrt(1 - leverage))
        # Cook's distance: how much the whole fit moves if that point is removed
        cook = studentized ** 2 * leverage / (2 * (1 - leverage))
        return leverage, studentized, cook

    return (influence,)


@app.cell
def _(mo):
    t3_x = mo.ui.slider(0, 25, step=0.5, value=20, show_value=True, label="Its x position")
    t3_offset = mo.ui.slider(-15, 15, step=0.5, value=-10, show_value=True,
                             label="Its distance from the true line (y units, + above, − below)")
    t3_new = mo.ui.button(label="Draw a new sample", value=0, on_click=lambda clicks: clicks + 1)
    mo.vstack([t3_x, t3_offset, t3_new])
    return t3_new, t3_offset, t3_x


@app.cell
def _(np, t3_new):
    # The twenty well-behaved readings
    t3_random = np.random.default_rng(23 + t3_new.value)
    t3_x_others = t3_random.uniform(0, 10, 20)
    t3_y_others = 1 + 2 * t3_x_others + t3_random.standard_normal(20)
    return t3_x_others, t3_y_others


@app.cell
def _(
    FIT,
    FIX,
    INK,
    PT,
    influence,
    np,
    ols,
    plt,
    t3_offset,
    t3_x,
    t3_x_others,
    t3_y_others,
):
    # Your point goes last in the arrays
    t3_your_x = t3_x.value
    t3_your_y = 1 + 2 * t3_your_x + t3_offset.value
    t3_all_x = np.append(t3_x_others, t3_your_x)
    t3_all_y = np.append(t3_y_others, t3_your_y)
    t3_n = len(t3_all_x)                                             # 21

    t3_leverage, t3_studentized, t3_cook = influence(t3_all_x, t3_all_y)
    t3_b0, t3_b1, t3_fitted, t3_residuals = ols(t3_all_x, t3_all_y)         # with your point
    t3_c0, t3_c1, t3_fitted_without, t3_residuals_without = ols(t3_x_others, t3_y_others)   # without it
    t3_leverage_limit = 2 * 2 / t3_n      # a common flag: twice the average leverage (2 numbers fitted)
    t3_cook_limit = 4 / t3_n              # a common flag for Cook's distance

    plt.close("all")
    t3_fig, (t3_left, t3_right) = plt.subplots(1, 2, figsize=(10, 4.2))

    # Left: the data, both fits, and a ring around your point
    t3_ends = np.array([-1, 26])
    t3_left.scatter(t3_x_others, t3_y_others, s=18, color=PT, alpha=0.8)
    t3_left.scatter([t3_your_x], [t3_your_y], s=140, facecolors="none", edgecolors=INK, lw=2)
    t3_left.plot(t3_ends, 1 + 2 * t3_ends, "--", color=INK, lw=1.4, label="the truth")
    t3_left.plot(t3_ends, t3_c0 + t3_c1 * t3_ends, color=FIX, lw=2.2, label=f"without it: slope {t3_c1:.2f}")
    t3_left.plot(t3_ends, t3_b0 + t3_b1 * t3_ends, color=FIT, lw=2.2, label=f"with it: slope {t3_b1:.2f}")
    t3_left.set(title="Red: fit with the point. Blue: without it.", xlabel="x", ylabel="y", xlim=(-1, 26))
    t3_left.legend(loc="upper left", frameon=False, fontsize=10)

    # Right: Cook's distance for every point; your point (the last bar) in red
    t3_bar_colors = [PT] * t3_n
    t3_bar_colors[-1] = FIT
    t3_right.bar(np.arange(1, t3_n + 1), t3_cook, color=t3_bar_colors)
    t3_right.axhline(t3_cook_limit, ls="--", color=INK, lw=1)
    t3_right.set(title="Cook's distance for every point (dashed: 4/n)", xlabel="point", ylabel="Cook's distance")
    t3_fig.tight_layout()

    # The three numbers for your point (index -1 = the last one), each against its flag
    t3_your_leverage = t3_leverage[-1]
    t3_your_studentized = t3_studentized[-1]
    t3_your_cook = t3_cook[-1]
    print(f"Slope with the point {t3_b1:.2f}   without it {t3_c1:.2f}")
    if t3_your_leverage > t3_leverage_limit:
        print(f"Leverage {t3_your_leverage:.2f}   FLAGGED (above {t3_leverage_limit:.2f}): far out in x")
    else:
        print(f"Leverage {t3_your_leverage:.2f}   ok (flag above {t3_leverage_limit:.2f})")
    if abs(t3_your_studentized) > 2:
        print(f"Studentized residual {t3_your_studentized:.2f}   FLAGGED (beyond ±2): far off the line")
    else:
        print(f"Studentized residual {t3_your_studentized:.2f}   ok (flag beyond ±2)")
    if t3_your_cook > t3_cook_limit:
        print(f"Cook's distance {t3_your_cook:.2f}   FLAGGED (above {t3_cook_limit:.2f}): it moves the whole fit")
    else:
        print(f"Cook's distance {t3_your_cook:.2f}   ok (flag above {t3_cook_limit:.2f})")
    t3_fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Three settings worth trying.** x = 20 on the line (distance 0): a lever point that
    agrees with everything else and only steadies the slope. x = 5, distance +12: an outlier
    in the middle; the slope barely moves, but the whole line lifts and every error bar widens.
    x = 20, distance −10: an influential point, off the line *and* out at the edge; it drags the
    slope toward itself, and its residual looks smaller than its real miss because the line bent
    toward it. That's why the checks use studentized residuals and Cook's distance, not the raw
    residual.

    ## Make it your own

    - In `make_y`, change the true model (try `y = 1 + 2 * x + 0.1 * x ** 2`) and see which
      residual plot catches it.
    - In Trial 1's data cell, change the two 40s to 10 or 200 (and the 41 in the figure cells).
      When does a fan stop being visible?
    - In Trial 2, change the true time constant (the 4.0 in `cooling(t2_t, 22, 58, 4.0)`) and
      watch how long a recording you need before the U shows.
    - Copy any cell's code into your own script: the helpers `ols`, `r2` and `influence` work on
      any pair of NumPy arrays.
    """)
    return


if __name__ == "__main__":
    app.run()
