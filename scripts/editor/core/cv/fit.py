"""The one-line fit rule for "Role · Org ⇥ Date" entry lines (plan §3).

Word puts the date at a right tab stop. If the text before the tab, one space,
and the date together are wider than the room between the paragraph's left
indent and that tab stop, Word wraps the date to the next line. Widths are
measured with Georgia itself (Pillow, C:\\Windows\\Fonts\\georgia*.ttf) at the
run's own size; the available width comes from the document's page size,
margins, indents and tab stop, never from hard-coded numbers. The exported PDF
is the authoritative check (pdfcheck.py); this one is the instant estimate.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .docxread import DocInfo, Para, Run

FONT_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
FONT_FILES = {
    (False, False): "georgia.ttf",
    (True, False): "georgiab.ttf",
    (False, True): "georgiai.ttf",
    (True, True): "georgiaz.ttf",
}
SCALE = 64  # measure at 64× the size: FreeType rounds advances to whole pixels
TIGHT_FRACTION = 0.03  # within 3% of overflowing → "tight" (plan §5 warning)


class FontUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=32)
def _font(bold: bool, italic: bool, size_pt: float):
    from PIL import ImageFont

    path = FONT_DIR / FONT_FILES[(bool(bold), bool(italic))]
    if not path.is_file():
        raise FontUnavailable(f"{path} is missing — cannot measure with Georgia")
    return ImageFont.truetype(str(path), size_pt * SCALE)


def fonts_available() -> Optional[str]:
    """None when every Georgia face is present, else the problem."""
    missing = [n for n in FONT_FILES.values() if not (FONT_DIR / n).is_file()]
    return None if not missing else "missing font file(s): " + ", ".join(missing)


def width_pt(text: str, bold: bool = False, italic: bool = False, size_pt: float = 11.0) -> float:
    """Advance width of `text` in points (1 pt = 1 px at 72 dpi)."""
    if not text:
        return 0.0
    text = text.replace("\xa0", " ")
    return _font(bold, italic, size_pt).getlength(text) / SCALE


def _runs_width(runs: list[Run]) -> float:
    return sum(width_pt(r.text, r.bold, r.italic, r.size_pt) for r in runs)


def split_at_tab(runs: list[Run]) -> tuple[list[Run], list[Run]]:
    """Runs before the last tab and after it (the tab itself dropped)."""
    joined = "".join(r.text for r in runs)
    cut = joined.rfind("\t")
    if cut < 0:
        return list(runs), []
    before, after, pos = [], [], 0
    for r in runs:
        start, end = pos, pos + len(r.text)
        pos = end
        if end <= cut:
            before.append(r)
        elif start > cut:
            after.append(r)
        else:  # the run holds the tab
            head, tail = r.text[: cut - start], r.text[cut - start + 1 :]
            if head:
                before.append(Run(head, r.bold, r.italic, r.underline, r.size_pt, r.font))
            if tail:
                after.append(Run(tail, r.bold, r.italic, r.underline, r.size_pt, r.font))
    return before, after


@dataclass
class FitLine:
    index: int
    text: str  # "Role · Org"
    date: str
    used_pt: float
    avail_pt: float
    left_pt: float
    left_pct: float
    status: str  # fits | tight | overflow

    def to_json(self) -> dict:
        d = asdict(self)
        for k in ("used_pt", "avail_pt", "left_pt", "left_pct"):
            d[k] = round(d[k], 2)
        return d


def check_entry(p: Para, doc: DocInfo) -> FitLine:
    before, after = split_at_tab(p.runs)
    gap_size = before[-1].size_pt if before else doc.body_size_pt
    gap = width_pt(" ", size_pt=gap_size)
    used = _runs_width(before) + gap + _runs_width(after)
    right_edge = doc.text_width_pt - p.right_indent_pt
    if p.tab_right_pt is not None:
        right_edge = min(p.tab_right_pt, right_edge)
    avail = right_edge - p.left_indent_pt
    left = avail - used
    if left < 0:
        status = "overflow"
    elif left < avail * TIGHT_FRACTION:
        status = "tight"
    else:
        status = "fits"
    return FitLine(
        index=p.index,
        text="".join(r.text for r in before).replace("\xa0", " ").strip(),
        date="".join(r.text for r in after).replace("\xa0", " ").strip(),
        used_pt=used,
        avail_pt=avail,
        left_pt=left,
        left_pct=(left / avail * 100.0) if avail else 0.0,
        status=status,
    )


def check_doc(doc: DocInfo) -> list[FitLine]:
    return [check_entry(p, doc) for p in doc.entries()]


def summary(lines: list[FitLine]) -> dict:
    worst = min(lines, key=lambda l: l.left_pt) if lines else None
    return {
        "count": len(lines),
        "overflow": sum(1 for l in lines if l.status == "overflow"),
        "tight": sum(1 for l in lines if l.status == "tight"),
        "worst": worst.to_json() if worst else None,
    }
