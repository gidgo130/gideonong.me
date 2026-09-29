"""Make the 1200x630 link-preview cards for /learning (learning/assets/og/*.png).

One card for the hub (learning.png) and one per module (<slug>.png), in the /learning
"lab notebook" look: paper background, faint grid, eyebrow, title, lead, and a crop of the
module's main figure from learning/workshop/modules/<slug>/figures/ (make those first by
running the module's .py, see learning/workshop/README.md). The hub card draws its own small
chart with the series' fixed colors (dashed ink = truth, red = ordinary fit, blue = corrected).

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


def figure_for(slug: str, spec: dict, size: tuple[int, int]) -> Image.Image:
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
