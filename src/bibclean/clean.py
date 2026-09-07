from __future__ import annotations

from typing import TYPE_CHECKING

from bibtexparser.bibdatabase import BibDatabase

from bibclean.config import _load_default_config
from bibclean.utils._checks import check_type, check_value
from bibclean.utils.logs import logger

if TYPE_CHECKING:
    from bibclean._typing import Entry


def clean_bib_database(
    bib_database: BibDatabase,
    exclude: list[str] | tuple[str, ...] = (),
    keep_fields: dict[str, set[str]] | None = None,
) -> BibDatabase:
    """Check and clean a BibTex database.

    Parameters
    ----------
    bib_database : ``BibDatabase``
        BibTex database.
    exclude : list of str
        List of entries to ignore. An entry is specified by its cite key.
    keep_fields : dict
        Fields to keep for each entry type. If None, a default configuration is
        loaded. The dictionary is defined with the entry-type as key (`str`) and
        the required fields as value (`set` of `str`).

    Returns
    -------
    bib_database : ``BibDatabase``
        BibTex database.
    """
    check_type(bib_database, (BibDatabase,), "bib_database")
    check_type(exclude, (list, tuple), "exclude")
    for elt in exclude:
        check_type(elt, (str,))
        check_value(elt, bib_database.entries_dict, "exclude")
    check_type(keep_fields, (dict, None), "keep_fields")
    if isinstance(keep_fields, dict):
        for key, value in keep_fields.items():
            check_type(key, (str,))
            check_type(value, (set,))
            for v in value:
                check_type(v, (str,))
    else:
        _, keep_fields = _load_default_config()

    # add URL and DOI to the fields to keep, they will be handled later
    for entry_type in keep_fields:
        keep_fields[entry_type].update({"url", "doi"})

    # remove un-wanted fields
    for k, entry in enumerate(bib_database.entries):
        if entry["ID"] in exclude:
            logger.info("Entry '%s' is listed for exclusion. Skipping.", entry["ID"])
            continue

        entry_type = entry["ENTRYTYPE"]
        if entry_type not in keep_fields:
            continue

        # determine the fields to remove
        fields_to_remove = [
            field for field in set(entry) - keep_fields[entry_type] if field.islower()
        ]
        # logging
        if len(fields_to_remove) == 0:
            logger.debug("No field will be removed from entry '%s'.", entry["ID"])
        else:
            logger.debug(
                "The fields %s will be removed from entry '%s'.",
                fields_to_remove,
                entry["ID"],
            )
        # remove fields
        for field in fields_to_remove:
            del bib_database.entries[k][field]

        # clean doi and url
        need_cleaning = _clean_doi_url(entry)
        if need_cleaning:
            del bib_database.entries[k]["url"]

    # remove comments
    bib_database.comments = []

    return bib_database


def _clean_doi_url(entry: Entry) -> bool:
    """Look for the fields DOI and URL.

    If only one is present, then we keep it, regardless of which one it is.
    If both are present, we remove the URL.
    """
    field = [key in entry for key in ("url", "doi")]
    if sum(field) == 0:
        logger.warning("Entry '%s' is missing a DOI or URL.", entry["ID"])
    elif sum(field) == 1:
        if field[0]:
            logger.warning("Entry '%s' has a URL instead of a DOI.", entry["ID"])
        return False
    elif sum(field) == 2:
        return True
    return False
