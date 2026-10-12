from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bibclean._model import Part, collapse_whitespace, crossref_target
from bibclean._parser import parse

if TYPE_CHECKING:
    from bibclean._model import Kind


@pytest.mark.parametrize(
    ("kind", "text", "expected"),
    [
        ("bare", "acm", True),
        ("bare", "jan2", True),
        ("bare", "2024", False),
        ("bare", "²", True),
        ("braced", "acm", False),
        ("quoted", "acm", False),
    ],
)
def test_part_is_macro(kind: Kind, text: str, expected: bool) -> None:
    """Test that only a bare part not made of ASCII digits is a macro."""
    assert Part(kind, text).is_macro is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [("a  b", "a b"), ("a\n\tb", "a b"), ("", ""), (" ", " ")],
)
def test_collapse_whitespace(text: str, expected: str) -> None:
    """Test the collapse of whitespace runs."""
    assert collapse_whitespace(text) == expected


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ("crossref = { Proc\n2020 }, CrossRef = {other}", "proc 2020"),
        ("title = {T}", None),
        ("crossref = {}", None),
        ("crossref = proc", None),
        ('crossref = "a" # "b"', None),
    ],
)
def test_crossref_target(fields: str, expected: str | None) -> None:
    """Test that the target is the lowercased text of the first crossref field."""
    assert crossref_target(parse(f"@misc{{k, {fields}}}")[0]) == expected
