from __future__ import annotations

import pytest

from bibclean._rules import RULE_NAMES, RULES, get_rule
from bibclean._rules._base import Rule

EXPECTED = [
    "syntax-error",
    "duplicate-key",
    "duplicate-doi",
    "duplicate-field",
    "empty-field",
    "strip-field",
    "url-with-doi",
    "doi-prefix",
    "month-format",
    "pages-range",
    "unescaped-percent",
    "undefined-string",
    "required-field",
]


def test_order() -> None:
    """Test the pipeline order of the registry."""
    assert list(RULE_NAMES) == EXPECTED
    assert len(RULES) == 13
    assert all(isinstance(item, Rule) for item in RULES)


def test_names_are_unique() -> None:
    """Test that no name appears twice."""
    assert len(set(RULE_NAMES)) == len(RULE_NAMES)


def test_get_rule() -> None:
    """Test the lookup by name and its error."""
    assert get_rule("doi-prefix").name == "doi-prefix"
    with pytest.raises(KeyError, match="unknown rule 'nope'"):
        get_rule("nope")


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
    """Test that every rule declares a known fixability and scope."""
    assert item.fixable in ("no", "partial", "yes")
    assert item.scope in ("block", "file", "entry", "field", "value")
