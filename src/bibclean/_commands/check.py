from __future__ import annotations

import sys
from typing import Any

import click

from bibclean._commands._common import common_options, execute


@click.command(name="check", help="Report the violations of one or more BibTeX files.")
@common_options
def run(files: tuple[str, ...], **options: Any) -> None:
    """Report the violations of one or more BibTeX files.

    Parameters
    ----------
    files : tuple of str
        Files to check, as typed on the command line.
    **options : dict
        The options shared by ``check`` and ``fix``, passed to ``execute``.
    """
    sys.exit(execute(files, mode="check", diff=False, **options))
