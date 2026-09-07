from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

import click
from bibtexparser import dumps

from bibclean._exception import DuplicateEntry, MissingReqField
from bibclean.check import check_bib_database
from bibclean.clean import clean_bib_database
from bibclean.config import load_config
from bibclean.io import load_bib
from bibclean.utils.logs import logger


class ReturnCode:  # noqa: D101
    no_violations_found = 0
    violations_found = 1
    violations_found_unfixable = 2
    invalid_options = 3


@click.command(name="check")
@click.argument("file", type=click.Path(path_type=Path))
@click.option(
    "-c",
    "--config",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to the TOML configuration.",
)
def run(file: Path, config: Path | None) -> None:
    """Check that a .bib file is already processed."""
    sys.exit(_run(file, config))


def _run(file: str | Path, config: str | Path | None) -> int:
    """Run the check and return an exit code."""
    try:
        bib_database = load_bib(file)
        if config is None:
            required_fields = None
            keep_fields = None
            exclude = []
        else:
            required_fields, keep_fields, exclude = load_config(config)
        check_bib_database(bib_database, exclude, required_fields)
        bib_database_clean = clean_bib_database(
            deepcopy(bib_database), exclude, keep_fields
        )
    except (DuplicateEntry, MissingReqField):
        return ReturnCode.violations_found_unfixable
    except Exception:
        return ReturnCode.invalid_options
    if dumps(bib_database) != dumps(bib_database_clean):
        logger.error(
            "The provided '.bib' file is not properly formatted. Please use "
            "'bibclean fix' to auto-format the entries."
        )
        return ReturnCode.violations_found
    return ReturnCode.no_violations_found
