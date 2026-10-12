from __future__ import annotations

import pytest

from bibclean._model import Part
from bibclean._rules.month_format import month_target
from tests.helpers import apply_rule, lint_config

NAME = "month-format"
SOURCE = "@article{k,\n  month = {September}\n}\n"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("jan", "January"),
        ("JAN", "January"),
        ("{Sep.}", "September"),
        ("{SEPTEMBER}", "September"),
        ("{ Sep }", "September"),
        ("{9}", "September"),
        ("{09}", "September"),
        ("12", "December"),
        ("{13}", None),
        ("{0}", None),
        ("{Sept}", None),
        ("{September.}", None),
        ("{Sept-Oct}", None),
    ],
)
def test_recognised_forms(text: str, expected: str | None) -> None:
    """Test every recognised and unrecognised month form."""
    source = "@misc{k, month = " + text + "}\n"
    rows, output = apply_rule(NAME, source, lint_config(month="name"))
    assert [row[3] for row in rows] == [expected is not None]
    if expected is not None:
        assert "month = {" + expected + "}" in output


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
        ("abbreviation", SOURCE, "month '{September}' should be 'sep'", "month = sep"),
        (
            "name",
            "@article{k,\n  month = sep\n}\n",
            "month 'sep' should be '{September}'",
            "month = {September}",
        ),
        ("number", SOURCE, "month '{September}' should be '{9}'", "month = {9}"),
    ],
)
def test_detection(mode: str, source: str, message: str, rendered: str) -> None:
    """Test the message and the rewritten value in each mode."""
    rows, output = apply_rule(NAME, source, lint_config(month=mode))
    assert rows == [(2, 3, message, True)]
    assert rendered in output


def test_already_canonical() -> None:
    """Test that a value already in the target form reports nothing."""
    assert apply_rule(NAME, "@article{k, month = sep}\n")[0] == []


def test_unrecognised() -> None:
    """Test that an unknown month is reported and left untouched."""
    rows, output = apply_rule(NAME, "@article{k,\n  month = {Sept-Oct}\n}\n")
    assert rows == [(2, 3, "unrecognised month '{Sept-Oct}'", False)]
    assert "month = {Sept-Oct}" in output


@pytest.mark.parametrize("value", ["jan # {~15}", 'jan # "-" # feb'])
def test_concatenation_skipped(value: str) -> None:
    """Test that a concatenated value is not inspected."""
    rows, output = apply_rule(NAME, "@article{k, month = " + value + "}\n")
    assert rows == []
    assert "month = jan # {" in output
