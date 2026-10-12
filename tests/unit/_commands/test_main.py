from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._commands.main import run
from bibclean._version import __version__

if TYPE_CHECKING:
    from click.testing import CliRunner


def test_version(runner: CliRunner) -> None:
    """Test the version line."""
    result = runner.invoke(run, ["--version"])
    assert result.exit_code == 0
    assert result.stdout == f"bibclean {__version__}\n"


def test_no_arguments(runner: CliRunner) -> None:
    """Test that the group prints its usage when called without a sub-command."""
    result = runner.invoke(run, [])
    assert result.exit_code == 2
    assert "Usage:" in result.stderr
