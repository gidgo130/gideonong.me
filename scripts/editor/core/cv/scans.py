"""Text scans on the CV set (plan §5): confidentiality blocklist, voice words,
and EN/ES parity.

The blocklist is staging/editor-private/blocklist.txt (gitignored):
    # comment
    term | why it must not appear
    term
Matching is case-insensitive and whitespace-normalized. Hits on a published
document are errors. The +1 (918) phone is allowed in the published CV and
résumé PDFs only (decision 9), so it is stripped from the text before the
blocklist runs on a PDF — anything else in the list is blocked everywhere.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .. import validate
from .docxread import DocInfo, Para
from .pdfcheck import normalize

# Decision 9: the work Google Voice number may appear in the published CV/résumé PDFs.
ALLOWED_IN_PUBLISHED_PDFS = [re.compile(r"\+?1?\s*\(?918\)?[\s.-]*\d{3}[\s.-]*\d{4}")]

SPINELLI_RE = re.compile(r"spinelli", re.IGNORECASE)


@dataclass(frozen=True)
class Term:
    text: str
    reason: str
    line: int


def load_blocklist(path: Path) -> tuple[list[Term], Optional[str]]:
    """(terms, warning). A missing or empty file is a warning, never an error."""
    path = Path(path)
    if not path.is_file():
        return [], f"no blocklist at {path.as_posix()} — the confidentiality scan has nothing to look for"
    terms = []
    for n, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        term, _, reason = line.partition("|")
        term = normalize(term)
        if term:
            terms.append(Term(term, reason.strip(), n))
    if not terms:
        return [], f"{path.as_posix()} has no terms"
    return terms, None


def _context(text: str, start: int, end: int, span: int = 40) -> str:
    a, b = max(0, start - span), min(len(text), end + span)
    return ("…" if a else "") + text[a:b] + ("…" if b < len(text) else "")


def blocklist_hits(text: str, terms: Iterable[Term], allow: Iterable[re.Pattern] = ()) -> list[dict]:
    """Every term found in text (after the allowed patterns are blanked out)."""
    norm = normalize(text)
    for pat in allow:
        norm = pat.sub(lambda m: " " * len(m.group(0)), norm)
    low = norm.lower()
    hits = []
    for t in terms:
        i = low.find(t.text.lower())
        if i >= 0:
            hits.append({"term": t.text, "reason": t.reason, "context": _context(norm, i, i + len(t.text))})
    return hits


def voice_hits(doc: DocInfo) -> list[dict]:
    """Voice words per paragraph. 'leveraged' is Gideon's own wording in the Spinelli bullet
    (the bullet itself or the entry line it belongs to names Spinelli)."""
    parent_text: dict[int, str] = {}
    for entry_index, bullets in _bullet_groups(doc).items():
        entry = doc.paragraphs[entry_index]
        for b in bullets:
            parent_text[b.index] = entry.text
    out = []
    for p in doc.paragraphs:
        if p.kind == "empty":
            continue
        words = validate.voice_words(p.text)
        if SPINELLI_RE.search(p.text) or SPINELLI_RE.search(parent_text.get(p.index, "")):
            words = [w for w in words if not w.startswith("leverag")]
        if words:
            out.append({"index": p.index, "text": normalize(p.text), "words": words})
    return out


_NUM_RE = re.compile(r"\d+(?:[.,]\d+)*\s?(?:k|mil)\b|\d+(?:[.,]\d+)*", re.IGNORECASE)


def _numbers(text: str) -> list[str]:
    """Numbers in a text, as comparable strings: thousands separators dropped, 'k' / 'mil' expanded."""
    out = []
    for tok in _NUM_RE.findall(text):
        t = tok.lower().replace(" ", "")
        k = t.endswith("k") or t.endswith("mil")
        if k:
            t = t[:-3] if t.endswith("mil") else t[:-1]
        t = re.sub(r"[.,](?=\d{3}(?:\D|$))", "", t)  # 10,000 / 10.000 → 10000
        if k:
            try:
                t = str(int(float(t.replace(",", ".")) * 1000))
            except ValueError:
                pass
        out.append(t)
    return sorted(out)


def parity(en: DocInfo, es: DocInfo) -> list[str]:
    """Plain-language differences between an EN master and its ES twin (warnings)."""
    notes = []
    en_p, es_p = en.nonempty(), es.nonempty()
    if len(en_p) != len(es_p):
        notes.append(f"EN has {len(en_p)} paragraphs, ES has {len(es_p)}")
    en_e, es_e = en.entries(), es.entries()
    if len(en_e) != len(es_e):
        notes.append(f"EN has {len(en_e)} entry lines, ES has {len(es_e)} — the pairwise checks below are skipped")
        return notes
    en_groups, es_groups = _bullet_groups(en), _bullet_groups(es)
    for i, (a, b) in enumerate(zip(en_e, es_e), 1):
        ta, tb = normalize(a.text), normalize(b.text)
        if _numbers(ta) != _numbers(tb):
            notes.append(f"entry {i}: numbers differ — EN “{ta}” vs ES “{tb}”")
        ga, gb = en_groups.get(a.index, []), es_groups.get(b.index, [])
        if len(ga) != len(gb):
            notes.append(f"entry {i} “{ta.split(chr(183))[0].strip()}”: {len(ga)} bullets in EN, {len(gb)} in ES")
            continue
        for j, (pa, pb) in enumerate(zip(ga, gb), 1):
            na, nb = _numbers(pa.text), _numbers(pb.text)
            if na != nb:
                notes.append(
                    f"entry {i}, bullet {j}: numbers differ — EN [{', '.join(na) or '-'}] vs ES [{', '.join(nb) or '-'}]"
                )
    return notes


def _bullet_groups(doc: DocInfo) -> dict[int, list[Para]]:
    """Entry paragraph index → the bullets that follow it."""
    groups: dict[int, list[Para]] = {}
    current = None
    for p in doc.paragraphs:
        if p.kind == "entry":
            current = p.index
            groups[current] = []
        elif p.kind == "bullet" and current is not None:
            groups[current].append(p)
        elif p.kind in ("heading", "plain"):
            current = None
    return groups
