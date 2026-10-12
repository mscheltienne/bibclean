from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "author-format"
SOURCE = "@misc{k,\n  author = {Dongarra, Jack, London, Kevin}\n}\n"


def test_detection(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a name with three commas is reported and left untouched."""
    rows, output = apply_rule(NAME, SOURCE)
    message = (
        "name 'Dongarra, Jack, London, Kevin' in field 'author' has more than two "
        "commas, separate the names with 'and'"
    )
    assert rows == [(2, 3, message, False)]
    assert "author = {Dongarra, Jack, London, Kevin}" in output


def test_each_name_is_checked(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
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
def test_no_finding(
    apply_rule: Callable[..., tuple[list[Any], str]], source: str
) -> None:
    """Test the values that the rule accepts or skips."""
    rows, _ = apply_rule(NAME, source)
    assert rows == []


def test_exclude(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded entry is exempt."""
    rows, _ = apply_rule(NAME, SOURCE, config(exclude=frozenset({"k"})))
    assert rows == []


def test_ignore(
    rules_reported: Callable[..., list[str]], config: Callable[..., Config]
) -> None:
    """Test that the rule can be disabled."""
    assert NAME in rules_reported(SOURCE)
    assert NAME not in rules_reported(SOURCE, config(ignore=frozenset({NAME})))
