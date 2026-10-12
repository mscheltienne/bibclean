from __future__ import annotations

import re

import pytest

from bibclean._rules import RULE_NAMES, RULES
from bibclean._rules._base import Rule

EXPECTED = [
    "syntax-error",
    "doi-prefix",
    "empty-field",
    "strip-field",
    "url-with-doi",
    "month-format",
    "pages-range",
    "unescaped-percent",
    "duplicate-field",
    "duplicate-key",
    "duplicate-doi",
    "undefined-string",
    "author-format",
    "required-field",
]


def test_order() -> None:
    """Test the pipeline order of the registry."""
    assert list(RULE_NAMES) == EXPECTED
    assert len(RULES) == 14
    assert all(isinstance(item, Rule) for item in RULES)


def test_names_are_unique() -> None:
    """Test that no name appears twice."""
    assert len(set(RULE_NAMES)) == len(RULE_NAMES)


@pytest.mark.parametrize("item", RULES, ids=lambda item: item.name)
def test_documentation_contract(item: Rule) -> None:
    """Test the docstring contract the generated rule page relies on."""
    lines = item.doc.splitlines()
    assert lines[0].endswith(".")
    assert len(lines) > 1
    assert lines[1] == ""
    assert not any(line.startswith("Fix:") for line in lines)
    assert "pybtex:" in item.doc
    assert ".. code-block:: bibtex" in item.doc


@pytest.mark.parametrize("item", RULES, ids=lambda item: item.name)
def test_metadata(item: Rule) -> None:
    """Test that every rule has a kebab-case name, a known fixability and scope."""
    assert re.fullmatch(r"[a-z]+(-[a-z]+)*", item.name)
    assert item.fixable in ("no", "partial", "yes")
    assert item.scope in ("block", "file", "entry", "field", "value")
