from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._rules._base import (
    Finding,
    _fields_named,
    _has_field,
    _remove_field,
    rule,
)

if TYPE_CHECKING:
    from bibclean._rules._base import Context


@rule(name="url-with-doi", fixable="yes", scope="entry")
def url_with_doi(ctx: Context) -> list[Finding]:
    """Report a ``url`` field made redundant by a ``doi`` field.

    The ``url`` field is removed. When only one of the two exists it is kept
    whatever the entry type keeps, so a citation always has a link when the
    source had one.

    .. code-block:: bibtex

       @article{k, doi = {10.1/x}, url = {https://example.org}}

    pybtex: nothing, the reference simply carries two links to the same work.
    """
    findings: list[Finding] = []
    for entry in ctx.entries():
        if ctx.is_excluded(entry) or not _has_field(entry, "doi"):
            continue
        for field in _fields_named(entry, "url"):
            _remove_field(entry, field)
            findings.append(
                Finding(field.start, "field 'url' is redundant with 'doi'", True)
            )
    return findings
