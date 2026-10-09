from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

_HEAVY = ("numpy", "psutil", "packaging", "bibtexparser")
_CODE = (
    "import sys\n"
    "import bibclean._commands.main\n"
    "heavy = [name for name in {names!r} if name in sys.modules]\n"
    "raise SystemExit('imported ' + ', '.join(heavy) if heavy else 0)\n"
)


def _executable() -> str | None:
    """Locate the ``bibclean`` console script."""
    found = shutil.which("bibclean")
    if found is not None:
        return found
    name = "bibclean.exe" if os.name == "nt" else "bibclean"
    candidate = Path(sys.executable).parent / name
    return str(candidate) if candidate.exists() else None


def test_version() -> None:
    """Test that the console script prints its version quickly."""
    executable = _executable()
    if executable is None:  # pragma: no cover
        pytest.skip("the 'bibclean' console script is not installed")
    start = time.perf_counter()
    result = subprocess.run(
        [executable, "--version"], capture_output=True, text=True, check=False
    )
    elapsed = time.perf_counter() - start
    assert result.returncode == 0, result.stdout + result.stderr
    assert re.fullmatch(r"bibclean \S+", result.stdout.strip())
    assert elapsed < 5.0


def test_heavy_modules_not_imported() -> None:
    """Test that the command-line interface imports nothing heavy."""
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", _CODE.format(names=_HEAVY)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
