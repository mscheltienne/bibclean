from typing import Dict, List, Optional, Set

from bibtexparser.bibdatabase import BibDatabase

from .check import check_bib_database
from .utils._checks import _check_type, _check_value
from .utils._logs import logger


def clean_bib_database(
    bib_database: BibDatabase,
    exclude: List[str] = [],
    keep_fields: Optional[Dict[str, Set[str]]] = None,
) -> BibDatabase:
    """Check and clean a BibTex database.

    Parameters
    ----------
    bib_database : BibDatabase
        BibTex database.
    exclude : list of str
        List of entries to ignore. An entry is specified by its cite key.
    keep_fields : dict | None
        Fields to keep for each entry type. If None, a default configuration
        is loaded. The dictionary format is:
            key : str - the entry type
            value : set of str - the fields to keep

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
    _check_type(keep_fields, (dict, None), "keep_fields")
    for key, value in keep_fields.items():
        _check_type(key, (str,))
        _check_type(value, (set,))
        for v in value:
            _check_type(v, (str,))
    check_bib_database(bib_database, exclude)

    # reset entries dictionary
    logger.debug("Resetting the entry dictionary.")
    bib_database._entries_dict = {}

    # add URL and DOI to the fields to keep, they will be handled later
    for entry_type in keep_fields:
        keep_fields[entry_type].update({"url", "doi"})

    # remove un-wanted fields
    for k, entry in enumerate(bib_database.entries):
        if entry["ID"] in exclude:
            logger.info(
                "Entry '%s' is listed for exclusion. Skipping.", entry["ID"]
            )
            continue

        entry_type = entry["ENTRYTYPE"]
        if entry_type not in keep_fields:
            continue

        # determine the fields to remove
        fields_to_remove = [
            field
            for field in set(entry) - keep_fields[entry_type]
            if field.islower()
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

    # remove comments
    bib_database.comments = []

    # clean doi and url
    _clean_doi_url()

    return bib_database


def _clean_doi_url():
    """Clean DOI and URL. Only one of the 2 is kept, preferably the DOI."""
    pass
