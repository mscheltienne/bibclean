from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "syntax-error"
SOURCE = "@misc{good, a = {1}}\n\n@misc{bad, a = {1\n\n@misc{last, a = {2}}\n"


def test_detection(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a malformed block is reported at its opening character."""
    rows, output = apply_rule(NAME, SOURCE)
    assert len(rows) == 1
    line, column, message, fixable = rows[0]
    assert (line, column, fixable) == (3, 1, False)
    assert message.startswith("entry 'bad' could not be parsed:")
    assert "@misc{bad, a = {1" in output


def test_no_finding(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a readable file reports nothing."""
    rows, _ = apply_rule(NAME, "@misc{k, a = {1}}\n")
    assert rows == []


def test_exclude_does_not_apply(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that a malformed block has no key or type to exempt it."""
    excluded = config(exclude=frozenset({"bad"}), exclude_types=frozenset({"misc"}))
    rows, _ = apply_rule(NAME, SOURCE, excluded)
    assert len(rows) == 1


def test_ignore(
    rules_reported: Callable[..., list[str]], config: Callable[..., Config]
) -> None:
    """Test that the rule can be disabled."""
    assert NAME in rules_reported(SOURCE)
    assert NAME not in rules_reported(SOURCE, config(ignore=frozenset({NAME})))
