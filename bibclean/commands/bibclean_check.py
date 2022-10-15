import argparse
import sys
from copy import deepcopy
from typing import Optional

from bibtexparser import dumps

from .. import check_bib_database, clean_bib_database, logger
from .._exception import DuplicateEntry, MissingReqField
from ..config import load_config
from ..io import load_bib


class ReturnCode:
    no_violations_found = 0
    violations_found = 1
    invalid_options = 2


def run():
    """Run bibclean-check() command."""
    parser = argparse.ArgumentParser(
        prog=f"{__package__.split('.')[0]}-check",
        description="confirms that a .bib file is processed.",
    )
    parser.add_argument(
        "bib",
        type=str,
        metavar="path",
        help="path to the .bib file to clean. If an output is not provided, "
        "this file is overwritten.",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="path",
        help="path to the TOML configuration.",
        default=None,
    )
    args = parser.parse_args()

    try:
        sys.exit(_run(args.bib, args.config))
    except KeyboardInterrupt:
        pass


def _run(file: str, config: Optional[str]):
    """Run bibclean-check() command and return an exit-code."""
    try:
        bib_database = load_bib(file)
        if config is None:
            required_fields = None
            keep_fields = None
            exclude = list()
        else:
            required_fields, keep_fields, exclude = load_config(config)
        check_bib_database(bib_database, exclude, required_fields)
        bib_database_clean = clean_bib_database(
            deepcopy(bib_database),
            exclude,
            keep_fields,
        )
    except (DuplicateEntry, MissingReqField):
        return ReturnCode.violations_found
    except Exception:
        return ReturnCode.invalid_options

    # check that the file is sorted
    original = dumps(bib_database)
    cleaned = dumps(bib_database_clean)
    if original != cleaned:
        logger.error(
            "The provided '.bib' file is not properly formatted. Please use "
            "the 'bibclean' command to auto-format the entries."
        )
        exit_code = ReturnCode.violations_found
    else:
        exit_code = ReturnCode.no_violations_found
    return exit_code
