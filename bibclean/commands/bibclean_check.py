import argparse

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

    load_bib(args.bib)

    raise NotImplementedError("A check-only mode will be soon implemented.")
