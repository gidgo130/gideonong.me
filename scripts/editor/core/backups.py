"""Backups, atomic writes and restore (plan §5).

Before any overwrite the original is copied to
    scripts/editor/.local/backups/<YYYYMMDD-HHMMSS>/<same relative path>
with a manifest.json beside it. Sets older than 60 days, or beyond the newest
100, are pruned after each new backup. A restore backs up the current file
first, so a restore is itself undoable.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional

from .jsdata import sha256_bytes

KEEP_DAYS = 60
KEEP_SETS = 100
_SET_ID_RE = re.compile(r"^\d{8}-\d{6}(-\d+)?$")


def atomic_write(path: Path, data: bytes) -> None:
    """Write bytes to `path` via a temp file in the same folder + os.replace."""
    path = Path(path)
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}-{int(time.time() * 1000)}")
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


@dataclass
class BackupSet:
    id: str
    created: str
    reason: str
    files: list[dict]

    def to_json(self) -> dict:
        return {"id": self.id, "created": self.created, "reason": self.reason, "files": self.files}


class Backups:
    def __init__(self, repo_root: Path, backups_dir: Path):
        self.repo_root = Path(repo_root)
        self.dir = Path(backups_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------ create
    def _new_set_dir(self) -> Path:
        base = datetime.now().strftime("%Y%m%d-%H%M%S")
        cand, n = self.dir / base, 2
        while cand.exists():
            cand = self.dir / f"{base}-{n}"
            n += 1
        cand.mkdir(parents=True)
        return cand

    def create(self, rel_paths: Iterable[str], reason: str) -> BackupSet:
        """Copy each existing file (repo-relative posix path) into a new set."""
        set_dir = self._new_set_dir()
        files = []
        for rel in rel_paths:
            src = self.repo_root / rel
            if not src.is_file():
                continue
            dst = set_dir / Path(rel)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            files.append({"path": rel, "sha256": sha256_bytes(src.read_bytes()), "size": src.stat().st_size})
        manifest = {
            "id": set_dir.name,
            "created": datetime.now().isoformat(timespec="seconds"),
            "reason": reason,
            "files": files,
        }
        (set_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        self.prune()
        return BackupSet(manifest["id"], manifest["created"], reason, files)

    # ------------------------------------------------------------ list
    def list(self) -> list[BackupSet]:
        sets = []
        for d in sorted(self.dir.iterdir(), reverse=True):
            if not d.is_dir() or not _SET_ID_RE.match(d.name):
                continue
            m = d / "manifest.json"
            if m.is_file():
                try:
                    j = json.loads(m.read_text(encoding="utf-8"))
                    sets.append(BackupSet(d.name, j.get("created", ""), j.get("reason", ""), j.get("files", [])))
                    continue
                except (OSError, ValueError):
                    pass
            files = [
                {"path": p.relative_to(d).as_posix(), "size": p.stat().st_size}
                for p in d.rglob("*")
                if p.is_file() and p.name != "manifest.json"
            ]
            sets.append(BackupSet(d.name, "", "(no manifest)", files))
        return sets

    def get(self, set_id: str) -> Optional[BackupSet]:
        if not _SET_ID_RE.match(set_id or ""):
            return None
        for s in self.list():
            if s.id == set_id:
                return s
        return None

    def read_file(self, set_id: str, rel: str) -> Optional[bytes]:
        if not _SET_ID_RE.match(set_id or ""):
            return None
        p = (self.dir / set_id / Path(rel)).resolve()
        if not str(p).startswith(str((self.dir / set_id).resolve())) or not p.is_file():
            return None
        return p.read_bytes()

    # ------------------------------------------------------------ restore
    def restore(self, set_id: str, rel_paths: Optional[Iterable[str]] = None) -> dict:
        """Restore files from a set. Returns {restored: [...], backup: <new set id>}."""
        s = self.get(set_id)
        if s is None:
            raise FileNotFoundError(f"no backup set {set_id!r}")
        wanted = set(rel_paths) if rel_paths is not None else {f["path"] for f in s.files}
        targets = [f["path"] for f in s.files if f["path"] in wanted]
        if not targets:
            raise FileNotFoundError("nothing to restore")
        pre = self.create(targets, f"before restoring {set_id}")
        restored = []
        for rel in targets:
            data = self.read_file(set_id, rel)
            if data is None:
                continue
            atomic_write(self.repo_root / rel, data)
            restored.append(rel)
        return {"restored": restored, "backup": pre.id}

    # ------------------------------------------------------------ prune
    def prune(self) -> list[str]:
        removed = []
        sets = [d for d in sorted(self.dir.iterdir(), reverse=True) if d.is_dir() and _SET_ID_RE.match(d.name)]
        cutoff = datetime.now() - timedelta(days=KEEP_DAYS)
        for i, d in enumerate(sets):
            try:
                created = datetime.strptime(d.name[:15], "%Y%m%d-%H%M%S")
            except ValueError:
                continue
            if i >= KEEP_SETS or created < cutoff:
                shutil.rmtree(d, ignore_errors=True)
                removed.append(d.name)
        return removed
