from __future__ import annotations

import codecs
import difflib
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from bibclean._formatter import format_blocks
from bibclean._model import Malformed
from bibclean._parser import parse
from bibclean._rules import RULES
from bibclean._rules._base import Context, Diagnostic

if TYPE_CHECKING:
    from bibclean._config import Config

NOT_FORMATTED_MESSAGE = "file is not formatted, run `bibclean fix`"


@dataclass(slots=True, frozen=True)
class Report:
    """Outcome of the pipeline for one file.

    Parameters
    ----------
    diagnostics : list of Diagnostic
        Every violation, sorted by position, the file-level one last.
    output : bytes | None
        Encoded canonical text to write, None when the file is left as it is
        because it is already canonical or holds a syntax error.
    """

    diagnostics: list[Diagnostic]
    output: bytes | None


def lint(context: Context) -> list[Diagnostic]:
    """Run every enabled rule over a working model.

    Parameters
    ----------
    context : Context
        Working model and configuration; the rules mutate its blocks.

    Returns
    -------
    list of Diagnostic
        The diagnostics of the rules, in pipeline order, with their rule name.
    """
    return [
        replace(diagnostic, rule=item.name)
        for item in RULES
        if item.name not in context.config.lint.ignore
        for diagnostic in item.check(context)
    ]


def process(data: bytes, encoding: str, config: Config) -> Report:
    """Run the whole pipeline over the content of one file.

    Parameters
    ----------
    data : bytes
        Content of the file.
    encoding : str
        Encoding used to decode the content and encode the output. A UTF-8 output
        never starts with a byte order mark: leading ``U+FEFF`` characters are dropped
        from the input and ``'utf-8-sig'`` encodes as ``'utf-8'``.
    config : Config
        Effective configuration of the file.

    Returns
    -------
    Report
        The diagnostics and the output to write. The fixable rules always run, so
        ``check`` and ``fix`` report exactly the same violations. A file with a
        syntax error is never rewritten and none of its violations is fixable.

    Raises
    ------
    UnicodeDecodeError
        If the content cannot be decoded with the encoding.
    """
    text = data.decode(encoding).lstrip("\N{BYTE ORDER MARK}")
    if codecs.lookup(encoding).name == "utf-8-sig":
        encoding = "utf-8"
    blocks = parse(text.replace("\r\n", "\n").replace("\r", "\n"))
    malformed = any(isinstance(block, Malformed) for block in blocks)
    formatted = None if malformed else format_blocks(blocks, config.format)
    context = Context(blocks=blocks, config=config)
    diagnostics = lint(context)
    if malformed:
        diagnostics = [replace(item, fixable=False) for item in diagnostics]
        output = None
    else:
        if formatted.encode(encoding) != data:
            diagnostics.append(Diagnostic(None, NOT_FORMATTED_MESSAGE, True))
        output = format_blocks(context.blocks, config.format).encode(encoding)
        if output == data:
            output = None
    diagnostics.sort(key=lambda item: (item.position is None, item.position))
    return Report(diagnostics=diagnostics, output=output)


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
