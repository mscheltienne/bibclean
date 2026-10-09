from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from bibclean._config import Config

NAME = "url-with-doi"
SOURCE = (
    "@article{k,\n  doi = {10.1/x},\n  url = {https://a},\n  URL = {https://b}\n}\n"
)


def test_detection(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that every url field is removed when a doi is present."""
    rows, output = apply_rule(NAME, SOURCE)
    assert rows == [
        (3, 3, "field 'url' is redundant with 'doi'", True),
        (4, 3, "field 'url' is redundant with 'doi'", True),
    ]
    assert "url" not in output
    assert "doi = {10.1/x}" in output


def test_url_alone_is_kept(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a url without a doi is kept and not reported."""
    rows, output = apply_rule(NAME, "@article{k, url = {https://a}}\n")
    assert rows == []
    assert "url" in output


def test_doi_alone(apply_rule: Callable[..., tuple[list[Any], str]]) -> None:
    """Test that a doi without a url reports nothing."""
    rows, _ = apply_rule(NAME, "@article{k, doi = {10.1/x}}\n")
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
