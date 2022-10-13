import pytest

from bibclean.io import load_bib, save_bib


def test_load_bib():
    """Test loading of BibTex files."""
    pass


def test_load_bib_invalid_args():
    """Test passing invalid arguments to load_bib()."""
    with pytest.raises(
        TypeError, match="'file' must be an instance of str or Path"
    ):
        load_bib(101)
    with pytest.raises(
        IOError,
        match="The provided file extension is not '.bib'. '.101' is invalid.",
    ):
        load_bib("101.101")
    with pytest.raises(IOError, match="The provided file does not exist."):
        load_bib("101.bib")


def test_save_bib(tmp_path):
    """Test saving of BibTex files."""
    pass


def test_save_bib_invalid_args():
    """Test passing invalid arguments to save_bib()."""
    with pytest.raises(
        TypeError, match="'bib_database' must be an instance of BibDatabase"
    ):
        save_bib(101, "101.bib")
