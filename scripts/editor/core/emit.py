"""Emit JavaScript values in the style of the site's data files.

  * strings double-quoted (jsdata.encode_string), numbers / booleans / null as JS;
  * short things inline: `tags: ["python", "cad"]`, `dates: { from: { season:
    "summer", year: 2026 } }`, `{ src: "...", altKey: "..." }` items, `light:
    { bg: "#…", border: "#…", accent: "#…" }`;
  * one item per line for `bulletKeys`, `gallery`, `page.sections / facts /
    photos`; `page` and `color` as multi-line objects; an entry object multi-line
    with one property per line, 2-space indent, no trailing comma.
The property name decides the layout (MULTILINE below); everything else is
inline. Keys are written bare — every key in these files is an identifier.
"""

from __future__ import annotations

import re
from typing import Any

from .jsdata import encode_string

INDENT = "  "
# properties whose value is laid out one line per item / property
MULTILINE = {"page", "color", "gallery", "photos", "sections", "facts", "bulletKeys"}
_IDENT = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return repr(v) if isinstance(v, float) else str(v)
    if isinstance(v, str):
        return encode_string(v, '"')
    raise TypeError(f"not a scalar: {type(v).__name__}")


def _key(k: str) -> str:
    return k if _IDENT.match(k) else encode_string(k, '"')


def inline(v: Any) -> str:
    if isinstance(v, dict):
        if not v:
            return "{}"
        return "{ " + ", ".join(f"{_key(k)}: {inline(x)}" for k, x in v.items()) + " }"
    if isinstance(v, list):
        return "[" + ", ".join(inline(x) for x in v) + "]"
    return scalar(v)


def value(v: Any, key: str, indent: str) -> str:
    """The text for `key: <value>` — the value part — with `indent` = the property's own indent."""
    if key in MULTILINE:
        if isinstance(v, list):
            if not v:
                return "[]"
            inner = indent + INDENT
            return "[\n" + ",\n".join(inner + inline(x) for x in v) + "\n" + indent + "]"
        if isinstance(v, dict):
            return obj(v, indent)
    return inline(v)


def obj(d: dict, indent: str) -> str:
    """A multi-line object: one property per line, closing brace on `indent`."""
    if not d:
        return "{}"
    inner = indent + INDENT
    lines = [f"{inner}{_key(k)}: {value(x, k, inner)}" for k, x in d.items()]
    return "{\n" + ",\n".join(lines) + "\n" + indent + "}"


def entry(d: dict, indent: str) -> str:
    """An entry object for the top-level array (first line unindented, closing brace on `indent`)."""
    return obj(d, indent)
