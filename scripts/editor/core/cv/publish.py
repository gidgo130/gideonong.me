"""Publish dated PDFs into assets/pdfs/<type>/ (plan §3), shared by the CV tab
and the transcript tab.

plan_docs():  what a publish would do — per document the target path, whether
              it is an add or an overwrite, and the older dated files of the same
              type + language that move to the backup set — plus the gate
              (errors block, warnings do not).
apply_docs(): backup every file that will be overwritten or moved, delete the
              moved ones, copy the new PDFs (temp + replace), then regenerate
              js/docs-data.js with node scripts/build-docs-manifest.js exactly
              as the pre-commit hook would (backed up first; a missing node is a
              warning). Never runs git.

plan() / apply() are the CV-specific wrappers (the six masters table).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from datetime import date
from pathlib import Path
from typing import Optional

from ..backups import Backups
from .masters import MASTERS, PDF_DIR, Master, pdf_path

MANIFEST_SCRIPT = "scripts/build-docs-manifest.js"
MANIFEST_OUT = "js/docs-data.js"
_DATE_RE = re.compile(r"^\d{8}$")


def valid_date(s: str) -> bool:
    if not _DATE_RE.match(s or ""):
        return False
    try:
        date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        return True
    except ValueError:
        return False


def today() -> str:
    return date.today().strftime("%Y%m%d")


# ------------------------------------------------------------- generic


def target_for(pub_type: str, lang: str, label: str, stamp: str) -> str:
    return f"{PDF_DIR}/{pub_type}/{lang} Gideon Ong {label} {stamp}.pdf"


def pattern_for(lang: str, label: str) -> re.Pattern:
    """The manifest generator's own filename rule for this type + language."""
    return re.compile(rf"^{lang} Gideon Ong {re.escape(label)} (\d{{8}})\.pdf$")


def existing_for(repo_root: Path, pub_type: str, lang: str, label: str) -> list[str]:
    d = Path(repo_root) / PDF_DIR / pub_type
    if not d.is_dir():
        return []
    pat = pattern_for(lang, label)
    return sorted(f"{PDF_DIR}/{pub_type}/{p.name}" for p in d.iterdir() if p.is_file() and pat.match(p.name))


def plan_docs(repo_root: Path, docs: list[dict], stamp: Optional[str] = None) -> dict:
    """docs: [{id, title, source (Path or None), type, lang, label, stamp?, errors, warnings}]."""
    stamp = stamp or today()
    errors, warnings, items = [], [], []
    if not valid_date(stamp):
        errors.append({"code": "date", "message": f"“{stamp}” is not a date (YYYYMMDD)"})
    for d in docs:
        own_stamp = d.get("stamp") or stamp
        target = target_for(d["type"], d["lang"], d["label"], own_stamp)
        src = Path(d["source"]) if d.get("source") else None
        items.append(
            {
                "id": d["id"],
                "title": d["title"],
                "source": src.name if src else None,
                "target": target,
                "action": "overwrite" if (Path(repo_root) / target).is_file() else "add",
                "moves": [p for p in existing_for(repo_root, d["type"], d["lang"], d["label"]) if p != target],
            }
        )
        if src is None or not src.is_file():
            errors.append({"code": "no-pdf", "id": d["id"], "message": f"{d['title']}: no PDF to publish yet"})
            continue
        for e in d.get("errors", []):
            errors.append(dict(e, id=d["id"], message=f"{d['title']}: {e['message']}"))
        for w in d.get("warnings", []):
            warnings.append(dict(w, id=d["id"], message=f"{d['title']}: {w['message']}"))
    return {"date": stamp, "items": items, "errors": errors, "warnings": warnings, "ok": not errors}


def apply_docs(repo_root: Path, backups: Backups, p: dict, sources: dict[str, Path], reason: str) -> dict:
    """Carry out a plan (which must be ok). `sources`: item id → the PDF to copy."""
    if not p.get("ok"):
        raise ValueError("plan has blocking errors")
    repo_root = Path(repo_root)
    to_backup: list[str] = []
    for item in p["items"]:
        to_backup += item["moves"]
        if item["action"] == "overwrite":
            to_backup.append(item["target"])
    if (repo_root / MANIFEST_OUT).is_file():
        to_backup.append(MANIFEST_OUT)
    bset = backups.create(sorted(set(to_backup)), reason)
    moved, added, overwritten = [], [], []
    for item in p["items"]:
        for rel in item["moves"]:
            try:
                (repo_root / rel).unlink()
                moved.append(rel)
            except OSError as e:
                raise OSError(f"could not move {rel} to the backup: {e}") from e
    for item in p["items"]:
        src = Path(sources[item["id"]])
        dst = repo_root / item["target"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_name(f"{dst.name}.tmp-{os.getpid()}-{int(time.time() * 1000)}")
        try:
            shutil.copyfile(src, tmp)
            os.replace(tmp, dst)
        finally:
            if tmp.exists():
                tmp.unlink()
        (overwritten if item["action"] == "overwrite" else added).append(item["target"])
    manifest = run_manifest(repo_root)
    return {"backup": bset.id, "added": added, "overwritten": overwritten, "moved": moved, "manifest": manifest}


def run_manifest(repo_root: Path) -> dict:
    """node scripts/build-docs-manifest.js — the same command the pre-commit hook runs."""
    script = Path(repo_root) / MANIFEST_SCRIPT
    if not script.is_file():
        return {"ran": False, "ok": False, "output": f"{MANIFEST_SCRIPT} not found"}
    node = shutil.which("node")
    if not node:
        return {"ran": False, "ok": False, "output": "node is not on PATH — js/docs-data.js was not regenerated; the pre-commit hook will do it, or run the script by hand"}
    try:
        r = subprocess.run(
            [node, str(script)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError) as e:
        return {"ran": True, "ok": False, "output": f"could not run node: {e}"}
    out = (r.stdout + ("\n" + r.stderr if r.stderr else "")).strip()
    return {"ran": True, "ok": r.returncode == 0, "output": out}


# ------------------------------------------------------------- CV wrappers


def target_rel(m: Master, stamp: str) -> str:
    return target_for(m.publish_type, m.lang, m.label, stamp)


def published_pattern(m: Master) -> re.Pattern:
    return pattern_for(m.lang, m.label)


def existing_published(repo_root: Path, m: Master) -> list[str]:
    return existing_for(repo_root, m.publish_type, m.lang, m.label)


def plan(repo_root: Path, checks: dict, stamp: Optional[str] = None) -> dict:
    """`checks`: master id → {"errors": [...], "warnings": [...]}."""
    docs = []
    for m in MASTERS:
        if not m.publish_type:
            continue
        c = checks.get(m.id) or {}
        src = pdf_path(repo_root, m)
        docs.append(
            {
                "id": m.id,
                "title": m.title,
                "source": src,
                "type": m.publish_type,
                "lang": m.lang,
                "label": m.label,
                "errors": c.get("errors", []),
                "warnings": c.get("warnings", []),
            }
        )
    p = plan_docs(repo_root, docs, stamp)
    for e in p["errors"]:
        if e.get("code") == "no-pdf":
            e["message"] = e["message"].replace("no PDF to publish yet", "no exported PDF yet — export first")
    return p


def apply(repo_root: Path, backups: Backups, p: dict) -> dict:
    sources = {m.id: pdf_path(repo_root, m) for m in MASTERS if m.publish_type}
    return apply_docs(repo_root, backups, p, sources, f"before publishing CV/résumé PDFs ({p['date']})")
