from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "duplicate-field"
SAME = '@article{k,\n  title = {Other},\n  TITLE = "Other"\n}\n'
DIFFERENT = "@article{k,\n  title = {Other},\n  title = {Another}\n}\n"


def test_same_value_is_removed(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that a repeat with the same value is removed."""
    rows, output = apply_rule(NAME, SAME)
    assert rows == [(3, 3, "field 'title' is defined twice with the same value", True)]
    assert output.count("title") == 1


def test_different_value_is_reported(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that a repeat with another value is kept and reported."""
    rows, output = apply_rule(NAME, DIFFERENT)
    assert rows == [
        (3, 3, "field 'title' is defined twice with different values", False)
    ]
    assert output.count("title") == 2


def test_three_occurrences(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that every repeat is compared with the first occurrence."""
    source = "@misc{k,\n  a = {1},\n  a = {2},\n  a = {1}\n}\n"
    rows, output = apply_rule(NAME, source)
    assert [(row[0], row[3]) for row in rows] == [(3, False), (4, True)]
    assert output.count("a = ") == 2


def test_no_finding(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that distinct field names report nothing."""
    rows, _ = apply_rule(NAME, "@misc{k, a = {1}, b = {1}}\n")
    assert rows == []


def test_exclude(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded entry is exempt."""
    rows, _ = apply_rule(NAME, SAME, config(exclude=frozenset({"k"})))
    assert rows == []


def test_exclude_types(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded entry type is exempt."""
    rows, _ = apply_rule(NAME, SAME, config(exclude_types=frozenset({"article"})))
    assert rows == []


def test_removal_runs_before_strip_field(
    rules_reported: Callable[..., list[str]],
) -> None:
    """Test that the repeat is gone before strip-field looks at the entry."""
    source = "@article{k,\n  issn = {1},\n  issn = {1}\n}\n"
    reported = rules_reported(source)
    assert reported.count("strip-field") == 1
    assert reported.count(NAME) == 1


def test_ignore(
    rules_reported: Callable[..., list[str]], config: Callable[..., Config]
) -> None:
    """Test that the rule can be disabled."""
    assert NAME in rules_reported(SAME)
    assert NAME not in rules_reported(SAME, config(ignore=frozenset({NAME})))
