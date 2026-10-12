from __future__ import annotations

import re
from typing import TYPE_CHECKING

from bibclean._model import StringDef
from bibclean._rules._base import Diagnostic, rule

if TYPE_CHECKING:
    from bibclean._model import Value
    from bibclean._rules._base import Context

_EXEMPT = frozenset({"doi", "file", "url"})
# the argument of \url and the first argument of \href, captured to survive a split
_URL = re.compile(r"(\\(?:url|href)\{[^{}]*\})")


@rule(name="unescaped-percent", fixable="yes", scope="value")
def unescaped_percent(ctx: Context) -> list[Diagnostic]:
    r"""Report a ``%`` that is not escaped by a backslash.

    Every unescaped ``%`` of the value becomes ``\%``, and one finding is
    emitted per field or ``@string`` value whatever the number of occurrences. The
    fields ``url``, ``doi`` and ``file`` are exempt, where a ``%`` is legitimate URL
    encoding, and so are the argument of ``\url`` and the first argument of
    ``\href`` in any other field or ``@string`` value. A ``@string`` value is always
    checked, since it is expanded into the fields using it.

    .. code-block:: bibtex

       @article{k, title = {Filtering (50% of the signal)}}

    pybtex: latexcodec treats ``%`` as the start of a comment and drops the rest
    of the value when the reference is decoded.

    Parameters
    ----------
    ctx : Context
        Working model and configuration of the file.

    Returns
    -------
    list of Diagnostic
        The violations found.
    """
    findings: list[Diagnostic] = []
    suffix = "pybtex drops the rest of the value"
    for block in ctx.blocks:
        if isinstance(block, StringDef) and _escape_value(block.value):
            message = f"unescaped '%' in string '{block.key}', {suffix}"
            findings.append(Diagnostic(block.start, message, True))
    for entry in ctx.checked_entries():
        for field in entry.fields:
            name = field.key.lower()
            if name not in _EXEMPT and _escape_value(field.value):
                message = f"unescaped '%' in field '{name}', {suffix}"
                findings.append(Diagnostic(field.start, message, True))
    return findings


def _escape_value(value: Value) -> bool:
    """Escape in place the unescaped percent signs of the literal parts of a value.

    Parameters
    ----------
    value : Value
        Value to escape.

    Returns
    -------
    bool
        True when a part was changed.
    """
    changed = False
    for part in value.parts:
        if part.kind == "bare":
            continue
        escaped = _escape(part.text)
        if escaped != part.text:
            part.text = escaped
            changed = True
    return changed


def _escape(text: str) -> str:
    r"""Prefix every unescaped percent sign outside a URL argument with a backslash.

    Parameters
    ----------
    text : str
        Text to escape.

    Returns
    -------
    str
        The text, every ``%`` preceded by an even number of backslashes escaped,
        except inside the argument of ``\url`` and the first argument of ``\href``.
    """
    spans = _URL.split(text)
    return "".join(
        span if index % 2 else _escape_plain(span) for index, span in enumerate(spans)
    )


def _escape_plain(text: str) -> str:
    """Prefix every unescaped percent sign with a backslash.

    Parameters
    ----------
    text : str
        Text to escape.

    Returns
    -------
    str
        The text, every ``%`` preceded by an even number of backslashes escaped.
    """
    out: list[str] = []
    backslashes = 0
    for char in text:
        if char == "%" and backslashes % 2 == 0:
            out.append("\\")
        out.append(char)
        backslashes = backslashes + 1 if char == "\\" else 0
    return "".join(out)
