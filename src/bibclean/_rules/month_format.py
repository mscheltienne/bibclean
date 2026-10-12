from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._defaults import MONTHS
from bibclean._formatter import collapse_whitespace, render_value
from bibclean._model import Part, Value
from bibclean._rules._base import Diagnostic, _fields_named, rule

if TYPE_CHECKING:
    from bibclean._config import Month
    from bibclean._rules._base import Context

_NUMBERS: dict[str, int] = {
    form: number
    for number, (macro, name) in enumerate(MONTHS, start=1)
    for form in (macro, f"{macro}.", name.lower(), str(number), f"{number:02}")
}


def month_target(number: int, mode: Month) -> Part:
    """Build the canonical part of a month.

    Parameters
    ----------
    number : int
        Month number between 1 and 12.
    mode : str
        One of ``'abbreviation'``, ``'name'`` or ``'number'``.

    Returns
    -------
    Part
        The bare macro, the braced English name or the braced number.
    """
    if mode == "abbreviation":
        return Part("bare", MONTHS[number - 1][0])
    if mode == "name":
        return Part("braced", MONTHS[number - 1][1])
    return Part("braced", str(number))


@rule(name="month-format", fixable="yes", scope="value")
def month_format(ctx: Context) -> list[Diagnostic]:
    """Report a ``month`` field that is not in the configured form.

    The value is rewritten as the macro, the English name or the number,
    following the ``month`` option. Recognised are the twelve macros, the English
    names, the three-letter abbreviations with or without a trailing period, in any
    case, and the numbers 1 to 12 with or without a leading zero. Any other value is
    reported and left untouched, except a concatenation such as ``jan # {~15}``,
    which is not inspected.

    .. code-block:: bibtex

       @article{k, month = {September}}

    pybtex: macros are substituted while literal names are printed as they are,
    so both forms render the same but a canonical file needs one of them.

    Parameters
    ----------
    ctx : Context
        Working model and configuration of the file.

    Returns
    -------
    list of Diagnostic
        The violations found.
    """
    mode = ctx.config.lint.month
    findings: list[Diagnostic] = []
    for entry in ctx.entries():
        if ctx.is_excluded(entry):
            continue
        for field in _fields_named(entry, "month"):
            parts = field.value.parts
            if len(parts) > 1:
                continue
            text = parts[0].text
            if parts[0].kind != "bare":
                text = collapse_whitespace(text).strip()
            number = _NUMBERS.get(text.lower())
            written = render_value(field.value)
            if number is None:
                message = f"unrecognised month '{written}'"
                findings.append(Diagnostic(field.start, message, False))
                continue
            target = month_target(number, mode)
            if parts == [target]:
                continue
            field.value = Value([target])
            message = f"month '{written}' should be '{render_value(field.value)}'"
            findings.append(Diagnostic(field.start, message, True))
    return findings
