from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bibclean._diagnostics import Diagnostic
from bibclean._formatter import format_blocks
from bibclean._parser import parse
from bibclean._rules import RULES
from bibclean._rules._base import Context

if TYPE_CHECKING:
    from pathlib import Path

    from bibclean._config import Config

BOM = "\ufeff"
NOT_FORMATTED_MESSAGE = "file is not formatted, run `bibclean fix`"


class ReadError(Exception):
    """A file could not be read or decoded."""


@dataclass(slots=True, frozen=True)
class Source:
    """Content of one input file.

    Parameters
    ----------
    text : str
        Decoded text, without the byte order mark, with the line endings of the
        file.
    had_bom : bool
        True when the file started with a byte order mark.
    """

    text: str
    had_bom: bool


@dataclass(slots=True, frozen=True)
class Report:
    """Outcome of the pipeline for one file.

    Parameters
    ----------
    diagnostics : list of Diagnostic
        Every finding, the file-level one included.
    output : str
        Canonical text after the fixable rules were applied.
    changed : bool
        True when the output differs from the file on disk.
    """

    diagnostics: list[Diagnostic]
    output: str
    changed: bool


def normalize_newlines(text: str) -> str:
    r"""Turn every line ending into a line feed.

    Parameters
    ----------
    text : str
        Text to normalise.

    Returns
    -------
    str
        The text with ``'\r\n'`` and ``'\r'`` replaced by ``'\n'``.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_source(path: Path, encoding: str) -> Source:
    """Read and decode one input file.

    Parameters
    ----------
    path : Path
        File to read.
    encoding : str
        Encoding used to decode the bytes.

    Returns
    -------
    Source
        The decoded text and whether a byte order mark was stripped.

    Raises
    ------
    ReadError
        If the file cannot be read or cannot be decoded.
    """
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ReadError(f"cannot read file: {exc.strerror or exc}")
    try:
        text = data.decode(encoding)
    except UnicodeDecodeError as exc:
        raise ReadError(
            f"cannot decode file with encoding '{encoding}': "
            f"{exc.reason} at byte {exc.start}"
        )
    had_bom = text.startswith(BOM)
    return Source(text=text[1:] if had_bom else text, had_bom=had_bom)


def write_source(path: Path, text: str, encoding: str) -> None:
    """Write one output file with line feed endings.

    Parameters
    ----------
    path : Path
        File to write.
    text : str
        Canonical text.
    encoding : str
        Encoding used to encode the text.
    """
    path.write_text(text, encoding=encoding, newline="\n")


def lint(context: Context) -> list[Diagnostic]:
    """Run every enabled rule over a working model.

    Parameters
    ----------
    context : Context
        Working model and configuration; the rules mutate its blocks.

    Returns
    -------
    list of Diagnostic
        The findings of the rules, in pipeline order.
    """
    ignore = context.config.lint.ignore
    diagnostics: list[Diagnostic] = []
    for item in RULES:
        if item.name in ignore:
            continue
        for finding in item.check(context):
            position = finding.position
            diagnostics.append(
                Diagnostic(
                    path=context.path,
                    line=None if position is None else position.line,
                    column=None if position is None else position.column,
                    rule=item.name,
                    message=finding.message,
                    fixable=finding.fixable,
                )
            )
    return diagnostics


def process(path: str, source: Source, config: Config) -> Report:
    """Run the whole pipeline over one file.

    Parameters
    ----------
    path : str
        File being processed, as typed on the command line.
    source : Source
        Decoded content of the file.
    config : Config
        Effective configuration of the file.

    Returns
    -------
    Report
        The diagnostics, the canonical output and whether it differs from the
        file on disk. The fixable rules always run, so ``check`` and ``fix``
        report exactly the same violations.

    Raises
    ------
    RuntimeError
        If a second pass over the output still finds something to fix.
    """
    text = normalize_newlines(source.text)
    blocks = parse(text)
    formatted = format_blocks(blocks, config.format)
    not_formatted = formatted != source.text or source.had_bom
    context = Context(path=path, blocks=blocks, config=config)
    diagnostics = lint(context)
    if not_formatted:
        diagnostics.append(_file_level(path, NOT_FORMATTED_MESSAGE))
    output = format_blocks(context.blocks, config.format)
    _assert_converged(path, output, config)
    changed = output != source.text or source.had_bom
    return Report(diagnostics=diagnostics, output=output, changed=changed)


def unified_diff(path: str, before: str, after: str) -> str:
    """Build the unified diff between two texts.

    Parameters
    ----------
    path : str
        File the diff is about, as typed on the command line.
    before : str
        Text of the file on disk.
    after : str
        Canonical text.

    Returns
    -------
    str
        The diff, with ``a/<path>`` and ``b/<path>`` headers, empty when the
        two texts are equal.
    """
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def _file_level(path: str, message: str) -> Diagnostic:
    """Build a diagnostic that is about the file rather than a position in it."""
    return Diagnostic(
        path=path, line=None, column=None, rule=None, message=message, fixable=True
    )


def _assert_converged(path: str, output: str, config: Config) -> None:
    """Check that a second pass over the output has nothing left to fix."""
    blocks = parse(output)
    diagnostics = lint(Context(path=path, blocks=blocks, config=config))
    again = format_blocks(blocks, config.format)
    if again != output or any(item.fixable for item in diagnostics):
        raise RuntimeError(
            f"{path}: internal error, fixes did not converge; please report this file"
        )
