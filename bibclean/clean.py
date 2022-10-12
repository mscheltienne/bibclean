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
    check_bib_database(bib_database, exclude)
