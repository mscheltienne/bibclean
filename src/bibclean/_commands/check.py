from __future__ import annotations

import sys
from typing import Any

import click

from bibclean._commands._common import common_options, execute


@click.command(name="check")
@common_options
def run(files: tuple[str, ...], **options: Any) -> None:
    """Report the violations of one or more BibTeX files."""
    sys.exit(execute(files, mode="check", diff=False, **options))
