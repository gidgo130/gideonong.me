"""Backups, atomic writes and restore (plan §5).

Before any overwrite the original is copied to
    scripts/editor/.local/backups/<YYYYMMDD-HHMMSS>/<same relative path>
with a manifest.json beside it. Sets older than 60 days, or beyond the newest
100, are pruned after each new backup — except sets marked KEEP (manifest
"keep": true), which stay for good and do not count toward the 100. A restore
backs up the current file first, so a restore is itself undoable.

copy_staging() copies the private staging/ folder (masters, content set, slot
maps, exports, blocklist) and every kept set into a timestamped folder under a
destination OUTSIDE the repo (OneDrive, an external drive): the one copy that
survives a lost disk or a re-clone.
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
    keep: bool = False

    def to_json(self) -> dict:
        return {"id": self.id, "created": self.created, "reason": self.reason, "files": self.files, "keep": self.keep}


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

    def move_away(self, rel_paths: Iterable[str], reason: str) -> BackupSet:
        """Back up the files, then delete the originals (a move into the set).

        Used by publish for the older dated PDFs. Restoring the set writes them
        back; files added after the backup are not removed by a restore.
        """
        rels = [r for r in rel_paths if (self.repo_root / r).is_file()]
        bset = self.create(rels, reason)
        for rel in rels:
            (self.repo_root / rel).unlink()
        return bset

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
                    sets.append(BackupSet(d.name, j.get("created", ""), j.get("reason", ""), j.get("files", []), bool(j.get("keep"))))
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

    def set_keep(self, set_id: str, keep: bool) -> BackupSet:
        """Mark a set as kept (never pruned) or let it expire again."""
        s = self.get(set_id)
        if s is None:
            raise FileNotFoundError(f"no backup set {set_id!r}")
        m = self.dir / set_id / "manifest.json"
        try:
            j = json.loads(m.read_text(encoding="utf-8")) if m.is_file() else {}
        except (OSError, ValueError):
            j = {}
        j.setdefault("id", s.id)
        j.setdefault("created", s.created)
        j.setdefault("reason", s.reason)
        j.setdefault("files", s.files)
        j["keep"] = bool(keep)
        atomic_write(m, json.dumps(j, indent=2, ensure_ascii=False).encode("utf-8"))
        s.keep = bool(keep)
        return s

    def read_file(self, set_id: str, rel: str) -> Optional[bytes]:
        if not _SET_ID_RE.match(set_id or ""):
            return None
        base = (self.dir / set_id).resolve()
        p = (base / Path(rel)).resolve()
        # is_relative_to, not a string prefix: "<set>-2/…" must not pass as "<set>".
        if not p.is_relative_to(base) or not p.is_file():
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
        """Drop expiring sets: older than KEEP_DAYS or beyond the newest KEEP_SETS. Kept sets
        (manifest "keep": true) are never dropped and are not counted."""
        removed = []
        sets = [d for d in sorted(self.dir.iterdir(), reverse=True) if d.is_dir() and _SET_ID_RE.match(d.name)]
        cutoff = datetime.now() - timedelta(days=KEEP_DAYS)
        rank = 0
        for d in sets:
            if self._is_kept(d):
                continue
            try:
                created = datetime.strptime(d.name[:15], "%Y%m%d-%H%M%S")
            except ValueError:
                continue
            if rank >= KEEP_SETS or created < cutoff:
                shutil.rmtree(d, ignore_errors=True)
                removed.append(d.name)
            rank += 1
        return removed

    @staticmethod
    def _is_kept(set_dir: Path) -> bool:
        m = set_dir / "manifest.json"
        try:
            return bool(json.loads(m.read_text(encoding="utf-8")).get("keep")) if m.is_file() else False
        except (OSError, ValueError):
            return False

    # ------------------------------------------------------------ the copy outside the repo
    STAGING = "staging"
    COPY_IGNORE = staticmethod(shutil.ignore_patterns("__pycache__", "*.tmp-*", "~$*"))

    def copy_staging(self, dest: Path, include_kept: bool = True) -> dict:
        """Copy <repo>/staging/ and every kept set into <dest>/gideonong-staging-<timestamp>/.

        `dest` must exist, be a folder, and lie outside the repo. Returns the folder written,
        the file count and the bytes copied."""
        dest = Path(dest)
        if not dest.is_dir():
            raise FileNotFoundError(f"{dest} is not a folder that exists")
        repo = self.repo_root.resolve()
        if dest.resolve() == repo or dest.resolve().is_relative_to(repo):
            raise ValueError("choose a folder outside the repo — a copy inside it would be lost with it")
        src = self.repo_root / self.STAGING
        if not src.is_dir():
            raise FileNotFoundError(f"{self.STAGING}/ does not exist in the repo")
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = dest / f"gideonong-staging-{stamp}"
        n = 2
        while target.exists():
            target = dest / f"gideonong-staging-{stamp}-{n}"
            n += 1
        shutil.copytree(src, target / self.STAGING, ignore=self.COPY_IGNORE)
        kept = []
        if include_kept:
            for s in self.list():
                if s.keep:
                    shutil.copytree(self.dir / s.id, target / "backups" / s.id, ignore=self.COPY_IGNORE)
                    kept.append(s.id)
        files = [p for p in target.rglob("*") if p.is_file()]
        return {"folder": str(target), "files": len(files), "bytes": sum(p.stat().st_size for p in files), "kept": kept, "when": datetime.now().isoformat(timespec="seconds")}
