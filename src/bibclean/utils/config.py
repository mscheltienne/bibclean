from __future__ import annotations

import platform
import sys
import tomllib
from functools import partial
from importlib.metadata import metadata, requires, version
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import IO

    from packaging.requirements import Requirement


def sys_info(
    fid: IO | None = None, *, extra: bool = False, developer: bool = False
) -> None:
    """Print the system information for debugging.

    Parameters
    ----------
    fid : file-like | None
        The file to write to, passed to :func:`print`. Can be None to use
        :data:`sys.stdout`.
    extra : bool
        If True, display information about optional dependencies.
    developer : bool
        If True, display information about developer dependencies, read from the
        ``pyproject.toml`` of ``bibclean`` installed from source.

    Raises
    ------
    RuntimeError
        If ``developer`` is True and the ``pyproject.toml`` of ``bibclean`` cannot be
        found.
    """
    from packaging.requirements import Requirement

    try:
        import psutil
    except ImportError:
        psutil = None

    ljust = 26
    out = partial(print, end="", file=fid)
    package = "bibclean"

    out("Platform:".ljust(ljust) + platform.platform() + "\n")
    out("Python:".ljust(ljust) + sys.version.replace("\n", " ") + "\n")
    out("Executable:".ljust(ljust) + sys.executable + "\n")
    out("CPU:".ljust(ljust) + platform.processor() + "\n")
    if psutil is not None:
        out("Physical cores:".ljust(ljust) + str(psutil.cpu_count(False)) + "\n")
        out("Logical cores:".ljust(ljust) + str(psutil.cpu_count(True)) + "\n")
        out("RAM:".ljust(ljust))
        out(f"{psutil.virtual_memory().total / float(2**30):0.1f} GB\n")
        out("SWAP:".ljust(ljust))
        out(f"{psutil.swap_memory().total / float(2**30):0.1f} GB\n")
    out(f"{package}:".ljust(ljust) + version(package) + "\n")

    out("\nCore dependencies\n")
    dependencies = [Requirement(elt) for elt in requires(package) or ()]
    core_dependencies = [dep for dep in dependencies if "extra" not in str(dep.marker)]
    _list_dependencies_info(out, ljust, package, core_dependencies)

    if extra:
        extras = metadata(package).get_all("Provides-Extra")
        if extras is not None:
            for key in sorted([elt for elt in extras if elt not in ("all", "full")]):
                extra_dependencies = [
                    dep
                    for dep in dependencies
                    if all(elt in str(dep.marker) for elt in ("extra", key))
                ]
                if len(extra_dependencies) == 0:
                    continue
                out(f"\nOptional '{key}' dependencies\n")
                _list_dependencies_info(out, ljust, package, extra_dependencies)

    if developer:
        # PEP 735 dependency groups are not part of the metadata.
        origin = Path(find_spec(package).origin)
        for folder in origin.parents[1:3]:  # support 'src' or 'flat' layout structure
            if (folder / "pyproject.toml").exists():
                pyproject = folder / "pyproject.toml"
                break
        else:
            raise RuntimeError(
                f"The pyproject.toml file for the package {package} could not be "
                "found. To retrieve developer dependencies, please install the package "
                "from source in an editable install, e.g. using 'uv sync'."
            )

        with open(pyproject, "rb") as fid:
            pyproject_data = tomllib.load(fid)
        dependency_groups = pyproject_data.get("dependency-groups", {})
        for key in sorted(dependency_groups):
            # Skip include-group references (dicts), only parse string dependencies
            dependencies = [
                Requirement(dep)
                for dep in dependency_groups[key]
                if isinstance(dep, str)
            ]
            if len(dependencies) == 0:
                continue
            out(f"\nDeveloper '{key}' dependencies\n")
            _list_dependencies_info(out, ljust, package, dependencies)


def _list_dependencies_info(
    out: Callable, ljust: int, package: str, dependencies: list[Requirement]
) -> None:
    """List the names and installed versions of dependencies.

    Parameters
    ----------
    out : Callable
        The function writing a line of output.
    ljust : int
        The width the dependency names are padded to.
    package : str
        The package whose dependencies are listed; skipped if listed as a dependency.
    dependencies : list of Requirement
        The dependencies to list.
    """
    unicode = sys.stdout.encoding.lower().startswith("utf")
    if unicode:
        ljust += 1

    not_found: list[Requirement] = []
    for dep in dependencies:
        if dep.name == package:
            continue
        try:
            version_ = version(dep.name)
        except Exception:
            not_found.append(dep)
            continue

        output = f"✔︎ {dep.name}" if unicode else dep.name
        if len(dep.specifier) != 0:
            output += f" ({str(dep.specifier)})"
        output += ":"
        output = output.ljust(ljust) + version_ + "\n"
        out(output)

    if len(not_found) != 0:
        not_found = [
            f"{dep.name} ({str(dep.specifier)})"
            if len(dep.specifier) != 0
            else dep.name
            for dep in not_found
        ]
        if unicode:
            out(f"✘ Not installed: {', '.join(not_found)}\n")
        else:
            out(f"Not installed: {', '.join(not_found)}\n")
