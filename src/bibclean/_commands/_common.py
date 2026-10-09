from __future__ import annotations

import codecs
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import click

from bibclean._config import ConfigError, ConfigResolver
from bibclean._diagnostics import (
    format_diagnostic,
    pluralize,
    sort_diagnostics,
    summary_check,
    summary_fix,
    use_color,
)
from bibclean._engine import ReadError, process, read_source, unified_diff, write_source
from bibclean._rules import RULE_NAMES
from bibclean._version import __version__

if TYPE_CHECKING:
    from collections.abc import Callable

    from bibclean._diagnostics import Diagnostic
    from bibclean._engine import Report

Mode = Literal["check", "fix"]


def common_options(f: Callable) -> Callable:
    """Add the arguments and options shared by ``check`` and ``fix``.

    Parameters
    ----------
    f : callable
        Function implementing the command.

    Returns
    -------
    callable
        The function, decorated with the file argument and the six shared
        options.
    """
    options = (
        click.option(
            "-q",
            "--quiet",
            is_flag=True,
            help="Print the summary line only.",
        ),
        click.option(
            "-v",
            "--verbose",
            is_flag=True,
            help="Report what is done with each file.",
        ),
        click.option(
            "--encoding",
            type=str,
            default="utf-8",
            show_default=True,
            callback=_validate_encoding,
            help="Encoding of the .bib files.",
        ),
        click.option(
            "--ignore",
            multiple=True,
            type=click.Choice(RULE_NAMES),
            metavar="RULE",
            help="Disable a rule, repeatable.",
        ),
        click.option(
            "--isolated",
            is_flag=True,
            help="Ignore every configuration file and use the defaults.",
        ),
        click.option(
            "-c",
            "--config",
            type=click.Path(dir_okay=False, exists=True, path_type=Path),
            default=None,
            help="Use this TOML file instead of the discovered configuration.",
        ),
        click.argument(
            "files",
            nargs=-1,
            required=True,
            type=click.Path(dir_okay=False, path_type=str),
        ),
    )
    for option in options:
        f = option(f)
    return f


def execute(
    files: tuple[str, ...],
    *,
    mode: Mode,
    config: Path | None,
    isolated: bool,
    ignore: tuple[str, ...],
    encoding: str,
    verbose: bool,
    quiet: bool,
    diff: bool,
) -> int:
    """Run one command over a set of files and print its output.

    Parameters
    ----------
    files : tuple of str
        Files to process, as typed on the command line.
    mode : str
        ``'check'`` to report only, ``'fix'`` to rewrite the files.
    config : Path | None
        Configuration file used for every input instead of the discovered one.
    isolated : bool
        Ignore every configuration file and use the defaults.
    ignore : tuple of str
        Rule names added to the ``ignore`` set of whichever configuration applies.
    encoding : str
        Encoding used to decode and encode the files.
    verbose : bool
        Report what is done with each file on the error stream.
    quiet : bool
        Print the summary line only.
    diff : bool
        Print the unified diff of what ``fix`` would write and write nothing.

    Returns
    -------
    int
        0 when nothing was reported, 1 when a violation was found or a file was
        written, 2 when a file could not be handled.

    Raises
    ------
    click.UsageError
        If mutually exclusive options are combined.
    """
    if config is not None and isolated:
        raise click.UsageError("--config and --isolated are mutually exclusive")
    if verbose and quiet:
        raise click.UsageError("--verbose and --quiet are mutually exclusive")
    ordered = _dedupe(files)
    resolver = ConfigResolver(
        known_rules=RULE_NAMES,
        override=config,
        isolated=isolated,
        extra_ignore=ignore,
    )
    if verbose:
        _echo_verbose(f"bibclean {__version__}")
    if config is not None:
        try:
            resolver.for_file(Path(ordered[0]))
        except ConfigError as exc:
            _echo_error(str(config), exc.message)
            return 2
    diagnostics: list[Diagnostic] = []
    errors = 0
    written = 0
    fixed = 0
    for file in ordered:
        try:
            configuration = resolver.for_file(Path(file))
        except ConfigError as exc:
            _echo_error(file, exc.message)
            errors += 1
            continue
        try:
            source = read_source(Path(file), encoding)
        except ReadError as exc:
            _echo_error(file, str(exc))
            errors += 1
            continue
        try:
            report = process(file, source, configuration)
        except RuntimeError as exc:
            _echo_error(file, str(exc).removeprefix(f"{file}: "))
            errors += 1
            continue
        diagnostics.extend(report.diagnostics)
        status = "unchanged"
        if mode == "fix":
            fixed += sum(1 for item in report.diagnostics if item.fixable)
            if report.changed:
                if diff:
                    click.echo(unified_diff(file, source.text, report.output), nl=False)
                    status = "would write"
                else:
                    try:
                        write_source(Path(file), report.output, encoding)
                    except OSError as exc:
                        _echo_error(file, f"cannot write file: {exc.strerror or exc}")
                        errors += 1
                        continue
                    status = "written"
                written += 1
        if verbose:
            _echo_verbose(f"{file}: configuration {configuration.source or 'defaults'}")
            _echo_verbose(_status(file, report, mode=mode, status=status))
    color = use_color(sys.stdout)
    ordered_diagnostics = sort_diagnostics(diagnostics, ordered)
    if mode == "check":
        shown = ordered_diagnostics
        summary = summary_check(diagnostics) if diagnostics else None
    else:
        shown = [item for item in ordered_diagnostics if not item.fixable]
        summary = (
            summary_fix(fixed, written, diff=diff)
            if fixed or written or shown
            else None
        )
    if not quiet:
        for item in shown:
            click.echo(format_diagnostic(item, color=color), color=color)
    if summary is not None:
        click.echo(click.style(summary, bold=True) if color else summary, color=color)
    if errors:
        return 2
    if mode == "check":
        return 1 if diagnostics else 0
    return 1 if written or shown else 0


def _validate_encoding(ctx: click.Context, param: click.Parameter, value: str) -> str:
    """Reject an encoding name that Python does not know."""
    try:
        codecs.lookup(value)
    except LookupError:
        raise click.BadParameter(f"unknown encoding '{value}'")
    return value


def _dedupe(files: tuple[str, ...]) -> list[str]:
    """Drop repeated paths, keeping the first occurrence."""
    seen: dict[str, None] = {}
    for file in files:
        seen.setdefault(file, None)
    return list(seen)


def _echo_error(path: str, message: str) -> None:
    """Report a file that could not be handled."""
    click.echo(f"{path}: error: {message}", err=True)


def _echo_verbose(message: str) -> None:
    """Report progress on the error stream."""
    click.echo(message, err=True)


def _status(path: str, report: Report, *, mode: Mode, status: str) -> str:
    """Build the second verbose line of a file."""
    if mode == "check":
        if not report.diagnostics:
            return f"{path}: ok"
        return f"{path}: {pluralize(len(report.diagnostics), 'violation')}"
    unfixable = sum(1 for item in report.diagnostics if not item.fixable)
    line = f"{path}: {status}"
    if unfixable:
        return f"{line}, {pluralize(unfixable, 'unfixable violation')}"
    return line
