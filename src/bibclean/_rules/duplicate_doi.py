from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._rules._base import Diagnostic, _fields_named, _single_text, rule
from bibclean._rules.doi_prefix import normalize_doi

if TYPE_CHECKING:
    from bibclean._model import Entry
    from bibclean._rules._base import Context


@rule(name="duplicate-doi", fixable="no", scope="file")
def duplicate_doi(ctx: Context) -> list[Diagnostic]:
    """Report two entries carrying the same DOI.

    DOIs are compared once the resolver prefixes are stripped and the case is
    folded. Both entries are kept and the repeat is reported: the documentation may
    cite either cite key, so only the author can merge them. A DOI identifies one
    work, so this catches a re-export under a second cite key without the false
    positives of comparing author, title and year.

    .. code-block:: bibtex

       @article{a, doi = {10.1/x}}
       @article{a-1, doi = {https://doi.org/10.1/X}}

    pybtex: nothing, the bibliography simply lists the work twice.
    """
    findings: list[Diagnostic] = []
    seen: dict[str, Entry] = {}
    for entry in ctx.entries():
        fields = _fields_named(entry, "doi")
        if not fields:
            continue
        text = _single_text(fields[0].value)
        if not text:
            continue
        identifier = normalize_doi(text)
        if not identifier:
            continue
        first = seen.setdefault(identifier, entry)
        if first is entry or ctx.is_excluded(entry):
            continue
        message = (
            f"entry shares DOI '{identifier}' with '{first.key}' "
            f"at line {first.start.line}"
        )
        findings.append(Diagnostic(entry.start, message, False))
    return findings
