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
_BLANK_LINES = re.compile(r"\n(?:[ \t\r\f\v]*\n)+")
# whitespace and the zero width no-break space, which a byte order mark decodes to
_BLANK = " \t\n\r\f\v﻿"


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
        rendered.append(text if part.is_macro else "{" + text + "}")
    return " # ".join(rendered)


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
    width = max((len(f.key) for f in fields), default=0) if options.align_values else 0
    indent = "\t" if options.indent == "tab" else " " * options.indent
    lines = [head]
    for index, item in enumerate(fields):
        key = item.key.lower().ljust(width)
        last = index == len(fields) - 1
        comma = "," if not last or options.trailing_comma else ""
        lines.append(indent + key + " = " + render_value(item.value) + comma)
    lines.append("}")
    return "\n".join(lines)


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
        The block, without a trailing newline. Free text is stripped and every run
        of blank lines inside it is collapsed to one blank line.
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
    return _BLANK_LINES.sub("\n\n", block.raw.strip(_BLANK))


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
        The canonical text: strings and preambles in source order, then entries
        with the malformed blocks back at their original index, one blank line between
        units and exactly one final newline. An input without any block renders
        as the empty string.
    """
    units = _order_units(_group_units(blocks), options)
    if not units:
        return ""
    return "\n\n".join(_render_unit(unit, options) for unit in units) + "\n"


def _sorted_fields(entry: Entry, options: FormatOptions) -> list[Field]:
    """Order the fields of an entry according to the options."""
    order = options.sort_fields
    if order is False:
        return list(entry.fields)
    if order is True:
        return sorted(entry.fields, key=lambda item: item.key.lower())
    rank = {name: i for i, name in enumerate(dict.fromkeys(n.lower() for n in order))}

    def key(item: Field) -> tuple[int, str]:
        name = item.key.lower()
        if name in rank:
            return (rank[name], "")
        return (len(rank), name)

    return sorted(entry.fields, key=key)


def _group_units(blocks: Sequence[Block]) -> list[_Unit]:
    """Group blocks into units, dropping whitespace-only junk."""
    units: list[_Unit] = []
    pending: list[Block] = []
    for block in blocks:
        if isinstance(block, Junk):
            if block.raw.strip(_BLANK):
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
    """Order units: strings and preambles in source order, entries, trailing prose."""
    header: list[_Unit] = []
    entries: list[_Unit] = []
    trailing: list[_Unit] = []
    for unit in units:
        if unit.block is None:
            trailing.append(unit)
        elif isinstance(unit.block, Preamble | StringDef):
            header.append(unit)
        else:
            entries.append(unit)
    malformed = [
        (index, unit)
        for index, unit in enumerate(entries)
        if isinstance(unit.block, Malformed)
    ]
    ordered = [unit for unit in entries if isinstance(unit.block, Entry)]
    if options.sort_entries:
        ordered.sort(key=lambda unit: unit.block.key.lower())
    for index, unit in malformed:
        ordered.insert(index, unit)
    return [*header, *ordered, *trailing]


def _render_unit(unit: _Unit, options: FormatOptions) -> str:
    """Render a unit: its prefixes then its block, one per line."""
    blocks = [*unit.prefixes, unit.block] if unit.block is not None else unit.prefixes
    return "\n".join(render_block(block, options) for block in blocks)
