from __future__ import annotations

import codecs
import difflib
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from bibclean._formatter import format_blocks
from bibclean._model import Malformed, StringDef
from bibclean._parser import parse
from bibclean._rules import RULES
from bibclean._rules._base import Context, Diagnostic

if TYPE_CHECKING:
    from bibclean._config import Config
    from bibclean._model import Block

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
        because it is already canonical, holds a syntax error or redefines a macro.
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


def decode(data: bytes, encoding: str) -> str:
    r"""Decode the content of a file into the text the parser reads.

    Parameters
    ----------
    data : bytes
        Content of the file.
    encoding : str
        Encoding of the content.

    Returns
    -------
    str
        The decoded text, without leading ``U+FEFF`` characters and with every line
        ending normalised to ``'\n'``.

    Raises
    ------
    UnicodeDecodeError
        If the content cannot be decoded with the encoding.
    """
    text = data.decode(encoding).lstrip("\N{BYTE ORDER MARK}")
    return text.replace("\r\n", "\n").replace("\r", "\n")


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
        syntax error or a redefined macro is never rewritten and none of its
        violations is fixable.

    Raises
    ------
    UnicodeDecodeError
        If the content cannot be decoded with the encoding.
    """
    blocks = parse(decode(data, encoding))
    if codecs.lookup(encoding).name == "utf-8-sig":
        encoding = "utf-8"
    frozen = _is_unsafe_to_rewrite(blocks)
    formatted = None if frozen else format_blocks(blocks, config.format)
    context = Context(blocks=blocks, config=config)
    diagnostics = lint(context)
    if frozen:
        diagnostics = [replace(item, fixable=False) for item in diagnostics]
        output = None
    else:
        # a rule emits a fixable diagnostic exactly when it mutates the model, so the
        # model is unchanged and renders as 'formatted' when none is fixable
        mutated = any(item.fixable for item in diagnostics)
        output = formatted.encode(encoding)
        if output != data:
            diagnostics.append(Diagnostic(None, NOT_FORMATTED_MESSAGE, True))
        if mutated:
            output = format_blocks(context.blocks, config.format).encode(encoding)
        if output == data:
            output = None
    diagnostics.sort(key=lambda item: (item.position is None, item.position))
    return Report(diagnostics=diagnostics, output=output)


def _is_unsafe_to_rewrite(blocks: list[Block]) -> bool:
    """Check whether rewriting a file could change its meaning.

    Parameters
    ----------
    blocks : list of Block
        Blocks of the file, as parsed.

    Returns
    -------
    bool
        True when a block is malformed, since it swallows the text up to the next
        ``@``, or when a ``@string`` macro is defined twice, case-insensitively,
        since hoisting the definitions changes the values of the entries between.
    """
    names = [block.key.lower() for block in blocks if isinstance(block, StringDef)]
    malformed = any(isinstance(block, Malformed) for block in blocks)
    return malformed or len(set(names)) < len(names)


def unified_diff(path: str, before: str, after: str) -> str:
    r"""Build the unified diff between two texts.

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
        The diff, with ``a/<path>`` and ``b/<path>`` headers, the leading ``/`` of
        an absolute path dropped, empty when the two texts are equal. A line without
        a final newline is followed by the ``\ No newline at end of file`` marker.
    """
    path = path.lstrip("/")
    lines = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
    )
    return "".join(
        line if line.endswith("\n") else line + "\n\\ No newline at end of file\n"
        for line in lines
    )
