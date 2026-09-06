from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "duplicate-key"
IDENTICAL = (
    "@article{Smith2020,\n  author = {Smith, John},\n  title = {On things}\n}\n\n"
    '@ARTICLE{smith2020,\n  author = "Smith, John",\n  title = "On things"\n}\n'
)
DIFFERENT = (
    "@article{Smith2020,\n  author = {Smith, John},\n  title = {On things}\n}\n\n"
    "@article{smith2020,\n  author = {Smith, John},\n  title = {On stuff}\n}\n"
)


def test_identical_is_removed(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that a repeat rendering identically is removed."""
    rows, output = apply_rule(NAME, IDENTICAL)
    assert rows == [
        (
            6,
            1,
            "cite key 'smith2020' is already defined as 'Smith2020' at line 1",
            True,
        )
    ]
    assert output.count("@article{") == 1
    assert "smith2020" not in output


def test_different_is_reported(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that a repeat with different content is kept and reported."""
    rows, output = apply_rule(NAME, DIFFERENT)
    assert rows == [
        (
            6,
            1,
            "cite key 'smith2020' is already defined as 'Smith2020' at line 1",
            False,
        )
    ]
    assert output.count("@article{") == 2


def test_third_occurrence_points_at_the_first(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that every repeat is reported against the first occurrence."""
    source = "@misc{A, a = {1}}\n\n@misc{b, a = {1}}\n\n@misc{a, a = {2}}\n"
    rows, _ = apply_rule(NAME, source)
    assert [row[2] for row in rows] == [
        "cite key 'a' is already defined as 'A' at line 1"
    ]


def test_exclude(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded repeat is neither reported nor removed."""
    rows, output = apply_rule(NAME, IDENTICAL, config(exclude=frozenset({"smith2020"})))
    assert rows == []
    assert output.count("@article{") == 2


def test_exclude_types(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded entry type is exempt."""
    rows, _ = apply_rule(NAME, IDENTICAL, config(exclude_types=frozenset({"article"})))
    assert rows == []


def test_excluded_entry_stays_the_reference(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded first occurrence still defines the key."""
    rows, _ = apply_rule(NAME, IDENTICAL, config(exclude=frozenset({"Smith2020"})))
    assert [row[2] for row in rows] == [
        "cite key 'smith2020' is already defined as 'Smith2020' at line 1"
    ]


def test_removal_enables_duplicate_doi(
    rules_reported: Callable[..., list[str]],
) -> None:
    """Test that a removed entry is not reported again by duplicate-doi."""
    source = (
        "@article{A,\n  author = {X},\n  doi = {10.1/x},\n  journal = {J},\n"
        "  title = {T},\n  year = {2020}\n}\n\n"
        "@article{a,\n  author = {X},\n  doi = {10.1/x},\n  journal = {J},\n"
        "  title = {T},\n  year = {2020}\n}\n"
    )
    reported = rules_reported(source)
    assert NAME in reported
    assert "duplicate-doi" not in reported


def test_ignore(
    rules_reported: Callable[..., list[str]], config: Callable[..., Config]
) -> None:
    """Test that the rule can be disabled."""
    assert NAME in rules_reported(DIFFERENT)
    assert NAME not in rules_reported(DIFFERENT, config(ignore=frozenset({NAME})))
