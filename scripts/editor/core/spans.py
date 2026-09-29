"""Structural edits on a jsdata.Document that touch only the characters they must.

jsdata renders string-token edits; this layer adds value replacement of any
kind, property insertion / deletion, and array item append / deletion, all as
character-span edits (start, end, replacement). `apply()` applies them from the
end of the file backwards and re-parses the result, so anything written is
proven to be inside the tokenizer's subset before it reaches disk.

Conventions matched to the site's data files (2-space indent, one entry per
block, a property per line): a deleted property takes its line, its comma and a
trailing same-line comment with it; an inserted property takes the indentation
of its neighbour; a deleted array item leaves the comments between items alone.
"""

from __future__ import annotations

from typing import Any, Optional, Union

from .jsdata import (
    ArrayNode,
    BoolNode,
    Document,
    JsDataError,
    NullNode,
    NumberNode,
    ObjectNode,
    Property,
    StringNode,
    ValueNode,
    encode_string,
)

Edit = tuple[int, int, str]


# ----------------------------------------------------------------- reading


def to_python(node: ValueNode) -> Any:
    if isinstance(node, StringNode):
        return node.value
    if isinstance(node, NumberNode):
        return node.value
    if isinstance(node, BoolNode):
        return node.value
    if isinstance(node, NullNode):
        return None
    if isinstance(node, ObjectNode):
        return {p.key: to_python(p.value) for p in node.props}
    if isinstance(node, ArrayNode):
        return [to_python(it) for it in node.items]
    raise TypeError(type(node).__name__)


def span(doc: Document, node: Union[ValueNode, Property]) -> tuple[int, int]:
    return doc.tokens[node.first].start, doc.tokens[node.last].end


def indent_of(doc: Document, tok_index: int) -> str:
    """The whitespace between the previous newline and this token."""
    start = doc.tokens[tok_index].start
    line_start = doc.text.rfind("\n", 0, start) + 1
    seg = doc.text[line_start:start]
    return seg if seg.strip() == "" else ""


def _prev_significant(doc: Document, tok_index: int) -> Optional[int]:
    i = tok_index - 1
    while i >= 0:
        if doc.tokens[i].kind not in ("ws", "comment"):
            return i
        i -= 1
    return None


def _next_significant(doc: Document, tok_index: int) -> Optional[int]:
    i = tok_index + 1
    while i < len(doc.tokens):
        if doc.tokens[i].kind not in ("ws", "comment"):
            return i
        i += 1
    return None


def _comma_after(doc: Document, last_tok: int) -> Optional[int]:
    n = _next_significant(doc, last_tok)
    if n is not None and doc.tokens[n].kind == "punct" and doc.tokens[n].text == ",":
        return n
    return None


def _end_with_trailing(doc: Document, last_tok: int) -> int:
    """End of the value (or its comma), plus a same-line trailing comment if any."""
    comma = _comma_after(doc, last_tok)
    end_tok = comma if comma is not None else last_tok
    trailing = doc.trailing_comment(last_tok if comma is None else comma)
    if trailing is None and comma is not None:
        trailing = doc.trailing_comment(last_tok)
    if trailing is not None:
        return trailing.end
    return doc.tokens[end_tok].end


# ----------------------------------------------------------------- editing


def replace_value(doc: Document, node: ValueNode, new_text: str) -> Edit:
    s, e = span(doc, node)
    return (s, e, new_text)


def replace_string(doc: Document, node: StringNode, value: str) -> Edit:
    tok = doc.tokens[node.tok]
    return (tok.start, tok.end, encode_string(value, tok.text[0]))


def _delete_member(doc: Document, container_first: int, members: list, i: int) -> Edit:
    """Delete member i of an object (props) or array (items)."""
    m = members[i]
    first, last = m.first, m.last
    comma = _comma_after(doc, last)
    if comma is not None:
        end = _end_with_trailing(doc, last)
        # keep any comment that sits between the previous member and this one
        prev_sig = _prev_significant(doc, first)
        start = doc.tokens[prev_sig].end if prev_sig is not None else doc.tokens[container_first].end
        for t in doc.tokens[(prev_sig if prev_sig is not None else container_first) + 1 : first]:
            if t.kind == "comment":
                start = t.end
        return (start, end, "")
    # last member: also remove the previous member's comma
    if i > 0:
        prev = members[i - 1]
        start = doc.tokens[prev.last].end
        for t in doc.tokens[prev.last + 1 : first]:
            if t.kind == "comment":
                start = t.end
    else:
        start = doc.tokens[container_first].end
    end = _end_with_trailing(doc, last)
    return (start, end, "")


def delete_prop(doc: Document, obj: ObjectNode, key: str) -> Edit:
    idx = next((i for i, p in enumerate(obj.props) if p.key == key), None)
    if idx is None:
        raise KeyError(key)
    return _delete_member(doc, obj.first, obj.props, idx)


def delete_item(doc: Document, arr: ArrayNode, index: int) -> Edit:
    return _delete_member(doc, arr.first, arr.items, index)


def insert_prop_after(doc: Document, obj: ObjectNode, after: Optional[str], key: str, value_text: str, blank_line_before: bool = False) -> Edit:
    """Insert `key: value_text` after property `after` (None → as the first property)."""
    if after is None:
        indent = indent_of(doc, obj.props[0].key_tok) if obj.props else indent_of(doc, obj.first) + "  "
        pos = doc.tokens[obj.first].end
        line = f"\n{indent}{key}: {value_text}" + ("," if obj.props else "")
        return (pos, pos, line)
    prop = obj.get(after)
    if prop is None:
        raise KeyError(after)
    indent = indent_of(doc, prop.key_tok)
    comma = _comma_after(doc, prop.last)
    gap = "\n\n" if blank_line_before else "\n"
    if comma is not None:
        pos = _end_with_trailing(doc, prop.last)
        return (pos, pos, f"{gap}{indent}{key}: {value_text},")
    pos = doc.tokens[prop.last].end
    return (pos, pos, f",{gap}{indent}{key}: {value_text}")


def insert_props_after(doc: Document, obj: ObjectNode, after: Optional[str], items: list[tuple[str, str]]) -> Edit:
    """Insert several `key: value_text` lines, in order, after property `after` (None → first)."""
    if not items:
        raise ValueError("nothing to insert")
    if after is None:
        indent = prop_indent(doc, obj)
        pos = doc.tokens[obj.first].end
        body = "".join(f"\n{indent}{k}: {v}," for k, v in items)
        return (pos, pos, body if obj.props else body.rstrip(","))
    prop = obj.get(after)
    if prop is None:
        raise KeyError(after)
    indent = indent_of(doc, prop.key_tok)
    comma = _comma_after(doc, prop.last)
    body = "".join(f"\n{indent}{k}: {v}," for k, v in items)
    if comma is not None:
        pos = _end_with_trailing(doc, prop.last)
        return (pos, pos, body)
    pos = doc.tokens[prop.last].end
    return (pos, pos, "," + body.rstrip(","))


def append_item(doc: Document, arr: ArrayNode, item_text: str, blank_line_before: bool = False) -> Edit:
    """Append an item (already emitted, first line unindented) before the closing bracket."""
    if arr.items:
        last = arr.items[-1]
        indent = indent_of(doc, last.first)
        pos = doc.tokens[last.last].end
        gap = "\n\n" if blank_line_before else "\n"
        return (pos, pos, f",{gap}{indent}{item_text}")
    indent = indent_of(doc, arr.first) + "  "
    pos = doc.tokens[arr.first].end
    return (pos, pos, f"\n{indent}{item_text}\n{indent_of(doc, arr.first)}")


def apply(doc: Document, edits: list[Edit]) -> Document:
    """A new Document with the edits applied (checked: non-overlapping, still in the subset)."""
    if not edits:
        return doc
    ordered = sorted(edits, key=lambda e: (e[0], e[1]))
    for a, b in zip(ordered, ordered[1:]):
        if b[0] < a[1]:
            raise JsDataError(f"internal: overlapping edits at {a[0]}–{a[1]} and {b[0]}–{b[1]}")
    text = doc.text
    for s, e, rep in reversed(ordered):
        text = text[:s] + rep + text[e:]
    try:
        return Document(text, bom=doc.bom, source=doc.source)
    except JsDataError as e:
        raise JsDataError(f"the edited file would fall outside the supported subset: {e}") from e


def prop_indent(doc: Document, obj: ObjectNode) -> str:
    return indent_of(doc, obj.props[0].key_tok) if obj.props else indent_of(doc, obj.first) + "  "
