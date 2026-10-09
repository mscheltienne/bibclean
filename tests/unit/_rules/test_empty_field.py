from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "empty-field"
SOURCE = '@article{k,\n  volume = {},\n  note = {  },\n  number = "" # {},\n}\n'


def test_detection(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that every empty value is removed and reported at its field key."""
    rows, output = apply_rule(NAME, SOURCE)
    assert rows == [
        (2, 3, "field 'volume' is empty", True),
        (3, 3, "field 'note' is empty", True),
        (4, 3, "field 'number' is empty", True),
    ]
    assert output == "@article{k\n}\n"


@pytest.mark.parametrize(
    "source",
    [
        "@misc{k, a = {x}}\n",
        "@misc{k, a = jan}\n",
        "@misc{k, a = {} # jan}\n",
    ],
)
def test_no_finding(
    apply_rule: Callable[..., tuple[list[Any], str]], source: str
) -> None:
    """Test the values that are not empty."""
    rows, _ = apply_rule(NAME, source)
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


def test_removal_enables_required_field(
    rules_reported: Callable[..., list[str]],
) -> None:
    """Test that a required field emptied out is reported as missing."""
    source = (
        "@article{k,\n  author = {},\n  journal = {J},\n  title = {T},\n"
        "  year = {2020}\n}\n"
    )
    reported = rules_reported(source)
    assert NAME in reported
    assert "required-field" in reported


def test_ignore(
    rules_reported: Callable[..., list[str]], config: Callable[..., Config]
) -> None:
    """Test that the rule can be disabled."""
    assert NAME in rules_reported(SOURCE)
    assert NAME not in rules_reported(SOURCE, config(ignore=frozenset({NAME})))
