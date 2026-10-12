from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._model import fields_named
from bibclean._rules._base import Diagnostic, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context


@rule(name="url-with-doi", fixable="yes", scope="entry")
def url_with_doi(ctx: Context) -> list[Diagnostic]:
    """Report a ``url`` field in an entry that has a ``doi`` field.

    The ``url`` field is removed, whatever it points to: the DOI is the stable link
    to the work.

    .. code-block:: bibtex

       @article{k, doi = {10.1/x}, url = {https://example.org}}

    pybtex: nothing, the reference simply carries two links to the same work.

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
    for entry in ctx.checked_entries():
        if not fields_named(entry, "doi"):
            continue
        for field in fields_named(entry, "url"):
            entry.fields.remove(field)
            findings.append(
                Diagnostic(field.start, "field 'url' is redundant with 'doi'", True)
            )
    return findings
