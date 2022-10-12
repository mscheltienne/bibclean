import argparse

from .. import clean_bib_database
from ..io import load_bib, save_bib


def run():
    """Run bibclean() command."""
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
    parser.add_argument(
        "-o", "--output",
        type=str,
        metavar="path",
        help="path to the output .bib file.",
        default=None,
    )
    parser.add_argument(
        "--overwrite",
        help="overwrite the file provided in --output if it exists.",
        action="store_true",
    )
    parser.add_argument(
        "--check",
        help="check that the .bib file is already cleaned.",
        action="store_true",
    )
    args = parser.parse_args()

    if args.check:
        raise NotImplementedError(
            "A check-only mode will be soon implemented."
        )

    bib_database = load_bib(args.bib)
    bib_database = clean_bib_database(bib_database)
    output = args.bib if args.output is None else args.output
    overwrite = True if args.output is None else args.overwrite
    save_bib(bib_database, output, overwrite=overwrite)
