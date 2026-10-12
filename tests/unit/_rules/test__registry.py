from __future__ import annotations

import inspect

import pytest

from bibclean._rules import RULE_NAMES, RULES
from bibclean._rules._base import Rule


def test_order() -> None:
    """Test the pipeline order of the registry."""
    assert list(RULE_NAMES) == [
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


@pytest.mark.parametrize("item", RULES, ids=lambda item: item.name)
def test_documentation_contract(item: Rule) -> None:
    """Test the docstring contract the generated rule page relies on."""
    doc = inspect.cleandoc(item.check.__doc__)
    lines = doc.splitlines()
    assert lines[0].endswith(".")
    assert len(lines) > 1
    assert lines[1] == ""
    assert not any(line.startswith("Fix:") for line in lines)
    assert "pybtex:" in doc
    assert ".. code-block:: bibtex" in doc
