from __future__ import annotations

import pytest

from tests.helpers import apply_rule

NAME = "undefined-string"


@pytest.mark.parametrize(
    ("source", "row"),
    [
        (
            "@string{jneuro = {Journal of Neuroscience}}\n\n"
            "@article{k,\n  journal = jnuero,\n  month = jan,\n  year = 2020\n}\n",
            (4, 3, "undefined string 'jnuero'", False),
        ),
        ("@string{a = b}\n\n@string{b = {x}}\n", (1, 1, "undefined string 'b'", False)),
        (
            "@preamble{missing}\n\n@string{missing = {x}}\n",
            (1, 1, "undefined string 'missing'", False),
        ),
    ],
    ids=["entry", "string-above-its-string", "preamble-above-its-string"],
)
def test_detection(source: str, row: tuple[int, int, str, bool]) -> None:
    """Test unknown macros, a string or a preamble seeing the strings above only."""
    assert apply_rule(NAME, source)[0] == [row]


@pytest.mark.parametrize(
    "source",
    [
        "@STRING{JNeuro = {J}}\n\n@article{k, journal = jneuro, month = DEC}\n",
        "@misc{k, journal = j}\n\n@string{j = {J}}\n",
    ],
    ids=["defined", "entry-above-its-string"],
)
def test_no_finding(source: str) -> None:
    """Test defined and month macros, and an entry above its string, hoisted by fix."""
    assert apply_rule(NAME, source)[0] == []
