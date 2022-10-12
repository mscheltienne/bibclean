from typing import List

from bibtexparser.bibdatabase import BibDatabase

from .utils._logs import logger
from .check import check_bib_database
from .utils._checks import _check_type, _check_value


def clean_bib_database(
    bib_database: BibDatabase, exclude: List[str] = []
) -> BibDatabase:
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

    Notes
    -----
    For now, this function was design to handle article entries.
    """
    _check_type(bib_database, (BibDatabase,), "bib_database")
    _check_type(exclude, (list, tuple), "exclude")
    for elt in exclude:
        _check_type(elt, (str,))
        _check_value(elt, bib_database.entries_dict)
    check_bib_database(bib_database, exclude)

    # reset entries dictionary
    logger.debug("Resetting the entry dictionary.")
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
            logger.info(
                "Entry '%s' is listed for exlusion. Skipping.", entry["ID"]
            )
            continue
        # determine the fields to remove
        fields_to_remove = [
            field for field in set(entry) - keep_fields if field.islower()
        ]
        # logging
        if len(fields_to_remove) == 0:
            logger.debug(
                "No field will be removed from entry '%s'.", entry["ID"]
            )
        else:
            logger.debug(
                "The fields %s will be removed from entry '%s'.",
                fields_to_remove,
                entry["ID"],
            )
        # remove fields
        for field in fields_to_remove:
            del bib_database.entries[k][field]

    # make entries dictionary
    logger.debug("Remaking the entry dictionary.")
    bib_database._make_entries_dict()

    return bib_database
