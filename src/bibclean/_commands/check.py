from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import click

from bibclean._commands._common import common_options, execute

if TYPE_CHECKING:
    from pathlib import Path


@click.command(name="check")
@common_options
def run(
    files: tuple[str, ...],
    config: Path | None,
    isolated: bool,
    ignore: tuple[str, ...],
    encoding: str,
    verbose: bool,
    quiet: bool,
) -> None:
    """Report the violations of one or more BibTeX files."""
    sys.exit(
        execute(
            files,
            mode="check",
            config=config,
            isolated=isolated,
            ignore=ignore,
            encoding=encoding,
            verbose=verbose,
            quiet=quiet,
            diff=False,
        )
    )
