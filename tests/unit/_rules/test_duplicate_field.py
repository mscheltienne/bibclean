from __future__ import annotations

from tests.helpers import apply_rule, rules_reported

NAME = "duplicate-field"


def test_same_value_is_removed() -> None:
    """Test that a repeat with the same value is removed."""
    rows, output = apply_rule(NAME, '@article{k,\n  title = {A},\n  TITLE = "A"\n}\n')
    assert rows == [(3, 3, "field 'title' is defined twice with the same value", True)]
    assert output.count("title") == 1


def test_different_value_is_reported() -> None:
    """Test that a repeat with another value is kept and reported."""
    rows, output = apply_rule(NAME, "@article{k,\n  title = {A},\n  title = {B}\n}\n")
    assert rows == [
        (3, 3, "field 'title' is defined twice with different values", False)
    ]
    assert output.count("title") == 2


def test_three_occurrences() -> None:
    """Test that every repeat is compared with the first occurrence."""
    rows, output = apply_rule(NAME, "@misc{k,\n  a = {1},\n  a = {2},\n  a = {1}\n}\n")
    assert [(row[0], row[3]) for row in rows] == [(3, False), (4, True)]
    assert output.count("a = ") == 2


def test_no_finding() -> None:
    """Test that distinct field names report nothing."""
    assert apply_rule(NAME, "@misc{k, a = {1}, b = {1}}\n")[0] == []


def test_runs_after_strip_field() -> None:
    """Test that a repeated field stripped by strip-field is not compared."""
    reported = rules_reported("@article{k,\n  issn = {1},\n  issn = {2}\n}\n")
    assert reported.count("strip-field") == 2
    assert reported.count(NAME) == 0
