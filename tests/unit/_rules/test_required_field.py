from __future__ import annotations

import pytest

from tests.helpers import apply_rule

NAME = "required-field"


def _missing(source: str) -> list[str]:
    """List the missing field names reported for a source."""
    return [row[2].rsplit("'", 2)[1] for row in apply_rule(NAME, source)[0]]


def test_detection() -> None:
    """Test that a missing field is reported at the opening character."""
    source = "@article{k,\n  author = {A},\n  title = {T},\n  year = {2021}\n}\n"
    rows, _ = apply_rule(NAME, source)
    assert rows == [(1, 1, "@article 'k' is missing required field 'journal'", False)]


def test_alternative_is_reported_as_written() -> None:
    """Test that the message lists the alternative as written."""
    source = "@book{k, publisher = {P}, title = {T}, year = {1984}}\n"
    assert _missing(source) == ["author|editor"]


def test_order_follows_the_table() -> None:
    """Test that findings follow the order of the required list."""
    assert _missing("@article{k, volume = {1}}\n") == [
        "author",
        "journal",
        "title",
        "year",
    ]


def test_crossref_missing_target() -> None:
    """Test that a crossref without target inherits nothing."""
    source = "@inproceedings{c, author = {A}, title = {T}, crossref = {p}}\n"
    assert _missing(source) == ["booktitle", "year"]


@pytest.mark.parametrize(
    "source",
    [
        "@book{k, editor = {E}, publisher = {P}, title = {T}, year = {1984}}\n",
        "@inproceedings{c, author = {A}, title = {T}, crossref = {P}}\n\n"
        "@proceedings{p, booktitle = {B}, title = {B}, year = {2000}}\n",
        "@weird{k, a = {1}}\n",
        "@ARTICLE{k, AUTHOR = {A}, Journal = {J}, title = {T}, year = {2021}}\n",
    ],
    ids=["alternative", "crossref", "unknown-type", "case-insensitive"],
)
def test_no_finding(source: str) -> None:
    """Test the entries that satisfy their table or have none."""
    assert apply_rule(NAME, source)[0] == []
