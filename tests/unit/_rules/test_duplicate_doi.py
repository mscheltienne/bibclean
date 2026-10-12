from __future__ import annotations

import pytest

from tests.helpers import apply_rule

NAME = "duplicate-doi"


@pytest.mark.parametrize(
    ("source", "doi"),
    [
        (
            "@article{a,\n  doi = {10.1000/THINGS},\n  title = {One}\n}\n\n"
            "@article{b,\n  doi = {https://doi.org/10.1000/things},\n"
            "  title = {Two}\n}\n",
            "10.1000/things",
        ),
        (
            "@article{a,\n  doi = {10.1/x},\n  title = {One}\n}\n\n"
            "@article{b,\n  doi = {10.1/x},\n  title = {One}\n}\n",
            "10.1/x",
        ),
    ],
    ids=["different", "identical"],
)
def test_detection(source: str, doi: str) -> None:
    """Test that a shared DOI is reported and both entries, maybe cited, are kept."""
    rows, output = apply_rule(NAME, source)
    assert rows == [(6, 1, f"entry shares DOI '{doi}' with 'a' at line 1", False)]
    assert output.count("@article{") == 2


@pytest.mark.parametrize(
    "source",
    [
        "@misc{a, title = {A}}\n\n@misc{b, title = {B}}\n",
        "@misc{a, doi = {10.1/x}}\n\n@misc{b, doi = {}}\n",
        '@misc{a, doi = {10.1/x}}\n\n@misc{b, doi = p # "x"}\n',
        "@misc{a, doi = {10.1/x}}\n\n@misc{b, doi = {10.1/y}}\n",
        "@misc{a, doi = {doi:}}\n\n@misc{b, doi = {doi:}}\n",
    ],
)
def test_no_finding(source: str) -> None:
    """Test the values that the rule skips, a prefix alone included."""
    assert apply_rule(NAME, source)[0] == []
