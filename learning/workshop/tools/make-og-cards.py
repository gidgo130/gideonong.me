"""Make the 1200x630 link-preview cards for /learning (learning/assets/og/*.png).

One card for the hub (learning.png) and one per module (<slug>.png), in the /learning
"lab notebook" look: paper background, faint grid, eyebrow, title, lead, and a crop of the
module's main figure from learning/workshop/modules/<slug>/figures/ (make those first by
running the module's .py, see learning/workshop/README.md). The hub card draws its own small
chart with the series' fixed colors (dashed ink = truth, red = ordinary fit, blue = corrected).
Reflections (learning/reflections/): reflections.png for the all-books and book pages, and
<book>-<reflection>.png per reflection. They have no workshop figure, so each entry names a
`chart` function below that draws its own, in the reflection series colors (reflections.css
--s1..--s4, light values), never the fit/fix pair. Marginalia (learning/marginalia/): marginalia.png
for the series index and marginalia-<slug>.png per entry, drawn the same way in the Marginalia
series colors (marginalia.css --s1..--s3, light values).

Run from anywhere:   python learning/workshop/tools/make-og-cards.py [slug ...]
Needs Pillow and matplotlib. Fonts: the script fetches Barlow Semi Condensed, Source Serif 4
and JetBrains Mono from the google/fonts GitHub repo into tools/fonts/ (git-ignored) on first
run; with no network it falls back to Arial / Georgia / Consolas.

The og: tags in each page point at these files by absolute URL, so keep the names stable.
"""
from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                       # repo root
FIG = HERE.parent / "modules"                # learning/workshop/modules/<slug>/figures/
OUT = ROOT / "learning" / "assets" / "og"
FONT_DIR = HERE / "fonts"

W, H = 1200, 630
PAD = 64
COL_W = 500                                  # text column width
FRAME = (PAD + COL_W + 40, PAD, W - PAD, H - PAD)   # figure frame (x0, y0, x1, y1)

# learning.css tokens (light theme)
PAPER, PLOT, GRID, RULE = "#f2f5f0", "#fbfcfa", "#dde5da", "#c5d0c3"
INK, MUTED, PT, FIT, FIX = "#1c2420", "#56645b", "#6b7b70", "#c93a22", "#1d5ea6"
S1, S2, S3, S4 = "#7e5b17", "#2c6390", "#ad4414", "#3a6d32"     # reflections.css series tokens (light)
M1, M2, M3 = "#2f4a7a", "#a83a2e", "#7a5c1e"                     # marginalia.css series tokens (light)

SITE = "gideonong.me/learning"

# Text on every card. Titles and leads match the EN strings of each page's index.html.
# `crop` = (left, top, right, bottom) as fractions of the source figure: the panel(s) that
# read best at card size.
CARDS = {
    "learning": {
        "eyebrow": "Gideon A. Ong · Learning",
        "title": "Reading Your Fits",
        "lead": "Six short interactive modules on checking a line fit against lab data. "
                "Each one runs in your browser on simulated data.",
    },
    "r-squared": {
        "eyebrow": "Reading Your Fits · Module 1",
        "title": "Why R² Isn't Enough",
        "lead": "It can't tell a good fit from a bad one, it rises when you test a wider "
                "range, and it always goes up when you add terms.",
        "figure": "t1_anscombe.png", "crop": (0.265, 0.0, 0.75, 1.0),
    },
    "residual-plots": {
        "eyebrow": "Reading Your Fits · Module 2",
        "title": "Reading a Residual Plot",
        "lead": "After you fit a line, the leftovers are the most useful thing on your "
                "screen. A handful of shapes tell you almost everything that can go wrong.",
        "figure": "t1_patterns.png", "crop": (0.235, 0.0, 0.615, 1.0),
    },
    "uneven-scatter": {
        "eyebrow": "Reading Your Fits · Module 3",
        "title": "Uneven Scatter",
        "lead": "Many sensors are rated as a percentage of the reading, so big readings "
                "carry big errors. The fitted line survives that. The error bars don't.",
        "figure": "t1_fan.png", "crop": (0.0, 0.0, 0.5, 1.0),
    },
    "time-order": {
        "eyebrow": "Reading Your Fits · Module 4",
        "title": "Time-Ordered Data",
        "lead": "A data logger can record a thousand samples a minute. That doesn't give "
                "you a thousand independent pieces of evidence, and your error bars don't know it.",
        "figure": "t1_autocorr.png", "crop": (0.0, 0.0, 0.5, 1.0),
    },
    "invisible-bias": {
        "eyebrow": "Reading Your Fits · Module 5",
        "title": "The Invisible Bias",
        "lead": "The fitted line comes out wrong, the leftovers look perfectly healthy, and "
                "taking more data makes you more confident in the wrong answer.",
        "figure": "t1_noise_y_vs_x.png", "crop": (0.5, 0.0, 1.0, 0.49),
    },
    "reporting": {
        "eyebrow": "Reading Your Fits · Module 6",
        "title": "Using and Reporting a Fit",
        "lead": "Once the checks pass, the fit is a tool: for predicting a reading, estimating "
                "a constant, or computing something from the coefficients.",
        "figure": "t1_bands.png", "crop": (0.0, 0.0, 0.51, 1.0),
    },
    # Reflections. No professor's name on a card, so a rename never needs a new image.
    "reflections": {
        "eyebrow": "Gideon A. Ong · Learning",
        "title": "Reflections",
        "lead": "Notes on 11 books recommended to industrial engineers, written as I read them. "
                "Some are short essays; some work the math out with interactive charts.",
        "chart": "mm1_chart",
    },
    "the-goal-balanced-plant": {
        "eyebrow": "Reflections · The Goal",
        "title": "The Balanced Plant Theorem",
        "lead": "Jonah says a mathematical proof shows that trimming capacity to match demand cuts "
                "throughput and sends inventory through the roof. Here is that proof, from queueing theory.",
        "chart": "buffers_chart",
    },
    # Marginalia. No course or professor on a card.
    "marginalia": {
        "eyebrow": "Gideon A. Ong · Learning",
        "title": "Marginalia",
        "lead": "Questions that come up while I study, each answered on one page, usually with "
                "something to play with. The practical answer first, then why it works.",
        "chart": "markov_chart",
    },
    "marginalia-markov-memory": {
        "eyebrow": "Marginalia · Probability",
        "title": "Does a Markov chain forget where it started?",
        "lead": "For a two-state chain the whole answer is one number, λ = 1 − a − b. It sets how "
                "fast the start is forgotten, and whether it ever is.",
        "chart": "markov_chart",
    },
    "marginalia-clt-sample-size": {
        "eyebrow": "Marginalia · Probability",
        "title": "How big does n have to be?",
        "lead": "The practical rule n > 28 + 25γ₁² for a 95% interval on a mean, and why the "
                "skewness of your data sets it.",
        "chart": "edgeworth_chart",
    },
}

FONT_FILES = {
    "display-bold": ("BarlowSemiCondensed-Bold.ttf", "ofl/barlowsemicondensed/BarlowSemiCondensed-Bold.ttf", "arialbd.ttf"),
    "display-semi": ("BarlowSemiCondensed-SemiBold.ttf", "ofl/barlowsemicondensed/BarlowSemiCondensed-SemiBold.ttf", "arialbd.ttf"),
    "body": ("SourceSerif4.ttf", "ofl/sourceserif4/SourceSerif4%5Bopsz%2Cwght%5D.ttf", "georgia.ttf"),
    "mono": ("JetBrainsMono.ttf", "ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf", "consola.ttf"),
}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    name, gh_path, fallback = FONT_FILES[kind]
    path = FONT_DIR / name
    if not path.exists():
        FONT_DIR.mkdir(exist_ok=True)
        try:
            url = "https://github.com/google/fonts/raw/main/" + gh_path
            with urllib.request.urlopen(url, timeout=20) as r:
                path.write_bytes(r.read())
        except Exception as e:                      # offline: system fallback
            print(f"  (font {name} not fetched: {e}; using {fallback})")
            return ImageFont.truetype(fallback, size)
    return ImageFont.truetype(str(path), size)


def wrap(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=f) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def hub_chart(size: tuple[int, int]) -> Image.Image:
    """A small chart in the series' colors: grey points, dashed truth, red fit, blue corrected."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(7)
    n = 28
    xt = rng.uniform(0, 10, n)
    x = xt + rng.normal(0, 1.6, n)             # noisy x: the ordinary fit flattens
    y = 1 + 2 * xt + rng.normal(0, 1.5, n)
    b1, b0 = np.polyfit(x, y, 1)
    lam = np.var(xt) / (np.var(xt) + 1.6 ** 2)
    c1 = b1 / lam
    c0 = y.mean() - c1 * x.mean()
    xx = np.linspace(-2, 12, 2)

    dpi = 100
    fig, ax = plt.subplots(figsize=(size[0] / dpi, size[1] / dpi), dpi=dpi)
    fig.patch.set_facecolor(PLOT)
    ax.set_facecolor(PLOT)
    ax.grid(True, color=GRID, lw=1)
    for s in ax.spines.values():
        s.set_color(RULE)
    ax.tick_params(colors=MUTED, labelsize=11)
    ax.plot(xx, 1 + 2 * xx, "--", color=INK, lw=1.8, label="truth")
    ax.plot(xx, b0 + b1 * xx, color=FIT, lw=2.6, label="ordinary fit")
    ax.plot(xx, c0 + c1 * xx, color=FIX, lw=2.2, label="corrected")
    ax.scatter(x, y, s=34, color=PT, zorder=3)
    ax.set_xlim(-2, 12)
    ax.set_ylim(-4, 26)
    ax.set_xlabel("x", color=MUTED, fontsize=12)
    ax.set_ylabel("y", color=MUTED, fontsize=12)
    ax.legend(loc="upper left", frameon=False, fontsize=11, labelcolor=INK)
    fig.tight_layout(pad=1.0)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=PLOT)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def _axes(size: tuple[int, int]):
    """A matplotlib figure/axes pair in the card's plot style (shared by the drawn charts)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dpi = 100
    fig, ax = plt.subplots(figsize=(size[0] / dpi, size[1] / dpi), dpi=dpi)
    fig.patch.set_facecolor(PLOT)
    ax.set_facecolor(PLOT)
    ax.grid(True, color=GRID, lw=1)
    for s in ax.spines.values():
        s.set_color(RULE)
    ax.tick_params(colors=MUTED, labelsize=11)
    return plt, fig, ax, dpi


def _render(plt, fig, dpi: int) -> Image.Image:
    fig.tight_layout(pad=1.0)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=PLOT)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def mm1_chart(size: tuple[int, int]) -> Image.Image:
    """Reflections card: the M/M/1 hockey stick L = ρ/(1−ρ) with its ±1 sd band (page §4)."""
    import numpy as np

    plt, fig, ax, dpi = _axes(size)
    r = np.linspace(0, 0.975, 300)
    L, sd = r / (1 - r), np.sqrt(r) / (1 - r)
    ax.fill_between(r, np.maximum(0, L - sd), L + sd, color=S2, alpha=0.15, lw=0)
    ax.plot(r, L, color=S1, lw=2.8, label="jobs in system, L = ρ/(1−ρ)")
    ax.plot(r, L + sd, color=S2, lw=1.4, ls=(0, (6, 4)), label="±1 standard deviation")
    ax.plot(r, np.maximum(0, L - sd), color=S2, lw=1.4, ls=(0, (6, 4)))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 40)
    ax.set_xlabel("utilization ρ", color=MUTED, fontsize=12)
    ax.set_ylabel("jobs in system", color=MUTED, fontsize=12)
    ax.legend(loc="upper left", frameon=False, fontsize=11, labelcolor=INK)
    return _render(plt, fig, dpi)


def buffers_chart(size: tuple[int, int]) -> Image.Image:
    """Balanced-plant card: exact throughput of balanced exponential lines vs buffer size (page §8).
    The numbers are the page's DATA.bufsweep (exact Markov-chain solutions)."""
    plt, fig, ax, dpi = _axes(size)
    data = {
        2: [0.66667, 0.75, 0.8, 0.83333, 0.85714, 0.875, 0.88889, 0.9, 0.90909],
        3: [0.5641, 0.67047, 0.73402, 0.77671, 0.80749, 0.83076, 0.84899, 0.86367, 0.87573],
        4: [0.51478, 0.63115, 0.70071, 0.74771, 0.78178, 0.80766, 0.82803, 0.84447, 0.85804],
        5: [0.4858, 0.60758, 0.68049, 0.72995, 0.76593, 0.79337, 0.815],
    }
    # The page's three line forms (solid / dashed / dotted) and a hollow square for the 4th series.
    styles = {2: (S1, "solid", "o"), 3: (S2, (0, (4, 2.4)), "o"), 4: (S3, (0, (0.01, 1.85)), "o"), 5: (S4, "solid", "s")}
    ax.axhline(1, color=MUTED, lw=1.5, ls=(0, (4, 2.4)))
    ax.text(7.9, 1.012, "demand", color=MUTED, fontsize=11, ha="right", va="bottom")
    for n, ys in data.items():
        c, ls, mk = styles[n]
        lw = 3.0 if n == 4 else 2.2
        kw = dict(marker=mk, ms=6, mfc=PLOT, mec=c, mew=1.8) if mk == "s" else dict(marker=mk, ms=5)
        ax.plot(range(len(ys)), ys, color=c, lw=lw, ls=ls, solid_capstyle="round", dash_capstyle="round", label=f"{n} stations", **kw)
    ax.set_xlim(-0.3, 8.3)
    ax.set_ylim(0.4, 1.04)
    ax.set_xlabel("buffer slots between stations", color=MUTED, fontsize=12)
    ax.set_ylabel("throughput ÷ demand", color=MUTED, fontsize=12)
    ax.legend(loc="lower right", frameon=False, fontsize=11, labelcolor=INK)
    return _render(plt, fig, dpi)


def markov_chart(size: tuple[int, int]) -> Image.Image:
    """Marginalia cards: P(up at step n) from both starts settling onto pi_up (a = 0.05, b = 0.30),
    exactly as the Markov page draws it, in the Marginalia colors."""
    import numpy as np

    plt, fig, ax, dpi = _axes(size)
    a, b, N = 0.05, 0.30, 30
    lam, pi_up = 1 - a - b, b / (a + b)
    n = np.arange(N + 1)
    up = pi_up + lam ** n * (1 - pi_up)
    dn = pi_up + lam ** n * (0 - pi_up)
    ax.axhline(pi_up, color=MUTED, lw=2.4, ls=(0, (0.01, 1.85)), dash_capstyle="round", label="long-run value")
    ax.plot(n, up, color=M1, lw=2.6, label="start up")
    ax.plot(n, dn, color=M2, lw=2.4, ls=(0, (4, 2.4)), label="start down")
    ax.set_xlim(0, N)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("step n", color=MUTED, fontsize=12)
    ax.set_ylabel("P(up at step n)", color=MUTED, fontsize=12)
    ax.legend(loc="lower right", frameon=False, fontsize=11, labelcolor=INK)
    return _render(plt, fig, dpi)


def edgeworth_chart(size: tuple[int, int]) -> Image.Image:
    """CLT card: the exact error F_n − Φ for an exponential parent at n = 10 (Gamma CDF) against the
    one-term Edgeworth prediction, as on the page."""
    import numpy as np
    from math import erf, exp, lgamma, log, sqrt, pi

    def gamma_cdf_int(k: int, s: float) -> float:          # 1 − Σ_{j<k} e^{−s} s^j / j!
        if s <= 0:
            return 0.0
        return 1 - sum(exp(-s + j * log(s) - lgamma(j + 1)) for j in range(k))

    plt, fig, ax, dpi = _axes(size)
    n = 10
    x = np.linspace(-4, 4, 321)
    Phi = np.array([0.5 * (1 + erf(v / sqrt(2))) for v in x])
    phi = np.exp(-x * x / 2) / sqrt(2 * pi)
    exact = np.array([gamma_cdf_int(n, n + v * sqrt(n)) for v in x]) - Phi
    one = -phi * 2 * (x * x - 1) / (6 * sqrt(n))
    ax.axhline(0, color=RULE, lw=1)
    ax.plot(x, 1000 * exact, color=M1, lw=2.6, label="exact error")
    ax.plot(x, 1000 * one, color=M2, lw=2.4, ls=(0, (4, 2.4)), label="one-term Edgeworth")
    ax.set_xlim(-4, 4)
    ax.set_xlabel("x (standardized mean), exponential data, n = 10", color=MUTED, fontsize=12)
    ax.set_ylabel("error × 1000", color=MUTED, fontsize=12)
    ax.legend(loc="upper left", frameon=False, fontsize=11, labelcolor=INK)
    return _render(plt, fig, dpi)


def figure_for(slug: str, spec: dict, size: tuple[int, int]) -> Image.Image:
    if "chart" in spec:
        return globals()[spec["chart"]](size)
    if "figure" not in spec:
        return hub_chart(size)
    src = FIG / slug / "figures" / spec["figure"]
    im = Image.open(src).convert("RGB")
    l, t, r, b = spec["crop"]
    im = im.crop((int(l * im.width), int(t * im.height), int(r * im.width), int(b * im.height)))
    im.thumbnail(size, Image.LANCZOS)         # contain-fit
    return im


def make_card(slug: str, spec: dict) -> Path:
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    for gx in range(0, W, 40):                 # faint notebook grid
        d.line([(gx, 0), (gx, H)], fill=GRID, width=1)
    for gy in range(0, H, 40):
        d.line([(0, gy), (W, gy)], fill=GRID, width=1)

    # figure frame at the right, figure contain-fitted and centered
    fx0, fy0, fx1, fy1 = FRAME
    fig = figure_for(slug, spec, (fx1 - fx0 - 2, fy1 - fy0 - 2))
    d.rectangle(FRAME, fill="#ffffff" if "figure" in spec else PLOT, outline=RULE, width=1)  # matplotlib figures are white
    ox = fx0 + 1 + (fx1 - fx0 - 2 - fig.width) // 2
    oy = fy0 + 1 + (fy1 - fy0 - 2 - fig.height) // 2
    im.paste(fig, (ox, oy))

    # text column
    x, y = PAD, PAD + 4
    f_eye = font("display-semi", 20)
    eyebrow = spec["eyebrow"].upper()
    cx = x                                     # letter-spaced eyebrow, char by char
    for ch in eyebrow:
        d.text((cx, y), ch, font=f_eye, fill=MUTED)
        cx += d.textlength(ch, font=f_eye) + 1.6
    y += 46

    f_title = font("display-bold", 64)
    lines = wrap(d, spec["title"], f_title, COL_W)
    if len(lines) > 2:
        f_title = font("display-bold", 54)
        lines = wrap(d, spec["title"], f_title, COL_W)
    for ln in lines:
        d.text((x - 3, y), ln, font=f_title, fill=INK)
        y += int(f_title.size * 1.04)
    y += 18
    d.line([(x, y), (x + 56, y)], fill=FIT, width=3)   # short red pencil rule
    y += 26

    f_body = font("body", 23)
    body = wrap(d, spec["lead"], f_body, COL_W)[:4]
    for ln in body:
        d.text((x, y), ln, font=f_body, fill=INK)
        y += 33

    f_mono = font("mono", 17)
    d.text((x, H - PAD - 20), SITE, font=f_mono, fill=MUTED)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{slug}.png"
    # 256-color palette keeps each card well under 300 KB with no visible loss on flat art
    im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).save(out, optimize=True)
    return out


def main(argv: list[str]) -> int:
    slugs = argv or list(CARDS)
    for slug in slugs:
        if slug not in CARDS:
            print(f"unknown card: {slug} (known: {', '.join(CARDS)})")
            return 1
        out = make_card(slug, CARDS[slug])
        print(f"{out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
