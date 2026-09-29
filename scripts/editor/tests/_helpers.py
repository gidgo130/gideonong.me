"""Shared fixtures: a temp copy of the real repo files the editor touches."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import logging

logging.getLogger("editor").setLevel(logging.CRITICAL)  # expected rejections would otherwise spam the run

EDITOR_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = EDITOR_DIR.parent.parent
if str(EDITOR_DIR) not in sys.path:
    sys.path.insert(0, str(EDITOR_DIR))

REAL_FILES = [
    "js/translations.js",
    "js/projects-data.js",
    "js/experience-data.js",
    "js/tags-data.js",
    ".vercelignore",
]


class TempRepo:
    """A temp folder holding copies of the real data files + a .local dir."""

    def __enter__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="editor-test-"))
        self.root = self.dir / "repo"
        self.local = self.dir / "local"
        for rel in REAL_FILES:
            src = REPO_ROOT / rel
            if src.is_file():
                dst = self.root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        (self.root / "index.html").write_text("<!doctype html><title>t</title>", encoding="utf-8")
        (self.root / "staging").mkdir()
        (self.root / "staging" / "secret.txt").write_text("private", encoding="utf-8")
        (self.root / "README.md").write_text("# dev only", encoding="utf-8")
        (self.root / "notes.md").write_text("# dev only", encoding="utf-8")
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "x.js").write_text("// dev", encoding="utf-8")
        # the two files that matter most if the preview ever leaked: the editor's
        # own lock (holds the tokenized URL) and Vercel's pulled env file
        (self.root / "scripts" / "editor" / ".local").mkdir(parents=True)
        (self.root / "scripts" / "editor" / ".local" / "editor.lock").write_text('{"url": "TOKEN"}', encoding="utf-8")
        (self.root / ".env.local").write_text("VERCEL_OIDC_TOKEN=secret", encoding="utf-8")
        # Phase 2: the sub-page shells and empty stand-ins for every asset the data
        # files reference, so the dev-check port sees the files it looks for.
        import re

        (self.root / "projects").mkdir(exist_ok=True)
        for p in (REPO_ROOT / "projects").glob("*.html"):
            shutil.copy2(p, self.root / "projects" / p.name)
        for rel in ("js/projects-data.js", "js/experience-data.js"):
            src = self.root / rel
            if src.is_file():
                for m in re.findall(r'"(assets/[\w./-]+\.(?:jpg|jpeg|png|webp|pdf))"', src.read_text(encoding="utf-8")):
                    f = self.root / m
                    f.parent.mkdir(parents=True, exist_ok=True)
                    if not f.exists():
                        f.write_bytes(b"")
        # Phase 1b: the manifest generator (publish runs it) and the PDF folders
        gen = REPO_ROOT / "scripts" / "build-docs-manifest.js"
        if gen.is_file():
            shutil.copy2(gen, self.root / "scripts" / "build-docs-manifest.js")
        for sub in ("resume", "cv", "transcript"):
            (self.root / "assets" / "pdfs" / sub).mkdir(parents=True, exist_ok=True)
        self.local.mkdir()
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)

    @property
    def translations(self) -> Path:
        return self.root / "js" / "translations.js"
