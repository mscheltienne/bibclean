from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bibclean._commands.sys_info import run

if TYPE_CHECKING:
    from click.testing import CliRunner


@pytest.mark.parametrize("flag", [None, "--developer"])
def test_sys_info(runner: CliRunner, flag: str | None) -> None:
    """Test the system information entry-point."""
    result = runner.invoke(run, [] if flag is None else [flag])
    assert result.exit_code == 0
    assert "Platform:" in result.stdout
    assert "Python:" in result.stdout
    assert "Executable:" in result.stdout
    assert "Core dependencies" in result.stdout
    if flag == "--developer":
        assert "Developer 'style' dependencies" in result.stdout
        assert "Developer 'test' dependencies" in result.stdout
