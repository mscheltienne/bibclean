from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._model import crossref_target, entry_type
from bibclean._rules._base import Diagnostic, rule

if TYPE_CHECKING:
    from bibclean._model import Entry
    from bibclean._rules._base import Context


@rule(name="required-field", fixable="no", scope="entry")
def required_field(ctx: Context) -> list[Diagnostic]:
    """Report a field that the entry type requires but the entry does not have.

    The requirements come from the shipped tables and can be overridden per type
    with ``required``. A name spelled ``'author|editor'`` is satisfied when at
    least one of the alternatives is present, and the message lists it as
    written. An entry with a ``crossref`` field also has every field of the entry
    with that cite key in the same file, compared case-insensitively. An entry type
    without a table is never reported.

    .. code-block:: bibtex

       @article{k, author = {A}, title = {T}, year = {2021}}

    pybtex: the style prints an incomplete reference, or fails outright. Like
    BibTeX, pybtex fills the fields missing from an entry with those of its
    ``crossref`` target.

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
    by_key: dict[str, Entry] = {}
    for entry in ctx.entries():
        by_key.setdefault(entry.key.lower(), entry)
    for entry in ctx.checked_entries():
        rules = ctx.type_rules(entry)
        if rules is None:
            continue
        names = {field.key.lower() for field in entry.fields}
        target = by_key.get(crossref_target(entry))
        if target is not None:
            names |= {item.key.lower() for item in target.fields}
        for required in rules.required:
            if names.isdisjoint(required.lower().split("|")):
                message = (
                    f"@{entry_type(entry)} '{entry.key}' is missing required field "
                    f"'{required}'"
                )
                findings.append(Diagnostic(entry.start, message, False))
    return findings
