from __future__ import annotations

import random

import pytest

from bibclean._model import (
    Block,
    Entry,
    Junk,
    Malformed,
    Position,
    Preamble,
    StringDef,
)
from bibclean._parser import LineIndex, parse
from tests.helpers import ASSETS

_CONSTRUCTS = (
    "@article{key{index},\n  author = {A, B},\n  year = 2020\n}\n",
    '@misc{k{index}, title = "A {Braced} title", note = a # " b" # {c}}\n',
    "@string{s{index} = {value}}\n",
    "@preamble{{\\newcommand{\\x}[1]{}}}\n",
    "@comment{a {nested} comment}\n",
    "@article(p{index}, a = 1)\n",
    "% a comment line with me@example.org\n",
    "@comment{ a { b \n",
    "some prose\n",
    "\n",
    "@misc{t{index},}\n",
    "@misc{e{index}}\n",
)


def test_line_index() -> None:
    """Test the conversion of offsets into positions."""
    index = LineIndex("ab\ncd\n")
    assert index.position(0) == Position(1, 1)
    assert index.position(2) == Position(1, 3)
    assert index.position(3) == Position(2, 1)
    assert index.position(6) == Position(3, 1)


def test_round_trip() -> None:
    """Test that the raw text of the blocks reproduces every asset."""
    for path in sorted(ASSETS.glob("*.bib")):
        source = path.read_text(encoding="utf-8")
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
            isinstance(block, Junk | Preamble | StringDef | Entry | Malformed)
            for block in blocks
        )


def _split_nth(text: str, char: str, count: int) -> tuple[str, str, str]:
    start = -1
    for _ in range(count):
        start = text.index(char, start + 1)
    return text[:start], char, text[start + 1 :]


def test_delimiters() -> None:
    """Test that parenthesis-delimited blocks parse."""
    blocks = parse(
        '@article(k, a = 1)\n@string(a = "b")\n@preamble("x")\n@comment(y)\n'
    )
    kinds = [block for block in blocks if not isinstance(block, Junk)]
    entry, string, preamble = kinds
    assert isinstance(entry, Entry)
    assert entry.fields[0].value.parts[0].text == "1"
    assert isinstance(string, StringDef)
    assert string.value.parts[0].kind == "quoted"
    assert isinstance(preamble, Preamble)
    assert blocks[-1].raw == "@comment(y)\n"


def test_values() -> None:
    """Test every value form, '%' and '@' inside a value being part of it."""
    source = (
        "@misc{k,\n"
        "  a = {nested {braces} and \\{balanced\\}},\n"
        '  b = "quoted {with} {\\"} inner",\n'
        "  c = macro,\n"
        "  d = 2024,\n"
        '  e = a # "b" # {c},\n'
        "  f = {50% of me@example.org @misc{x}},\n"
        '  g = "50% of me@example.org",\n'
        "}\n"
    )
    blocks = parse(source)
    assert len(blocks) == 2
    entry = blocks[0]
    assert isinstance(entry, Entry)
    values = {field.key: field.value for field in entry.fields}
    assert values["f"].parts[0].text == "50% of me@example.org @misc{x}"
    assert values["g"].parts[0].text == "50% of me@example.org"
    assert values["a"].parts[0].text == "nested {braces} and \\{balanced\\}"
    assert values["b"].parts[0].kind == "quoted"
    assert values["b"].parts[0].text == 'quoted {with} {\\"} inner'
    assert values["c"].parts[0].kind == "bare"
    assert values["d"].parts[0].text == "2024"
    assert [part.kind for part in values["e"].parts] == ["bare", "quoted", "braced"]


@pytest.mark.parametrize(
    ("source", "key"),
    [
        ("@misc{Smith(2020), title = {A}}\n", "Smith(2020)"),
        ("@misc(Smith(2020, title = {A})\n", "Smith(2020"),
        ("@misc{key\xa0, title = {A}}\n", "key"),
    ],
)
def test_cite_key(source: str, key: str) -> None:
    """Test that parentheses belong to a key and that Unicode spaces are skipped."""
    entry = parse(source)[0]
    assert isinstance(entry, Entry)
    assert entry.key == key
    assert [field.key for field in entry.fields] == ["title"]


def test_entry_without_fields() -> None:
    """Test entries with no field and with a trailing comma only."""
    plain = parse("@misc{k}\n")[0]
    comma = parse("@misc{k,}\n")[0]
    assert isinstance(plain, Entry)
    assert isinstance(comma, Entry)
    assert plain.fields == []
    assert comma.fields == []


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
        (
            "@article{k\xa0x}\n",
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
        (
            "@comment this is junk\n",
            "expected '{' or '(' after '@comment'",
            Position(1, 10),
        ),
        (
            "@article{k, title = {a \\{ b}}\n",
            "expected ',' or '}' after field 'title'",
            Position(2, 1),
        ),
        (
            '@article{k, title = "Schr\\"odinger"}\n',
            "expected ',' or '}' after field 'title'",
            Position(1, 28),
        ),
        (
            '@article{k, month = jan"x"}\n',
            "expected ',' or '}' after field 'month'",
            Position(1, 24),
        ),
    ],
)
def test_errors(source: str, reason: str, error: Position) -> None:
    """Test every failure reason, its position and its recovery."""
    blocks = parse(source)
    malformed = blocks[0]
    assert isinstance(malformed, Malformed)
    assert reason in malformed.message
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


@pytest.mark.parametrize(
    ("source", "kinds"),
    [
        ("foo @misc{k}\n", ["Junk", "Entry", "Junk"]),
        ("  @misc{k}\n", ["Junk", "Entry", "Junk"]),
        ("% @misc{old, a = {1}}\n", ["Junk", "Entry", "Junk"]),
        ("% write to me@example.org\n", ["Junk", "Malformed"]),
        ("@misc{k} % note @x\n", ["Entry", "Junk", "Malformed"]),
        ("@misc{k, a = {b\n} @misc{j}\n", ["Malformed", "Entry", "Junk"]),
    ],
)
def test_every_at_starts_a_block(source: str, kinds: list[str]) -> None:
    """Test that every '@' outside a block starts a block, as in BibTeX and pybtex."""
    blocks = parse(source)
    assert [type(block).__name__ for block in blocks] == kinds
    assert all("@" not in block.raw for block in blocks if isinstance(block, Junk))


@pytest.mark.parametrize(
    "source", ["@comment{ a { b \n", "@Comment ( x } y\n", "@comment{x}\n"]
)
def test_comment(source: str) -> None:
    """Test that an @comment and the text after its delimiter are free text."""
    blocks = parse(source + "@misc{k}")
    assert [type(block).__name__ for block in blocks] == ["Junk", "Entry"]
    assert blocks[0].raw == source


@pytest.mark.parametrize(
    ("source", "kinds"),
    [
        (
            "@article{a, title={A}} @article{b, title={B}}\n",
            ["Entry", "Junk", "Entry", "Junk"],
        ),
        ("@comment{x}@string{s={S}}\n", ["Junk", "StringDef", "Junk"]),
        ("@misc{a}\t@misc{b,} @misc{c}", ["Entry", "Junk", "Entry", "Junk", "Entry"]),
    ],
)
def test_blocks_on_one_line(source: str, kinds: list[str]) -> None:
    """Test that a block right after another block on the same line is parsed."""
    assert [type(block).__name__ for block in parse(source)] == kinds


def test_zotero_file_field() -> None:
    """Test that backslashes in a Zotero file field do not affect brace counting."""
    value = "Paper.pdf:C\\:\\\\Users\\\\me\\\\Paper.pdf:application/pdf"
    entry = parse(f"@misc{{k,\n  file = {{{value}}}\n}}\n")[0]
    assert isinstance(entry, Entry)
    assert entry.fields[0].value.parts[0].text == value


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
