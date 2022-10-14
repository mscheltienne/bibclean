from pathlib import Path

import pytest
from bibtexparser import dumps

from bibclean import clean_bib_database
from bibclean.io import load_bib


def test_clean_bib_database():
    """Test cleaning of a BibTex database."""
    directory = Path(__file__).parent / "data"

    bib_db = clean_bib_database(load_bib(directory / "zotero-articles.bib"))
    bib_db_clean = load_bib(directory / "zotero-clean.bib")
    assert dumps(bib_db) == dumps(bib_db_clean)

    # test exclude
    bib_db = clean_bib_database(
        load_bib(directory / "zotero-keep-fields.bib"),
        exclude=["gramfort_mne_2014"],
    )
    assert "doi" in bib_db.entries[0]
    assert "url" in bib_db.entries[0]
    assert "issn" in bib_db.entries[0]

    # test keep-fields
    bib_db = clean_bib_database(
        load_bib(directory / "zotero-keep-fields.bib"),
        keep_fields=dict(article={"title", "issn"}),
    )
    assert "title" in bib_db.entries[0]
    assert "issn" in bib_db.entries[0]
    assert "author" not in bib_db.entries[0]
    assert "year" not in bib_db.entries[0]

    # test skip
    bib_db = clean_bib_database(
        load_bib(directory / "zotero-keep-fields.bib"),
        keep_fields=dict(book={"title", "issn"}),
    )
    assert "author" in bib_db.entries[0]


def test_clean_bib_database_invalid_args():
    """Test passing invalid argument to clean_bib_database."""
    with pytest.raises(
        TypeError, match="'bib_database' must be an instance of BibDatabase"
    ):
        clean_bib_database(101)
    directory = Path(__file__).parent / "data"
    with pytest.raises(
        TypeError, match="'exclude' must be an instance of list or tuple"
    ):
        clean_bib_database(
            load_bib(directory / "zotero-articles.bib"), exclude=101
        )
    with pytest.raises(TypeError, match="Item must be an instance of str"):
        clean_bib_database(
            load_bib(directory / "zotero-articles.bib"), exclude=[101]
        )
    with pytest.raises(
        ValueError, match="Invalid value for the 'exclude' parameter"
    ):
        clean_bib_database(
            load_bib(directory / "zotero-articles.bib"), exclude=["101"]
        )
    with pytest.raises(
        TypeError,
        match="'keep_fields' must be an instance of dict or None",
    ):
        clean_bib_database(
            load_bib(directory / "zotero-articles.bib"),
            exclude=["gramfort_mne_2014"],
            keep_fields=101,
        )
    with pytest.raises(TypeError, match="Item must be an instance of str"):
        clean_bib_database(
            load_bib(directory / "zotero-articles.bib"),
            exclude=["gramfort_mne_2014"],
            keep_fields={101: {"test"}},
        )
    with pytest.raises(TypeError, match="Item must be an instance of str"):
        clean_bib_database(
            load_bib(directory / "zotero-articles.bib"),
            exclude=["gramfort_mne_2014"],
            keep_fields={"article": {101}},
        )
    with pytest.raises(TypeError, match="Item must be an instance of set"):
        clean_bib_database(
            load_bib(directory / "zotero-articles.bib"),
            exclude=["gramfort_mne_2014"],
            keep_fields={"article": ["101"]},
        )
