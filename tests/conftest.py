from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from bibclean.utils.logs import logger


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest options."""
    logger.propagate = True  # setup logging


@pytest.fixture(scope="session")
def assets() -> Path:
    """Path to the test assets directory."""
    return Path(__file__).parent / "assets"


@pytest.fixture
def runner() -> CliRunner:
    """Click runner invoking the command-line interface in-process."""
    return CliRunner()


@pytest.fixture
def case_dir(
    request: pytest.FixtureRequest,
    assets: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Copy the files of one golden case into a temporary working directory.

    The test using this fixture must be parametrised on ``case``. A case without
    a ``.fixed.bib`` asset gets a copy of its input under that name, so that
    every case can be compared the same way.
    """
    case = request.getfixturevalue("case")
    for path in assets.glob(f"{case}.*"):
        (tmp_path / path.name).write_bytes(path.read_bytes())
    fixed = tmp_path / f"{case}.fixed.bib"
    if not fixed.exists():
        fixed.write_bytes((assets / f"{case}.bib").read_bytes())
    monkeypatch.chdir(tmp_path)
    return tmp_path
