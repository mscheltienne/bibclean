from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._defaults import DOI_PREFIXES
from bibclean._model import Part, Value
from bibclean._rules._base import Finding, _fields_named, _single_text, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context

_SORTED_PREFIXES = tuple(sorted(DOI_PREFIXES, key=len, reverse=True))


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
        Prefixes are matched case-insensitively, longest first, and repeatedly.
        The case of the identifier itself is preserved.
    """
    stripped = text.strip()
    changed = True
    while changed:
        changed = False
        lowered = stripped.lower()
        for prefix in _SORTED_PREFIXES:
            if lowered.startswith(prefix):
                stripped = stripped[len(prefix) :].strip()
                changed = True
                break
    return stripped


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
def doi_prefix(ctx: Context) -> list[Finding]:
    """Report a ``doi`` field carrying a resolver prefix.

    The prefix is removed and the bare identifier is kept. Recognised prefixes
    are ``https://doi.org/``, ``http://doi.org/``, ``https://dx.doi.org/``,
    ``http://dx.doi.org/``, ``https://www.doi.org/`` and ``doi:``, matched
    case-insensitively.

    .. code-block:: bibtex

       @article{k, doi = {https://doi.org/10.1/x}}

    pybtex: the styles prepend the resolver themselves, producing a broken
    double link.
    """
    findings: list[Finding] = []
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
            findings.append(Finding(field.start, message, True))
    return findings
