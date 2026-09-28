"""Review = dry run: plain-language change list + the exact unified diff."""

from __future__ import annotations

import difflib
from typing import Optional


def unified_diff(old: bytes, new: bytes, rel_path: str) -> str:
    """Unified diff of two UTF-8 files, line endings shown as-is (CR stripped for display)."""
    a = old.decode("utf-8", "replace").splitlines(keepends=True)
    b = new.decode("utf-8", "replace").splitlines(keepends=True)
    lines = difflib.unified_diff(a, b, fromfile=f"a/{rel_path}", tofile=f"b/{rel_path}", n=3)
    return "".join(line.replace("\r\n", "\n") if line.endswith("\r\n") else line for line in lines)


def count_changed_lines(diff_text: str) -> dict:
    added = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))
    return {"added": added, "removed": removed}


def change_list(edits: dict[str, str], entries: dict, sections: list[dict]) -> list[dict]:
    """One human-readable line per edit: Site text › <Section> › <key> (ES): old → new."""
    titles = {s["id"]: s["title"] for s in sections}
    out = []
    for k in sorted(edits, key=lambda k: (_order(entries, k), k)):
        lang, _, key = k.partition(".")
        e = entries.get(key) or {}
        old: Optional[str] = e.get(lang)
        out.append(
            {
                "id": k,
                "key": key,
                "lang": lang,
                "section": titles.get(e.get("section", ""), ""),
                "old": old,
                "new": edits[k],
                "text": f"Site text › {titles.get(e.get('section', ''), '?')} › {key} ({lang.upper()}): "
                f"{_q(old)} → {_q(edits[k])}",
            }
        )
    return out


def _order(entries: dict, k: str) -> int:
    key = k.partition(".")[2]
    e = entries.get(key)
    return (e.get("enLine") or e.get("esLine") or 0) if e else 0


def _q(s: Optional[str]) -> str:
    if s is None:
        return "(missing)"
    s = s.replace("\n", "⏎")
    return "“" + (s if len(s) <= 120 else s[:117] + "…") + "”"
