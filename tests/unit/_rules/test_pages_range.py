from __future__ import annotations

import pytest

from tests.helpers import apply_rule

NAME = "pages-range"


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
def test_detection(text: str, target: str) -> None:
    """Test every dash and spacing form."""
    rows, output = apply_rule(NAME, "@article{k,\n  pages = {" + text + "}\n}\n")
    assert rows == [(2, 3, f"page range '{text}' should use '--'", True)]
    assert f"pages = {{{target}}}" in output


@pytest.mark.parametrize(
    "value",
    [
        "{1--10}",
        "{4484}",
        "{e12--e19}",
        "{S1-S9}",
        "{1, 2}",
        "{1-2-3}",
        'a # "1-2"',
    ],
)
def test_no_finding(value: str) -> None:
    """Test the values that are left untouched, a concatenation included."""
    assert apply_rule(NAME, "@article{k, pages = " + value + "}\n")[0] == []
