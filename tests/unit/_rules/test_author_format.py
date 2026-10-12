from __future__ import annotations

import pytest

from tests.helpers import apply_rule

NAME = "author-format"


def test_detection() -> None:
    """Test that a name with three commas is reported and left untouched."""
    source = "@misc{k,\n  author = {Dongarra, Jack, London, Kevin}\n}\n"
    rows, output = apply_rule(NAME, source)
    message = (
        "name 'Dongarra, Jack, London, Kevin' in field 'author' has more than two "
        "commas, separate the names with 'and'"
    )
    assert rows == [(2, 3, message, False)]
    assert "author = {Dongarra, Jack, London, Kevin}" in output


def test_each_name_is_checked() -> None:
    """Test the split on 'and' in any case, outside braces only."""
    source = "@misc{k, EDITOR = {{A, B, C, D} and Doe, J. AND a, b, c, d}}\n"
    rows, _ = apply_rule(NAME, source)
    assert [row[2].split("'")[1] for row in rows] == ["a, b, c, d"]
    assert "in field 'editor'" in rows[0][2]


@pytest.mark.parametrize(
    "source",
    [
        "@misc{k, author = {von Last, Jr, First and Doe, John}}\n",
        "@misc{k, author = {{Barnes, Noble, and, Co}}}\n",
        "@misc{k, author = {a{ and }b, c, d and e}}\n",
        "@misc{k, title = {a, b, c, d}}\n",
        "@misc{k, author = a # {, b, c, d}}\n",
    ],
)
def test_no_finding(source: str) -> None:
    """Test the values that the rule accepts or skips."""
    assert apply_rule(NAME, source)[0] == []
