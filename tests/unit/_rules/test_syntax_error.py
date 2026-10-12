from __future__ import annotations

from tests.helpers import apply_rule, lint_config

NAME = "syntax-error"
SOURCE = "@misc{good, a = {1}}\n\n@misc{bad, a = {1\n\n@misc{last, a = {2}}\n"


def test_detection() -> None:
    """Test that a malformed block is reported at its opening character."""
    rows, output = apply_rule(NAME, SOURCE)
    assert len(rows) == 1
    line, column, message, fixable = rows[0]
    assert (line, column, fixable) == (3, 1, False)
    assert message.startswith("entry 'bad' could not be parsed:")
    assert "@misc{bad, a = {1" in output


def test_no_finding() -> None:
    """Test that a readable file reports nothing."""
    assert apply_rule(NAME, "@misc{k, a = {1}}\n")[0] == []


def test_exclude_does_not_apply() -> None:
    """Test that a malformed block has no key or type to exempt it."""
    config = lint_config(exclude=frozenset({"bad"}), exclude_types=frozenset({"misc"}))
    assert len(apply_rule(NAME, SOURCE, config)[0]) == 1
