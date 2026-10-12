from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._model import crossref_target, entry_type
from bibclean._rules._base import Diagnostic, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context

_ALWAYS_KEPT = frozenset({"crossref", "doi", "url"})


@rule(name="strip-field", fixable="yes", scope="field")
def strip_field(ctx: Context) -> list[Diagnostic]:
    """Report a field that the entry type does not keep.

    The field is removed. The kept names of a type always contain its required
    names, ``doi`` and ``url`` are never stripped so that a citation keeps its
    link, and ``crossref`` is never stripped so that the entry keeps the fields it
    inherits. A type without a keep list is never stripped, and neither is an entry
    that another entry references with ``crossref``, since its fields are inherited.

    .. code-block:: bibtex

       @article{k, abstract = {...}, file = {...}, urldate = {...}}

    pybtex: nothing, noise only.

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
    targets = {crossref_target(entry) for entry in ctx.entries()}
    for entry in ctx.checked_entries():
        if entry.key.lower() in targets:
            continue
        rules = ctx.type_rules(entry)
        if rules is None or rules.keep is None:
            continue
        for field in list(entry.fields):
            name = field.key.lower()
            if name in rules.keep or name in _ALWAYS_KEPT:
                continue
            entry.fields.remove(field)
            message = f"field '{name}' is not kept for @{entry_type(entry)}"
            findings.append(Diagnostic(field.start, message, True))
    return findings
