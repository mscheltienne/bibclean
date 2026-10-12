"""Print the platform, Python and hardware of the machine, for CI logs.

Run with ``uv run --no-sync --with psutil python tools/sys_info.py``.
"""

from __future__ import annotations

import platform
import sys

import psutil


def main() -> None:
    """Print one line per property of the machine."""
    gib = 2**30
    rows = {
        "Platform": platform.platform(),
        "Python": sys.version.replace("\n", " "),
        "Executable": sys.executable,
        "CPU": platform.processor() or platform.machine(),
        "Physical cores": psutil.cpu_count(logical=False),
        "Logical cores": psutil.cpu_count(logical=True),
        "RAM": f"{psutil.virtual_memory().total / gib:0.1f} GiB",
        "SWAP": f"{psutil.swap_memory().total / gib:0.1f} GiB",
    }
    for name, value in rows.items():
        print(f"{name + ':':<16}{value}")  # noqa: T201


if __name__ == "__main__":
    main()
