from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._rules._base import Finding, rule, signature

if TYPE_CHECKING:
    from bibclean._model import Entry
    from bibclean._rules._base import Context


@rule(name="duplicate-key", fixable="partial", scope="file")
def duplicate_key(ctx: Context) -> list[Finding]:
    """Report a cite key that is already defined, case-insensitively.

    The repeat is removed when it renders exactly like the first occurrence,
    entry type and fields included; otherwise both entries are kept and the
    repeat is reported, because only the author knows which of the two keys the
    documentation cites. A third occurrence is reported against the first.

    .. code-block:: bibtex

       @article{Smith2020, author = {Smith, John}, title = {On things}}
       @article{smith2020, author = {Smith, John}, title = {On things}}

    pybtex: cite keys are stored in a case-insensitive dictionary and the
    documentation build fails on the repeat.
    """
    findings: list[Finding] = []
    seen: dict[str, Entry] = {}
    for entry in ctx.entries():
        first = seen.get(entry.key.lower())
        if first is None:
            seen[entry.key.lower()] = entry
            continue
        if ctx.is_excluded(entry):
            continue
        message = (
            f"cite key '{entry.key}' is already defined as '{first.key}' "
            f"at line {first.start.line}"
        )
        options = ctx.config.format
        identical = signature(entry, options) == signature(first, options)
        if identical:
            ctx.remove(entry)
        findings.append(Finding(entry.start, message, identical))
    return findings
