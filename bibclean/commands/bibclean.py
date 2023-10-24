import argparse

from bibtexparser import dumps

from .. import check_bib_database, clean_bib_database
from .._exception import DuplicateEntry, MissingReqField
from ..config import load_config
from ..io import load_bib, save_bib


class ReturnCode:  # noqa: D101
    no_violations_found = 0
    violations_fixed = 1
    violations_found_unfixable = 2
    invalid_options = 3
    could_not_save = 4


def run():
    """Run bibclean() command."""
    parser = argparse.ArgumentParser(
        prog=f"{__package__.split('.')[0]}", description="cleans a .bib file."
    )
    parser.add_argument(
        "bib",
        type=str,
        metavar="path",
        help="path to the .bib file to clean. If an output is not provided, "
        "this file is overwritten.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="path",
        help="path to the output .bib file.",
        default=None,
    )
    parser.add_argument(
        "-e",
        "--encoding",
        type=str,
        metavar="str",
        help="encoding of the .bib file.",
        default="utf-8",
    )
    parser.add_argument(
        "--overwrite",
        help="overwrite the file provided in --output if it exists.",
        action="store_true",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="path",
        help="path to the TOML configuration.",
        default=None,
    )
    parser.add_argument(
        "--exit-non-zero-on-fix",
        help="exit with a non-zero status code if the .bib file was changed.",
        action="store_true",
    )
    args = parser.parse_args()

    try:
        # load
        bib_database = load_bib(args.bib, encoding=args.encoding)

        # determine configuration and clean
        if args.config is None:
            required_fields = None
            keep_fields = None
            exclude = list()
        else:
            required_fields, keep_fields, exclude = load_config(args.config)
        check_bib_database(bib_database, exclude, required_fields)
        bib_database_clean = clean_bib_database(bib_database, exclude, keep_fields)
    except (DuplicateEntry, MissingReqField):
        return ReturnCode.violations_found_unfixable
    except Exception:
        return ReturnCode.invalid_options

    original = dumps(bib_database)
    cleaned = dumps(bib_database_clean)
    if args.exit_non_zero_on_fix:
        exit_code = (
            ReturnCode.no_violations_found
            if original == cleaned
            else ReturnCode.violations_fixed
        )
    else:
        exit_code = ReturnCode.no_violations_found

    # save
    try:
        output = args.bib if args.output is None else args.output
        overwrite = True if args.output is None else args.overwrite
        save_bib(bib_database, output, encoding=args.encoding, overwrite=overwrite)
    except Exception:
        exit_code = ReturnCode.could_not_save
    return exit_code
