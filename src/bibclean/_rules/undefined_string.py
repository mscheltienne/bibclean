from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._defaults import MONTH_MACROS
from bibclean._model import Entry, Preamble, StringDef
from bibclean._rules._base import Diagnostic, rule

if TYPE_CHECKING:
    from bibclean._model import Position, Value
    from bibclean._rules._base import Context


@rule(name="undefined-string", fixable="no", scope="value")
def undefined_string(ctx: Context) -> list[Diagnostic]:
    """Report a bare macro that no ``@string`` block defines.

    The twelve month macros are always defined. An entry may reference any
    ``@string`` of the file, since the canonical format writes every ``@string``
    before the entries. A ``@string`` or ``@preamble`` block may only reference
    macros defined above it, since definitions are processed in order. Names are
    compared case-insensitively.

    .. code-block:: bibtex

       @string{jneuro = {Journal of Neuroscience}}
       @article{k, journal = jnuero}

    pybtex: the documentation build fails with an undefined macro error.

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
    every = {block.key.lower() for block in ctx.blocks if isinstance(block, StringDef)}
    defined: set[str] = set()
    for block in ctx.blocks:
        if isinstance(block, StringDef):
            findings += _check(block.value, block.start, defined)
            defined.add(block.key.lower())
        elif isinstance(block, Preamble):
            findings += _check(block.value, block.start, defined)
        elif isinstance(block, Entry) and not ctx.is_excluded(block):
            for field in block.fields:
                findings += _check(field.value, field.start, every)
    return findings


def _check(value: Value, position: Position, defined: set[str]) -> list[Diagnostic]:
    """Report the macros of a value that are not defined.

    Parameters
    ----------
    value : Value
        Value to inspect.
    position : Position
        Position reported for the value.
    defined : set of str
        Lowercased names of the macros defined for the value; the month macros are
        always defined.

    Returns
    -------
    list of Diagnostic
        One violation per undefined macro.
    """
    findings: list[Diagnostic] = []
    for part in value.parts:
        if not part.is_macro:
            continue
        text = part.text
        if text.lower() in MONTH_MACROS or text.lower() in defined:
            continue
        findings.append(Diagnostic(position, f"undefined string '{text}'", False))
    return findings
