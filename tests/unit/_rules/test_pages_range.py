from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "pages-range"
SOURCE = "@article{k,\n  pages = {4101-4105}\n}\n"


@pytest.mark.parametrize(
    ("text", "target"),
    [
        ("181–197", "181--197"),
        ("181—197", "181--197"),
        ("4101-4105", "4101--4105"),
        ("1 -- 10", "1--10"),
        ("1---10", "1--10"),
    ],
)
def test_detection(
    apply_rule: Callable[..., tuple[list[Any], str]], text: str, target: str
) -> None:
    """Test every dash and spacing form."""
    rows, output = apply_rule(NAME, "@article{k,\n  pages = {" + text + "}\n}\n")
    assert rows == [(2, 3, f"page range '{text}' should use '--'", True)]
    assert f"pages = {{{target}}}" in output


@pytest.mark.parametrize(
    "text",
    ["1--10", "4484", "e12--e19", "S1-S9", "1, 2", "1-2-3"],
)
def test_no_finding(
    apply_rule: Callable[..., tuple[list[Any], str]], text: str
) -> None:
    """Test the values that are left untouched."""
    rows, _ = apply_rule(NAME, "@article{k, pages = {" + text + "}}\n")
    assert rows == []


def test_macro_is_skipped(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a value that is not a single text is skipped."""
    rows, _ = apply_rule(NAME, '@article{k, pages = a # "1-2"}\n')
    assert rows == []


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
