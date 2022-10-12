from typing import List

from bibtexparser.bibdatabase import BibDatabase

from .check import check_bib_database
from .utils._checks import _check_type, _check_value


def clean(bib_database: BibDatabase, exclude: List[str] = []) -> BibDatabase:
    """Check and clean a BibTex database.

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
    check_bib_database(bib_database, exclude)

    # reset entries dictionary
    bib_database._entries_dict = {}

    # remove un-wanted fields
    keep_fields = {
        "author",
        "doi",
        "journal",
        "month",
        "number",
        "pages",
        "title",
        "volume",
        "year",
    }
    for k, entry in enumerate(bib_database.entries):
        if entry["ID"] in exclude:
            continue
        fields_to_remove = [
            field for field in set(entry) - keep_fields if field.islower()
        ]
        for field in fields_to_remove:
            del bib_database.entries[k][field]

    # make entries dictionary
    bib_database._make_entries_dict()

    return bib_database
