from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._model import entry_type
from bibclean._rules._base import Finding, _remove_field, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context

_ALWAYS_KEPT = frozenset({"doi", "url"})


@rule(name="strip-field", fixable="yes", scope="field")
def strip_field(ctx: Context) -> list[Finding]:
    """Report a field that the entry type does not keep.

    The field is removed. The kept names of a type always contain its required
    names, and ``doi`` and ``url`` are never stripped so that a citation keeps
    its link. A type without a keep list is never stripped, and
    ``strip-fields = false`` disables the rule entirely.

    .. code-block:: bibtex

       @article{k, abstract = {...}, file = {...}, urldate = {...}}

    pybtex: nothing, noise only.
    """
    if not ctx.config.lint.strip_fields:
        return []
    findings: list[Finding] = []
    for entry in ctx.entries():
        if ctx.is_excluded(entry):
            continue
        rules = ctx.type_rules(entry)
        if rules is None or rules.keep is None:
            continue
        for field in list(entry.fields):
            name = field.key.lower()
            if name in rules.keep or name in _ALWAYS_KEPT:
                continue
            _remove_field(entry, field)
            message = f"field '{name}' is not kept for @{entry_type(entry)}"
            findings.append(Finding(field.start, message, True))
    return findings
