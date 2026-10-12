from __future__ import annotations

import pytest

from bibclean._config import FormatOptions
from bibclean._formatter import (
    collapse_whitespace,
    format_blocks,
    render_block,
    render_entry,
    render_value,
)
from bibclean._model import Entry
from bibclean._parser import parse

DEFAULTS = FormatOptions()


def _first_entry(source: str) -> Entry:
    entry = parse(source)[0]
    assert isinstance(entry, Entry)
    return entry


def _first_value(source: str) -> str:
    return render_value(_first_entry(source).fields[0].value)


@pytest.mark.parametrize(
    ("text", "expected"),
    [("a  b", "a b"), ("a\n\tb", "a b"), ("", ""), (" ", " ")],
)
def test_collapse_whitespace(text: str, expected: str) -> None:
    """Test the collapse of whitespace runs."""
    assert collapse_whitespace(text) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("@misc{k, a = {x}}", "{x}"),
        ("@misc{k, a = { x  y }}", "{x y}"),
        ('@misc{k, a = "x"}', "{x}"),
        ("@misc{k, a = 2024}", "{2024}"),
        ("@misc{k, a = jan}", "jan"),
        ("@misc{k, a = JAN}", "JAN"),
        ('@misc{k, a = acm # " Press"}', "acm # { Press}"),
        ('@misc{k, a = " x " # acm}', "{x } # acm"),
        ('@misc{k, a = {  x } # " y  "}', "{x } # { y}"),
        ("@misc{k, a = {}}", "{}"),
        ("@misc{k, a = {A {Title} With    Braces}}", "{A {Title} With Braces}"),
    ],
)
def test_render_value(source: str, expected: str) -> None:
    """Test the rendering of every value form."""
    assert _first_value(source) == expected


def test_render_block_kinds() -> None:
    """Test the rendering of each block kind."""
    blocks = parse(
        "% prose  \n"
        '@preamble{"\\x"}\n'
        '@string(a = "b")\n'
        "@comment(un{balanced)\n"
        "@misc{k, a = {b}}\n"
    )
    rendered = [render_block(block, DEFAULTS) for block in blocks]
    assert "% prose" in rendered
    assert "@preamble{{\\x}}" in rendered
    assert "@string{a = {b}}" in rendered
    assert "@comment(un{balanced)" in rendered
    assert "@misc{k,\n  a = {b}\n}" in rendered


def test_string_value_keeps_outer_whitespace() -> None:
    """Test that a macro value keeps the spaces a concatenation relies on."""
    (block,) = parse('@string{stoc = "  Symposium  on  Theory "}')
    assert render_block(block, DEFAULTS) == "@string{stoc = { Symposium on Theory }}"


def test_render_entry() -> None:
    """Test the entry head, the body lines and the closing delimiter."""
    entry = _first_entry("@Article{Key,\n  Year = 2020,\n  author = {A}\n}")
    assert render_entry(entry, DEFAULTS) == (
        "@article{Key,\n  author = {A},\n  year = {2020}\n}"
    )


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        (FormatOptions(indent=4), "@misc{k,\n    author = {A},\n    year = {2020}\n}"),
        (
            FormatOptions(indent="tab"),
            "@misc{k,\n\tauthor = {A},\n\tyear = {2020}\n}",
        ),
        (
            FormatOptions(trailing_comma=True),
            "@misc{k,\n  author = {A},\n  year = {2020},\n}",
        ),
        (
            FormatOptions(sort_fields=False),
            "@misc{k,\n  year = {2020},\n  author = {A}\n}",
        ),
        (
            FormatOptions(sort_fields=("year", "absent", "year")),
            "@misc{k,\n  year = {2020},\n  author = {A}\n}",
        ),
    ],
)
def test_entry_options(options: FormatOptions, expected: str) -> None:
    """Test each formatting option in isolation."""
    entry = _first_entry("@misc{k,\n  year = 2020,\n  author = {A}\n}")
    assert render_entry(entry, options) == expected


def test_align_values() -> None:
    """Test that alignment pads the lowercased keys."""
    entry = _first_entry("@misc{k,\n  year = 2020,\n  author = jan\n}")
    assert render_entry(entry, FormatOptions(align_values=True)) == (
        "@misc{k,\n  author = jan,\n  year   = {2020}\n}"
    )


def test_entry_without_fields() -> None:
    """Test entries with no field, with and without a trailing comma."""
    entry = _first_entry("@misc{k}\n")
    assert render_entry(entry, DEFAULTS) == "@misc{k\n}"
    assert render_entry(entry, FormatOptions(trailing_comma=True)) == "@misc{k,\n}"


def test_sort_entries() -> None:
    """Test the case-insensitive stable sort of the entries."""
    source = "@misc{b, a = {1}}\n\n@misc{A, a = {2}}\n\n@misc{a, a = {3}}\n"
    ordered = format_blocks(parse(source), DEFAULTS)
    assert [line for line in ordered.splitlines() if line.startswith("@")] == [
        "@misc{A,",
        "@misc{a,",
        "@misc{b,",
    ]
    kept = format_blocks(parse(source), FormatOptions(sort_entries=False))
    assert [line for line in kept.splitlines() if line.startswith("@")] == [
        "@misc{b,",
        "@misc{A,",
        "@misc{a,",
    ]


def test_sort_entries_crossref_targets_last() -> None:
    """Test that the entries a crossref points to follow every other entry."""
    source = (
        "@proceedings{Proc, title = {P}}\n@misc{z, crossref = {proc}}\n"
        "@book{a, title = {B}}\n@misc{b, crossref = {A}}\n"
    )
    ordered = format_blocks(parse(source), DEFAULTS)
    heads = [line for line in ordered.splitlines() if line.startswith("@")]
    assert heads == ["@misc{b,", "@misc{z,", "@book{a,", "@proceedings{Proc,"]


def test_block_order() -> None:
    """Test that strings and preambles keep their order, before entries and prose."""
    source = (
        "@misc{k, a = {1}}\n\n@string{s = {S}}\n\n@preamble{s # {x}}\n\n"
        "@string{t = {T}}\n\ntrailing prose\n"
    )
    assert format_blocks(parse(source), DEFAULTS) == (
        "@string{s = {S}}\n\n@preamble{s # {x}}\n\n@string{t = {T}}\n\n"
        "@misc{k,\n  a = {1}\n}\n\ntrailing prose\n"
    )


def test_blank_lines_in_free_text() -> None:
    """Test that runs of blank lines inside free text collapse to one."""
    source = "% a  \n\n \n\t\n% b\n\n% c\n@misc{k, a = {1}}\n"
    once = format_blocks(parse(source), DEFAULTS)
    assert once == "% a  \n\n% b\n\n% c\n@misc{k,\n  a = {1}\n}\n"
    assert format_blocks(parse(once), DEFAULTS) == once


def test_comments_travel_with_the_next_block() -> None:
    """Test that prose and comments stick to the block below them."""
    source = "@misc{z, a = {1}}\n\n% note\n@comment{c}\n@misc{a, a = {2}}\n"
    assert format_blocks(parse(source), DEFAULTS) == (
        "% note\n@comment{c}\n@misc{a,\n  a = {2}\n}\n\n@misc{z,\n  a = {1}\n}\n"
    )


@pytest.mark.parametrize("source", ["", "   \n\n\t\n"])
def test_empty_files(source: str) -> None:
    """Test that an empty or whitespace-only file renders as nothing."""
    assert format_blocks(parse(source), DEFAULTS) == ""


def test_comments_only_file() -> None:
    """Test that a file of comments renders them once."""
    assert format_blocks(parse("\n% a\n% b\n\n"), DEFAULTS) == "% a\n% b\n"
