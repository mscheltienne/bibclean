from __future__ import annotations

import sys
from typing import Any

import click

from bibclean._commands._common import common_options, execute


@click.command(name="fix")
@common_options
@click.option(
    "--diff",
    is_flag=True,
    help="Print the changes instead of applying them.",
)
def run(files: tuple[str, ...], **options: Any) -> None:
    """Fix and format one or more BibTeX files in place."""
    sys.exit(execute(files, mode="fix", **options))
