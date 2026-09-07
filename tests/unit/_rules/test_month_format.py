from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bibclean._model import Part
from bibclean._parser import parse
from bibclean._rules.month_format import month_target, parse_month

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "month-format"
SOURCE = "@article{k,\n  month = {September}\n}\n"


def _value(text: str) -> Any:
    entry = parse("@misc{k, month = " + text + "}")[0]
    return entry.fields[0].value


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("jan", 1),
        ("{Sep.}", 9),
        ("{SEPTEMBER}", 9),
        ("{ Sep }", 9),
        ("{9}", 9),
        ("{09}", 9),
        ("12", 12),
        ("{13}", None),
        ("{0}", None),
        ("{Sept}", None),
        ("{Sept-Oct}", None),
        ('a # "b"', None),
    ],
)
def test_parse_month(text: str, expected: int | None) -> None:
    """Test every recognised and unrecognised month form."""
    assert parse_month(_value(text)) == expected


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("abbreviation", Part("bare", "sep")),
        ("name", Part("braced", "September")),
        ("number", Part("braced", "9")),
    ],
)
def test_month_target(mode: str, expected: Part) -> None:
    """Test the canonical part built for each mode."""
    assert month_target(9, mode) == expected


@pytest.mark.parametrize(
    ("mode", "source", "message", "rendered"),
    [
        (
            "abbreviation",
            SOURCE,
            "month 'September' should be the macro 'sep'",
            "month = sep",
        ),
        (
            "name",
            "@article{k,\n  month = sep\n}\n",
            "month 'sep' should be 'September'",
            "month = {September}",
        ),
        (
            "number",
            SOURCE,
            "month 'September' should be '9'",
            "month = {9}",
        ),
    ],
)
def test_detection(
    apply_rule: Callable[..., tuple[list[Any], str]],
    config: Callable[..., Config],
    mode: str,
    source: str,
    message: str,
    rendered: str,
) -> None:
    """Test the message and the rewritten value in each mode."""
    rows, output = apply_rule(NAME, source, config(month=mode))
    assert rows == [(2, 3, message, True)]
    assert rendered in output


def test_already_canonical(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a value already in the target form reports nothing."""
    rows, _ = apply_rule(NAME, "@article{k, month = sep}\n")
    assert rows == []


def test_unrecognised(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that an unknown month is reported and left untouched."""
    rows, output = apply_rule(NAME, "@article{k,\n  month = {Sept-Oct}\n}\n")
    assert rows == [(2, 3, "unrecognised month 'Sept-Oct'", False)]
    assert "month = {Sept-Oct}" in output


def test_unrecognised_concatenation(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that a concatenated value is reported as written."""
    rows, _ = apply_rule(NAME, '@article{k,\n  month = jan # "-" # feb\n}\n')
    assert rows == [(2, 3, "unrecognised month 'jan # {-} # feb'", False)]


def test_preserve(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that the preserve mode disables the rule."""
    rows, output = apply_rule(NAME, SOURCE, config(month="preserve"))
    assert rows == []
    assert "month = {September}" in output


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
