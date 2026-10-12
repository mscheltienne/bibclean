from __future__ import annotations

import pytest

from bibclean._config import default_config
from bibclean._formatter import format_blocks
from bibclean._parser import parse
from tests.helpers import apply_rule, lint_config

# A source reported by each rule and the cite key exempting it.
EXCLUDED = [
    ("author-format", "@article{k, author = {a, b, c, d}}\n", "k"),
    ("doi-prefix", "@article{k, doi = {https://doi.org/10.1/x}}\n", "k"),
    (
        "duplicate-doi",
        "@article{a, doi = {10.1/x}}\n\n@article{b, doi = {10.1/x}}\n",
        "b",
    ),
    ("duplicate-field", "@article{k, title = {A}, title = {A}}\n", "k"),
    ("duplicate-key", "@article{A, a = {1}}\n\n@article{a, a = {1}}\n", "a"),
    ("empty-field", "@article{k, volume = {}}\n", "k"),
    ("month-format", "@article{k, month = {September}}\n", "k"),
    ("pages-range", "@article{k, pages = {1-2}}\n", "k"),
    ("required-field", "@article{k, title = {T}}\n", "k"),
    ("strip-field", "@article{k, issn = {1}}\n", "k"),
    ("undefined-string", "@article{k, journal = jnuero}\n", "k"),
    ("unescaped-percent", "@article{k, title = {50%}}\n", "k"),
    ("url-with-doi", "@article{k, doi = {10.1/x}, url = {https://a}}\n", "k"),
]


@pytest.mark.parametrize(("name", "source", "key"), EXCLUDED)
def test_exclusion(name: str, source: str, key: str) -> None:
    """Test that an excluded cite key or entry type is neither reported nor fixed."""
    rows, _ = apply_rule(name, source)
    assert rows
    untouched = format_blocks(parse(source), default_config().format)
    for config in (
        lint_config(exclude=frozenset({key})),
        lint_config(exclude_types=frozenset({"article"})),
    ):
        assert apply_rule(name, source, config) == ([], untouched)
