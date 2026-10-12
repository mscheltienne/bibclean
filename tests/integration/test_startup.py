from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_CODE = (
    "import sys\n"
    "import bibclean._config, bibclean._engine\n"
    "assert 'click' not in sys.modules, 'click'\n"
)


def test_entry_point() -> None:
    """Test that the console script is installed and runs."""
    executable = shutil.which("bibclean", path=Path(sys.executable).parent)
    if executable is None:  # pragma: no cover
        pytest.skip("the 'bibclean' console script is not installed")
    result = subprocess.run(
        [executable, "--version"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_startup_imports() -> None:
    """Test that the engine and the configuration import no click."""
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", _CODE],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
