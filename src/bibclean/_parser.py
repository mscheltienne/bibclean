from __future__ import annotations

import re
from bisect import bisect_right

from bibclean._model import (
    Block,
    Entry,
    Field,
    Junk,
    Malformed,
    Part,
    Position,
    Preamble,
    StringDef,
    Value,
)

# '\s' matches the characters for which str.isspace() is true, as in pybtex
_WHITESPACE = re.compile(r"\s*")
_IDENTIFIER = re.compile(r"[^\s\"#%'(),={}]*")
# a cite key ends at whitespace, ',', a brace or the closing delimiter of its entry
_CITE_KEY = {"}": re.compile(r"[^\s,{}]*"), ")": re.compile(r"[^\s,{})]*")}


def _next_at(source: str, pos: int) -> int:
    """Find the next ``'@'``.

    Parameters
    ----------
    source : str
        Source text.
    pos : int
        Offset at which the search starts.

    Returns
    -------
    int
        Offset of the first ``'@'`` at or after ``pos``, the length of the source
        when there is none.
    """
    at = source.find("@", pos)
    return len(source) if at == -1 else at


class LineIndex:
    """Line and column lookup for one source text.

    Parameters
    ----------
    source : str
        Decoded source text.
    """

    def __init__(self, source: str) -> None:
        self._starts = [0] + [match.end() for match in re.finditer("\n", source)]

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
    """Failure inside a block, turned into a :class:`~bibclean._model.Malformed`.

    Parameters
    ----------
    message : str
        Description of the failure.
    offset : int
        Character offset at which the failure was detected.
    """

    def __init__(self, message: str, offset: int) -> None:
        super().__init__(message)
        self.offset = offset


class _Scanner:
    """Recursive descent scanner over one source text.

    Parameters
    ----------
    source : str
        Decoded source text.
    """

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.index = LineIndex(source)
        self._key: str | None = None

    def _peek(self) -> str:
        """Return the character at the current offset.

        Returns
        -------
        str
            The character, an empty string at the end of the source.
        """
        return self.source[self.pos] if self.pos < len(self.source) else ""

    def _skip_ws(self) -> None:
        """Advance the current offset past whitespace, Unicode spaces included."""
        self.pos = _WHITESPACE.match(self.source, self.pos).end()

    def _expect(self, char: str, message: str) -> None:
        """Consume one expected character.

        Parameters
        ----------
        char : str
            Character expected at the current offset.
        message : str
            Message of the error raised when another character is found.

        Raises
        ------
        _ParseError
            If the character at the current offset is not ``char``.
        """
        if self._peek() != char:
            raise _ParseError(message, self.pos)
        self.pos += 1

    def _scan_identifier(self) -> str:
        """Consume an entry type, a field name, a string name or a bare macro.

        Returns
        -------
        str
            The identifier, empty when the current character cannot start one.
        """
        start = self.pos
        self.pos = _IDENTIFIER.match(self.source, start).end()
        return self.source[start : self.pos]

    def _scan_cite_key(self, closing: str) -> str:
        """Consume a cite key, which ends at whitespace, ``','``, ``'{'`` or ``'}'``.

        Parameters
        ----------
        closing : str
            Delimiter closing the entry, ``'}'`` or ``')'``, which also ends the key.

        Returns
        -------
        str
            The cite key, empty when the current character cannot start one.
        """
        start = self.pos
        self.pos = _CITE_KEY[closing].match(self.source, start).end()
        return self.source[start : self.pos]

    def scan_block(self, at: int) -> tuple[Block, int]:
        """Scan one ``'@'`` block, recovering from any failure.

        Parameters
        ----------
        at : int
            Offset of the ``'@'`` starting the block.

        Returns
        -------
        block : Block
            The parsed block. An ``@comment`` and the text after its delimiter, up to
            the next ``'@'``, form a :class:`~bibclean._model.Junk`. A block that
            cannot be read is a :class:`~bibclean._model.Malformed` extending to the
            next ``'@'``.
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
                self.pos = _next_at(self.source, self.pos)
                block = Junk(
                    start=self.index.position(at), raw=self.source[at : self.pos]
                )
            elif kind == "string":
                block = self._scan_string(at, closing)
            elif kind == "preamble":
                block = self._scan_preamble(at, closing)
            else:
                block = self._scan_entry(at, kind_text, closing)
        except _ParseError as error:
            if self._key is not None:
                what = f"entry '{self._key}'"
            elif kind_text:
                what = f"@{kind_text.lower()} block"
            else:
                what = "block"
            position = self.index.position(min(error.offset, len(self.source)))
            end = _next_at(self.source, at + 1)
            malformed = Malformed(
                start=self.index.position(at),
                raw=self.source[at:end],
                message=(
                    f"{what} could not be parsed: {error} "
                    f"at line {position.line}, column {position.column}"
                ),
            )
            return malformed, end
        return block, self.pos

    def _scan_string(self, at: int, closing: str) -> StringDef:
        """Consume the body of an ``@string`` block, after its opening delimiter.

        Parameters
        ----------
        at : int
            Offset of the ``'@'`` starting the block.
        closing : str
            Delimiter closing the block, ``'}'`` or ``')'``.

        Returns
        -------
        StringDef
            The macro definition.

        Raises
        ------
        _ParseError
            If the body is not ``name = value`` followed by the closing delimiter.
        """
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
        """Consume the body of an ``@preamble`` block, after its opening delimiter.

        Parameters
        ----------
        at : int
            Offset of the ``'@'`` starting the block.
        closing : str
            Delimiter closing the block, ``'}'`` or ``')'``.

        Returns
        -------
        Preamble
            The preamble.

        Raises
        ------
        _ParseError
            If the body is not a value followed by the closing delimiter.
        """
        self._skip_ws()
        value = self._scan_value("preamble")
        self._skip_ws()
        self._expect(closing, f"expected '{closing}' after preamble")
        return Preamble(
            start=self.index.position(at),
            raw=self.source[at : self.pos],
            value=value,
        )

    def _scan_entry(self, at: int, kind_text: str, closing: str) -> Entry:
        """Consume the body of an entry, after its opening delimiter.

        Parameters
        ----------
        at : int
            Offset of the ``'@'`` starting the block.
        kind_text : str
            Entry type, as written.
        closing : str
            Delimiter closing the block, ``'}'`` or ``')'``.

        Returns
        -------
        Entry
            The entry.

        Raises
        ------
        _ParseError
            If the body is not a cite key followed by comma-separated
            ``name = value`` fields and the closing delimiter.
        """
        self._skip_ws()
        key = self._scan_cite_key(closing)
        if not key:
            raise _ParseError("expected a cite key", self.pos)
        self._key = key
        self._skip_ws()
        fields: list[Field] = []
        char = self._peek()
        if char == closing:
            self.pos += 1
        elif char == ",":
            self.pos += 1
            while True:
                self._skip_ws()
                if self._peek() == closing:
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
        )

    def _scan_value(self, what: str) -> Value:
        """Consume a value: parts joined by ``'#'``.

        Parameters
        ----------
        what : str
            Name of the construct holding the value, used in error messages.

        Returns
        -------
        Value
            The value. The current offset is left after its last part, before any
            trailing whitespace.

        Raises
        ------
        _ParseError
            If a part cannot be read.
        """
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
        """Consume one braced, quoted or bare part of a value.

        Braces are counted as BibTeX counts them: a backslash escapes nothing, and a
        quoted part ends at the first ``'"'`` outside braces.

        Parameters
        ----------
        what : str
            Name of the construct holding the value, used in error messages.

        Returns
        -------
        Part
            The part, its text without the delimiters.

        Raises
        ------
        _ParseError
            If no part starts at the current offset, if the braces of a quoted part
            are unbalanced, or if the source ends inside the part.
        """
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
        text = self._scan_identifier()
        if text:
            return Part("bare", text)
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
        :class:`~bibclean._model.Malformed` and the scan resumes at the next ``'@'``.

    Notes
    -----
    Like BibTeX and pybtex, every ``'@'`` outside a block starts a block, wherever
    it is: ``'%'`` is not a comment character. An ``@comment`` and the text after its
    delimiter, up to the next ``'@'``, are free text.
    """
    scanner = _Scanner(source)
    blocks: list[Block] = []
    pos = 0
    end = len(source)
    while pos < end:
        at = _next_at(source, pos)
        if at > pos:
            blocks.append(Junk(start=scanner.index.position(pos), raw=source[pos:at]))
        if at == end:
            break
        block, pos = scanner.scan_block(at)
        blocks.append(block)
    return blocks
