"""CV text (Phase 4). 4a: import the six masters into staging/cv-content/ once the
losslessness proof passes on every one of them. Owned by app.EditorState as `cvtext`.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..backups import Backups, atomic_write
from . import importer, masters, renderer

log = logging.getLogger("editor.cvtext")

CONTENT_DIR = "staging/cv-content"
CONTENT_FILE = f"{CONTENT_DIR}/content.json"
SLOTS_DIR = f"{CONTENT_DIR}/slots"
REPORT_FILE = f"{CONTENT_DIR}/import-report.json"


def _dump(obj) -> bytes:
    return json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")


class CvTextService:
    def __init__(self, repo_root: Path, backups: Backups):
        self.repo_root = Path(repo_root)
        self.backups = backups

    # ------------------------------------------------------------- state
    def content_path(self) -> Path:
        return self.repo_root / CONTENT_FILE

    def load_content(self) -> Optional[dict]:
        p = self.content_path()
        if not p.is_file():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError as e:
            log.error("content.json unreadable: %s", e)
            return None

    def load_report(self) -> Optional[dict]:
        p = self.repo_root / REPORT_FILE
        if not p.is_file():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return None

    def state(self) -> dict:
        content = self.load_content()
        p = self.content_path()
        summary = None
        if content:
            items = content.get("items", {})
            summary = {
                "items": len(items),
                "entries": sum(1 for i in items.values() if i.get("kind") == "entry"),
                "children": sum(len(i.get("children", {})) for i in items.values()),
                "sections": len(content.get("sections", [])),
                "shared": sum(1 for i in items.values() if sum(i.get("include", {}).values()) > 1),
                "modified": os.stat(p).st_mtime,
            }
        return {
            "contentPath": CONTENT_FILE,
            "content": summary,
            "masters": masters.all_info(self.repo_root),
            "lastImport": self.load_report(),
        }

    # ------------------------------------------------------------- import
    def run_import(self) -> dict:
        """Read the six masters, merge, prove every one re-renders losslessly, then write the content set."""
        missing = [m.file for m in masters.MASTERS if not masters.docx_path(self.repo_root, m).is_file()]
        if missing:
            return {"ok": False, "error": "missing-masters", "message": "missing masters: " + ", ".join(missing)}
        started = time.time()
        docs: dict[str, dict] = {}
        try:
            for v in importer.VARIANTS:
                docs[v] = {}
                for lang in ("en", "es"):
                    m = masters.BY_ID[f"{v}-{lang}"]
                    docs[v][lang] = importer.read_master(masters.docx_path(self.repo_root, m))
        except importer.ImportError_ as e:
            return {"ok": False, "error": "unsupported", "message": str(e)}
        content, slots, report = importer.merge(docs)
        proof = {}
        tmp = Path(tempfile.mkdtemp(prefix="cv-proof-"))
        try:
            for v, langs in docs.items():
                for lang, doc in langs.items():
                    out = renderer.force_render(doc, slots[doc.path.name], content, tmp / doc.path.name)
                    proof[doc.path.name] = importer.compare(doc.path, out)
        except Exception as e:  # a render crash is a failed proof, not a server error
            log.exception("proof render failed")
            proof["(render)"] = [f"render failed: {e}"]
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        ok = all(not v for v in proof.values())
        result = {
            "ok": ok,
            "ran": datetime.now().isoformat(timespec="seconds"),
            "seconds": round(time.time() - started, 1),
            "proof": proof,
            "report": report,
            "written": False,
        }
        if not ok:
            result["error"] = "not-lossless"
            result["message"] = "The round trip is not lossless for every master; nothing was written."
            return result
        existing = [CONTENT_FILE] + [f"{SLOTS_DIR}/{p.name}" for p in (self.repo_root / SLOTS_DIR).glob("*.json")] if self.content_path().is_file() else []
        if existing:
            result["backup"] = self.backups.create(existing, "before re-importing the CV masters").id
        (self.repo_root / SLOTS_DIR).mkdir(parents=True, exist_ok=True)
        atomic_write(self.content_path(), _dump(content))
        for name, sl in slots.items():
            atomic_write(self.repo_root / SLOTS_DIR / (name + ".json"), _dump(sl))
        atomic_write(self.repo_root / REPORT_FILE, _dump({k: v for k, v in result.items() if k != "written"}))
        result["written"] = True
        log.info("imported CV masters: %d items, proof lossless", len(content["items"]))
        return result
