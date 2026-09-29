"""Lossless tokenizer / span tree for the site's JS data files.

The data files (js/translations.js, js/projects-data.js, ...) use a small,
regular subset of JavaScript: top-level `const NAME = <literal>;`, object and
array literals, quoted strings, numbers, true/false/null, and `//` or `/* */`
comments. This module reads such a file into tokens that carry their exact
character positions, so an edit replaces only the characters of one string
value and everything else (comments, blank lines, key order, indentation,
line endings, quote style) is copied byte for byte.

Anything outside the subset (template literals, spreads, function calls,
identifiers used as values, ...) raises JsDataError naming the line, and so
does a property name that appears twice in one object (JavaScript keeps the
last one, so an edit to the first would change a value the site never shows).
Callers must then refuse to write the file.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union


class JsDataError(ValueError):
    """Raised when a file is outside the supported subset (with a 1-based line)."""

    def __init__(self, message: str, line: Optional[int] = None):
        self.line = line
        self.detail = message
        super().__init__(f"line {line}: {message}" if line else message)


@dataclass
class Token:
    kind: str  # ws | comment | punct | ident | number | string
    text: str
    start: int
    end: int
    line: int  # 1-based line where the token starts


PUNCT = set("{}[]:,;=")
_IDENT_START = re.compile(r"[A-Za-z_$]")
_IDENT_REST = re.compile(r"[A-Za-z0-9_$]*")
_NUMBER = re.compile(r"-?(?:0[xX][0-9a-fA-F]+|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)")
_WS_CHARS = " \t\r\n\f\v ﻿"
_WS = re.compile("[" + _WS_CHARS + "]+")

_UNSUPPORTED_HINTS = {
    "`": "template literal (backtick string)",
    "(": "parentheses / function call",
    ")": "parentheses / function call",
    "+": "expression (string concatenation or arithmetic)",
    ".": "member access or spread (...)",
    "?": "conditional expression",
    "&": "logical expression",
    "|": "logical expression",
    "!": "negation",
    "<": "comparison or JSX",
    ">": "arrow function or comparison",
    "/": "regular expression or division",
}


def tokenize(text: str) -> list[Token]:
    """Split text into tokens that cover it completely (ws and comments included)."""
    tokens: list[Token] = []
    i, n, line = 0, len(text), 1
    while i < n:
        ch = text[i]
        if ch in _WS_CHARS:
            m = _WS.match(text, i)
            seg = m.group(0)
            tokens.append(Token("ws", seg, i, m.end(), line))
            line += seg.count("\n")
            i = m.end()
        elif text.startswith("//", i):
            j = text.find("\n", i)
            if j == -1:
                j = n
            # keep a trailing \r with the newline, not the comment
            if j > i and text[j - 1] == "\r":
                j -= 1
            tokens.append(Token("comment", text[i:j], i, j, line))
            i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j == -1:
                raise JsDataError("unterminated block comment", line)
            seg = text[i : j + 2]
            tokens.append(Token("comment", seg, i, j + 2, line))
            line += seg.count("\n")
            i = j + 2
        elif ch in PUNCT:
            tokens.append(Token("punct", ch, i, i + 1, line))
            i += 1
        elif ch in "\"'":
            j = i + 1
            while True:
                if j >= n:
                    raise JsDataError("unterminated string", line)
                c = text[j]
                if c == "\\":
                    if j + 1 >= n:
                        raise JsDataError("unterminated string", line)
                    if text[j + 1] in "\r\n":
                        raise JsDataError("line continuation inside a string is not supported", line)
                    j += 2
                    continue
                if c in "\r\n":
                    raise JsDataError("newline inside a string", line)
                if c == ch:
                    break
                j += 1
            tokens.append(Token("string", text[i : j + 1], i, j + 1, line))
            i = j + 1
        elif ch == "`":
            raise JsDataError("unsupported syntax: template literal (backtick string)", line)
        elif (
            ch.isdigit()
            or (ch == "-" and i + 1 < n and (text[i + 1].isdigit() or text[i + 1] == "."))
            or (ch == "." and i + 1 < n and text[i + 1].isdigit())
        ):
            m = _NUMBER.match(text, i)
            if not m:
                raise JsDataError("malformed number", line)
            tokens.append(Token("number", m.group(0), i, m.end(), line))
            i = m.end()
        elif _IDENT_START.match(ch):
            m = _IDENT_REST.match(text, i + 1)
            tokens.append(Token("ident", text[i : m.end()], i, m.end(), line))
            i = m.end()
        else:
            hint = _UNSUPPORTED_HINTS.get(ch, f"character {ch!r}")
            raise JsDataError(f"unsupported syntax: {hint}", line)
    return tokens


# ---------------------------------------------------------------- tree nodes


@dataclass
class Node:
    first: int  # index of first significant token
    last: int  # index of last significant token (inclusive)
    line: int


@dataclass
class StringNode(Node):
    tok: int  # token index of the string literal
    value: str
    quote: str


@dataclass
class NumberNode(Node):
    value: Union[float, int]
    text: str


@dataclass
class BoolNode(Node):
    value: bool


@dataclass
class NullNode(Node):
    pass


@dataclass
class Property:
    key: str
    key_tok: int
    value: "ValueNode"
    first: int
    last: int  # last token of the value (not the comma)
    line: int


@dataclass
class ObjectNode(Node):
    props: list[Property] = field(default_factory=list)

    def get(self, key: str) -> Optional[Property]:
        for p in self.props:
            if p.key == key:
                return p
        return None

    def keys(self) -> list[str]:
        return [p.key for p in self.props]

    def value(self, key: str):
        p = self.get(key)
        return None if p is None else p.value


@dataclass
class ArrayNode(Node):
    items: list["ValueNode"] = field(default_factory=list)


ValueNode = Union[StringNode, NumberNode, BoolNode, NullNode, ObjectNode, ArrayNode]


@dataclass
class Statement:
    keyword: str
    name: str
    value: ValueNode
    first: int
    last: int
    line: int


# ------------------------------------------------------------ string codecs

_SIMPLE_ESCAPES = {
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "b": "\b",
    "f": "\f",
    "v": "\v",
    "0": "\0",
    "'": "'",
    '"': '"',
    "\\": "\\",
    "/": "/",
}


def decode_string(literal: str, line: Optional[int] = None) -> str:
    """Decode a JS string literal (with its quotes) into its value."""
    body = literal[1:-1]
    out: list[str] = []
    i, n = 0, len(body)
    while i < n:
        c = body[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        i += 1
        if i >= n:
            raise JsDataError("dangling backslash in string", line)
        e = body[i]
        if e in _SIMPLE_ESCAPES:
            out.append(_SIMPLE_ESCAPES[e])
            i += 1
        elif e == "u":
            if i + 1 < n and body[i + 1] == "{":
                j = body.find("}", i + 2)
                if j == -1:
                    raise JsDataError("bad \\u{...} escape", line)
                out.append(chr(int(body[i + 2 : j], 16)))
                i = j + 1
            else:
                hexs = body[i + 1 : i + 5]
                if len(hexs) != 4 or not re.fullmatch(r"[0-9a-fA-F]{4}", hexs):
                    raise JsDataError("bad \\u escape", line)
                out.append(chr(int(hexs, 16)))
                i += 5
        elif e == "x":
            hexs = body[i + 1 : i + 3]
            if not re.fullmatch(r"[0-9a-fA-F]{2}", hexs):
                raise JsDataError("bad \\x escape", line)
            out.append(chr(int(hexs, 16)))
            i += 3
        else:
            # JS treats an unknown escape as the character itself
            out.append(e)
            i += 1
    s = "".join(out)
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in s):
        # two \u escapes forming a surrogate pair → one code point
        s = s.encode("utf-16", "surrogatepass").decode("utf-16", "replace")
    return s


def encode_string(value: str, quote: str = '"') -> str:
    """Encode a value as a JS string literal. Non-ASCII stays literal (UTF-8 file)."""
    out = [quote]
    for ch in value:
        if ch == quote:
            out.append("\\" + quote)
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ord(ch) < 0x20 or ch in "  ":
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
    out.append(quote)
    return "".join(out)


# ------------------------------------------------------------------ parser


class _Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.sig = [i for i, t in enumerate(tokens) if t.kind not in ("ws", "comment")]
        self.pos = 0  # index into self.sig

    # helpers
    def _peek(self) -> Optional[Token]:
        if self.pos < len(self.sig):
            return self.tokens[self.sig[self.pos]]
        return None

    def _idx(self) -> int:
        return self.sig[self.pos]

    def _take(self) -> tuple[int, Token]:
        if self.pos >= len(self.sig):
            last = self.tokens[-1] if self.tokens else None
            raise JsDataError("unexpected end of file", last.line if last else None)
        i = self.sig[self.pos]
        self.pos += 1
        return i, self.tokens[i]

    def _expect(self, text: str) -> int:
        i, t = self._take()
        if t.text != text:
            raise JsDataError(f"expected {text!r} but found {t.text!r}", t.line)
        return i

    # grammar
    def program(self) -> list[Statement]:
        stmts = []
        while self._peek() is not None:
            stmts.append(self.statement())
        return stmts

    def statement(self) -> Statement:
        i, t = self._take()
        if t.kind != "ident" or t.text not in ("const", "let", "var"):
            raise JsDataError(
                f"unsupported statement starting with {t.text!r} (only const/let/var declarations)", t.line
            )
        _ni, name = self._take()
        if name.kind != "ident":
            raise JsDataError(f"expected a name after {t.text}", name.line)
        self._expect("=")
        value = self.value()
        last = value.last
        nxt = self._peek()
        if nxt is not None and nxt.text == ";":
            last = self._idx()
            self.pos += 1
        return Statement(t.text, name.text, value, i, last, t.line)

    def value(self) -> ValueNode:
        i, t = self._take()
        if t.kind == "string":
            return StringNode(i, i, t.line, i, decode_string(t.text, t.line), t.text[0])
        if t.kind == "number":
            txt = t.text
            try:
                num = int(txt, 0) if re.fullmatch(r"-?(0[xX][0-9a-fA-F]+|\d+)", txt) else float(txt)
            except ValueError:
                raise JsDataError(f"malformed number {txt!r}", t.line)
            return NumberNode(i, i, t.line, num, txt)
        if t.kind == "ident":
            if t.text in ("true", "false"):
                return BoolNode(i, i, t.line, t.text == "true")
            if t.text == "null":
                return NullNode(i, i, t.line)
            raise JsDataError(f"unsupported syntax: identifier {t.text!r} used as a value", t.line)
        if t.text == "{":
            return self.object(i, t.line)
        if t.text == "[":
            return self.array(i, t.line)
        raise JsDataError(f"unexpected {t.text!r}", t.line)

    def object(self, first: int, line: int) -> ObjectNode:
        node = ObjectNode(first, first, line)
        seen: dict[str, int] = {}  # key → line of its first occurrence
        while True:
            nxt = self._peek()
            if nxt is None:
                raise JsDataError("unterminated object literal", line)
            if nxt.text == "}":
                node.last = self._idx()
                self.pos += 1
                return node
            ki, kt = self._take()
            if kt.kind == "ident":
                key = kt.text
            elif kt.kind == "string":
                key = decode_string(kt.text, kt.line)
            elif kt.kind == "number":
                key = kt.text
            else:
                raise JsDataError(f"unexpected {kt.text!r} where a property name should be", kt.line)
            if key in seen:
                raise JsDataError(
                    f"duplicate property {key!r} (first on line {seen[key]}) — JavaScript keeps the last one, "
                    "so an edit could change a value the site never shows; remove one",
                    kt.line,
                )
            seen[key] = kt.line
            self._expect(":")
            val = self.value()
            node.props.append(Property(key, ki, val, ki, val.last, kt.line))
            nxt = self._peek()
            if nxt is None:
                raise JsDataError("unterminated object literal", line)
            if nxt.text == ",":
                self.pos += 1
            elif nxt.text != "}":
                raise JsDataError(f"expected ',' or '}}' but found {nxt.text!r}", nxt.line)

    def array(self, first: int, line: int) -> ArrayNode:
        node = ArrayNode(first, first, line)
        while True:
            nxt = self._peek()
            if nxt is None:
                raise JsDataError("unterminated array literal", line)
            if nxt.text == "]":
                node.last = self._idx()
                self.pos += 1
                return node
            node.items.append(self.value())
            nxt = self._peek()
            if nxt is None:
                raise JsDataError("unterminated array literal", line)
            if nxt.text == ",":
                self.pos += 1
            elif nxt.text != "]":
                raise JsDataError(f"expected ',' or ']' but found {nxt.text!r}", nxt.line)


# ---------------------------------------------------------------- document


class Document:
    """A parsed data file. `render(edits)` re-emits it with string edits applied.

    `edits` maps a StringNode's token index to its new value. With no edits the
    output is the input, byte for byte — checked on construction.
    """

    def __init__(self, text: str, bom: bool = False, source: str = "<text>"):
        self.text = text
        self.bom = bom
        self.source = source
        self.tokens = tokenize(text)
        self.statements = _Parser(self.tokens).program()
        if self.render({}) != text:
            raise JsDataError("round-trip self-check failed: re-emitted text differs from the file")

    # loading -------------------------------------------------------------
    @classmethod
    def from_bytes(cls, data: bytes, source: str = "<bytes>") -> "Document":
        bom = data.startswith(b"\xef\xbb\xbf")
        try:
            text = data[3:].decode("utf-8") if bom else data.decode("utf-8")
        except UnicodeDecodeError as e:
            raise JsDataError(f"file is not valid UTF-8 ({e})") from e
        doc = cls(text, bom=bom, source=source)
        if doc.to_bytes({}) != data:
            raise JsDataError("round-trip self-check failed: re-encoded bytes differ from the file")
        return doc

    @classmethod
    def load(cls, path: Union[str, Path]) -> "Document":
        p = Path(path)
        return cls.from_bytes(p.read_bytes(), source=str(p))

    # queries -------------------------------------------------------------
    def const(self, name: str) -> ValueNode:
        for s in self.statements:
            if s.name == name:
                return s.value
        raise JsDataError(f"no declaration named {name!r} in {self.source}")

    def const_names(self) -> list[str]:
        return [s.name for s in self.statements]

    def strings(self):
        """Yield every StringNode used as a value (depth-first)."""

        def walk(v):
            if isinstance(v, StringNode):
                yield v
            elif isinstance(v, ObjectNode):
                for p in v.props:
                    yield from walk(p.value)
            elif isinstance(v, ArrayNode):
                for it in v.items:
                    yield from walk(it)

        for s in self.statements:
            yield from walk(s.value)

    def comments_between(self, after: int, before: int) -> list[Token]:
        """Comment tokens strictly between token indexes `after` and `before`."""
        return [t for t in self.tokens[after + 1 : before] if t.kind == "comment"]

    def trailing_comment(self, tok_index: int) -> Optional[Token]:
        """A comment that follows token `tok_index` on the same line (after an optional comma)."""
        line = self.tokens[tok_index].line
        for t in self.tokens[tok_index + 1 :]:
            if t.kind == "ws":
                if "\n" in t.text:
                    return None
                continue
            if t.kind == "punct" and t.text == ",":
                continue
            if t.kind == "comment" and t.line == line:
                return t
            return None
        return None

    # emitting ------------------------------------------------------------
    def render(self, edits: dict[int, str]) -> str:
        if not edits:
            return "".join(t.text for t in self.tokens)
        parts = []
        for i, t in enumerate(self.tokens):
            if i in edits:
                if t.kind != "string":
                    raise JsDataError("internal: edit target is not a string token", t.line)
                parts.append(encode_string(edits[i], t.text[0]))
            else:
                parts.append(t.text)
        return "".join(parts)

    def to_bytes(self, edits: dict[int, str]) -> bytes:
        out = self.render(edits).encode("utf-8")
        return (b"\xef\xbb\xbf" + out) if self.bom else out


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def comment_text(tok: Token) -> str:
    """The human text of a comment token without its // or /* */ markers."""
    s = tok.text
    if s.startswith("//"):
        return s[2:].strip()
    if s.startswith("/*"):
        return s[2:-2].strip()
    return s.strip()
