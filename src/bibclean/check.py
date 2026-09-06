from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from bibtexparser.bibdatabase import BibDatabase

from bibclean._exception import DuplicateEntry, MissingReqField
from bibclean.config import _load_default_config
from bibclean.utils._checks import check_type, check_value

if TYPE_CHECKING:
    from bibclean._typing import Entry


def check_bib_database(
    bib_database: BibDatabase,
    exclude: list[str] | tuple[str, ...] = (),
    required_fields: dict[str, set[str]] | None = None,
) -> None:
    """Check a BibTex database.

    Parameters
    ----------
    bib_database : ``BibDatabase``
        BibTex database.
    exclude : list of str
        List of entries to ignore. An entry is specified by its cite key.
    required_fields : dict
        Required fields for each entry type. If None, a default configuration
        is loaded. The dictionary is defined with the entry-type as key (`str`)
        and the required fields as value (`set` of `str`).
    """
    check_type(bib_database, (BibDatabase,), "bib_database")
    check_type(exclude, (list, tuple), "exclude")
    for elt in exclude:
        check_type(elt, (str,))
        check_value(elt, bib_database.entries_dict, "exclude")
    check_type(required_fields, (dict, None), "required_fields")
    if isinstance(required_fields, dict):
        for key, value in required_fields.items():
            check_type(key, (str,))
            check_type(value, (set,))
            for v in value:
                check_type(v, (str,))
    else:
        required_fields, _ = _load_default_config()

    entries = [entry for entry in bib_database.entries if entry["ID"] not in exclude]

    # check for duplicate entries
    _check_duplicate_entries(entries)
    # check minimum fields
    _check_minimum_fields(
        entries,
        required_fields=required_fields,
    )


def _check_duplicate_entries(entries: list[Entry]) -> None:
    """Check for duplicate entries."""
    # check for duplicate entries with the same cite key
    idx = [entry["ID"] for entry in entries]
    if len(idx) != len(set(idx)):
        duplicates = (
            f"{cite_key} ({n})" for cite_key, n in Counter(idx).items() if n != 1
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
        hash((entry["year"], entry["author"], entry["title"])) for entry in entries
    ]
    if len(hashes) != len(set(hashes)):
        duplicates = []
        duplicate_hashes = [hash_ for hash_, n in Counter(hashes).items() if n != 1]
        for hash_ in duplicate_hashes:
            idx = [k for k, h in enumerate(hashes) if h == hash_]
            duplicates.append(f"({', '.join(entries[k]['ID'] for k in idx)})")
        raise DuplicateEntry(
            "The BibTex file contains duplicate entries with different cite "
            f"keys: {', '.join(duplicates)}."
        )


def _check_minimum_fields(
    entries: list[Entry],
    required_fields: dict[str, set[str]],
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
