from __future__ import annotations

from dataclasses import replace

import pytest

from bibclean._config import FormatOptions, default_config
from bibclean._model import Entry
from bibclean._parser import parse
from bibclean._rules._base import (
    Context,
    Finding,
    Rule,
    _fields_named,
    _has_field,
    _remove_field,
    _single_text,
    rule,
    signature,
)

SOURCE = (
    "@article{Key,\n  title = {A},\n  TITLE = {B}\n}\n\n@software{s, title = {C}}\n"
)


def _context(**options: object) -> Context:
    base = default_config()
    config = replace(base, lint=replace(base.lint, **options))
    return Context(path="t.bib", blocks=parse(SOURCE), config=config)


def test_decorator() -> None:
    """Test that the decorator builds a rule out of a function."""

    @rule(name="my-rule", fixable="yes", scope="entry")
    def my_rule(ctx: Context) -> list[Finding]:
        """Do something.

        More text.
        """
        return []

    assert isinstance(my_rule, Rule)
    assert my_rule.name == "my-rule"
    assert my_rule.fixable == "yes"
    assert my_rule.scope == "entry"
    assert my_rule.doc == "Do something.\n\nMore text."
    assert my_rule.check(_context()) == []


@pytest.mark.parametrize("name", ["My-Rule", "my_rule", "my rule", "", "my--rule"])
def test_decorator_rejects_bad_names(name: str) -> None:
    """Test that a rule name must be kebab-case."""
    with pytest.raises(ValueError, match="invalid rule name"):
        rule(name=name, fixable="no", scope="entry")


def test_decorator_requires_a_docstring() -> None:
    """Test that a rule function must be documented."""
    with pytest.raises(ValueError, match="has no docstring"):

        @rule(name="my-rule", fixable="no", scope="entry")
        def my_rule(ctx: Context) -> list[Finding]:  # noqa: D103 - the point of the test
            return []


def test_context_entries() -> None:
    """Test that the context exposes the entries in order."""
    context = _context()
    assert [entry.key for entry in context.entries()] == ["Key", "s"]


def test_context_remove() -> None:
    """Test that a block is removed by identity."""
    context = _context()
    context.remove(context.entries()[0])
    assert [entry.key for entry in context.entries()] == ["s"]
    context.remove(context.blocks[0])
    assert len(context.blocks) == 2


def test_context_is_excluded() -> None:
    """Test exclusion by cite key and by entry type."""
    context = _context(exclude=frozenset({"Key"}))
    assert context.is_excluded(context.entries()[0]) is True
    assert context.is_excluded(context.entries()[1]) is False
    context = _context(exclude_types=frozenset({"software"}))
    assert context.is_excluded(context.entries()[0]) is False
    assert context.is_excluded(context.entries()[1]) is True


def test_context_type_rules() -> None:
    """Test the per-type lookup, including an unknown type."""
    context = _context()
    assert context.type_rules(context.entries()[0]).required[0] == "author"
    entry = context.entries()[1]
    entry.entry_type = "Unknown"
    assert context.type_rules(entry) is None


def test_signature_ignores_the_cite_key() -> None:
    """Test that the signature compares type and fields only."""
    first, second = parse('@misc{a, x = {1}}\n\n@MISC{b, x = "1"}\n')[::2]
    assert isinstance(first, Entry)
    assert isinstance(second, Entry)
    options = FormatOptions()
    assert signature(first, options) == signature(second, options)


def test_field_helpers() -> None:
    """Test the private field helpers."""
    entry = _context().entries()[0]
    assert [field.key for field in _fields_named(entry, "TiTle")] == ["title", "TITLE"]
    assert _has_field(entry, "TITLE") is True
    assert _has_field(entry, "author") is False
    assert _single_text(entry.fields[0].value) == "A"
    _remove_field(entry, entry.fields[0])
    assert [field.key for field in entry.fields] == ["TITLE"]


def test_single_text() -> None:
    """Test that only a single braced or quoted part has a text."""
    entry = parse('@misc{k, a = {  x  y }, b = jan, c = a # "b"}')[0]
    assert isinstance(entry, Entry)
    assert _single_text(entry.fields[0].value) == "x y"
    assert _single_text(entry.fields[1].value) is None
    assert _single_text(entry.fields[2].value) is None


def test_remove_ignores_foreign_objects() -> None:
    """Test that removing something absent leaves the model untouched."""
    context = _context()
    other = parse("@misc{other}\n")[0]
    context.remove(other)
    assert len(context.blocks) == 4
    entry = context.entries()[0]
    _remove_field(entry, parse("@misc{k, a = {1}}")[0].fields[0])
    assert len(entry.fields) == 2
