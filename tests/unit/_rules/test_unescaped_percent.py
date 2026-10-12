from __future__ import annotations

import pytest

from tests.helpers import apply_rule

NAME = "unescaped-percent"


def test_detection() -> None:
    """Test that every unescaped percent is escaped and reported once."""
    source = "@article{k,\n  title = {Filtering (50% of 90% of the signal)}\n}\n"
    rows, output = apply_rule(NAME, source)
    message = "unescaped '%' in field 'title', pybtex drops the rest of the value"
    assert rows == [(2, 3, message, True)]
    assert "{Filtering (50\\% of 90\\% of the signal)}" in output


@pytest.mark.parametrize(
    ("value", "escaped"),
    [
        ("{a\\\\%b}", "{a\\\\\\%b}"),
        ('jan # "50%"', "jan # {50\\%}"),
        (
            "{\\url{http://x/a%20b} 50% \\href{http://y/%41}{5%}}",
            "{\\url{http://x/a%20b} 50\\% \\href{http://y/%41}{5\\%}}",
        ),
    ],
    ids=["escaped-backslash", "quoted-part", "url-arguments"],
)
def test_escape(value: str, escaped: str) -> None:
    """Test a percent behind an escaped backslash, in a quoted part and near URLs."""
    rows, output = apply_rule(NAME, "@article{k, title = " + value + "}\n")
    assert len(rows) == 1
    assert escaped in output


@pytest.mark.parametrize(
    "source",
    [
        "@article{k, title = {Filtering (50\\% of the signal)}}\n",
        "@article{k, title = {no percent here}}\n",
        "@article{k,\n  url = {https://x/a%2Fb},\n  doi = {10.1/a%2Fb},\n"
        "  file = {a%b}\n}\n",
    ],
    ids=["escaped", "none", "exempt-fields"],
)
def test_no_finding(source: str) -> None:
    """Test escaped or percent-free values and the url, doi and file fields."""
    rows, output = apply_rule(NAME, source)
    assert rows == []
    assert output.count("\\%") == source.count("\\%")
