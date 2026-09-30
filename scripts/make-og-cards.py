"""Make the 1200x630 link-preview cards for the main site (assets/images/og/).

One card per page: four designed cards for index / about / experience / projects (the main
site's look: Palette B tokens, Lora + DM Sans, a photo panel on the right) and one per project
sub-page (a crop of an image already on that page, or a designed text card when no photo may
be used). The og:image tags in each page's <head> point at these files by absolute URL, so
keep the names stable. Sub-page cards are named <slug>.jpg / <slug>.png.

Run from anywhere:   <python> scripts/make-og-cards.py [name ...]
  (on this machine: & "$env:LOCALAPPDATA\\Python\\pythoncore-3.14-64\\python.exe" scripts/make-og-cards.py)
Needs Pillow. Fonts: the script fetches Lora and DM Sans from the google/fonts GitHub repo into
scripts/.og-fonts/ (git-ignored) on first run; with no network it falls back to Georgia /
Segoe UI. Modeled on learning/workshop/tools/make-og-cards.py (the /learning cards).

After changing a card: rerun this script, deploy, then run the page's URL through LinkedIn
Post Inspector (https://www.linkedin.com/post-inspector/) so LinkedIn drops its cached copy.
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                            # repo root
OUT = ROOT / "assets" / "images" / "og"
FONT_DIR = HERE / ".og-fonts"

W, H = 1200, 630
PAD = 72
PANEL_X = 720                                 # photo panel: PANEL_X..W, full height

# css/style.css Palette B (Warm Neutral, active) tokens
BG, BG_SECTION, INK, MUTED = "#FAFAF8", "#EDE6D5", "#1A1A17", "#6B6963"
BRONZE, BORDER = "#6B4F1A", "#DDD5C8"

SITE = "gideonong.me"
IMG = ROOT / "assets" / "images"

# kind "designed": text column + optional photo panel (`panel`: list of (path, focus_x, focus_y);
#   two items stack). kind "photo": a cover crop of one image around (focus_x, focus_y).
# Text matches the EN strings on the site (titles, meta descriptions, translations.js).
CARDS = {
    "home": {
        "kind": "designed", "format": "jpg",
        "title": "Gideon A. Ong",
        "line": "Mechanical Engineering & Spanish\nUniversity of Tulsa",
        "panel": [(IMG / "about" / "headshot.jpg", 0.5, 0.4)],
    },
    "about": {
        "kind": "designed", "format": "jpg",
        "kicker": "Gideon A. Ong",
        "title": "About",
        "line": "Education, skills, honors, and languages",
        "panel": [(IMG / "about" / "headshot.jpg", 0.5, 0.4)],
    },
    "experience": {
        "kind": "designed", "format": "jpg",
        "kicker": "Gideon A. Ong",
        "title": "Experience",
        "line": "Engineering internships, machine shop, research, and grading experience",
        "panel": [(IMG / "experience" / "hero" / "lathe-tile.jpg", 0.52, 0.5)],
    },
    "projects": {
        "kind": "designed", "format": "jpg",
        "kicker": "Gideon A. Ong",
        "title": "Projects",
        "line": "Failure analysis, fabrication, data tools, and research",
        "panel": [(IMG / "projects" / "pump-cylinder-failure" / "pin-installed-wide.jpg", 0.58, 0.5),
                  (IMG / "projects" / "g-view" / "g-view-demo.png", 0.6, 0.4)],
    },
    "pump-cylinder-failure": {
        "kind": "photo", "format": "jpg",
        "src": IMG / "projects" / "pump-cylinder-failure" / "pin-installed-wide.jpg", "focus": (0.5, 0.5),
    },
    "g-view": {
        "kind": "photo", "format": "png",
        "src": IMG / "projects" / "g-view" / "g-view-demo.png", "focus": (0.5, 0.0),   # trim the empty bottom
    },
    # Designed, no photo: the Eagle photos are Matthew Rowan's (credit OK pending).
    "eagle-pathway": {
        "kind": "designed", "format": "png",
        "kicker": "Gideon A. Ong",
        "title": "Wheelchair-Accessible Pathway (Eagle Scout Project)",
        "line": "Planned and led 27 volunteers to build a 273.5 sq ft ADA-compliant pathway "
                "for a business that employs adults with special needs.",
        "meta": "Service · July 2022",
    },
}

# (cache name, google/fonts path, {axis: value}, system fallback)
FONT_FILES = {
    "serif-semi": ("Lora.ttf", "ofl/lora/Lora%5Bwght%5D.ttf", {"Weight": 600}, "georgiab.ttf"),
    "serif": ("Lora.ttf", "ofl/lora/Lora%5Bwght%5D.ttf", {"Weight": 400}, "georgia.ttf"),
    "sans": ("DMSans.ttf", "ofl/dmsans/DMSans%5Bopsz%2Cwght%5D.ttf", {"Weight": 400, "Optical size": 14}, "segoeui.ttf"),
    "sans-medium": ("DMSans.ttf", "ofl/dmsans/DMSans%5Bopsz%2Cwght%5D.ttf", {"Weight": 500, "Optical size": 14}, "seguisb.ttf"),
}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    name, gh_path, axes, fallback = FONT_FILES[kind]
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
    f = ImageFont.truetype(str(path), size)
    try:                                            # variable font: set the named axes
        f.set_variation_by_axes([axes.get(a["name"].decode() if isinstance(a["name"], bytes) else a["name"], a["default"])
                                 for a in f.get_variation_axes()])
    except OSError:
        pass
    return f


def wrap(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, width: int) -> list[str]:
    if "\n" in text:                           # explicit breaks: wrap each part on its own
        return [ln for part in text.split("\n") for ln in wrap(draw, part, f, width)]
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


def cover(src: Path, size: tuple[int, int], focus: tuple[float, float]) -> Image.Image:
    """Scale to cover `size`, then crop around the focus point (fractions of the source)."""
    im = Image.open(src).convert("RGB")
    w, h = size
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    x = min(max(round(focus[0] * im.width - w / 2), 0), im.width - w)
    y = min(max(round(focus[1] * im.height - h / 2), 0), im.height - h)
    return im.crop((x, y, x + w, y + h))


def draw_panel(im: Image.Image, d: ImageDraw.ImageDraw, panel: list) -> None:
    pw = W - PANEL_X
    gap = 4
    ph = (H - gap * (len(panel) - 1)) // len(panel)
    y = 0
    for i, (src, fx, fy) in enumerate(panel):
        h = ph if i < len(panel) - 1 else H - y
        im.paste(cover(src, (pw, h), (fx, fy)), (PANEL_X, y))
        y += h + gap
    if len(panel) > 1:                              # hairline gaps between stacked photos
        d.rectangle((PANEL_X, ph, W, ph + gap - 1), fill=BG)
    d.line([(PANEL_X - 1, 0), (PANEL_X - 1, H)], fill=BORDER, width=1)


def make_designed(spec: dict) -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    panel = spec.get("panel")
    if panel:
        draw_panel(im, d, panel)
    col_w = (PANEL_X if panel else W) - 2 * PAD

    # measure the text block, then center it vertically above the footer
    f_kick = font("serif", 30)
    f_title = font("serif-semi", 84 if panel else 62)
    t_lines = wrap(d, spec["title"], f_title, col_w)
    f_line = font("sans", 32 if panel else 30)
    l_lines = wrap(d, spec["line"], f_line, col_w)[:4]
    f_meta = font("sans-medium", 24)

    t_lead, l_lead = int(f_title.size * 1.14), int(f_line.size * 1.42)
    block = (48 if "kicker" in spec else 0) + t_lead * len(t_lines) + 30 + 4 + 34 + l_lead * len(l_lines) \
        + (44 if "meta" in spec else 0)
    y = max(PAD - 8, (H - 60 - block) // 2)
    x = PAD

    if "kicker" in spec:
        d.text((x, y), spec["kicker"], font=f_kick, fill=MUTED)
        y += 48
    for ln in t_lines:
        d.text((x - 2, y), ln, font=f_title, fill=INK)
        y += t_lead
    y += 30
    d.rectangle((x, y, x + 64, y + 3), fill=BRONZE)  # the hero's short bronze rule
    y += 4 + 34
    for ln in l_lines:
        d.text((x, y), ln, font=f_line, fill=INK)
        y += l_lead
    if "meta" in spec:
        y += 14
        d.text((x, y), spec["meta"], font=f_meta, fill=MUTED)

    d.text((x, H - PAD + 10 - 24), SITE, font=font("sans-medium", 24), fill=BRONZE)
    return im


def make_photo(spec: dict) -> Image.Image:
    return cover(spec["src"], (W, H), spec["focus"])


def save(im: Image.Image, name: str, fmt: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{name}.{fmt}"
    if fmt == "jpg":
        im.save(out, "JPEG", quality=86, progressive=True, optimize=True, subsampling=0)
    else:
        # 256-color palette keeps flat cards and screenshots well under 300 KB
        im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).save(out, optimize=True)
    return out


def main(argv: list[str]) -> int:
    names = argv or list(CARDS)
    for name in names:
        if name not in CARDS:
            print(f"unknown card: {name} (known: {', '.join(CARDS)})")
            return 1
        spec = CARDS[name]
        im = make_designed(spec) if spec["kind"] == "designed" else make_photo(spec)
        out = save(im, name, spec["format"])
        print(f"{out.relative_to(ROOT).as_posix()}  {im.width}x{im.height}  {out.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
