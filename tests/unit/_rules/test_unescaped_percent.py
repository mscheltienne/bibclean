from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "unescaped-percent"
SOURCE = "@article{k,\n  title = {Filtering (50% of 90% of the signal)}\n}\n"


def test_detection(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that every unescaped percent is escaped and reported once."""
    rows, output = apply_rule(NAME, SOURCE)
    assert rows == [
        (
            2,
            3,
            "unescaped '%' in field 'title', pybtex drops the rest of the value",
            True,
        )
    ]
    assert "{Filtering (50\\% of 90\\% of the signal)}" in output


@pytest.mark.parametrize(
    "text",
    ["Filtering (50\\% of the signal)", "no percent here"],
)
def test_no_finding(
    apply_rule: Callable[..., tuple[list[Any], str]], text: str
) -> None:
    """Test that an already escaped or percent-free value is untouched."""
    rows, _ = apply_rule(NAME, "@article{k, title = {" + text + "}}\n")
    assert rows == []


def test_double_backslash_is_escaped(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that a percent behind an escaped backslash is still escaped."""
    rows, output = apply_rule(NAME, "@article{k, title = {a\\\\%b}}\n")
    assert len(rows) == 1
    assert "{a\\\\\\%b}" in output


def test_exempt_fields(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that url, doi and file keep their percent signs."""
    source = (
        "@article{k,\n  url = {https://x/a%2Fb},\n  doi = {10.1/a%2Fb},\n"
        "  file = {a%b}\n}\n"
    )
    rows, output = apply_rule(NAME, source)
    assert rows == []
    assert "\\%" not in output


def test_quoted_part(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a quoted part is escaped too, and a macro is skipped."""
    rows, output = apply_rule(NAME, '@article{k, title = jan # "50%"}\n')
    assert len(rows) == 1
    assert "jan # {50\\%}" in output


def test_exclude(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded entry is exempt."""
    rows, _ = apply_rule(NAME, SOURCE, config(exclude=frozenset({"k"})))
    assert rows == []


def test_exclude_types(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded entry type is exempt."""
    rows, _ = apply_rule(NAME, SOURCE, config(exclude_types=frozenset({"article"})))
    assert rows == []


def test_ignore(
    rules_reported: Callable[..., list[str]], config: Callable[..., Config]
) -> None:
    """Test that the rule can be disabled."""
    assert NAME in rules_reported(SOURCE)
    assert NAME not in rules_reported(SOURCE, config(ignore=frozenset({NAME})))
