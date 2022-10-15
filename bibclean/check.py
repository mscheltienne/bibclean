from typing import Dict, List, Optional, Set

import numpy as np
from bibtexparser.bibdatabase import BibDatabase

from ._exception import DuplicateEntry, MissingReqField
from ._typing import Entry
from .config import _load_default_config
from .utils._checks import _check_type, _check_value
from .utils._docs import fill_doc


@fill_doc
def check_bib_database(
    bib_database: BibDatabase,
    exclude: List[str] = [],
    required_fields: Optional[Dict[str, Set[str]]] = None,
) -> None:
    """Check a BibTex database.

    Parameters
    ----------
    bib_database : BibDatabase
        BibTex database.
    %(exclude)s
    %(required_fields)s
    """
    _check_type(bib_database, (BibDatabase,), "bib_database")
    _check_type(exclude, (list, tuple), "exclude")
    for elt in exclude:
        _check_type(elt, (str,))
        _check_value(elt, bib_database.entries_dict, "exclude")
    _check_type(required_fields, (dict, None), "required_fields")
    if isinstance(required_fields, dict):
        for key, value in required_fields.items():
            _check_type(key, (str,))
            _check_type(value, (set,))
            for v in value:
                _check_type(v, (str,))
    else:
        required_fields, _ = _load_default_config()

    entries = [
        entry for entry in bib_database.entries if entry["ID"] not in exclude
    ]

    # check for duplicate entries
    _check_duplicate_entries(entries)
    # check minimum fields
    _check_minimum_fields(
        entries,
        required_fields=required_fields,
    )


def _check_duplicate_entries(entries: List[Entry]) -> None:
    """Check for duplicate entries."""
    # check for duplicate entries with the same cite key
    idx = [entry["ID"] for entry in entries]
    if len(idx) != len(set(idx)):
        from collections import Counter

        duplicates = (
            f"{cite_key} ({n})"
            for cite_key, n in Counter(idx).items()
            if n != 1
        )
        raise DuplicateEntry(
            "The BibTex file contains duplicate entries with the same cite "
            f"key: {', '.join(duplicates)}."
        )

    # check minimum set of fields for hash
    hash_fields = {"year", "author", "title"}
    for entry in entries:
        if len(hash_fields - set(entry)) != 0:
            raise MissingReqField(
                f"The BibTex file entry '{entry['ID']}' is missing some basic "
                "information: year, author, title."
            )

    # define hash as (title, authors, year)
    hashes = [
        hash((entry["year"], entry["author"], entry["title"]))
        for entry in entries
    ]
    if len(hashes) != len(set(hashes)):
        from collections import Counter

        duplicates = list()
        duplicate_hashes = [
            hash_ for hash_, n in Counter(hashes).items() if n != 1
        ]
        hashes = np.array(hashes)
        for hash_ in duplicate_hashes:
            idx = np.where(hashes == hash_)[0]
            duplicates.append(f"({', '.join(entries[k]['ID'] for k in idx)})")
        raise DuplicateEntry(
            "The BibTex file contains duplicate entries with different cite "
            f"keys: {', '.join(duplicates)}."
        )


def _check_minimum_fields(
    entries: List[Entry],
    required_fields: Dict[str, Set[str]],
) -> None:
    """Check that each entry has the minimum required fields."""
    for entry in entries:
        entry_type = entry["ENTRYTYPE"]
        if entry_type not in required_fields:
            continue
        if len(required_fields[entry_type] - set(entry)) != 0:
            raise MissingReqField(
                f"The BibTex file entry '{entry['ID']}' is missing one of "
                f"the required field for a '{entry['ENTRYTYPE']}':"
                f"{', '.join(required_fields[entry_type])}."
            )
