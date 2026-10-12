from __future__ import annotations

import sys
from typing import Any

import click

from bibclean._commands._common import common_options, execute


@click.command(name="fix", help="Fix and format one or more BibTeX files in place.")
@common_options
@click.option(
    "--diff",
    is_flag=True,
    help="Print the changes instead of applying them.",
)
def run(files: tuple[str, ...], **options: Any) -> None:
    """Fix and format one or more BibTeX files in place.

    Parameters
    ----------
    files : tuple of str
        Files to fix, as typed on the command line.
    **options : dict
        The options of ``fix``, passed to ``execute``.
    """
    sys.exit(execute(files, mode="fix", **options))
