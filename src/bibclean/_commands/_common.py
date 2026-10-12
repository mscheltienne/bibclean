from __future__ import annotations

import codecs
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import click

from bibclean._config import ConfigError, find_config, load_config
from bibclean._engine import process, unified_diff
from bibclean._rules import RULE_NAMES

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import IO

    from bibclean._config import Config
    from bibclean._rules._base import Diagnostic

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
        The function, decorated with the file argument and the five shared options.
    """
    options = (
        click.option(
            "-q",
            "--quiet",
            is_flag=True,
            help="Print only the summary line, not the violations.",
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
    quiet: bool,
    diff: bool,
) -> int:
    """Run one command over a set of files and print its output.

    Parameters
    ----------
    files : tuple of str
        Files to process, as typed on the command line. A file named twice is
        processed once, under its first spelling.
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
    quiet : bool
        Print only the summary line, not the violations.
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
        If ``--config`` and ``--isolated`` are combined.
    """
    if config is not None and isolated:
        raise click.UsageError("--config and --isolated are mutually exclusive")
    override: Config | None = None
    if isolated or config is not None:
        try:
            override = load_config(
                None if isolated else config.resolve(), extra_ignore=ignore
            )
        except ConfigError as exc:
            _echo_error(str(config), str(exc))
            return 2
    lines: list[str] = []
    errors = 0
    written = 0
    fixable = 0
    unique: dict[Path, str] = {}
    for file in files:
        unique.setdefault(Path(file).resolve(), file)
    for path, file in unique.items():
        try:
            configuration = override or load_config(
                find_config(path.parent), extra_ignore=ignore
            )
            data = path.read_bytes()
            report = process(data, encoding, configuration)
        except ConfigError as exc:
            error = str(exc)
        except OSError as exc:
            error = f"cannot read file: {exc.strerror or exc}"
        except UnicodeDecodeError as exc:
            error = (
                f"cannot decode file with encoding '{encoding}': "
                f"{exc.reason} at byte {exc.start}"
            )
        else:
            error = None
            fixable += sum(item.fixable for item in report.diagnostics)
            lines.extend(
                format_diagnostic(file, item)
                for item in report.diagnostics
                if mode == "check" or not item.fixable
            )
            if mode == "fix" and report.output is not None:
                if diff:
                    before = data.decode(encoding)
                    after = report.output.decode(encoding)
                    click.echo(unified_diff(file, before, after), nl=False)
                else:
                    try:
                        path.write_bytes(report.output)
                    except OSError as exc:
                        error = f"cannot write file: {exc.strerror or exc}"
                written += error is None
        if error is not None:
            _echo_error(file, error)
            errors += 1
    if mode == "check":
        summary = f"Found {pluralize(len(lines), 'violation')} ({fixable} fixable)."
        failed = bool(lines)
    else:
        fixed, wrote = ("Would fix", "would write") if diff else ("Fixed", "wrote")
        summary = (
            f"{fixed} {pluralize(fixable, 'violation')}, "
            f"{wrote} {pluralize(written, 'file')}."
        )
        failed = bool(written or lines)
    color = use_color(sys.stdout)
    if not quiet:
        for line in lines:
            click.echo(line, color=color)
    if failed or fixable:
        click.echo(click.style(summary, bold=True), color=color)
    return 2 if errors else int(failed)


def format_diagnostic(path: str, diagnostic: Diagnostic) -> str:
    """Render one diagnostic as a single styled line.

    Parameters
    ----------
    path : str
        File the diagnostic belongs to, as typed on the command line.
    diagnostic : Diagnostic
        Diagnostic to render.

    Returns
    -------
    str
        ``'<path>:<line>:<column>: <rule> <message>'`` for a positioned violation,
        ``'<path>: <message>'`` for a file-level one, with ``' [*]'`` appended when
        the violation is fixable. The pieces carry ANSI escape codes, which
        ``click.echo`` strips when colours are disabled.
    """
    location = click.style(path, bold=True)
    marker = click.style(" [*]", fg="cyan") if diagnostic.fixable else ""
    if diagnostic.position is None:
        return f"{location}: {diagnostic.message}{marker}"
    rule = click.style(diagnostic.rule, fg="yellow" if diagnostic.fixable else "red")
    position = diagnostic.position
    return (
        f"{location}:{position.line}:{position.column}: "
        f"{rule} {diagnostic.message}{marker}"
    )


def pluralize(count: int, singular: str) -> str:
    """Render a count with the matching form of a noun.

    Parameters
    ----------
    count : int
        Number of items.
    singular : str
        Singular form of the noun, made plural by appending an ``'s'``.

    Returns
    -------
    str
        The count and the noun, e.g. ``'1 violation'`` or ``'2 violations'``.
    """
    return f"{count} {singular if count == 1 else singular + 's'}"


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


def _validate_encoding(ctx: click.Context, param: click.Parameter, value: str) -> str:
    """Reject an encoding name that Python does not know.

    Parameters
    ----------
    ctx : click.Context
        Context of the command being parsed.
    param : click.Parameter
        The ``--encoding`` option.
    value : str
        Encoding name given on the command line.

    Returns
    -------
    str
        The encoding name, unchanged.

    Raises
    ------
    click.BadParameter
        If Python has no codec of that name.
    """
    try:
        codecs.lookup(value)
    except LookupError:
        raise click.BadParameter(f"unknown encoding '{value}'")
    return value


def _echo_error(path: str, message: str) -> None:
    """Report a file that could not be handled.

    Parameters
    ----------
    path : str
        File that could not be handled, as typed on the command line.
    message : str
        Reason of the failure.
    """
    click.echo(f"{path}: error: {message}", err=True)
