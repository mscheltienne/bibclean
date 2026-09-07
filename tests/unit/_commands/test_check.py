from __future__ import annotations

from typing import TYPE_CHECKING

from click.testing import CliRunner

from bibclean._commands.check import ReturnCode, _run, run

if TYPE_CHECKING:
    from pathlib import Path


def test_run(assets: Path) -> None:
    """Test the exit code returned by _run."""
    assert _run(assets / "zotero-clean.bib", None) == ReturnCode.no_violations_found
    assert _run(assets / "zotero-clean.bib", "101.toml") == ReturnCode.invalid_options
    assert _run(assets / "zotero-articles.bib", None) == ReturnCode.violations_found
    assert (
        _run(assets / "zotero-duplicates.bib", None)
        == ReturnCode.violations_found_unfixable
    )
    # invalid but with excluded elements, thus valid
    assert (
        _run(assets / "zotero-duplicates.bib", assets / "zotero-duplicates.toml")
        == ReturnCode.no_violations_found
    )


def test_cli(assets: Path) -> None:
    """Test the click command."""
    runner = CliRunner()
    result = runner.invoke(run, [str(assets / "zotero-clean.bib")])
    assert result.exit_code == ReturnCode.no_violations_found
    result = runner.invoke(run, [str(assets / "zotero-articles.bib")])
    assert result.exit_code == ReturnCode.violations_found
    result = runner.invoke(
        run,
        [
            str(assets / "zotero-duplicates.bib"),
            "-c",
            str(assets / "zotero-duplicates.toml"),
        ],
    )
    assert result.exit_code == ReturnCode.no_violations_found
    result = runner.invoke(
        run, [str(assets / "zotero-clean.bib"), "--config", "101.toml"]
    )
    assert result.exit_code == ReturnCode.invalid_options
    result = runner.invoke(run, ["--help"])
    assert result.exit_code == 0
    assert "--config" in result.output
