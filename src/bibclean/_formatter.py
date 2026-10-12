from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bibclean._model import Block, Entry, Junk, Preamble, StringDef

if TYPE_CHECKING:
    from collections.abc import Sequence

    from bibclean._config import FormatOptions
    from bibclean._model import Field, Value

_WHITESPACE_RUN = re.compile(r"[ \t\n\r\f\v]+")
_BLANK_LINES = re.compile(r"\n(?:[ \t\r\f\v]*\n)+")
# whitespace and the zero width no-break space, which a byte order mark decodes to
_BLANK = " \t\n\r\f\v\N{BYTE ORDER MARK}"


@dataclass(slots=True)
class _Unit:
    """A block together with the comments and prose written directly above it.

    Parameters
    ----------
    prefixes : list of Block
        The free text written directly above the block.
    block : Block | None
        The block, None for the free text at the end of a file.
    """

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


def render_value(value: Value, *, strip: bool = True) -> str:
    """Render a value in canonical form.

    Parameters
    ----------
    value : Value
        Value to render.
    strip : bool
        Strip the whitespace at both ends of the value. A macro value keeps it,
        since a concatenation such as ``"ACM" # stoc`` relies on it.

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
    if strip and parts[0].kind != "bare":
        texts[0] = texts[0].lstrip()
    if strip and parts[-1].kind != "bare":
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
        value = render_value(block.value, strip=False)
        return "@string{" + block.key + " = " + value + "}"
    if isinstance(block, Preamble):
        return "@preamble{" + render_value(block.value) + "}"
    return _BLANK_LINES.sub("\n\n", block.raw.strip(_BLANK))


def format_blocks(blocks: Sequence[Block], options: FormatOptions) -> str:
    """Render a list of blocks as a canonical file.

    Parameters
    ----------
    blocks : sequence of Block
        Blocks to render, in source order, none of them malformed.
    options : FormatOptions
        Formatting options.

    Returns
    -------
    str
        The canonical text: strings and preambles in source order, then entries,
        one blank line between units and exactly one final newline. An input
        without any block renders as the empty string.
    """
    units = _order_units(_group_units(blocks), options)
    if not units:
        return ""
    return "\n\n".join(_render_unit(unit, options) for unit in units) + "\n"


def _sorted_fields(entry: Entry, options: FormatOptions) -> list[Field]:
    """Order the fields of an entry according to the options.

    Parameters
    ----------
    entry : Entry
        Entry whose fields are ordered.
    options : FormatOptions
        Formatting options, of which ``sort_fields`` is used.

    Returns
    -------
    list of Field
        The fields in source order, sorted by name, or with the names listed in
        ``sort_fields`` first, in that order, and the others sorted by name.
    """
    order = options.sort_fields
    if order is False:
        return list(entry.fields)
    if order is True:
        return sorted(entry.fields, key=lambda item: item.key.lower())
    rank = {name: i for i, name in enumerate(dict.fromkeys(n.lower() for n in order))}

    def key(item: Field) -> tuple[int, str]:
        """Return the sort key of a field.

        Parameters
        ----------
        item : Field
            Field to sort.

        Returns
        -------
        tuple of (int, str)
            The rank of the name in ``sort_fields``, then the name for the fields
            not listed there.
        """
        name = item.key.lower()
        if name in rank:
            return (rank[name], "")
        return (len(rank), name)

    return sorted(entry.fields, key=key)


def _group_units(blocks: Sequence[Block]) -> list[_Unit]:
    """Group blocks into units, dropping whitespace-only free text.

    Parameters
    ----------
    blocks : sequence of Block
        Blocks, in source order.

    Returns
    -------
    list of _Unit
        The units, in source order. Free text after the last block forms a unit
        without block.
    """
    units: list[_Unit] = []
    pending: list[Block] = []
    for block in blocks:
        if isinstance(block, Junk):
            if block.raw.strip(_BLANK):
                pending.append(block)
            continue
        units.append(_Unit(prefixes=pending, block=block))
        pending = []
    if pending:
        units.append(_Unit(prefixes=pending, block=None))
    return units


def _order_units(units: Sequence[_Unit], options: FormatOptions) -> list[_Unit]:
    """Order units: strings and preambles, entries, trailing prose.

    Parameters
    ----------
    units : sequence of _Unit
        Units, in source order.
    options : FormatOptions
        Formatting options, of which ``sort_entries`` is used.

    Returns
    -------
    list of _Unit
        The ordered units. Only the entries are sorted, by cite key without case,
        every crossref target after the entries that are not, as BibTeX requires;
        the other groups keep their source order.
    """
    header: list[_Unit] = []
    entries: list[_Unit] = []
    trailing: list[_Unit] = []
    for unit in units:
        if unit.block is None:
            trailing.append(unit)
        elif isinstance(unit.block, Entry):
            entries.append(unit)
        else:
            header.append(unit)
    if options.sort_entries:
        targets = {
            field.value.parts[0].text.strip().lower()
            for unit in entries
            for field in unit.block.fields
            if field.key.lower() == "crossref" and len(field.value.parts) == 1
        }
        entries.sort(
            key=lambda unit: (unit.block.key.lower() in targets, unit.block.key.lower())
        )
    return [*header, *entries, *trailing]


def _render_unit(unit: _Unit, options: FormatOptions) -> str:
    """Render a unit: its prefixes then its block, one per line.

    Parameters
    ----------
    unit : _Unit
        Unit to render.
    options : FormatOptions
        Formatting options.

    Returns
    -------
    str
        The unit, without a trailing newline.
    """
    blocks = [*unit.prefixes, unit.block] if unit.block is not None else unit.prefixes
    return "\n".join(render_block(block, options) for block in blocks)
