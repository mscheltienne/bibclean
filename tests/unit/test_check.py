from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bibclean import check_bib_database
from bibclean._exception import DuplicateEntry, MissingReqField
from bibclean.io import load_bib

if TYPE_CHECKING:
    from pathlib import Path


def test_check_bib_database(assets: Path) -> None:
    """Test checking of a BibTex database."""
    # test without providing a configuration
    check_bib_database(load_bib(assets / "zotero-articles.bib"))
    # test with configuration
    check_bib_database(
        load_bib(assets / "zotero-articles.bib"),
        required_fields={"test": {"test"}},
    )

    # test with an excluded duplicate
    check_bib_database(
        load_bib(assets / "zotero-duplicates.bib"),
        exclude=["gramfort_meg_2013"],
    )

    # test with duplicate entries
    with pytest.raises(
        DuplicateEntry,
        match="BibTex file contains duplicate entries with the same cite key",
    ):
        check_bib_database(load_bib(assets / "zotero-duplicates.bib"))

    with pytest.raises(
        DuplicateEntry,
        match="BibTex file contains duplicate entries with different cite ",
    ):
        check_bib_database(load_bib(assets / "zotero-duplicates-2.bib"))

    # test with missing basic field
    with pytest.raises(
        MissingReqField,
        match="BibTex file entry 'ablin_faster_2018' is missing some basic",
    ):
        check_bib_database(load_bib(assets / "zotero-missing-fields.bib"))

    # test with missing required field
    with pytest.raises(
        MissingReqField,
        match="BibTex file entry 'appelhoff_mne-bids_2019' is missing one of",
    ):
        check_bib_database(
            load_bib(assets / "zotero-missing-fields.bib"),
            exclude=["ablin_faster_2018"],
            required_fields={"article": {"test"}},
        )


def test_check_bib_database_invalid_args(assets: Path) -> None:
    """Test passing invalid arguments to check_bib_database."""
    with pytest.raises(
        TypeError, match="'bib_database' must be an instance of BibDatabase"
    ):
        check_bib_database(101)
    with pytest.raises(
        TypeError, match="'exclude' must be an instance of list or tuple"
    ):
        check_bib_database(load_bib(assets / "zotero-articles.bib"), exclude=101)
    with pytest.raises(TypeError, match="Item must be an instance of str"):
        check_bib_database(load_bib(assets / "zotero-articles.bib"), exclude=[101])
    with pytest.raises(ValueError, match="Invalid value for the 'exclude' parameter"):
        check_bib_database(load_bib(assets / "zotero-articles.bib"), exclude=["101"])
    with pytest.raises(
        TypeError,
        match="'required_fields' must be an instance of dict or None",
    ):
        check_bib_database(
            load_bib(assets / "zotero-articles.bib"),
            exclude=["gramfort_mne_2014"],
            required_fields=101,
        )
    with pytest.raises(TypeError, match="Item must be an instance of str"):
        check_bib_database(
            load_bib(assets / "zotero-articles.bib"),
            exclude=["gramfort_mne_2014"],
            required_fields={101: {"test"}},
        )
    with pytest.raises(TypeError, match="Item must be an instance of str"):
        check_bib_database(
            load_bib(assets / "zotero-articles.bib"),
            exclude=["gramfort_mne_2014"],
            required_fields={"article": {101}},
        )
    with pytest.raises(TypeError, match="Item must be an instance of set"):
        check_bib_database(
            load_bib(assets / "zotero-articles.bib"),
            exclude=["gramfort_mne_2014"],
            required_fields={"article": ["101"]},
        )
