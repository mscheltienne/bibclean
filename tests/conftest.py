from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from bibclean.utils.logs import logger

if TYPE_CHECKING:
    from collections.abc import Callable


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest options."""
    logger.propagate = True  # setup logging


@pytest.fixture(scope="session")
def assets() -> Path:
    """Path to the test assets directory."""
    return Path(__file__).parent / "assets"


@pytest.fixture
def bib_copy(assets: Path, tmp_path: Path) -> Callable[[str], Path]:
    """Return a function copying an asset into a temporary directory."""

    def _copy(name: str) -> Path:
        target = tmp_path / name
        target.write_bytes((assets / name).read_bytes())
        return target

    return _copy
