from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._model import entry_type
from bibclean._rules._base import Finding, _has_field, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context


@rule(name="required-field", fixable="no", scope="entry")
def required_field(ctx: Context) -> list[Finding]:
    """Report a field that the entry type requires but the entry does not have.

    The requirements come from the shipped tables and can be overridden per type
    with ``required``. A name spelled ``'author|editor'`` is satisfied when at
    least one of the alternatives is present, and the message lists it as
    written. An entry type without a table is never reported.

    .. code-block:: bibtex

       @article{k, author = {A}, title = {T}, year = {2021}}

    pybtex: the style prints an incomplete reference, or fails outright.
    """
    findings: list[Finding] = []
    for entry in ctx.entries():
        if ctx.is_excluded(entry):
            continue
        rules = ctx.type_rules(entry)
        if rules is None:
            continue
        for required in rules.required:
            if any(_has_field(entry, name) for name in required.split("|")):
                continue
            message = (
                f"@{entry_type(entry)} '{entry.key}' is missing required field "
                f"'{required}'"
            )
            findings.append(Finding(entry.start, message, False))
    return findings
