from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

from bibclean._config import default_config
from bibclean._engine import lint, process
from bibclean._formatter import format_blocks
from bibclean._parser import parse
from bibclean._rules import RULES
from bibclean._rules._base import Context

if TYPE_CHECKING:
    from bibclean._config import Config

ASSETS = Path(__file__).parent / "assets"
Row = tuple[int | None, int | None, str, bool]


def write(path: Path, text: str) -> Path:
    """Write a UTF-8 file with line feed endings, creating its parent directories.

    Parameters
    ----------
    path : Path
        File to write.
    text : str
        Content of the file.

    Returns
    -------
    Path
        The written file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def lint_config(**options: Any) -> Config:
    """Build the default configuration with lint overrides.

    Parameters
    ----------
    **options : Any
        Fields of the lint options to replace, e.g. ``exclude=frozenset({"k"})``.

    Returns
    -------
    Config
        The configuration.
    """
    base = default_config()
    return replace(base, lint=replace(base.lint, **options))


def apply_rule(
    name: str, source: str, config: Config | None = None
) -> tuple[list[Row], str]:
    """Run one rule over a source and render the result.

    Parameters
    ----------
    name : str
        Name of the rule.
    source : str
        BibTeX text.
    config : Config | None
        Configuration, the defaults when None.

    Returns
    -------
    rows : list of tuple
        The ``(line, column, message, fixable)`` of every diagnostic.
    output : str
        The blocks rendered after the rule ran.
    """
    config = default_config() if config is None else config
    context = Context(blocks=parse(source), config=config)
    diagnostics = next(item for item in RULES if item.name == name).check(context)
    rows = [
        (
            None if item.position is None else item.position.line,
            None if item.position is None else item.position.column,
            item.message,
            item.fixable,
        )
        for item in diagnostics
    ]
    return rows, format_blocks(context.blocks, config.format)


def rules_reported(source: str) -> list[str]:
    """List the rule names reported by the whole lint pipeline with the defaults.

    Parameters
    ----------
    source : str
        BibTeX text.

    Returns
    -------
    list of str
        The rule name of every diagnostic, in pipeline order.
    """
    context = Context(blocks=parse(source), config=default_config())
    return [item.rule for item in lint(context)]


def assert_converged(data: bytes, config: Config) -> None:
    """Check that one fix leaves a fixed point with nothing left to fix.

    Parameters
    ----------
    data : bytes
        Content of a UTF-8 file. A file with a syntax error is exempt, as it is never
        rewritten.
    config : Config
        Configuration used by both passes.
    """
    report = process(data, "utf-8", config)
    if any(item.rule == "syntax-error" for item in report.diagnostics):
        return
    fixed = data if report.output is None else report.output
    again = process(fixed, "utf-8", config)
    assert again.output is None, data
    assert not any(item.fixable for item in again.diagnostics), data
    assert not any(item.rule == "syntax-error" for item in again.diagnostics), data


def corpus_manifest() -> dict[str, tuple[str, str]]:
    """Read the manifest of the external corpus.

    Returns
    -------
    dict
        Maps the name ``<owner>/<repo>/<path>`` of every file to its download URL
        and its SHA-256 digest.
    """
    manifest = json.loads((ASSETS / "corpus.json").read_text(encoding="utf-8"))
    return {
        "/".join(base.split("/")[3:5]) + "/" + unquote(path): (base + path, digest)
        for base, group in manifest.items()
        for path, digest in group["files"].items()
    }
