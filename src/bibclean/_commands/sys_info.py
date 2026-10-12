from __future__ import annotations

import click


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
    # imported on use, so that check and fix do not pay for importlib.metadata
    from bibclean.utils.config import sys_info

    sys_info(developer=developer)
