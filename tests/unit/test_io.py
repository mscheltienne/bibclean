from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from bibtexparser.bibdatabase import BibDatabase

from bibclean.io import load_bib, save_bib

if TYPE_CHECKING:
    from pathlib import Path


def test_load_bib(assets: Path) -> None:
    """Test loading of BibTex files."""
    file = assets / "zotero-articles.bib"
    bib_database = load_bib(file)
    assert isinstance(bib_database, BibDatabase)


def test_load_bib_invalid_args() -> None:
    """Test passing invalid arguments to load_bib()."""
    with pytest.raises(TypeError, match="'file' must be an instance of str or Path"):
        load_bib(101)
    with pytest.raises(
        OSError,
        match="The provided file extension is not '.bib'. '.101' is invalid.",
    ):
        load_bib("101.101")
    with pytest.raises(OSError, match="The provided file does not exist."):
        load_bib("101.bib")


def test_save_bib(assets: Path, tmp_path: Path) -> None:
    """Test saving of BibTex files."""
    file = assets / "zotero-articles.bib"
    bib_database = load_bib(file)

    # save/reload
    save_bib(bib_database, tmp_path / "101.bib")
    bib_database_loaded = load_bib(tmp_path / "101.bib")
    assert all(elt in bib_database_loaded.entries for elt in bib_database.entries)
    assert all(elt in bib_database.entries for elt in bib_database_loaded.entries)

    # overwrite
    with pytest.raises(OSError, match="The provided file already exist."):
        save_bib(bib_database, tmp_path / "101.bib")
    save_bib(bib_database, tmp_path / "101.bib", overwrite=True)

    # encoding
    save_bib(bib_database, tmp_path / "101-2.bib", encoding="utf-16")
    bib_database_loaded = load_bib(tmp_path / "101-2.bib", encoding="utf-16")
    assert all(elt in bib_database_loaded.entries for elt in bib_database.entries)
    assert all(elt in bib_database.entries for elt in bib_database_loaded.entries)


def test_save_bib_invalid_args(assets: Path) -> None:
    """Test passing invalid arguments to save_bib()."""
    with pytest.raises(
        TypeError, match="'bib_database' must be an instance of BibDatabase"
    ):
        save_bib(101, "101.bib")

    file = assets / "zotero-articles.bib"
    bib_database = load_bib(file)
    with pytest.raises(
        OSError,
        match="The provided file extension is not '.bib'. '.101' is invalid.",
    ):
        save_bib(bib_database, "101.101")
