from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

import pytest

from bibclean._config import default_config
from bibclean._engine import lint
from bibclean._formatter import format_blocks
from bibclean._parser import parse
from bibclean._rules import get_rule
from bibclean._rules._base import Context

if TYPE_CHECKING:
    from collections.abc import Callable

    from bibclean._config import Config


@pytest.fixture
def config() -> Callable[..., Config]:
    """Return a factory building a configuration with lint overrides."""

    def _build(**options: Any) -> Config:
        base = default_config()
        return replace(base, lint=replace(base.lint, **options))

    return _build


@pytest.fixture
def apply_rule() -> Callable[..., tuple[list[tuple[Any, ...]], str]]:
    """Return a function running one rule over a source and rendering the result."""

    def _apply(
        name: str, source: str, cfg: Config | None = None
    ) -> tuple[list[tuple[Any, ...]], str]:
        cfg = default_config() if cfg is None else cfg
        context = Context(path="t.bib", blocks=parse(source), config=cfg)
        findings = get_rule(name).check(context)
        rows = [
            (
                None if item.position is None else item.position.line,
                None if item.position is None else item.position.column,
                item.message,
                item.fixable,
            )
            for item in findings
        ]
        return rows, format_blocks(context.blocks, cfg.format)

    return _apply


@pytest.fixture
def rules_reported() -> Callable[..., list[str]]:
    """Return a function listing the rule names reported by the whole pipeline."""

    def _reported(source: str, cfg: Config | None = None) -> list[str]:
        cfg = default_config() if cfg is None else cfg
        context = Context(path="t.bib", blocks=parse(source), config=cfg)
        return [item.rule for item in lint(context)]

    return _reported
