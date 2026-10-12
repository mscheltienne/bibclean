from __future__ import annotations

import click

from bibclean.utils.config import sys_info


@click.command(
    name="sys-info", help="Print the platform, Python and dependency versions."
)
@click.option(
    "--developer",
    help="Display information for developer dependencies.",
    is_flag=True,
)
def run(developer: bool) -> None:
    """Print the platform, Python and dependency versions.

    Parameters
    ----------
    developer : bool
        Also print the developer dependencies.
    """
    sys_info(developer=developer)
