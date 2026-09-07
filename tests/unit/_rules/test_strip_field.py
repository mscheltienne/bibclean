from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from bibclean._config import TypeRules

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "strip-field"
SOURCE = (
    "@article{k,\n  abstract = {A},\n  doi = {10.1/x},\n  issn = {1},\n"
    "  title = {T},\n  url = {https://x},\n  note = {N}\n}\n"
)


def test_detection(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that only the fields outside the keep list are removed."""
    rows, output = apply_rule(NAME, SOURCE)
    assert rows == [
        (2, 3, "field 'abstract' is not kept for @article", True),
        (4, 3, "field 'issn' is not kept for @article", True),
        (7, 3, "field 'note' is not kept for @article", True),
    ]
    assert "doi = {10.1/x}" in output
    assert "url = {https://x}" in output
    assert "title = {T}" in output


def test_note_is_kept_for_misc(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that note is kept for the types whose table lists it."""
    rows, _ = apply_rule(NAME, "@misc{k, note = {N}, title = {T}}\n")
    assert rows == []


def test_required_fields_are_never_stripped(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that a required field is always part of the keep set."""
    rows, output = apply_rule(NAME, "@article{k, journal = {J}}\n")
    assert rows == []
    assert "journal" in output


def test_master_switch(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that strip-fields disables the rule entirely."""
    rows, _ = apply_rule(NAME, SOURCE, config(strip_fields=False))
    assert rows == []


def test_unknown_type_and_missing_keep(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that a type without a table or without a keep list is never stripped."""
    rows, _ = apply_rule(NAME, "@weird{k, abstract = {A}}\n")
    assert rows == []
    base = config()
    types = dict(base.lint.types)
    types["weird"] = TypeRules(required=("title",), keep=None)
    custom = replace(base, lint=replace(base.lint, types=types))
    rows, _ = apply_rule(NAME, "@weird{k, abstract = {A}}\n", custom)
    assert rows == []


def test_exclude(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded entry is exempt."""
    rows, _ = apply_rule(NAME, SOURCE, config(exclude=frozenset({"k"})))
    assert rows == []


def test_exclude_types(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded entry type is exempt."""
    rows, _ = apply_rule(NAME, SOURCE, config(exclude_types=frozenset({"article"})))
    assert rows == []


def test_ignore(
    rules_reported: Callable[..., list[str]], config: Callable[..., Config]
) -> None:
    """Test that the rule can be disabled."""
    assert NAME in rules_reported(SOURCE)
    assert NAME not in rules_reported(SOURCE, config(ignore=frozenset({NAME})))
