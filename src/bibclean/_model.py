from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Kind = Literal["braced", "quoted", "bare"]


@dataclass(slots=True, frozen=True, order=True)
class Position:
    """Location in a source file.

    Parameters
    ----------
    line : int
        1-based line number.
    column : int
        1-based column number, counted in characters of the decoded text.
    """

    line: int
    column: int


@dataclass(slots=True)
class Part:
    """One component of a ``#``-concatenated value.

    Parameters
    ----------
    kind : str
        One of ``'braced'``, ``'quoted'`` or ``'bare'``.
    text : str
        Content without the delimiters; for a bare part, the macro or the digits.
    """

    kind: Kind
    text: str

    @property
    def is_macro(self) -> bool:
        """Whether the part is a bare macro name rather than a bare number.

        Returns
        -------
        bool
            True for a bare part whose text is not made of ASCII digits only.
        """
        return self.kind == "bare" and not (self.text.isascii() and self.text.isdigit())


@dataclass(slots=True)
class Value:
    """Field, string or preamble value.

    Parameters
    ----------
    parts : list of Part
        The concatenated components, at least one.
    """

    parts: list[Part]


@dataclass(slots=True)
class Field:
    """Field of an entry.

    Parameters
    ----------
    key : str
        Field name as written in the source.
    value : Value
        Field value.
    start : Position
        Position of the first character of the field name.
    """

    key: str
    value: Value
    start: Position


@dataclass(slots=True)
class Block:
    """Top-level element of a file.

    Parameters
    ----------
    start : Position
        Position of the ``'@'`` for delimited blocks, of the first character for junk.
    raw : str
        Exact source slice covered by the block.
    """

    start: Position
    raw: str


@dataclass(slots=True)
class Junk(Block):
    """Free text between blocks: whitespace, ``%`` lines, prose and ``@comment``.

    Free text holds no ``'@'``, except the one opening an ``@comment`` at its start.
    """


@dataclass(slots=True)
class Preamble(Block):
    """``@preamble`` block.

    Parameters
    ----------
    value : Value
        Preamble value.
    """

    value: Value


@dataclass(slots=True)
class StringDef(Block):
    """``@string`` block defining one macro.

    Parameters
    ----------
    key : str
        Macro name as written in the source.
    value : Value
        Macro value.
    """

    key: str
    value: Value


@dataclass(slots=True)
class Entry(Block):
    """Bibliography entry.

    Parameters
    ----------
    entry_type : str
        Entry type as written in the source.
    key : str
        Cite key as written in the source.
    fields : list of Field
        Fields of the entry, in source order.
    """

    entry_type: str
    key: str
    fields: list[Field]


@dataclass(slots=True)
class Malformed(Block):
    """Block the parser could not read, preserved verbatim.

    Parameters
    ----------
    message : str
        Full description of the failure.
    """

    message: str


def entry_type(entry: Entry) -> str:
    """Return the lowercased type of an entry.

    Parameters
    ----------
    entry : Entry
        Entry to inspect.

    Returns
    -------
    str
        The entry type, lowercased.
    """
    return entry.entry_type.lower()
