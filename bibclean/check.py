from typing import List

from bibtexparser.bibdatabase import BibDatabase

from .utils._checks import _check_type, _check_value


def check(bib_database: BibDatabase, exclude: List[str] = []) -> BibDatabase:
    """Check a BibTex database.

    Parameters
    ----------
    bib_database : BibDatabase
        BibTex database.
    exclude : TYPE, optional
        DESCRIPTION. The default is list().

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

    # check for duplicate entries with the same cite key
    if len(bib_database.entries) != len(bib_database.entries_dict):
        raise RuntimeError(
            "The BibTex file contain duplicate entries with the same cite key."
        )
