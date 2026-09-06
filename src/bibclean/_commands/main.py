from __future__ import annotations

import click

from bibclean._commands.check import run as check
from bibclean._commands.fix import run as fix
from bibclean._commands.sys_info import run as sys_info


@click.group()
def run() -> None:
    """Main package entry-point."""  # noqa: D401


run.add_command(check)
run.add_command(fix)
run.add_command(sys_info)
