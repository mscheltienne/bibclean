from __future__ import annotations

from typing import TYPE_CHECKING

from bibtexparser import dumps
from click.testing import CliRunner

from bibclean._commands.main import run
from bibclean.io import load_bib

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def test_check_then_fix(assets: Path, bib_copy: Callable[[str], Path]) -> None:
    """Test that 'check' fails on a raw export, 'fix' cleans it and 'check' passes."""
    runner = CliRunner()
    file = bib_copy("zotero-articles.bib")
    assert runner.invoke(run, ["check", str(file)]).exit_code == 1
    assert runner.invoke(run, ["fix", str(file)]).exit_code == 0
    assert dumps(load_bib(file)) == dumps(load_bib(assets / "zotero-clean.bib"))
    assert runner.invoke(run, ["check", str(file)]).exit_code == 0


def test_sys_info() -> None:
    """Test that 'sys-info' runs through the group."""
    result = CliRunner().invoke(run, ["sys-info"])
    assert result.exit_code == 0
    assert "bibclean:" in result.output
    assert "Core dependencies" in result.output
