from __future__ import annotations

import pytest

from tests.helpers import apply_rule, rules_reported

NAME = "empty-field"


def test_detection() -> None:
    """Test that every empty value is removed and reported at its field key."""
    source = '@article{k,\n  volume = {},\n  note = {  },\n  number = "" # {},\n}\n'
    rows, output = apply_rule(NAME, source)
    assert rows == [
        (2, 3, "field 'volume' is empty", True),
        (3, 3, "field 'note' is empty", True),
        (4, 3, "field 'number' is empty", True),
    ]
    assert output == "@article{k\n}\n"


@pytest.mark.parametrize(
    "source",
    ["@misc{k, a = {x}}\n", "@misc{k, a = jan}\n", "@misc{k, a = {} # jan}\n"],
)
def test_no_finding(source: str) -> None:
    """Test the values that are not empty."""
    assert apply_rule(NAME, source)[0] == []


def test_removal_enables_required_field() -> None:
    """Test that a required field emptied out is reported as missing."""
    source = (
        "@article{k,\n  author = {},\n  journal = {J},\n  title = {T},\n"
        "  year = {2020}\n}\n"
    )
    reported = rules_reported(source)
    assert NAME in reported
    assert "required-field" in reported
