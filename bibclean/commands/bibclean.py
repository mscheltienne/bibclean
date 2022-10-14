import argparse

from .. import clean_bib_database
from ..config import load_config
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
    args = parser.parse_args()

    # load
    bib_database = load_bib(args.bib, encoding=args.encoding)

    # determine configuration and clean
    if args.config is None:
        required_fields = None
        keep_fields = None
    else:
        required_fields, keep_fields = load_config(args.config)
    bib_database = clean_bib_database(
        bib_database, required_fields=required_fields, keep_fields=keep_fields
    )

    # save
    output = args.bib if args.output is None else args.output
    overwrite = True if args.output is None else args.overwrite
    save_bib(bib_database, output, encoding=args.encoding, overwrite=overwrite)
