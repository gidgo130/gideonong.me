"""Validation rules for js/translations.js (the Phase 1 subset of plan §5).

Errors block a save, warnings do not. Which errors block is decided in
`blocking()`: only errors the draft introduces, or errors on keys the draft
touches. Pre-existing errors elsewhere are reported separately so a problem
Phase 1 cannot fix (a key missing in one language) never locks every save.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Iterable, Optional

# Strings that are legitimately identical in EN and ES.
IDENTICAL_ALLOWED = {
    "Python",
    "MATLAB",
    "CAD",
    "IEL",
    "LinkedIn",
    "GitHub",
    "Arduino",
    "SolidWorks",
    "Excel",
    "Baker Hughes",
    "Velora",
    "MLP",
    "UCI",
    "EN",
    "ES",
    "Gideon A. Ong",
    "Personal",
    "Machine Learning",
}
# Keys whose EN and ES values are expected to match (names, addresses, ids).
IDENTICAL_ALLOWED_KEY_RE = re.compile(
    r"^(footerContact|footerCopyright|aboutIdentifiers(EN|ES)|exp\w+Org(Short)?|proj\w+Fact\d+Value)$"
)

# English voice words that read as AI or résumé filler.
VOICE_WORDS = [
    "leveraged",
    "leverage",
    "leveraging",
    "spearheaded",
    "spearhead",
    "passionate",
    "showcasing",
    "showcase",
    "showcased",
    "moreover",
    "furthermore",
    "additionally",
    "delve",
    "delved",
    "cutting-edge",
    "synergy",
    "synergies",
    "robust",
    "seamless",
    "seamlessly",
    "utilize",
    "utilized",
    "utilizing",
    "in today's",
    "testament to",
    "tapestry",
    "elevate",
    "unlock",
    "empower",
    "empowering",
    "game-changer",
    "holistic",
]
_VOICE_RE = re.compile(r"(?<![\w'-])(" + "|".join(re.escape(w) for w in VOICE_WORDS) + r")(?![\w-])", re.IGNORECASE)
_HTML_RE = re.compile(r"</?[A-Za-z][^>]*>|&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);")
_TODO_RE = re.compile(r"\bTODO\b")


@dataclass(frozen=True)
class Issue:
    level: str  # error | warning
    code: str  # missing-key | todo | html | same | voice | todo-hidden
    key: str
    lang: str  # en | es | "" (both)
    message: str

    def ident(self) -> tuple:
        return (self.code, self.key, self.lang)

    def to_json(self) -> dict:
        return asdict(self)


def is_todo(value: str) -> bool:
    return bool(_TODO_RE.search(value))


def has_html(value: str) -> bool:
    return bool(_HTML_RE.search(value))


def voice_words(value: str) -> list[str]:
    seen, out = set(), []
    for m in _VOICE_RE.finditer(value):
        w = m.group(1).lower()
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def identical_allowed(key: str, value: str) -> bool:
    v = value.strip()
    if not v or v in IDENTICAL_ALLOWED:
        return True
    if IDENTICAL_ALLOWED_KEY_RE.match(key):
        return True
    if not re.search(r"[A-Za-z]", v):
        return True  # numbers, symbols, punctuation only
    if "{" in v and "}" in v:
        return True  # a template such as "{season} {year}"
    if re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", v):
        return True  # email
    if re.match(r"https?://|www\.", v):
        return True  # URL
    if re.fullmatch(r"[A-Z0-9/&+.\- ]{1,12}", v):
        return True  # short acronym-like label ("CAD", "ES 4863", "MLP")
    return False


def _hidden(key: str, prefixes: Iterable[str]) -> bool:
    """True if key belongs to a hidden entry's prefix (proj<SlugCamel> / exp<SlugCamel>).

    The character after the prefix must be uppercase or a digit — the start of
    the next key part (…Role, …Bullet1) — so "expEslTutor" never claims a
    visible "expEslTutoringRole".
    """
    for p in prefixes:
        if len(key) > len(p) and key.startswith(p) and (key[len(p)].isupper() or key[len(p)].isdigit()):
            return True
    return False


def validate(en: dict, es: dict, hidden_prefixes: Iterable[str] = ()) -> list[Issue]:
    prefixes = list(hidden_prefixes)
    issues: list[Issue] = []
    keys = list(en) + [k for k in es if k not in en]
    for key in keys:
        e, s = en.get(key), es.get(key)
        if e is None:
            issues.append(Issue("error", "missing-key", key, "en", "Missing in EN (exists only in ES)"))
        if s is None:
            issues.append(Issue("error", "missing-key", key, "es", "Missing in ES (exists only in EN)"))
        for lang, val in (("en", e), ("es", s)):
            if val is None:
                continue
            if is_todo(val):
                if _hidden(key, prefixes):
                    issues.append(Issue("warning", "todo-hidden", key, lang, "TODO placeholder (entry is hidden on the site)"))
                else:
                    issues.append(Issue("error", "todo", key, lang, "TODO placeholder in visible text"))
            if has_html(val):
                issues.append(Issue("error", "html", key, lang, "HTML in a string — translations.js is plain text only"))
            words = voice_words(val)
            if words:
                issues.append(Issue("warning", "voice", key, lang, "Voice words: " + ", ".join(words)))
        if e is not None and s is not None and e == s and not identical_allowed(key, e):
            issues.append(Issue("warning", "same", key, "", "ES is identical to EN"))
    return issues


@dataclass
class SaveGate:
    blocking: list[Issue]
    preexisting: list[Issue]
    warnings: list[Issue]

    def ok(self) -> bool:
        return not self.blocking

    def to_json(self) -> dict:
        return {
            "ok": self.ok(),
            "blocking": [i.to_json() for i in self.blocking],
            "preexisting": [i.to_json() for i in self.preexisting],
            "warnings": [i.to_json() for i in self.warnings],
        }


def blocking(baseline: list[Issue], draft: list[Issue], touched_keys: Iterable[str]) -> SaveGate:
    """Split the draft's issues into blocking errors, pre-existing errors and warnings."""
    touched = set(touched_keys)
    base = {i.ident() for i in baseline if i.level == "error"}
    block, pre, warn = [], [], []
    for i in draft:
        if i.level != "error":
            warn.append(i)
        elif i.key in touched or i.ident() not in base:
            block.append(i)
        else:
            pre.append(i)
    return SaveGate(block, pre, warn)
