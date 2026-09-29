"""The six CV masters: the fixed table, where their files and PDFs live, and
whether Word has one open.

Masters live in staging/cv-masters/ (gitignored); exported PDFs go to
staging/cv-out/ (gitignored) under the master's own stem. Only the Professional
CV and the résumé are ever published (plan decision 7); the Full CV stays
private.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

MASTERS_DIR = "staging/cv-masters"
OUT_DIR = "staging/cv-out"
BLOCKLIST_PATH = "staging/editor-private/blocklist.txt"
PDF_DIR = "assets/pdfs"


@dataclass(frozen=True)
class Master:
    id: str
    file: str
    variant: str  # full | professional | resume
    lang: str  # en | es
    publish_type: Optional[str]  # cv | resume | None (never published)
    label: Optional[str]  # the word in the published filename ("CV" | "Resume")

    @property
    def title(self) -> str:
        names = {"full": "Full CV", "professional": "Professional CV", "resume": "Résumé"}
        return f"{names[self.variant]} ({self.lang.upper()})"

    @property
    def pair_id(self) -> str:
        """The id of the other-language master of the same variant."""
        return f"{self.variant}-{'es' if self.lang == 'en' else 'en'}"

    @property
    def one_page(self) -> bool:
        return self.variant == "resume"


MASTERS: list[Master] = [
    Master("full-en", "Gideon Ong CV Full EN.docx", "full", "en", None, None),
    Master("full-es", "Gideon Ong CV Completo ES.docx", "full", "es", None, None),
    Master("professional-en", "Gideon Ong CV Professional EN.docx", "professional", "en", "cv", "CV"),
    Master("professional-es", "Gideon Ong CV Profesional ES.docx", "professional", "es", "cv", "CV"),
    Master("resume-en", "Gideon Ong Resume EN.docx", "resume", "en", "resume", "Resume"),
    Master("resume-es", "Gideon Ong Resume ES.docx", "resume", "es", "resume", "Resume"),
]
BY_ID = {m.id: m for m in MASTERS}


def docx_path(repo_root: Path, m: Master) -> Path:
    return Path(repo_root) / MASTERS_DIR / m.file


def pdf_path(repo_root: Path, m: Master) -> Path:
    return Path(repo_root) / OUT_DIR / (Path(m.file).stem + ".pdf")


def word_lock_file(docx: Path) -> Optional[Path]:
    """Word's owner file for an open document, or None.

    Word writes "~$" + the name with its first two characters dropped (first
    one for short names) next to the document while it is open. Both forms are
    checked; the file is hidden, so this is a plain existence test.
    """
    docx = Path(docx)
    for cut in (2, 1):
        cand = docx.with_name("~$" + docx.name[cut:])
        if cand.exists():
            return cand
    return None


def _stat(p: Path) -> Optional[dict]:
    try:
        st = os.stat(p)
    except OSError:
        return None
    return {"mtime": st.st_mtime, "size": st.st_size}


def info(repo_root: Path, m: Master) -> dict:
    """Everything the page shows about one master before any check runs."""
    dp, pp = docx_path(repo_root, m), pdf_path(repo_root, m)
    ds, ps = _stat(dp), _stat(pp)
    lock = word_lock_file(dp) if ds else None
    return {
        "id": m.id,
        "title": m.title,
        "variant": m.variant,
        "lang": m.lang,
        "file": m.file,
        "path": (Path(MASTERS_DIR) / m.file).as_posix(),
        "exists": ds is not None,
        "mtime": ds["mtime"] if ds else None,
        "size": ds["size"] if ds else None,
        "openInWord": lock is not None,
        "publishType": m.publish_type,
        "onePage": m.one_page,
        "pdf": {
            "path": (Path(OUT_DIR) / pp.name).as_posix(),
            "exists": ps is not None,
            "mtime": ps["mtime"] if ps else None,
            "size": ps["size"] if ps else None,
            # a PDF older than its master was exported before the last Word edit
            "stale": bool(ds and ps and ps["mtime"] < ds["mtime"]),
        },
    }


def all_info(repo_root: Path) -> list[dict]:
    return [info(repo_root, m) for m in MASTERS]
