from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bibclean._model import (
    Block,
    Entry,
    ExplicitComment,
    Junk,
    Malformed,
    Preamble,
    StringDef,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from bibclean._config import FormatOptions
    from bibclean._model import Field, Value

_WHITESPACE_RUN = re.compile(r"[ \t\n\r\f\v]+")
_DIGITS = frozenset("0123456789")


@dataclass(slots=True)
class _Unit:
    """A block together with the comments and prose written directly above it."""

    prefixes: list[Block]
    block: Block | None


def collapse_whitespace(text: str) -> str:
    r"""Replace every run of whitespace by a single space.

    Parameters
    ----------
    text : str
        Text to collapse.

    Returns
    -------
    str
        The text with every run of ``[ \t\n\r\f\v]`` replaced by one space.
    """
    return _WHITESPACE_RUN.sub(" ", text)


def sort_key(entry: Entry) -> str:
    """Return the sort key of an entry.

    Parameters
    ----------
    entry : Entry
        Entry to sort.

    Returns
    -------
    str
        The cite key, lowercased.
    """
    return entry.key.lower()


def render_value(value: Value) -> str:
    """Render a value in canonical form.

    Parameters
    ----------
    value : Value
        Value to render.

    Returns
    -------
    str
        The concatenated parts joined by ``' # '``. Braced, quoted and bare
        numeric parts are rendered with braces; bare macros are left untouched.
    """
    parts = value.parts
    texts = [
        part.text if part.kind == "bare" else collapse_whitespace(part.text)
        for part in parts
    ]
    if parts[0].kind != "bare":
        texts[0] = texts[0].lstrip()
    if parts[-1].kind != "bare":
        texts[-1] = texts[-1].rstrip()
    rendered = []
    for part, text in zip(parts, texts, strict=True):
        if part.kind == "bare" and not (text and set(text) <= _DIGITS):
            rendered.append(text)
        else:
            rendered.append("{" + text + "}")
    return " # ".join(rendered)


def render_fields(entry: Entry, options: FormatOptions) -> str:
    """Render the body lines of an entry.

    Parameters
    ----------
    entry : Entry
        Entry to render.
    options : FormatOptions
        Formatting options.

    Returns
    -------
    str
        The indented field lines, without the head and the closing delimiter.
    """
    return "\n".join(_field_lines(entry, options))


def render_entry(entry: Entry, options: FormatOptions) -> str:
    """Render an entry in canonical form.

    Parameters
    ----------
    entry : Entry
        Entry to render.
    options : FormatOptions
        Formatting options.

    Returns
    -------
    str
        The entry, without a trailing newline.
    """
    fields = _sorted_fields(entry, options)
    head = "@" + entry.entry_type.lower() + "{" + entry.key
    if fields or options.trailing_comma:
        head += ","
    return "\n".join([head, *_field_lines(entry, options), "}"])


def render_block(block: Block, options: FormatOptions) -> str:
    """Render one block in canonical form.

    Parameters
    ----------
    block : Block
        Block to render.
    options : FormatOptions
        Formatting options.

    Returns
    -------
    str
        The block, without a trailing newline.
    """
    if isinstance(block, Entry):
        return render_entry(block, options)
    if isinstance(block, StringDef):
        return "@string{" + block.key + " = " + render_value(block.value) + "}"
    if isinstance(block, Preamble):
        return "@preamble{" + render_value(block.value) + "}"
    if isinstance(block, ExplicitComment):
        closing = "}" if block.delimiter == "{" else ")"
        return "@comment" + block.delimiter + block.body + closing
    if isinstance(block, Malformed):
        return block.raw.rstrip()
    return block.raw.strip()


def format_blocks(blocks: Sequence[Block], options: FormatOptions) -> str:
    """Render a list of blocks as a canonical file.

    Parameters
    ----------
    blocks : sequence of Block
        Blocks to render, in source order.
    options : FormatOptions
        Formatting options.

    Returns
    -------
    str
        The canonical text: preambles, then strings, then entries with the
        malformed blocks back at their original index, one blank line between
        units and exactly one final newline. An input without any block renders
        as the empty string.
    """
    units = _order_units(_group_units(blocks), options)
    if not units:
        return ""
    return "\n\n".join(_render_unit(unit, options) for unit in units) + "\n"


def _field_lines(entry: Entry, options: FormatOptions) -> list[str]:
    """Build the indented field lines of an entry."""
    fields = _sorted_fields(entry, options)
    width = max((len(f.key) for f in fields), default=0) if options.align_values else 0
    indent = _indent(options)
    lines = []
    for index, item in enumerate(fields):
        key = item.key.lower().ljust(width) if width else item.key.lower()
        last = index == len(fields) - 1
        comma = "," if not last or options.trailing_comma else ""
        lines.append(indent + key + " = " + render_value(item.value) + comma)
    return lines


def _indent(options: FormatOptions) -> str:
    """Return the indent string of one field line."""
    return "\t" if options.indent == "tab" else " " * options.indent


def _sorted_fields(entry: Entry, options: FormatOptions) -> list[Field]:
    """Order the fields of an entry according to the options."""
    order = options.sort_fields
    if order is False:
        return list(entry.fields)
    if order is True:
        return sorted(entry.fields, key=lambda item: item.key.lower())
    first: list[str] = []
    for name in order:
        if name.lower() not in first:
            first.append(name.lower())

    def key(item: Field) -> tuple[int, str]:
        name = item.key.lower()
        if name in first:
            return (first.index(name), "")
        return (len(first), name)

    return sorted(entry.fields, key=key)


def _group_units(blocks: Sequence[Block]) -> list[_Unit]:
    """Group blocks into units, dropping whitespace-only junk."""
    units: list[_Unit] = []
    pending: list[Block] = []
    for block in blocks:
        if isinstance(block, Junk):
            if block.raw.strip():
                pending.append(block)
            continue
        if isinstance(block, ExplicitComment):
            pending.append(block)
            continue
        units.append(_Unit(prefixes=pending, block=block))
        pending = []
    if pending:
        units.append(_Unit(prefixes=pending, block=None))
    return units


def _order_units(units: Sequence[_Unit], options: FormatOptions) -> list[_Unit]:
    """Order units: preambles, strings, entries, trailing prose."""
    preambles: list[_Unit] = []
    strings: list[_Unit] = []
    entries: list[_Unit] = []
    trailing: list[_Unit] = []
    for unit in units:
        if unit.block is None:
            trailing.append(unit)
        elif isinstance(unit.block, Preamble):
            preambles.append(unit)
        elif isinstance(unit.block, StringDef):
            strings.append(unit)
        else:
            entries.append(unit)
    malformed = [
        (index, unit)
        for index, unit in enumerate(entries)
        if isinstance(unit.block, Malformed)
    ]
    ordered = [unit for unit in entries if isinstance(unit.block, Entry)]
    if options.sort_entries:
        ordered.sort(key=lambda unit: sort_key(unit.block))
    for index, unit in malformed:
        ordered.insert(index, unit)
    return [*preambles, *strings, *ordered, *trailing]


def _render_unit(unit: _Unit, options: FormatOptions) -> str:
    """Render a unit: its prefixes then its block, one per line."""
    blocks = [*unit.prefixes, unit.block] if unit.block is not None else unit.prefixes
    return "\n".join(render_block(block, options) for block in blocks)
