from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._formatter import collapse_whitespace
from bibclean._rules._base import Finding, _remove_field, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context


@rule(name="empty-field", fixable="yes", scope="field")
def empty_field(ctx: Context) -> list[Finding]:
    """Report a field whose value is empty once whitespace is collapsed.

    The field is removed. A value holding a macro is never empty and is left
    alone.

    .. code-block:: bibtex

       @article{k, volume = {}, note = {  }}

    pybtex: the field is dropped silently, so the file lies about its content.
    """
    findings: list[Finding] = []
    for entry in ctx.entries():
        if ctx.is_excluded(entry):
            continue
        for field in list(entry.fields):
            parts = field.value.parts
            if any(part.kind == "bare" for part in parts):
                continue
            text = "".join(collapse_whitespace(part.text) for part in parts)
            if text.strip():
                continue
            _remove_field(entry, field)
            message = f"field '{field.key.lower()}' is empty"
            findings.append(Finding(field.start, message, True))
    return findings
