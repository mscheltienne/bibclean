from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from typing import IO


@dataclass(slots=True, frozen=True)
class Diagnostic:
    """One reported violation.

    Parameters
    ----------
    path : str
        File the violation belongs to, as typed on the command line.
    line : int | None
        1-based line, None for a file-level finding.
    column : int | None
        1-based column, None for a file-level finding.
    rule : str | None
        Name of the rule, None for a file-level finding.
    message : str
        Description of the violation.
    fixable : bool
        True when running ``bibclean fix`` resolves the violation.
    """

    path: str
    line: int | None
    column: int | None
    rule: str | None
    message: str
    fixable: bool


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """Render a count with the matching form of a noun.

    Parameters
    ----------
    count : int
        Number of items.
    singular : str
        Singular form of the noun.
    plural : str | None
        Plural form, defaulting to the singular with an ``'s'`` appended.

    Returns
    -------
    str
        The count and the noun, e.g. ``'1 violation'`` or ``'2 violations'``.
    """
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def format_diagnostic(diagnostic: Diagnostic, *, color: bool) -> str:
    """Render one diagnostic as a single line.

    Parameters
    ----------
    diagnostic : Diagnostic
        Diagnostic to render.
    color : bool
        Style the pieces with ANSI escape codes.

    Returns
    -------
    str
        ``'<path>:<line>:<column>: <rule> <message>'`` for a positioned finding,
        ``'<path>: <message>'`` for a file-level one, with ``' [*]'`` appended
        when the finding is fixable.
    """
    if color:
        import click

        path = click.style(diagnostic.path, bold=True)
        marker = click.style(" [*]", fg="cyan") if diagnostic.fixable else ""
        if diagnostic.rule is None:
            return f"{path}: {diagnostic.message}{marker}"
        rule = click.style(
            diagnostic.rule, fg="yellow" if diagnostic.fixable else "red"
        )
        return (
            f"{path}:{diagnostic.line}:{diagnostic.column}: "
            f"{rule} {diagnostic.message}{marker}"
        )
    marker = " [*]" if diagnostic.fixable else ""
    if diagnostic.rule is None:
        return f"{diagnostic.path}: {diagnostic.message}{marker}"
    return (
        f"{diagnostic.path}:{diagnostic.line}:{diagnostic.column}: "
        f"{diagnostic.rule} {diagnostic.message}{marker}"
    )


def sort_diagnostics(
    diagnostics: Iterable[Diagnostic], file_order: Sequence[str]
) -> list[Diagnostic]:
    """Order diagnostics by file, then by position.

    Parameters
    ----------
    diagnostics : iterable of Diagnostic
        Diagnostics to order.
    file_order : sequence of str
        Paths in the order they were given on the command line.

    Returns
    -------
    list of Diagnostic
        The diagnostics, stably sorted. File-level findings come last for their
        file.
    """
    order = {path: index for index, path in enumerate(file_order)}

    def key(diagnostic: Diagnostic) -> tuple[int, int, int]:
        return (
            order.get(diagnostic.path, len(order)),
            diagnostic.line if diagnostic.line is not None else sys.maxsize,
            diagnostic.column if diagnostic.column is not None else sys.maxsize,
        )

    return sorted(diagnostics, key=key)


def summary_check(diagnostics: Sequence[Diagnostic]) -> str:
    """Build the summary line of ``bibclean check``.

    Parameters
    ----------
    diagnostics : sequence of Diagnostic
        Every diagnostic of the run.

    Returns
    -------
    str
        ``'Found N violations (M fixable).'``
    """
    fixable = sum(1 for diagnostic in diagnostics if diagnostic.fixable)
    return f"Found {pluralize(len(diagnostics), 'violation')} ({fixable} fixable)."


def summary_fix(n_fixed: int, n_written: int, *, diff: bool) -> str:
    """Build the summary line of ``bibclean fix``.

    Parameters
    ----------
    n_fixed : int
        Number of fixable violations resolved.
    n_written : int
        Number of files written, or that would be written with ``--diff``.
    diff : bool
        True when nothing was written because ``--diff`` was given.

    Returns
    -------
    str
        ``'Fixed N violations, wrote M files.'``
    """
    verb = "would write" if diff else "wrote"
    return (
        f"Fixed {pluralize(n_fixed, 'violation')}, "
        f"{verb} {pluralize(n_written, 'file')}."
    )


def use_color(stream: IO[str]) -> bool:
    """Decide whether a stream should carry ANSI escape codes.

    Parameters
    ----------
    stream : file-like
        Output stream.

    Returns
    -------
    bool
        False when ``NO_COLOR`` is set to a non-empty value, when ``TERM`` is
        ``'dumb'`` or when the stream is not a terminal.
    """
    if os.environ.get("NO_COLOR", "") != "":
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return bool(stream.isatty())
