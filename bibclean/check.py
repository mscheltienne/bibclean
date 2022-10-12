from typing import Dict, List

from bibtexparser.bibdatabase import BibDatabase

from .utils._checks import _check_type, _check_value
from ._typing import Entry, Entries


def check(bib_database: BibDatabase, exclude: List[str] = []) -> BibDatabase:
    """Check a BibTex database.

    Parameters
    ----------
    bib_database : BibDatabase
        BibTex database.
    exclude : list of str
        List of entries to ignore. An entry is specified by its cite key.

    Returns
    -------
    bib_database : BibDatabase
        BibTex database.
    """
    _check_type(bib_database, (BibDatabase,), "bib_database")
    _check_type(exclude, (list, tuple), "exclude")
    for elt in exclude:
        _check_type(elt, (str,))
        _check_value(elt, bib_database.entries_dict)

    entries = [entry for entry in bib_database.entries if entry["ID"] not in exclude]
    entries_dict = {cite_key: entry for cite_key, entry in bib_database.entries_dict.items() if cite_key not in exclude}

    # check for duplicate entries
    _check_duplicate_entries(entries, entries_dict)


def _check_duplicate_entries(entries: Entries, entries_dict: Dict[str, Entry]):
    """Check for duplicate entries."""
    # check for duplicate entries with the same cite key
    if len(entries) != len(entries_dict):
        raise RuntimeError(
            "The BibTex file contains duplicate entries with the same cite "
            "key."
        )

    # check minimum set of keys for hash
    for entry in entries_dict.values():
        if any(field not in entry for field in ("year", "author", "title")):
            raise RuntimeError(
                "The BibTex file contains entries that are missing some basic "
                "information: year, author, title."
            )

    # define hash as (title, authors, year)
    hashes = [hash((entry["year"], entry["author"], entry["title"]) for entry in entries)]
    if len(hashes) != len(set(hashes)):
        raise RuntimeError(
            "The BibTex file contains duplicate entries with different cite "
            "keys."
        )
