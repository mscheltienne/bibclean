from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "duplicate-doi"
DIFFERENT = (
    "@article{a,\n  doi = {10.1000/THINGS},\n  title = {One}\n}\n\n"
    "@article{b,\n  doi = {https://doi.org/10.1000/things},\n  title = {Two}\n}\n"
)
IDENTICAL = (
    "@article{a,\n  doi = {10.1/x},\n  title = {One}\n}\n\n"
    "@article{b,\n  doi = {10.1/x},\n  title = {One}\n}\n"
)


def test_different_is_reported(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that a shared DOI on differing entries is reported."""
    rows, output = apply_rule(NAME, DIFFERENT)
    assert rows == [
        (6, 1, "entry shares DOI '10.1000/things' with 'a' at line 1", False)
    ]
    assert output.count("@article{") == 2


def test_identical_is_removed(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that an identical repeat is removed."""
    rows, output = apply_rule(NAME, IDENTICAL)
    assert rows == [(6, 1, "entry shares DOI '10.1/x' with 'a' at line 1", True)]
    assert output.count("@article{") == 1


@pytest.mark.parametrize(
    "source",
    [
        "@misc{a, title = {A}}\n\n@misc{b, title = {B}}\n",
        "@misc{a, doi = {10.1/x}}\n\n@misc{b, doi = {}}\n",
        '@misc{a, doi = {10.1/x}}\n\n@misc{b, doi = p # "x"}\n',
        "@misc{a, doi = {10.1/x}}\n\n@misc{b, doi = {10.1/y}}\n",
    ],
)
def test_no_finding(
    apply_rule: Callable[..., tuple[list[Any], str]], source: str
) -> None:
    """Test the values that the rule skips."""
    rows, _ = apply_rule(NAME, source)
    assert rows == []


def test_exclude(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded repeat is exempt."""
    rows, _ = apply_rule(NAME, DIFFERENT, config(exclude=frozenset({"b"})))
    assert rows == []


def test_exclude_types(
    apply_rule: Callable[..., tuple[list[Any], str]], config: Callable[..., Config]
) -> None:
    """Test that an excluded entry type is exempt."""
    rows, _ = apply_rule(NAME, DIFFERENT, config(exclude_types=frozenset({"article"})))
    assert rows == []


def test_ignore(
    rules_reported: Callable[..., list[str]], config: Callable[..., Config]
) -> None:
    """Test that the rule can be disabled."""
    assert NAME in rules_reported(DIFFERENT)
    assert NAME not in rules_reported(DIFFERENT, config(ignore=frozenset({NAME})))


def test_prefix_only_doi_is_skipped(
    apply_rule: Callable[..., tuple[list[Any], str]],
) -> None:
    """Test that a value made of a prefix alone has no identifier."""
    rows, _ = apply_rule(NAME, "@misc{a, doi = {doi:}}\n\n@misc{b, doi = {doi:}}\n")
    assert rows == []
