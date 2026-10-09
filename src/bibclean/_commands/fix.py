from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import click

from bibclean._commands._common import common_options, execute

if TYPE_CHECKING:
    from pathlib import Path


@click.command(name="fix")
@common_options
@click.option(
    "--diff",
    is_flag=True,
    help="Print the changes instead of applying them.",
)
def run(
    files: tuple[str, ...],
    config: Path | None,
    isolated: bool,
    ignore: tuple[str, ...],
    encoding: str,
    verbose: bool,
    quiet: bool,
    diff: bool,
) -> None:
    """Fix and format one or more BibTeX files in place."""
    sys.exit(
        execute(
            files,
            mode="fix",
            config=config,
            isolated=isolated,
            ignore=ignore,
            encoding=encoding,
            verbose=verbose,
            quiet=quiet,
            diff=diff,
        )
    )
