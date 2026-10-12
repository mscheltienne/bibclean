from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor, wait
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest
from click.testing import CliRunner

from bibclean.utils.logs import logger
from tests.helpers import corpus_manifest


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest options."""
    logger.propagate = True  # setup logging


@pytest.fixture(scope="session")
def assets() -> Path:
    """Path to the test assets directory."""
    return Path(__file__).parent / "assets"


def _download(url: str, digest: str, path: Path) -> Path | None:
    """Download one corpus file unless a valid copy is cached.

    Parameters
    ----------
    url : str
        URL of the file.
    digest : str
        Expected SHA-256 digest of the file.
    path : Path
        Location of the cached copy.

    Returns
    -------
    Path | None
        The cached copy, None when the file cannot be downloaded or does not match
        its digest.
    """
    if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest:
        return path
    try:
        with urlopen(url, timeout=10) as response:
            data = response.read()
    except HTTPError as error:
        error.close()
        return None
    except (OSError, HTTPException):
        return None
    if hashlib.sha256(data).hexdigest() != digest:
        return None
    path.write_bytes(data)
    return path


@pytest.fixture(scope="session")
def corpus(pytestconfig: pytest.Config) -> dict[str, Path | None]:
    """Download the external corpus into the pytest cache.

    Files are cached by digest across runs. The download stops after 40 seconds, below
    the test timeout, and the files missing by then are None.

    Returns
    -------
    dict
        Maps the name of every file of :func:`tests.helpers.corpus_manifest` to its
        cached copy, or to None when it is not available.
    """
    cache = pytestconfig.cache.mkdir("corpus")
    pool = ThreadPoolExecutor(16)
    futures = {
        name: pool.submit(_download, url, digest, cache / digest)
        for name, (url, digest) in corpus_manifest().items()
    }
    done, _ = wait(futures.values(), timeout=40)
    pool.shutdown(wait=False, cancel_futures=True)
    return {name: f.result() if f in done else None for name, f in futures.items()}


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
