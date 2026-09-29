"""Checks on an exported PDF (pdfplumber): page count, whether every entry line
of the master ended up on ONE line, and whether every paragraph of the master
is in the PDF at all (a paragraph edited in Word after the export is missing →
the PDF is stale). The extracted text also feeds the scans.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

LINE_TOLERANCE_PT = 2.0  # words whose tops differ by less than this share a line


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").replace("\xa0", " ").replace("\t", " ")
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class PdfText:
    path: str
    pages: int
    lines: list[str] = field(default_factory=list)  # normalized, in reading order
    text: str = ""  # normalized, lines joined with single spaces
    page_of_line: list[int] = field(default_factory=list)


def read_pdf(path: Path) -> PdfText:
    import pdfplumber

    out = PdfText(str(path), 0)
    with pdfplumber.open(str(path)) as pdf:
        out.pages = len(pdf.pages)
        for pi, page in enumerate(pdf.pages, 1):
            words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
            words.sort(key=lambda w: (w["top"], w["x0"]))
            rows: list[list[dict]] = []
            for w in words:
                if rows and abs(w["top"] - rows[-1][0]["top"]) < LINE_TOLERANCE_PT:
                    rows[-1].append(w)
                else:
                    rows.append([w])
            for row in rows:
                row.sort(key=lambda w: w["x0"])
                out.lines.append(normalize(" ".join(w["text"] for w in row)))
                out.page_of_line.append(pi)
    out.text = " ".join(out.lines)
    return out


def _hyphen_joined(text: str) -> str:
    """'lessons- learned' (a hyphenated word broken across PDF lines) → 'lessons-learned'."""
    return re.sub(r"(\w)- (\w)", r"\1-\2", text)


def entry_lines_check(entry_texts: list[str], pdf: PdfText) -> list[dict]:
    """For each master entry line, whether it appears as ONE line in the PDF."""
    lines = set(pdf.lines)
    out = []
    for t in entry_texts:
        n = normalize(t)
        out.append({"text": n, "ok": n in lines})
    return out


def coverage_check(paragraph_texts: list[str], pdf: PdfText) -> list[str]:
    """Master paragraphs (normalized) that do not appear in the PDF text."""
    text = pdf.text
    joined = _hyphen_joined(text)
    missing = []
    for t in paragraph_texts:
        n = normalize(t)
        if not n:
            continue
        if n in text or n in joined or _hyphen_joined(n) in joined:
            continue
        missing.append(n)
    return missing


def word_width(pdf_path: Path, phrase: str, page_no: int = 1) -> float | None:
    """Width in points of the first occurrence of `phrase` (consecutive words) on a page; tests use it."""
    import pdfplumber

    target = normalize(phrase).split(" ")
    with pdfplumber.open(str(pdf_path)) as pdf:
        page = pdf.pages[page_no - 1]
        words = page.extract_words(use_text_flow=False)
        words.sort(key=lambda w: (round(w["top"]), w["x0"]))
        for i in range(len(words) - len(target) + 1):
            seg = words[i : i + len(target)]
            if [normalize(w["text"]) for w in seg] == target and abs(seg[0]["top"] - seg[-1]["top"]) < LINE_TOLERANCE_PT:
                return seg[-1]["x1"] - seg[0]["x0"]
    return None
