from typing import Dict

from bibtexparser.bibdatabase import BibDatabase


def get_entry_types(bib_database: BibDatabase) -> Dict[str, str]:
    """Retrieve the entry type from a BibTex database.

    Parameters
    ----------
    bib_database : BibDatabase
        BibTex database.

    Returns
    -------
    entry_types : dict
        A dictionary with the cite key as key and the type as value.
    """
    bib_database._make_entries_dict()
    return {
        cite_key: entry["ENTRYTYPE"]
        for cite_key, entry in bib_database.entries_dict.items()
    }
