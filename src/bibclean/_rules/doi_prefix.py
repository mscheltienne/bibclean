from __future__ import annotations

import re
from typing import TYPE_CHECKING

from bibclean._model import Part, Value
from bibclean._rules._base import Diagnostic, _fields_named, _single_text, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context

_PREFIXES = re.compile(
    r"\s*(?:(?:https?://(?:dx\.|www\.)?doi\.org/|doi:)\s*)*", re.IGNORECASE
)


def strip_doi_prefix(text: str) -> str:
    """Remove the resolver prefixes of a DOI.

    Parameters
    ----------
    text : str
        DOI as written.

    Returns
    -------
    str
        The DOI without any resolver prefix, stripped of surrounding whitespace.
        Prefixes are matched case-insensitively and repeatedly. The case of the
        identifier itself is preserved.
    """
    return text[_PREFIXES.match(text).end() :].strip()


def normalize_doi(text: str) -> str:
    """Build the comparison form of a DOI.

    Parameters
    ----------
    text : str
        DOI as written.

    Returns
    -------
    str
        The DOI without any resolver prefix, lowercased.
    """
    return strip_doi_prefix(text).lower()


@rule(name="doi-prefix", fixable="yes", scope="value")
def doi_prefix(ctx: Context) -> list[Diagnostic]:
    """Report a ``doi`` field carrying a resolver prefix.

    The prefix is removed and the bare identifier is kept. Recognised prefixes
    are ``https://doi.org/``, ``https://dx.doi.org/``, ``https://www.doi.org/``,
    their ``http://`` forms and ``doi:``, matched case-insensitively.

    .. code-block:: bibtex

       @article{k, doi = {https://doi.org/10.1/x}}

    pybtex: the styles prepend the resolver themselves, producing a broken
    double link.

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
        for field in _fields_named(entry, "doi"):
            text = _single_text(field.value)
            if text is None:
                continue
            stripped = strip_doi_prefix(text)
            if stripped == text:
                continue
            field.value = Value([Part("braced", stripped)])
            message = "field 'doi' has a URL prefix, expected the bare identifier"
            findings.append(Diagnostic(field.start, message, True))
    return findings
