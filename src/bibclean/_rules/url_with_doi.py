from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._rules._base import Diagnostic, _fields_named, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context


@rule(name="url-with-doi", fixable="yes", scope="entry")
def url_with_doi(ctx: Context) -> list[Diagnostic]:
    """Report a ``url`` field made redundant by a ``doi`` field.

    The ``url`` field is removed.

    .. code-block:: bibtex

       @article{k, doi = {10.1/x}, url = {https://example.org}}

    pybtex: nothing, the reference simply carries two links to the same work.
    """
    findings: list[Diagnostic] = []
    for entry in ctx.entries():
        if ctx.is_excluded(entry) or not _fields_named(entry, "doi"):
            continue
        for field in _fields_named(entry, "url"):
            entry.fields.remove(field)
            findings.append(
                Diagnostic(field.start, "field 'url' is redundant with 'doi'", True)
            )
    return findings
