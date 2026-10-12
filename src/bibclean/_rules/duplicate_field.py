from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._formatter import render_value
from bibclean._rules._base import Diagnostic, rule

if TYPE_CHECKING:
    from bibclean._model import Field
    from bibclean._rules._base import Context


@rule(name="duplicate-field", fixable="partial", scope="entry")
def duplicate_field(ctx: Context) -> list[Diagnostic]:
    """Report a field defined twice in one entry, case-insensitively.

    The repeat is removed when both definitions render to the same value,
    otherwise it is reported and both are kept.

    .. code-block:: bibtex

       @article{k, title = {Other}, title = {Other}}
       @article{k, title = {Other}, title = {Another}}

    pybtex: the documentation build fails on the repeated field.

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
        seen: dict[str, Field] = {}
        for field in list(entry.fields):
            name = field.key.lower()
            first = seen.get(name)
            if first is None:
                seen[name] = field
                continue
            identical = render_value(field.value) == render_value(first.value)
            if identical:
                entry.fields.remove(field)
                message = f"field '{name}' is defined twice with the same value"
            else:
                message = f"field '{name}' is defined twice with different values"
            findings.append(Diagnostic(field.start, message, identical))
    return findings
