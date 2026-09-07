from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._defaults import MONTH_MACROS
from bibclean._model import Entry, Preamble, StringDef
from bibclean._rules._base import Finding, rule

if TYPE_CHECKING:
    from bibclean._model import Position, Value
    from bibclean._rules._base import Context

_DIGITS = frozenset("0123456789")


@rule(name="undefined-string", fixable="no", scope="value")
def undefined_string(ctx: Context) -> list[Finding]:
    """Report a bare macro that no ``@string`` block defines.

    The twelve month macros are always defined. A ``@string`` block may only
    reference macros defined above it, since definitions are processed in order.
    Names are compared case-insensitively.

    .. code-block:: bibtex

       @string{jneuro = {Journal of Neuroscience}}
       @article{k, journal = jnuero}

    pybtex: the documentation build fails with an undefined macro error.
    """
    findings: list[Finding] = []
    defined: set[str] = set()
    for block in ctx.blocks:
        if isinstance(block, StringDef):
            findings += _check(block.value, block.start, defined)
            defined.add(block.key.lower())
        elif isinstance(block, Preamble):
            findings += _check(block.value, block.start, defined)
        elif isinstance(block, Entry) and not ctx.is_excluded(block):
            for field in block.fields:
                findings += _check(field.value, field.start, defined)
    return findings


def _check(value: Value, position: Position, defined: set[str]) -> list[Finding]:
    """Report the bare parts of a value that are neither digits nor defined."""
    findings: list[Finding] = []
    for part in value.parts:
        if part.kind != "bare":
            continue
        text = part.text
        if text and set(text) <= _DIGITS:
            continue
        if text.lower() in MONTH_MACROS or text.lower() in defined:
            continue
        findings.append(Finding(position, f"undefined string '{text}'", False))
    return findings
