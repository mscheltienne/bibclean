from __future__ import annotations

import click

from bibclean._commands.check import run as check
from bibclean._commands.fix import run as fix
from bibclean._commands.sys_info import run as sys_info
from bibclean._version import __version__


@click.group()
@click.version_option(
    version=__version__, prog_name="bibclean", message="%(prog)s %(version)s"
)
def run() -> None:
    """Lint and format BibTeX files."""


run.add_command(check)
run.add_command(fix)
run.add_command(sys_info)
