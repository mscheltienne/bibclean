from __future__ import annotations

import re
from bisect import bisect_right

from bibclean._model import (
    Block,
    Entry,
    ExplicitComment,
    Field,
    Junk,
    Malformed,
    Part,
    Position,
    Preamble,
    StringDef,
    Value,
)

WHITESPACE = " \t\n\r\f\v"
_NOT_IDENTIFIER = frozenset(WHITESPACE + "#%'(),={}")
_NOT_CITE_KEY = frozenset(WHITESPACE + ",{}()")
# an '@' that is the first non-blank character of its line; with a start offset, '^'
# matches only at real line starts, never at the offset itself
_LINE_START = re.compile(r"^[ \t]*@", re.MULTILINE)
# an '@' separated from the end of the previous block by spaces and tabs only
_AFTER_BLOCK = re.compile(r"[ \t]*@")


class LineIndex:
    """Line and column lookup for one source text.

    Parameters
    ----------
    source : str
        Decoded source text.
    """

    def __init__(self, source: str) -> None:
        self._starts = [0]
        self._starts += [index + 1 for index, char in enumerate(source) if char == "\n"]

    def position(self, offset: int) -> Position:
        """Convert a character offset into a position.

        Parameters
        ----------
        offset : int
            Character offset into the source text.

        Returns
        -------
        Position
            The 1-based line and column of the offset.
        """
        line = bisect_right(self._starts, offset)
        return Position(line, offset - self._starts[line - 1] + 1)


class _ParseError(Exception):
    """Failure inside a block, caught and turned into a :class:`~Malformed`."""

    def __init__(self, message: str, offset: int) -> None:
        super().__init__(message)
        self.offset = offset


class _Scanner:
    """Recursive descent scanner over one source text."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.index = LineIndex(source)
        self._key: str | None = None

    def _peek(self) -> str:
        return self.source[self.pos] if self.pos < len(self.source) else ""

    def _skip_ws(self) -> None:
        source = self.source
        end = len(source)
        while self.pos < end and source[self.pos] in WHITESPACE:
            self.pos += 1

    def _expect(self, char: str, message: str) -> None:
        if self._peek() != char:
            raise _ParseError(message, self.pos)
        self.pos += 1

    def _scan_identifier(self) -> str:
        source = self.source
        end = len(source)
        start = self.pos
        while self.pos < end and source[self.pos] not in _NOT_IDENTIFIER:
            self.pos += 1
        return source[start : self.pos]

    def _scan_cite_key(self) -> str:
        source = self.source
        end = len(source)
        start = self.pos
        while self.pos < end and source[self.pos] not in _NOT_CITE_KEY:
            self.pos += 1
        return source[start : self.pos]

    def scan_block(self, at: int) -> tuple[Block, int]:
        """Scan one ``'@'`` block, recovering from any failure.

        Parameters
        ----------
        at : int
            Offset of the ``'@'`` starting the block.

        Returns
        -------
        block : Block
            The parsed block, a :class:`~bibclean._model.Malformed` on failure. A
            malformed block extends to the start of the next line whose first
            non-blank character is ``'@'``.
        end : int
            Offset of the first character after the block.
        """
        self.pos = at + 1
        self._key = None
        kind_text: str | None = None
        try:
            kind_text = self._scan_identifier()
            if not kind_text:
                raise _ParseError("expected an entry type after '@'", self.pos)
            self._skip_ws()
            opening = self._peek()
            if opening not in ("{", "("):
                raise _ParseError(
                    f"expected '{{' or '(' after '@{kind_text}'", self.pos
                )
            self.pos += 1
            closing = "}" if opening == "{" else ")"
            kind = kind_text.lower()
            if kind == "comment":
                block = self._scan_comment(at, opening)
            elif kind == "string":
                block = self._scan_string(at, closing)
            elif kind == "preamble":
                block = self._scan_preamble(at, closing)
            else:
                block = self._scan_entry(at, kind_text, opening, closing)
        except _ParseError as error:
            if self._key is not None:
                what = f"entry '{self._key}'"
            elif kind_text:
                what = f"@{kind_text.lower()} block"
            else:
                what = "block"
            position = self.index.position(min(error.offset, len(self.source)))
            resync = _LINE_START.search(self.source, at + 1)
            end = resync.start() if resync else len(self.source)
            malformed = Malformed(
                start=self.index.position(at),
                raw=self.source[at:end],
                message=(
                    f"{what} could not be parsed: {error} "
                    f"at line {position.line}, column {position.column}"
                ),
                error=position,
            )
            return malformed, end
        return block, self.pos

    def _scan_comment(self, at: int, opening: str) -> ExplicitComment:
        source = self.source
        end = len(source)
        body_start = self.pos
        depth = 0
        while self.pos < end:
            char = source[self.pos]
            if char == "{":
                depth += 1
            elif char == "}":
                if depth == 0:
                    if opening != "{":
                        raise _ParseError("unbalanced '}' in @comment", self.pos)
                    body = source[body_start : self.pos]
                    self.pos += 1
                    return ExplicitComment(
                        start=self.index.position(at),
                        raw=source[at : self.pos],
                        body=body,
                        delimiter="{",
                    )
                depth -= 1
            elif char == ")" and depth == 0 and opening == "(":
                body = source[body_start : self.pos]
                self.pos += 1
                return ExplicitComment(
                    start=self.index.position(at),
                    raw=source[at : self.pos],
                    body=body,
                    delimiter="(",
                )
            self.pos += 1
        raise _ParseError("unterminated @comment", end)

    def _scan_string(self, at: int, closing: str) -> StringDef:
        self._skip_ws()
        key = self._scan_identifier()
        if not key:
            raise _ParseError("expected a string name", self.pos)
        self._skip_ws()
        self._expect("=", f"expected '=' after string name '{key}'")
        self._skip_ws()
        value = self._scan_value(f"string '{key}'")
        self._skip_ws()
        self._expect(closing, f"expected '{closing}' after string '{key}'")
        return StringDef(
            start=self.index.position(at),
            raw=self.source[at : self.pos],
            key=key,
            value=value,
        )

    def _scan_preamble(self, at: int, closing: str) -> Preamble:
        self._skip_ws()
        value = self._scan_value("preamble")
        self._skip_ws()
        self._expect(closing, f"expected '{closing}' after preamble")
        return Preamble(
            start=self.index.position(at),
            raw=self.source[at : self.pos],
            value=value,
        )

    def _scan_entry(self, at: int, kind_text: str, opening: str, closing: str) -> Entry:
        self._skip_ws()
        key = self._scan_cite_key()
        if not key:
            raise _ParseError("expected a cite key", self.pos)
        self._key = key
        self._skip_ws()
        fields: list[Field] = []
        trailing_comma = False
        char = self._peek()
        if char == closing:
            self.pos += 1
        elif char == ",":
            self.pos += 1
            while True:
                self._skip_ws()
                if self._peek() == closing:
                    trailing_comma = True
                    self.pos += 1
                    break
                field_start = self.pos
                name = self._scan_identifier()
                if not name:
                    raise _ParseError("expected a field name", self.pos)
                self._skip_ws()
                self._expect("=", f"expected '=' after field '{name}'")
                self._skip_ws()
                value = self._scan_value(f"field '{name}'")
                fields.append(
                    Field(
                        key=name,
                        value=value,
                        start=self.index.position(field_start),
                    )
                )
                self._skip_ws()
                if self._peek() == ",":
                    self.pos += 1
                    continue
                if self._peek() == closing:
                    self.pos += 1
                    break
                raise _ParseError(
                    f"expected ',' or '{closing}' after field '{name}'", self.pos
                )
        else:
            raise _ParseError(
                f"expected ',' or '{closing}' after cite key '{key}'", self.pos
            )
        return Entry(
            start=self.index.position(at),
            raw=self.source[at : self.pos],
            entry_type=kind_text,
            key=key,
            fields=fields,
            delimiter=opening,
            trailing_comma=trailing_comma,
        )

    def _scan_value(self, what: str) -> Value:
        parts = [self._scan_part(what)]
        while True:
            saved = self.pos
            self._skip_ws()
            if self._peek() == "#":
                self.pos += 1
                self._skip_ws()
                parts.append(self._scan_part(what))
            else:
                self.pos = saved
                return Value(parts)

    def _scan_part(self, what: str) -> Part:
        source = self.source
        end = len(source)
        char = self._peek()
        if char == "{":
            self.pos += 1
            start = self.pos
            depth = 1
            while self.pos < end:
                current = source[self.pos]
                if current == "{":
                    depth += 1
                elif current == "}":
                    depth -= 1
                    if depth == 0:
                        text = source[start : self.pos]
                        self.pos += 1
                        return Part("braced", text)
                self.pos += 1
            raise _ParseError(f"unexpected end of file in {what}", end)
        if char == '"':
            self.pos += 1
            start = self.pos
            depth = 0
            while self.pos < end:
                current = source[self.pos]
                if current == "{":
                    depth += 1
                elif current == "}":
                    depth -= 1
                    if depth < 0:
                        raise _ParseError(f"unbalanced '}}' in {what}", self.pos)
                elif current == '"' and depth == 0:
                    text = source[start : self.pos]
                    self.pos += 1
                    return Part("quoted", text)
                self.pos += 1
            raise _ParseError(f"unexpected end of file in {what}", end)
        if char and char not in _NOT_IDENTIFIER:
            return Part("bare", self._scan_identifier())
        raise _ParseError(f"expected a value for {what}", self.pos)


def parse(source: str) -> list[Block]:
    r"""Parse a source text into a lossless list of blocks.

    Parameters
    ----------
    source : str
        Decoded source text, with ``'\n'`` line endings only.

    Returns
    -------
    list of Block
        Blocks covering the source exactly: joining their raw text reproduces the
        input. A block the parser could not read becomes a
        :class:`~bibclean._model.Malformed` and the scan resumes at the next line
        whose first non-blank character is ``'@'``.

    Notes
    -----
    An ``'@'`` starts a block when it is the first non-blank character of its line,
    or when only spaces and tabs separate it from the end of the previous parsed
    block. Any other ``'@'`` belongs to free text.
    """
    scanner = _Scanner(source)
    blocks: list[Block] = []
    pos = 0
    end = len(source)
    after_block = False
    while pos < end:
        match = (after_block and _AFTER_BLOCK.match(source, pos)) or (
            _LINE_START.search(source, pos)
        )
        at = match.end() - 1 if match else end
        if at > pos:
            blocks.append(Junk(start=scanner.index.position(pos), raw=source[pos:at]))
        if at == end:
            break
        block, pos = scanner.scan_block(at)
        blocks.append(block)
        after_block = not isinstance(block, Malformed)
    return blocks
