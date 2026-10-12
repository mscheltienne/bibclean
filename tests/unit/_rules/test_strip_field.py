from __future__ import annotations

import pytest

from bibclean._config import TypeRules, default_config
from tests.helpers import apply_rule, lint_config

NAME = "strip-field"


def test_detection() -> None:
    """Test that only the fields outside the keep list are removed."""
    source = (
        "@article{k,\n  abstract = {A},\n  doi = {10.1/x},\n  issn = {1},\n"
        "  title = {T},\n  url = {https://x},\n  note = {N}\n}\n"
    )
    rows, output = apply_rule(NAME, source)
    assert rows == [
        (2, 3, "field 'abstract' is not kept for @article", True),
        (4, 3, "field 'issn' is not kept for @article", True),
        (7, 3, "field 'note' is not kept for @article", True),
    ]
    assert "doi = {10.1/x}" in output
    assert "url = {https://x}" in output
    assert "title = {T}" in output


@pytest.mark.parametrize(
    "source",
    [
        "@article{k, crossref = {p}}\n",
        "@inproceedings{c, crossref = {P}, title = {T}}\n"
        "@proceedings{p, booktitle = {B}, title = {Proc}}\n",
        "@misc{k, note = {N}, title = {T}}\n",
        "@article{k, journal = {J}}\n",
        "@weird{k, abstract = {A}}\n",
    ],
    ids=["crossref", "crossref-target", "kept", "required", "unknown-type"],
)
def test_no_finding(source: str) -> None:
    """Test the fields that are never stripped and the types without a table."""
    rows, output = apply_rule(NAME, source)
    assert rows == []
    assert output.count(" = ") == source.count(" = ")


def test_missing_keep() -> None:
    """Test that a type table without a keep list strips nothing."""
    types = {**default_config().lint.types, "weird": TypeRules(("title",), None)}
    rows, _ = apply_rule(NAME, "@weird{k, abstract = {A}}\n", lint_config(types=types))
    assert rows == []
