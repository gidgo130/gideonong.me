"""A JSON file the editor can rewrite without changing anything but the values.

The transcript inputs (scripts/transcript/*.json) are plain `json.dumps(obj,
indent=2, ensure_ascii=False)` output with LF line endings and no trailing
newline. This class loads a file, detects those settings (BOM, newline style,
indent, trailing newline), and proves on load that re-emitting the parsed
object reproduces the bytes exactly. If it does not, the file is read-only in
the editor and the first differing line is named — a save would otherwise
reformat lines Gideon never touched.
"""

from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path
from typing import Any, Optional

from .jsdata import sha256_bytes
from .review import unified_diff


class JsonFile:
    def __init__(self, repo_root: Path, rel_path: str):
        self.repo_root = Path(repo_root)
        self.rel_path = rel_path
        self.path = self.repo_root / rel_path
        st = os.stat(self.path)
        self.raw = self.path.read_bytes()
        self.mtime_ns = st.st_mtime_ns
        self.size = st.st_size
        self.sha256 = sha256_bytes(self.raw)
        self.bom = self.raw.startswith(b"\xef\xbb\xbf")
        text = self.raw[3:].decode("utf-8") if self.bom else self.raw.decode("utf-8")
        self.newline = "\r\n" if "\r\n" in text else "\n"
        self.trailing_newline = text.endswith(self.newline)
        m = re.search(r"\n( +)\S", text)
        self.indent = len(m.group(1)) if m else 2
        self.obj: Any = json.loads(text)
        self.read_only: Optional[str] = None
        again = self.render(self.obj)
        if again != self.raw:
            self.read_only = self._first_difference(self.raw, again)

    # ------------------------------------------------------------- emit
    def render(self, obj: Any) -> bytes:
        text = json.dumps(obj, indent=self.indent, ensure_ascii=False)
        if self.newline != "\n":
            text = text.replace("\n", self.newline)
        if self.trailing_newline:
            text += self.newline
        data = text.encode("utf-8")
        return (b"\xef\xbb\xbf" + data) if self.bom else data

    def _first_difference(self, a: bytes, b: bytes) -> str:
        al, bl = a.split(b"\n"), b.split(b"\n")
        for i, (x, y) in enumerate(zip(al, bl), 1):
            if x != y:
                return f"{self.rel_path} is not in the editor's JSON layout (line {i} would be rewritten as {y.decode('utf-8', 'replace').strip()!r}); it is read-only here"
        return f"{self.rel_path} is not in the editor's JSON layout (length differs); it is read-only here"

    # ------------------------------------------------------------- queries
    def fresh_copy(self) -> Any:
        return copy.deepcopy(self.obj)

    def disk_changed(self) -> bool:
        try:
            st = os.stat(self.path)
            if st.st_mtime_ns == self.mtime_ns and st.st_size == self.size == len(self.raw):
                return False
            return sha256_bytes(self.path.read_bytes()) != self.sha256
        except OSError:
            return True

    def diff(self, obj: Any) -> str:
        return unified_diff(self.raw, self.render(obj), self.rel_path)


# ----------------------------------------------------------------- paths


def flatten(obj: Any, prefix: tuple = ()) -> dict[tuple, Any]:
    """{path tuple: leaf value} for every scalar and every empty container."""
    out: dict[tuple, Any] = {}
    if isinstance(obj, dict):
        if not obj:
            out[prefix] = {}
        for k, v in obj.items():
            out.update(flatten(v, prefix + (k,)))
    elif isinstance(obj, list):
        if not obj:
            out[prefix] = []
        for i, v in enumerate(obj):
            out.update(flatten(v, prefix + (i,)))
    else:
        out[prefix] = obj
    return out


def changes(base: Any, draft: Any) -> list[dict]:
    """Leaf-level differences between two objects, in draft order."""
    a, b = flatten(base), flatten(draft)
    out = []
    for path, val in b.items():
        if path not in a:
            out.append({"path": list(path), "kind": "added", "old": None, "new": val})
        elif a[path] != val:
            out.append({"path": list(path), "kind": "changed", "old": a[path], "new": val})
    for path, val in a.items():
        if path not in b:
            out.append({"path": list(path), "kind": "removed", "old": val, "new": None})
    return out


def get_path(obj: Any, path: list) -> Any:
    cur = obj
    for p in path:
        cur = cur[p]
    return cur


def set_path(obj: Any, path: list, value: Any) -> None:
    """Set a value at path, creating intermediate dicts; list indexes must exist (or equal len → append)."""
    if not path:
        raise ValueError("empty path")
    cur = obj
    for p in path[:-1]:
        if isinstance(cur, dict):
            if p not in cur:
                cur[p] = {}
            cur = cur[p]
        elif isinstance(cur, list):
            cur = cur[p]
        else:
            raise ValueError(f"cannot descend into {type(cur).__name__} at {p!r}")
    last = path[-1]
    if isinstance(cur, dict):
        cur[last] = value
    elif isinstance(cur, list):
        if last == len(cur):
            cur.append(value)
        else:
            cur[last] = value
    else:
        raise ValueError(f"cannot set {last!r} on {type(cur).__name__}")


def delete_path(obj: Any, path: list) -> None:
    parent = get_path(obj, path[:-1])
    last = path[-1]
    if isinstance(parent, dict):
        parent.pop(last, None)
    elif isinstance(parent, list) and 0 <= last < len(parent):
        del parent[last]
