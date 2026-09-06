from __future__ import annotations

import sys
from pathlib import Path

import click

from bibclean._exception import DuplicateEntry, MissingReqField
from bibclean.check import check_bib_database
from bibclean.clean import clean_bib_database
from bibclean.config import load_config
from bibclean.io import load_bib, save_bib


class ReturnCode:  # noqa: D101
    no_violations_found = 0
    violations_found_unfixable = 2
    invalid_options = 3
    could_not_save = 4


@click.command(name="fix")
@click.argument("file", type=click.Path(path_type=Path))
@click.option(
    "-c",
    "--config",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to the TOML configuration.",
)
@click.option(
    "--encoding",
    type=str,
    default="utf-8",
    show_default=True,
    help="Encoding of the .bib file.",
)
def run(file: Path, config: Path | None, encoding: str) -> None:
    """Check and clean a .bib file in place."""
    sys.exit(_run(file, config, encoding))


def _run(file: str | Path, config: str | Path | None, encoding: str = "utf-8") -> int:
    """Run the fix and return an exit code."""
    try:
        bib_database = load_bib(file, encoding=encoding)
        if config is None:
            required_fields = None
            keep_fields = None
            exclude = []
        else:
            required_fields, keep_fields, exclude = load_config(config)
        check_bib_database(bib_database, exclude, required_fields)
        bib_database = clean_bib_database(bib_database, exclude, keep_fields)
    except (DuplicateEntry, MissingReqField):
        return ReturnCode.violations_found_unfixable
    except Exception:
        return ReturnCode.invalid_options
    try:
        save_bib(bib_database, file, encoding=encoding, overwrite=True)
    except Exception:
        return ReturnCode.could_not_save
    return ReturnCode.no_violations_found
