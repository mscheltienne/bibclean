from __future__ import annotations

import re
from typing import TYPE_CHECKING

from bibclean._commands.main import run
from bibclean._version import __version__

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_help(runner: CliRunner) -> None:
    """Test the help of the main entry-point."""
    result = runner.invoke(run, ["--help"])
    assert result.exit_code == 0
    assert "Lint and format BibTeX files." in result.stdout
    assert "Commands:" in result.stdout
    for command in ("check", "fix", "sys-info"):
        assert command in result.stdout


def test_version(runner: CliRunner) -> None:
    """Test the format of the version line."""
    result = runner.invoke(run, ["--version"])
    assert result.exit_code == 0
    assert result.stdout == f"bibclean {__version__}\n"
    assert re.fullmatch(r"bibclean \S+", result.stdout.strip())


def test_no_arguments(runner: CliRunner) -> None:
    """Test that the group prints its help when called without a sub-command."""
    result = runner.invoke(run, [])
    assert result.exit_code == 2
    assert "Usage:" in result.stderr
