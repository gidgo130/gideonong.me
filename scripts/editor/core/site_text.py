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
from typing import Iterable, Optional

from . import validate
from .jsdata import Document, JsDataError, ObjectNode, StringNode, Property, comment_text, sha256_bytes

_IDENT = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")

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
        # stat BEFORE the read: a write that lands between the two then shows up
        # as a changed mtime on the next disk_changed() and forces the hash path.
        st = os.stat(self.path)
        self.raw = self.path.read_bytes()
        self.sha256 = sha256_bytes(self.raw)
        self.mtime_ns = st.st_mtime_ns
        self.size = st.st_size
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
        """True if the file on disk no longer matches what was loaded.

        Cheap path first (the heartbeat calls this every few seconds): an
        unchanged mtime and size means unchanged. Otherwise compare hashes, so a
        same-size rewrite or a touched-but-identical file are both answered
        correctly.
        """
        try:
            st = os.stat(self.path)
            if st.st_mtime_ns == self.mtime_ns and st.st_size == self.size == len(self.raw):
                return False
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

    def render(self, edits: dict[str, str], adds: Optional[dict] = None, removes: Optional[Iterable[str]] = None, renames: Optional[dict] = None) -> bytes:
        """The file bytes with the given edits applied and nothing else changed.

        `adds`: {key: {"en": str, "es": str}} — new keys, inserted in both language
        objects after the last key of the same entry (same proj<SlugCamel> / exp<SlugCamel>
        prefix) or, for a new entry, after the last key of the same family (proj / exp /
        tag) with a blank line before it. `removes`: keys deleted from both objects.
        `renames`: {old key: new key} — the key token is replaced in place in both objects
        (the value and its position stay; `edits` still address the old name).
        """
        if not adds and not removes and not renames:
            tok_edits: dict[int, str] = {}
            for k, v in self.normalize_edits(edits).items():
                lang, _, key = k.partition(".")
                p = self.objs[lang].get(key)
                assert p is not None and isinstance(p.value, StringNode)
                tok_edits[p.value.tok] = v
            return self.doc.to_bytes(tok_edits)
        from . import spans
        from .emit import scalar

        removes = set(removes or ())
        span_edits: list[spans.Edit] = []
        for k, v in self.normalize_edits(edits).items():
            lang, _, key = k.partition(".")
            if key in removes:
                continue
            p = self.objs[lang].get(key)
            assert p is not None and isinstance(p.value, StringNode)
            span_edits.append(spans.replace_string(self.doc, p.value, v))
        for lang, obj in self.objs.items():
            for old, new in (renames or {}).items():
                p = obj.get(old)
                if p is not None and old not in removes:
                    tok = self.doc.tokens[p.key_tok]
                    span_edits.append((tok.start, tok.end, new if _IDENT.match(new) else scalar(new)))
            for key in removes:
                if obj.get(key) is not None:
                    span_edits.append(spans.delete_prop(self.doc, obj, key))
            # new keys: group per anchor so several keys for one entry chain in order
            planned: dict[Optional[str], list[tuple[str, str, bool]]] = {}
            existing = [p.key for p in obj.props if p.key not in removes]
            for key, vals in (adds or {}).items():
                if obj.get(key) is not None:
                    continue  # already there: treat as an edit of that key instead
                after, blank = self._anchor(existing, key)
                planned.setdefault(after, []).append((key, scalar(vals.get(lang, "")), blank))
            for after, items in planned.items():
                # insert in reverse so the first planned key ends up right after the anchor
                text = "".join(_line(key, val, i == 0 and blank) for i, (key, val, blank) in enumerate(items))
                span_edits.append(self._insert_block(obj, after, text))
        new_doc = spans.apply(self.doc, span_edits)
        return new_doc.to_bytes({})

    def _anchor(self, existing: list[str], key: str) -> tuple[Optional[str], bool]:
        """(key to insert after, blank line before?) for a new key."""
        prefix = entry_prefix(key)
        same_entry = [k for k in existing if prefix and k.startswith(prefix) and (len(k) == len(prefix) or k[len(prefix)].isupper() or k[len(prefix)].isdigit())]
        if same_entry:
            return same_entry[-1], False
        fam = family(key)
        same_family = [k for k in existing if family(k) == fam] if fam else []
        if same_family:
            return same_family[-1], True
        return existing[-1] if existing else None, True

    def _insert_block(self, obj: ObjectNode, after: Optional[str], text: str):
        """Insert already-formatted lines (each starting with a newline) after `after`."""
        from . import spans

        if after is None:
            pos = self.doc.tokens[obj.first].end
            return (pos, pos, text + ("," if obj.props else ""))
        prop = obj.get(after)
        comma = spans._comma_after(self.doc, prop.last)
        if comma is not None:
            pos = spans._end_with_trailing(self.doc, prop.last)
            return (pos, pos, text.rstrip(",") + ",")
        pos = self.doc.tokens[prop.last].end
        return (pos, pos, "," + text.rstrip(","))


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


# ------------------------------------------------------------- key families (Phase 2)


def _line(key: str, value_text: str, blank_before: bool) -> str:
    return ("\n\n" if blank_before else "\n") + "    " + key + ": " + value_text + ","


_FAMILY_RE = re.compile(r"^(proj|exp|tag)(?=[A-Z0-9])")
_ENTRY_RE = re.compile(r"^((?:proj|exp)[A-Z][A-Za-z0-9]*?)(Title|Desc|LongDesc|Alt|Search|Gallery\d+Alt|Section\d+(?:Heading|Body)|Fact\d+(?:Label|Value)|Photo\d+Alt|Credit|Role|Org|OrgShort|Bullet\d+|ImageAlt)$")


def family(key: str) -> Optional[str]:
    m = _FAMILY_RE.match(key)
    return m.group(1) if m else None


def entry_prefix(key: str) -> Optional[str]:
    """proj<SlugCamel> / exp<SlugCamel> for a per-entry key, tag<IdCamel> for a tag label, else None."""
    m = _ENTRY_RE.match(key)
    if m:
        return m.group(1)
    if key.startswith("tag") and len(key) > 3 and key[3].isupper():
        return key
    return None
