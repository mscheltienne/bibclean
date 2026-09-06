from __future__ import annotations

import click

from bibclean.utils.config import sys_info


@click.command(name="sys-info")
@click.option(
    "--extra",
    help="Display information for optional dependencies.",
    is_flag=True,
)
@click.option(
    "--developer",
    help="Display information for developer dependencies.",
    is_flag=True,
)
def run(extra: bool, developer: bool) -> None:
    """Print the platform, Python and dependency versions."""
    sys_info(extra=extra, developer=developer)
