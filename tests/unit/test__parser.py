from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pytest

from bibclean._model import (
    Block,
    Entry,
    ExplicitComment,
    Junk,
    Malformed,
    Position,
    Preamble,
    StringDef,
)
from bibclean._parser import LineIndex, parse

if TYPE_CHECKING:
    from pathlib import Path

_CONSTRUCTS = (
    "@article{key{index},\n  author = {A, B},\n  year = 2020\n}\n",
    '@misc{k{index}, title = "A {Braced} title", note = a # " b" # {c}}\n',
    "@string{s{index} = {value}}\n",
    "@preamble{{\\newcommand{\\x}[1]{}}}\n",
    "@comment{a {nested} comment}\n",
    "@article(p{index}, a = 1)\n",
    "% a comment line with me@example.org\n",
    "some prose\n",
    "\n",
    "@misc{t{index},}\n",
    "@misc{e{index}}\n",
)


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def _assets(assets: Path) -> list[Path]:
    return sorted(assets.rglob("*.bib"))


def test_line_index() -> None:
    """Test the conversion of offsets into positions."""
    index = LineIndex("ab\ncd\n")
    assert index.position(0) == Position(1, 1)
    assert index.position(2) == Position(1, 3)
    assert index.position(3) == Position(2, 1)
    assert index.position(6) == Position(3, 1)


def test_round_trip(assets: Path) -> None:
    """Test that the raw text of the blocks reproduces every asset."""
    files = _assets(assets)
    assert files
    for path in files:
        source = _read(path)
        blocks = parse(source)
        assert "".join(block.raw for block in blocks) == source, path
        assert all(isinstance(block, Block) for block in blocks)


def test_round_trip_property() -> None:
    """Test the round trip on generated files mixing every construct."""
    rng = random.Random(0)
    for index in range(200):
        parts = [
            rng.choice(_CONSTRUCTS).replace("{index}", str(index))
            for _ in range(rng.randint(1, 8))
        ]
        source = "".join(parts)
        if rng.random() < 0.3 and "}" in source:
            cut = rng.randrange(source.count("}")) + 1
            head, _, tail = _split_nth(source, "}", cut)
            source = head + tail
        blocks = parse(source)
        assert "".join(block.raw for block in blocks) == source
        assert all(
            isinstance(
                block, Junk | Preamble | StringDef | ExplicitComment | Entry | Malformed
            )
            for block in blocks
        )


def _split_nth(text: str, char: str, count: int) -> tuple[str, str, str]:
    start = -1
    for _ in range(count):
        start = text.index(char, start + 1)
    return text[:start], char, text[start + 1 :]


def test_malformed_message(assets: Path) -> None:
    """Test the message and the position of the malformed example."""
    source = _read(assets / "malformed.bib")
    blocks = parse(source)
    assert [type(block).__name__ for block in blocks] == [
        "Entry",
        "Junk",
        "Malformed",
        "Entry",
        "Junk",
    ]
    malformed = blocks[2]
    assert isinstance(malformed, Malformed)
    assert malformed.start == Position(8, 1)
    assert malformed.error == Position(14, 1)
    expected = _read(assets / "malformed.check.txt").splitlines()[0]
    assert malformed.message == expected.split("syntax-error ", 1)[1]
    assert malformed.raw.startswith("@article{broken_entry,")
    assert malformed.raw.endswith("}\n\n")


def test_positions(assets: Path) -> None:
    """Test the positions of an entry and of its tab-indented fields."""
    blocks = parse(_read(assets / "zotero-export.bib"))
    entry = blocks[1]
    assert isinstance(entry, Entry)
    assert entry.start == Position(2, 1)
    assert [field.start.column for field in entry.fields] == [2] * len(entry.fields)
    assert entry.fields[0].start.line == 3
    assert entry.fields[-1].start.line == 17


def test_delimiters() -> None:
    """Test that parenthesis-delimited blocks parse."""
    blocks = parse(
        '@article(k, a = 1)\n@string(a = "b")\n@preamble("x")\n@comment(y)\n'
    )
    kinds = [block for block in blocks if not isinstance(block, Junk)]
    entry, string, preamble, comment = kinds
    assert isinstance(entry, Entry)
    assert entry.delimiter == "("
    assert entry.fields[0].value.parts[0].text == "1"
    assert isinstance(string, StringDef)
    assert string.value.parts[0].kind == "quoted"
    assert isinstance(preamble, Preamble)
    assert isinstance(comment, ExplicitComment)
    assert comment.delimiter == "("
    assert comment.body == "y"


def test_values() -> None:
    """Test every value form."""
    source = (
        "@misc{k,\n"
        "  a = {nested {braces} and \\{escaped\\}},\n"
        '  b = "quoted {with} \\" inner",\n'
        "  c = macro,\n"
        "  d = 2024,\n"
        '  e = a # "b" # {c},\n'
        "}\n"
    )
    entry = parse(source)[0]
    assert isinstance(entry, Entry)
    assert entry.trailing_comma is True
    values = {field.key: field.value for field in entry.fields}
    assert values["a"].parts[0].text == "nested {braces} and \\{escaped\\}"
    assert values["b"].parts[0].kind == "quoted"
    assert values["b"].parts[0].text == 'quoted {with} \\" inner'
    assert values["c"].parts[0].kind == "bare"
    assert values["d"].parts[0].text == "2024"
    assert [part.kind for part in values["e"].parts] == ["bare", "quoted", "braced"]


def test_entry_without_fields() -> None:
    """Test entries with no field and with a trailing comma only."""
    plain = parse("@misc{k}\n")[0]
    comma = parse("@misc{k,}\n")[0]
    assert isinstance(plain, Entry)
    assert isinstance(comma, Entry)
    assert plain.fields == []
    assert plain.trailing_comma is False
    assert comma.fields == []
    assert comma.trailing_comma is True


@pytest.mark.parametrize(
    ("source", "reason", "error"),
    [
        ("@{k}\n", "expected an entry type after '@'", Position(1, 2)),
        ("@article k}\n", "expected '{' or '(' after '@article'", Position(1, 10)),
        ("@string{= {x}}\n", "expected a string name", Position(1, 9)),
        ("@string{a {x}}\n", "expected '=' after string name 'a'", Position(1, 11)),
        ("@string{a = {x} y}\n", "expected '}' after string 'a'", Position(1, 17)),
        ("@preamble{{x} y}\n", "expected '}' after preamble", Position(1, 15)),
        ("@article{,}\n", "expected a cite key", Position(1, 10)),
        (
            "@article{k x}\n",
            "expected ',' or '}' after cite key 'k'",
            Position(1, 12),
        ),
        ("@article{k, = {x}}\n", "expected a field name", Position(1, 13)),
        (
            "@article{k, title {x}}\n",
            "expected '=' after field 'title'",
            Position(1, 19),
        ),
        (
            "@article{k, title = ,}\n",
            "expected a value for field 'title'",
            Position(1, 21),
        ),
        (
            "@article{k, title = {x\n",
            "unexpected end of file in field 'title'",
            Position(2, 1),
        ),
        (
            '@article{k, title = "a}b"}\n',
            "unbalanced '}' in field 'title'",
            Position(1, 23),
        ),
        ("@comment{abc\n", "unterminated @comment", Position(2, 1)),
        ("@comment(a}b)\n", "unbalanced '}' in @comment", Position(1, 11)),
    ],
)
def test_errors(source: str, reason: str, error: Position) -> None:
    """Test every failure reason, its position and its recovery."""
    blocks = parse(source)
    malformed = blocks[0]
    assert isinstance(malformed, Malformed)
    assert reason in malformed.message
    assert malformed.error == error
    assert f"at line {error.line}, column {error.column}" in malformed.message
    assert "".join(block.raw for block in blocks) == source


def test_error_names_the_entry() -> None:
    """Test that a failure after the cite key names the entry."""
    malformed = parse("@article{k, title = {x\n")[0]
    assert isinstance(malformed, Malformed)
    assert malformed.message.startswith("entry 'k' could not be parsed:")


def test_error_names_the_block() -> None:
    """Test the wording when neither a key nor a type could be read."""
    malformed = parse("@{k}\n")[0]
    assert isinstance(malformed, Malformed)
    assert malformed.message.startswith("block could not be parsed:")
    typed = parse("@string{= {x}}\n")[0]
    assert isinstance(typed, Malformed)
    assert typed.message.startswith("@string block could not be parsed:")


def test_recovery() -> None:
    """Test that the scan resumes at the next block after a failure."""
    source = "% prose\n@misc{a, x = {y\n\n@misc{b,\n  x = {y}\n}\n"
    blocks = parse(source)
    assert [type(block).__name__ for block in blocks] == [
        "Junk",
        "Malformed",
        "Entry",
        "Junk",
    ]
    assert blocks[1].raw == "@misc{a, x = {y\n\n"
    assert isinstance(blocks[2], Entry)
    assert blocks[2].key == "b"


def test_at_in_junk() -> None:
    """Test that an '@' that does not start a line is junk."""
    blocks = parse("% mail me@x.org\n@misc{k,\n}\n")
    assert [type(block).__name__ for block in blocks] == ["Junk", "Entry", "Junk"]
    single = parse("foo @misc{k}\n")
    assert [type(block).__name__ for block in single] == ["Junk"]
    indented = parse("  @misc{k}\n")
    assert [type(block).__name__ for block in indented] == ["Junk", "Entry", "Junk"]


def test_comment_nested_braces(assets: Path) -> None:
    """Test that a comment body keeps its nested braces."""
    blocks = parse(_read(assets / "blocks.bib"))
    comment = next(block for block in blocks if isinstance(block, ExplicitComment))
    assert comment.body == "Entries exported from Zotero, see the wiki for {details}."


def test_empty_source() -> None:
    """Test that an empty source yields no block."""
    assert parse("") == []


def test_sources_without_a_final_newline() -> None:
    """Test the scan and the recovery when the file has no trailing newline."""
    assert [type(block).__name__ for block in parse("@misc{k}tail")] == [
        "Entry",
        "Junk",
    ]
    assert [type(block).__name__ for block in parse("a\nb")] == ["Junk"]
    trailing = parse("@misc{k, a = {b")
    assert isinstance(trailing[0], Malformed)
    assert trailing[0].raw == "@misc{k, a = {b"
    prose = parse("@misc{k, a = {b\nplain")
    assert isinstance(prose[0], Malformed)
    assert prose[0].raw == "@misc{k, a = {b\nplain"
