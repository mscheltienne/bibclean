from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._rules._base import Finding, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context

_EXEMPT = frozenset({"doi", "file", "url"})


@rule(name="unescaped-percent", fixable="yes", scope="value")
def unescaped_percent(ctx: Context) -> list[Finding]:
    r"""Report a ``%`` that is not escaped by a backslash.

    Every unescaped ``%`` of the value becomes ``\%``, and one finding is
    emitted per field whatever the number of occurrences. The fields ``url``,
    ``doi`` and ``file`` are exempt, where a ``%`` is legitimate URL encoding.

    .. code-block:: bibtex

       @article{k, title = {Filtering (50% of the signal)}}

    pybtex: latexcodec treats ``%`` as the start of a comment and drops the rest
    of the value when the reference is decoded.
    """
    findings: list[Finding] = []
    for entry in ctx.entries():
        if ctx.is_excluded(entry):
            continue
        for field in entry.fields:
            name = field.key.lower()
            if name in _EXEMPT:
                continue
            changed = False
            for part in field.value.parts:
                if part.kind == "bare":
                    continue
                escaped = _escape(part.text)
                if escaped != part.text:
                    part.text = escaped
                    changed = True
            if changed:
                message = (
                    f"unescaped '%' in field '{name}', "
                    "pybtex drops the rest of the value"
                )
                findings.append(Finding(field.start, message, True))
    return findings


def _escape(text: str) -> str:
    """Prefix every unescaped percent sign with a backslash."""
    out: list[str] = []
    backslashes = 0
    for char in text:
        if char == "%" and backslashes % 2 == 0:
            out.append("\\")
        out.append(char)
        backslashes = backslashes + 1 if char == "\\" else 0
    return "".join(out)
