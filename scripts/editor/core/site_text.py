"""js/translations.js as an editable set of EN/ES keys.

Builds, from a jsdata.Document:
  * the ordered list of keys (EN order, then ES-only keys),
  * the sections the file's own `//` comment blocks define inside the `en`
    object (a key belongs to the section opened by the comment block right
    above it; ES-only keys get their own section from the ES comment),
  * per-key trailing notes (a `//` comment on the same line as the value),
  * parity status per key.

Everything here is read-side. Edits are a dict {"en.key" | "es.key": value}
that `render()` turns back into file bytes via the Document.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import validate
from .jsdata import Document, JsDataError, ObjectNode, StringNode, Property, comment_text, sha256_bytes

LANGS = ("en", "es")
STATUSES = ("both", "en-only", "es-only", "same", "todo")


@dataclass
class Section:
    id: str
    title: str
    note: str
    keys: list[str] = field(default_factory=list)
    es_only: bool = False


@dataclass
class Entry:
    key: str
    en: Optional[str]
    es: Optional[str]
    en_line: Optional[int]
    es_line: Optional[int]
    en_note: str
    es_note: str
    section: str


def parity_status(key: str, en: Optional[str], es: Optional[str]) -> str:
    if en is None:
        return "es-only"
    if es is None:
        return "en-only"
    if validate.is_todo(en) or validate.is_todo(es):
        return "todo"
    if en == es and not validate.identical_allowed(key, en):
        return "same"
    return "both"


def clean_title(text: str) -> str:
    """Strip decorative dashes/rules from a comment line ("---- Projects: index ----")."""
    t = re.sub(r"^[\s\-=_*#]+|[\s\-=_*#]+$", "", text)
    return t or text.strip()


def _section_id(title: str, used: set) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or "section"
    sid, n = base, 2
    while sid in used:
        sid = f"{base}-{n}"
        n += 1
    used.add(sid)
    return sid


class SiteText:
    """The translations file loaded from disk (bytes, hash, parsed tree)."""

    REL_PATH = "js/translations.js"

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.path = self.repo_root / self.REL_PATH
        self.raw = self.path.read_bytes()
        self.sha256 = sha256_bytes(self.raw)
        self.mtime = os.stat(self.path).st_mtime
        self.doc = Document.from_bytes(self.raw, source=str(self.path))
        root = self.doc.const("translations")
        if not isinstance(root, ObjectNode):
            raise JsDataError("`translations` is not an object literal", root.line)
        self.root = root
        self.objs: dict[str, ObjectNode] = {}
        for lang in LANGS:
            node = root.value(lang)
            if not isinstance(node, ObjectNode):
                raise JsDataError(f"translations.{lang} is missing or not an object literal", root.line)
            self.objs[lang] = node
        self._check_strings()
        self.sections: list[Section] = []
        self.entries: dict[str, Entry] = {}
        self.keys: list[str] = []
        self._build()

    # ------------------------------------------------------------ loading
    def _check_strings(self):
        for lang, obj in self.objs.items():
            for p in obj.props:
                if not isinstance(p.value, StringNode):
                    raise JsDataError(f"translations.{lang}.{p.key} is not a string", p.line)

    def _header_comments(self, obj: ObjectNode, i: int) -> list[str]:
        """Comment lines that open the block above property i (not trailing notes)."""
        p = obj.props[i]
        after = obj.props[i - 1].last if i > 0 else obj.first
        prev_line = self.doc.tokens[after].line
        lines = []
        for t in self.doc.comments_between(after, p.key_tok):
            if t.line == prev_line and i > 0:
                continue  # a trailing note on the previous value
            lines.append(comment_text(t))
        return lines

    def _note(self, p: Property) -> str:
        t = self.doc.trailing_comment(p.last)
        return comment_text(t) if t else ""

    def _build(self):
        used: set = set()
        en, es = self.objs["en"], self.objs["es"]
        current: Optional[Section] = None
        for i, p in enumerate(en.props):
            header = self._header_comments(en, i)
            if header or current is None:
                title = clean_title(header[0]) if header else "General"
                current = Section(_section_id(title, used), title, "\n".join(header[1:]))
                self.sections.append(current)
            esp = es.get(p.key)
            self.entries[p.key] = Entry(
                key=p.key,
                en=p.value.value,
                es=esp.value.value if esp else None,
                en_line=p.line,
                es_line=esp.line if esp else None,
                en_note=self._note(p),
                es_note=self._note(esp) if esp else "",
                section=current.id,
            )
            current.keys.append(p.key)
            self.keys.append(p.key)
        # ES-only keys keep their own comment sections
        current = None
        for i, p in enumerate(es.props):
            if p.key in self.entries:
                current = None
                continue
            header = self._header_comments(es, i)
            if header or current is None:
                title = clean_title(header[0]) if header else "General (ES only)"
                current = Section(_section_id(title, used), title, "\n".join(header[1:]), es_only=True)
                self.sections.append(current)
            self.entries[p.key] = Entry(p.key, None, p.value.value, None, p.line, "", self._note(p), current.id)
            current.keys.append(p.key)
            self.keys.append(p.key)

    # ------------------------------------------------------------ queries
    def value(self, lang: str, key: str) -> Optional[str]:
        e = self.entries.get(key)
        return None if e is None else getattr(e, lang)

    def as_dicts(self) -> tuple[dict, dict]:
        en = {k: e.en for k, e in self.entries.items() if e.en is not None}
        es = {k: e.es for k, e in self.entries.items() if e.es is not None}
        return en, es

    def disk_changed(self) -> bool:
        try:
            return sha256_bytes(self.path.read_bytes()) != self.sha256
        except OSError:
            return True

    # ------------------------------------------------------------ editing
    def apply(self, edits: dict[str, str]) -> tuple[dict, dict]:
        """EN/ES dicts with edits ("en.key" → value) applied. Unknown keys are ignored."""
        en, es = self.as_dicts()
        for k, v in edits.items():
            lang, _, key = k.partition(".")
            d = en if lang == "en" else es
            if key in d:
                d[key] = v
        return en, es

    def normalize_edits(self, edits: dict[str, str]) -> dict[str, str]:
        """Drop edits that target unknown keys or equal the value on disk."""
        out = {}
        for k, v in edits.items():
            lang, _, key = k.partition(".")
            if lang not in LANGS:
                continue
            cur = self.value(lang, key)
            if cur is None or cur == v:
                continue
            out[k] = v
        return out

    def render(self, edits: dict[str, str]) -> bytes:
        """The file bytes with the given edits applied and nothing else changed."""
        tok_edits: dict[int, str] = {}
        for k, v in self.normalize_edits(edits).items():
            lang, _, key = k.partition(".")
            p = self.objs[lang].get(key)
            assert p is not None and isinstance(p.value, StringNode)
            tok_edits[p.value.tok] = v
        return self.doc.to_bytes(tok_edits)

    def to_json(self) -> dict:
        entries = {}
        for k, e in self.entries.items():
            entries[k] = {
                "key": k,
                "en": e.en,
                "es": e.es,
                "enLine": e.en_line,
                "esLine": e.es_line,
                "enNote": e.en_note,
                "esNote": e.es_note,
                "section": e.section,
                "status": parity_status(k, e.en, e.es),
            }
        return {
            "path": self.REL_PATH,
            "sha256": self.sha256,
            "lines": self.doc.text.count("\n") + 1,
            "sections": [
                {"id": s.id, "title": s.title, "note": s.note, "keys": s.keys, "esOnly": s.es_only}
                for s in self.sections
            ],
            "keys": self.keys,
            "entries": entries,
        }


# ------------------------------------------------------------- hidden keys


def slug_camel(slug: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[-_\s]+", slug) if part)


def hidden_key_prefixes(repo_root: Path) -> list[str]:
    """Key prefixes of entries the site never renders (hidden roles / hidden projects).

    Read from js/experience-data.js (visible: false) and js/projects-data.js
    (listing: "hidden") with the same tokenizer. A parse problem in either file
    just means no prefixes from it — this is only used to soften TODO warnings.
    """
    prefixes = []
    root = Path(repo_root)
    specs = [
        ("js/experience-data.js", "experienceData", "exp", lambda o: _bool(o, "visible") is False),
        ("js/projects-data.js", "projectsData", "proj", lambda o: _str(o, "listing") == "hidden"),
    ]
    for rel, const, prefix, is_hidden in specs:
        try:
            doc = Document.load(root / rel)
            arr = doc.const(const)
        except (OSError, JsDataError):
            continue
        for item in getattr(arr, "items", []):
            if isinstance(item, ObjectNode) and is_hidden(item):
                slug = _str(item, "slug")
                if slug:
                    prefixes.append(prefix + slug_camel(slug))
    return prefixes


def _str(obj: ObjectNode, key: str) -> Optional[str]:
    v = obj.value(key)
    return v.value if isinstance(v, StringNode) else None


def _bool(obj: ObjectNode, key: str):
    v = obj.value(key)
    return getattr(v, "value", None) if v is not None and v.__class__.__name__ == "BoolNode" else None
