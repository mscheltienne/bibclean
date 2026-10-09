from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "required-field"
SOURCE = "@article{k,\n  author = {A},\n  title = {T},\n  year = {2021}\n}\n"


def test_detection(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a missing field is reported at the opening character."""
    rows, _ = apply_rule(NAME, SOURCE)
    assert rows == [(1, 1, "@article 'k' is missing required field 'journal'", False)]


def test_alternative_is_satisfied(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that one of the alternatives is enough."""
    source = "@book{k, editor = {E}, publisher = {P}, title = {T}, year = {1984}}\n"
    rows, _ = apply_rule(NAME, source)
    assert rows == []


def test_alternative_is_reported_as_written(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that the message lists the alternative as written."""
    source = "@book{k, publisher = {P}, title = {T}, year = {1984}}\n"
    rows, _ = apply_rule(NAME, source)
    assert rows == [
        (1, 1, "@book 'k' is missing required field 'author|editor'", False)
    ]


def test_order_follows_the_table(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that findings follow the order of the required list."""
    rows, _ = apply_rule(NAME, "@article{k, volume = {1}}\n")
    assert [row[2].rsplit("'", 2)[1] for row in rows] == [
        "author",
        "journal",
        "title",
        "year",
    ]


def test_unknown_type(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a type without a table is never reported."""
    rows, _ = apply_rule(NAME, "@weird{k, a = {1}}\n")
    assert rows == []


def test_case_insensitive_lookup(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that field names are matched case-insensitively."""
    source = "@ARTICLE{k, AUTHOR = {A}, Journal = {J}, title = {T}, year = {2021}}\n"
    rows, _ = apply_rule(NAME, source)
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
