import argparse
from copy import deepcopy

from bibtexparser import dumps

from .. import clean_bib_database
from ..io import load_bib


def run():
    """Run bibclean-check() command."""
    parser = argparse.ArgumentParser(
        prog=f"{__package__.split('.')[0]}-sys_info", description="sys_info"
    )
    parser.add_argument(
        "bib",
        type=str,
        metavar="path",
        help="path to the .bib file to clean. If an output is not provided, "
        "this file is overwritten.",
    )
    args = parser.parse_args()

    bib_database = load_bib(args.bib)
    bib_database_clean = clean_bib_database(deepcopy(bib_database))

    # check that the file is sorted
    original = dumps(bib_database)
    cleaned = dumps(bib_database_clean)
    if original != cleaned:
        raise RuntimeError(
            "The provided '.bib' file is not properly formatted. Please use "
            "the 'bibclean' command to auto-format the entries."
        )
