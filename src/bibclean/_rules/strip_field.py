from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._model import entry_type
from bibclean._rules._base import Diagnostic, _fields_named, _single_text, rule

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
    """
    findings: list[Diagnostic] = []
    targets = {
        text.lower()
        for entry in ctx.entries()
        for field in _fields_named(entry, "crossref")
        if (text := _single_text(field.value))
    }
    for entry in ctx.entries():
        if ctx.is_excluded(entry) or entry.key.lower() in targets:
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
