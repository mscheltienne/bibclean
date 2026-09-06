from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "undefined-string"
SOURCE = (
    "@string{jneuro = {Journal of Neuroscience}}\n\n"
    "@article{k,\n  journal = jnuero,\n  month = jan,\n  year = 2020\n}\n"
)


def test_detection(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that an unknown macro is reported at the field key."""
    rows, _ = apply_rule(NAME, SOURCE)
    assert rows == [(4, 3, "undefined string 'jnuero'", False)]


def test_defined_macros(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a defined macro, a month macro and digits are accepted."""
    source = "@STRING{JNeuro = {J}}\n\n@article{k, journal = jneuro, month = DEC}\n"
    rows, _ = apply_rule(NAME, source)
    assert rows == []


def test_forward_reference(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a string may not reference a string defined below it."""
    source = "@string{a = b}\n\n@string{b = {x}}\n"
    rows, _ = apply_rule(NAME, source)
    assert rows == [(1, 1, "undefined string 'b'", False)]


def test_preamble(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a preamble value is checked too."""
    rows, _ = apply_rule(NAME, "@preamble{missing}\n")
    assert rows == [(1, 1, "undefined string 'missing'", False)]


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
