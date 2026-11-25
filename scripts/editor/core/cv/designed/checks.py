"""What blocks a Designed CV export or marks it failed (D8), on the printed PDF:

errors    more or fewer than one page; a blocklist term; the birth date in any of its usual
          forms; a ticked item's text that is not in the PDF (something got clipped)
warnings  voice words, Spanish text identical to the English, a photo under 300 dpi

The column overflow is checked before printing, from the page's own measure (export.measure).

Reading the PDF: the browser writes each piece of text in page order — a whole role, then its
date; the sidebar, then the main column — so the characters are read in that order
(pdfplumber's page.chars) instead of being regrouped into visual rows, where a date sitting
beside a two-line role would land in the middle of it.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from .. import scans
from ... import validate
from ..pdfcheck import normalize
from . import model as M
from . import schema as S

MIN_DPI = 300
_MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
AGE_RE = re.compile(r"\b(?:Edad|Age):\s*(\d{1,3})\b")


def read_pdf(path: Path) -> tuple[int, str]:
    """(pages, text): the text in the order the PDF holds it, one space where a line or a
    block ends, normalized like the other PDF checks."""
    import pdfplumber

    out: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        pages = len(pdf.pages)
        for page in pdf.pages:
            prev = None
            for ch in page.chars:
                t = ch.get("text") or ""
                if prev is not None and t.strip():
                    same_line = abs(ch["top"] - prev["top"]) < 2.0
                    gap = ch["x0"] - prev["x1"]
                    if not same_line or gap > max(1.0, 0.25 * float(ch.get("size") or 8)) or gap < -2.0:
                        out.append(" ")
                out.append(t)
                if t.strip():
                    prev = ch
            out.append(" ")
    return pages, normalize("".join(out))


def birth_forms(birth: date) -> list[str]:
    """The ways a birth date is usually written; none may appear in the PDF (D7 / D8)."""
    d, m, y = birth.day, birth.month, birth.year
    es, en = _MONTHS_ES[m - 1], _MONTHS_EN[m - 1]
    forms = [
        birth.isoformat(),
        f"{d:02d}/{m:02d}/{y}",
        f"{m:02d}/{d:02d}/{y}",
        f"{d}/{m}/{y}",
        f"{m}/{d}/{y}",
        f"{d} de {es} de {y}",
        f"{d} de {es}",
        f"{en} {d}, {y}",
        f"{en} {d}",
    ]
    return list(dict.fromkeys(forms))


def birth_hits(text: str, birth: date) -> list[str]:
    low = normalize(text).lower()
    hits = []
    for form in birth_forms(birth):
        if re.search(r"(?<![\d/])" + re.escape(form.lower()) + r"(?![\d/])", low):
            hits.append(form)
    return hits


def _squash(s: str) -> str:
    return re.sub(r"\s+", "", normalize(s)).lower()


def missing_texts(wanted: Iterable[tuple[str, str]], pdf_text: str) -> list[tuple[str, str]]:
    """(label, text) of everything that should be on the page and is not in the PDF text.
    Compared without spaces and case: a line break or a small-caps heading is not a miss."""
    hay = _squash(pdf_text)
    return [(label, text) for label, text in wanted if _squash(text) and _squash(text) not in hay]


def photo_dpi(pixels: tuple[int, int], css_px: int) -> float:
    """The photo's resolution at its printed size: a square cut from the picture's shorter
    side, printed css_px wide (96 CSS px = 1 inch)."""
    return min(pixels) / (css_px / 96.0)


def identical_texts(content: dict) -> list[str]:
    """Labels of ticked Designed text whose Spanish equals its English (a likely missing
    translation; names, numbers and short labels are let through)."""
    en, es = dict(M.ticked_texts(content, "en")), dict(M.ticked_texts(content, "es"))
    out = []
    for label, text in en.items():
        if label in ("name",) or label.endswith(("› org", "› years", "› issuer", "› date")):
            continue
        if es.get(label) == text and not validate.identical_allowed("", text):
            out.append(label)
    return out


def check_pdf(
    pdf: Path,
    content: dict,
    lang: str,
    *,
    age_line: Optional[str],
    birth: Optional[date],
    terms: Iterable[scans.Term] = (),
    photo: Optional[tuple[tuple[int, int], int]] = None,
) -> dict:
    """{"pages", "errors": [{code, message}], "warnings": [...], "age": int | None}."""
    errors: list[dict] = []
    warnings: list[dict] = []
    pages, text = read_pdf(pdf)
    if pages != 1:
        errors.append({"code": "pages", "message": f"the PDF is {pages} pages; it must be exactly one"})
    for h in scans.blocklist_hits(text, terms, scans.ALLOWED_IN_PUBLISHED_PDFS):
        errors.append({"code": "blocklist", "message": f"blocked term “{h['term']}” ({h['reason'] or 'no reason given'}): {h['context']}"})
    if birth is not None:
        for form in birth_hits(text, birth):
            errors.append({"code": "birth-date", "message": f"the birth date is in the PDF (written as “{form}”) — only the age may print"})
    wanted = M.ticked_texts(content, lang)
    if age_line:
        wanted.append(("age line", age_line))
    for label, t in missing_texts(wanted, text):
        errors.append({"code": "missing-text", "message": f"{label} is ticked but not in the PDF: “{t if len(t) <= 80 else t[:77] + '…'}”"})
    for label, t in wanted:
        words = validate.voice_words(t)
        if words:
            warnings.append({"code": "voice", "message": f"{label}: voice words — {', '.join(words)}"})
    for label in identical_texts(content):
        warnings.append({"code": "same", "message": f"{label}: the Spanish text is identical to the English"})
    if photo is not None:
        dpi = photo_dpi(*photo)
        if dpi < MIN_DPI:
            warnings.append({"code": "photo-dpi", "message": f"the photo prints at {dpi:.0f} dpi (under {MIN_DPI})"})
    m = AGE_RE.search(text)
    return {"pages": pages, "errors": errors, "warnings": warnings, "age": int(m.group(1)) if m else None, "chars": len(text)}


def pdf_age(pdf: Path) -> Optional[int]:
    """The age a Designed CV PDF carries ("Edad: 20 años" / "Age: 20"), None when unreadable."""
    try:
        _, text = read_pdf(pdf)
    except Exception:
        return None
    m = AGE_RE.search(text)
    return int(m.group(1)) if m else None
