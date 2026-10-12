from __future__ import annotations

import pytest

from bibclean._rules.doi_prefix import normalize_doi, strip_doi_prefix
from tests.helpers import apply_rule

NAME = "doi-prefix"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("10.1/x", "10.1/x"),
        ("  10.1/x  ", "10.1/x"),
        ("https://doi.org/10.1/x", "10.1/x"),
        ("HTTP://DOI.ORG/10.1/x", "10.1/x"),
        ("https://dx.doi.org/10.1/x", "10.1/x"),
        ("http://dx.doi.org/10.1/x", "10.1/x"),
        ("https://www.doi.org/10.1/x", "10.1/x"),
        ("http://www.doi.org/10.1/x", "10.1/x"),
        ("doi:10.1/x", "10.1/x"),
        ("DOI: 10.1/x", "10.1/x"),
        ("doi:https://doi.org/10.1/x", "10.1/x"),
        (" doi: https://doi.org/ 10.1/x ", "10.1/x"),
        ("https://example.org/10.1/x", "https://example.org/10.1/x"),
        ("10.1/DOI:x", "10.1/DOI:x"),
    ],
)
def test_strip_doi_prefix(text: str, expected: str) -> None:
    """Test the prefix removal on every documented input form."""
    assert strip_doi_prefix(text) == expected


def test_normalize_doi() -> None:
    """Test that the comparison form is lowercased."""
    assert normalize_doi("https://doi.org/10.1000/THINGS") == "10.1000/things"


def test_detection() -> None:
    """Test that the prefix is removed and the identifier case is kept."""
    rows, output = apply_rule(
        NAME, "@article{k,\n  doi = {https://doi.org/10.1016/J.X}\n}\n"
    )
    assert rows == [
        (2, 3, "field 'doi' has a URL prefix, expected the bare identifier", True)
    ]
    assert "doi = {10.1016/J.X}" in output


@pytest.mark.parametrize(
    "source",
    [
        "@misc{k, doi = {10.1/x}}\n",
        "@misc{k, doi = macro}\n",
        '@misc{k, doi = a # "b"}\n',
        "@misc{k, title = {https://doi.org/10.1/x}}\n",
    ],
)
def test_no_finding(source: str) -> None:
    """Test the values that the rule skips."""
    assert apply_rule(NAME, source)[0] == []
