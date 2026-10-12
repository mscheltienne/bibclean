from __future__ import annotations

from tests.helpers import apply_rule, lint_config, rules_reported

NAME = "duplicate-key"
MESSAGE = "cite key 'smith2020' is already defined as 'Smith2020' at line 1"
IDENTICAL = (
    "@article{Smith2020,\n  author = {Smith, John},\n  title = {On things}\n}\n\n"
    '@ARTICLE{smith2020,\n  author = "Smith, John",\n  title = "On things"\n}\n'
)


def test_identical_is_removed() -> None:
    """Test that a repeat rendering identically is removed."""
    rows, output = apply_rule(NAME, IDENTICAL)
    assert rows == [(6, 1, MESSAGE, True)]
    assert output.count("@article{") == 1
    assert "smith2020" not in output


def test_different_is_reported() -> None:
    """Test that a repeat with different content is kept and reported."""
    rows, output = apply_rule(NAME, IDENTICAL.replace('"On things"', '"On stuff"'))
    assert rows == [(6, 1, MESSAGE, False)]
    assert output.count("@article{") == 2


def test_third_occurrence_points_at_the_first() -> None:
    """Test that every repeat is reported against the first occurrence."""
    source = "@misc{A, a = {1}}\n\n@misc{b, a = {1}}\n\n@misc{a, a = {2}}\n"
    rows, _ = apply_rule(NAME, source)
    assert [row[2] for row in rows] == [
        "cite key 'a' is already defined as 'A' at line 1"
    ]


def test_excluded_entry_stays_the_reference() -> None:
    """Test that an excluded first occurrence still defines the key."""
    rows, _ = apply_rule(NAME, IDENTICAL, lint_config(exclude=frozenset({"Smith2020"})))
    assert [row[2] for row in rows] == [MESSAGE]


def test_removal_enables_duplicate_doi() -> None:
    """Test that a removed entry is not reported again by duplicate-doi."""
    entry = (
        "@article{{{key},\n  author = {{X}},\n  doi = {{10.1/x}},\n  journal = {{J}},\n"
        "  title = {{T}},\n  year = {{2020}}\n}}\n"
    )
    reported = rules_reported(entry.format(key="A") + "\n" + entry.format(key="a"))
    assert NAME in reported
    assert "duplicate-doi" not in reported
