from __future__ import annotations

import pytest

from bibclean._model import (
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
    entry_type,
    field_name,
    is_whitespace,
)


def test_position_order() -> None:
    """Test that positions compare by line then column."""
    assert Position(1, 1) < Position(1, 2) < Position(2, 1)
    assert Position(3, 4) == Position(3, 4)
    assert sorted([Position(2, 1), Position(1, 9)]) == [Position(1, 9), Position(2, 1)]


def test_entry() -> None:
    """Test the construction of an entry and of its fields."""
    field = Field(key="Title", value=Value([Part("braced", "x")]), start=Position(2, 3))
    entry = Entry(
        start=Position(1, 1),
        raw="@Article{k,\n  Title = {x}\n}",
        entry_type="Article",
        key="k",
        fields=[field],
        delimiter="{",
        trailing_comma=False,
    )
    assert entry_type(entry) == "article"
    assert field_name(entry.fields[0]) == "title"
    assert entry.fields[0].value.parts[0].kind == "braced"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("", True), ("  \n\t", True), ("% x", False), ("a", False)],
)
def test_is_whitespace(raw: str, expected: bool) -> None:
    """Test the detection of whitespace-only blocks."""
    assert is_whitespace(Junk(start=Position(1, 1), raw=raw)) is expected


def test_other_blocks() -> None:
    """Test the construction of the remaining block kinds."""
    value = Value([Part("bare", "acm")])
    preamble = Preamble(start=Position(1, 1), raw="@preamble{acm}", value=value)
    string = StringDef(
        start=Position(1, 1), raw="@string{a = acm}", key="a", value=value
    )
    comment = ExplicitComment(
        start=Position(1, 1), raw="@comment{x}", body="x", delimiter="{"
    )
    malformed = Malformed(
        start=Position(1, 1), raw="@article{k", message="boom", error=Position(1, 11)
    )
    assert preamble.value is value
    assert string.key == "a"
    assert comment.delimiter == "{"
    assert malformed.error == Position(1, 11)
