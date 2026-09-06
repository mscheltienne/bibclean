from __future__ import annotations

from typing import TYPE_CHECKING

from bibtexparser import dumps
from click.testing import CliRunner

from bibclean._commands.fix import ReturnCode, _run, run
from bibclean.io import load_bib

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def test_run(assets: Path, bib_copy: Callable[[str], Path]) -> None:
    """Test the exit code returned by _run and the in-place cleaning."""
    file = bib_copy("zotero-articles.bib")
    assert _run(file, None) == ReturnCode.no_violations_found
    assert dumps(load_bib(file)) == dumps(load_bib(assets / "zotero-clean.bib"))
    # already clean file is idempotent
    before = file.read_text(encoding="utf-8")
    assert _run(file, None) == ReturnCode.no_violations_found
    assert file.read_text(encoding="utf-8") == before
    # unfixable violations leave the file untouched
    file = bib_copy("zotero-duplicates.bib")
    before = file.read_text(encoding="utf-8")
    assert _run(file, None) == ReturnCode.violations_found_unfixable
    assert file.read_text(encoding="utf-8") == before
    # excluded duplicates are accepted
    assert (
        _run(file, assets / "zotero-duplicates.toml") == ReturnCode.no_violations_found
    )
    # invalid options
    assert _run(file, "101.toml") == ReturnCode.invalid_options
    assert _run(assets / "101.bib", None) == ReturnCode.invalid_options


def test_cli(assets: Path, bib_copy: Callable[[str], Path]) -> None:
    """Test the click command."""
    runner = CliRunner()
    file = bib_copy("zotero-articles.bib")
    result = runner.invoke(run, [str(file)])
    assert result.exit_code == ReturnCode.no_violations_found
    assert dumps(load_bib(file)) == dumps(load_bib(assets / "zotero-clean.bib"))
    result = runner.invoke(run, [str(file), "--encoding", "utf-8"])
    assert result.exit_code == ReturnCode.no_violations_found
    result = runner.invoke(run, [str(file), "-c", "101.toml"])
    assert result.exit_code == ReturnCode.invalid_options
    result = runner.invoke(run, ["--help"])
    assert result.exit_code == 0
    assert "--encoding" in result.output
