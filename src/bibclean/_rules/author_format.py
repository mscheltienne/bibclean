from __future__ import annotations

import re
from typing import TYPE_CHECKING

from bibclean._rules._base import Diagnostic, _single_text, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context

_AND = re.compile(r"\s+and\s+", re.IGNORECASE)
_COMMA = re.compile(",")


@rule(name="author-format", fixable="no", scope="value")
def author_format(ctx: Context) -> list[Diagnostic]:
    """Report a name with more than two commas in an ``author`` or ``editor`` field.

    The value is split into names on the word ``and`` surrounded by whitespace, in
    any case, and a name is reported when it holds more than two commas, both
    outside braces. A comma-separated list of authors is the usual cause. A value
    made of a macro or of a concatenation is not inspected.

    .. code-block:: bibtex

       @article{k, author = {Jack Dongarra, Kevin London, Shirley Moore, Phil Mucci}}

    pybtex: the name is rejected with ``Too many commas`` and the documentation
    build fails.

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
    for entry in ctx.entries():
        if ctx.is_excluded(entry):
            continue
        for field in entry.fields:
            name = field.key.lower()
            text = _single_text(field.value) if name in ("author", "editor") else None
            if not text:
                continue
            for person in _split(text, _AND):
                if len(_split(person, _COMMA)) > 3:
                    message = (
                        f"name '{person}' in field '{name}' has more than two "
                        "commas, separate the names with 'and'"
                    )
                    findings.append(Diagnostic(field.start, message, False))
    return findings


def _split(text: str, separator: re.Pattern[str]) -> list[str]:
    """Split a text on the matches of a separator found outside braces.

    Parameters
    ----------
    text : str
        Text to split.
    separator : re.Pattern
        Pattern of the separator, which never matches a brace.

    Returns
    -------
    list of str
        The pieces between the separators found at brace depth 0, at least one.
    """
    pieces: list[str] = []
    start = 0
    for match in separator.finditer(text):
        head = text[: match.start()]
        if head.count("{") == head.count("}"):
            pieces.append(text[start : match.start()])
            start = match.end()
    pieces.append(text[start:])
    return pieces
