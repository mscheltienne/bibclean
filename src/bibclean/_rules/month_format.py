from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._defaults import MONTHS
from bibclean._formatter import collapse_whitespace, render_value
from bibclean._model import Part, Value
from bibclean._rules._base import Finding, _fields_named, rule

if TYPE_CHECKING:
    from bibclean._config import Month
    from bibclean._rules._base import Context

_DIGITS = frozenset("0123456789")


def parse_month(value: Value) -> int | None:
    """Read a month value as a number.

    Parameters
    ----------
    value : Value
        Value of a ``month`` field.

    Returns
    -------
    int | None
        The month number between 1 and 12, None when the value is not a single
        recognised month. Recognised are the twelve macros, the English names,
        the three-letter abbreviations with or without a trailing period in any
        case, and the numbers 1 to 12 with or without a leading zero.
    """
    if len(value.parts) != 1:
        return None
    part = value.parts[0]
    text = part.text if part.kind == "bare" else collapse_whitespace(part.text).strip()
    text = text.lower()
    if text.endswith("."):
        text = text[:-1]
    for number, (macro, name) in enumerate(MONTHS, start=1):
        if text == macro or text == name.lower():
            return number
    if 1 <= len(text) <= 2 and set(text) <= _DIGITS and 1 <= int(text) <= 12:
        return int(text)
    return None


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
def month_format(ctx: Context) -> list[Finding]:
    """Report a ``month`` field that is not in the configured form.

    The value is rewritten as the macro, the English name or the number,
    following the ``month`` option. A value that is not a recognised month is
    reported and left untouched. ``month = "preserve"`` disables the rule.

    .. code-block:: bibtex

       @article{k, month = {September}}

    pybtex: macros are substituted while literal names are printed as they are,
    so both forms render the same but a canonical file needs one of them.
    """
    mode = ctx.config.lint.month
    if mode == "preserve":
        return []
    findings: list[Finding] = []
    for entry in ctx.entries():
        if ctx.is_excluded(entry):
            continue
        for field in _fields_named(entry, "month"):
            number = parse_month(field.value)
            original = _original(field.value)
            if number is None:
                message = f"unrecognised month '{original}'"
                findings.append(Finding(field.start, message, False))
                continue
            target = month_target(number, mode)
            parts = field.value.parts
            if (
                len(parts) == 1
                and parts[0].kind == target.kind
                and parts[0].text == target.text
            ):
                continue
            field.value = Value([target])
            if mode == "abbreviation":
                message = f"month '{original}' should be the macro '{target.text}'"
            else:
                message = f"month '{original}' should be '{target.text}'"
            findings.append(Finding(field.start, message, True))
    return findings


def _original(value: Value) -> str:
    """Render a month value as it appears in the message of a finding."""
    if len(value.parts) != 1:
        return render_value(value)
    part = value.parts[0]
    if part.kind == "bare":
        return part.text
    return collapse_whitespace(part.text).strip()
