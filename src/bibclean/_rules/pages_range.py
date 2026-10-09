from __future__ import annotations

import re
from typing import TYPE_CHECKING

from bibclean._model import Part, Value
from bibclean._rules._base import Finding, _fields_named, _single_text, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context

_RANGE = re.compile(r"([0-9]+)\s*(?:-{1,3}|–|—)\s*([0-9]+)")


@rule(name="pages-range", fixable="yes", scope="value")
def pages_range(ctx: Context) -> list[Finding]:
    """Report a numeric page range that does not use an en dash.

    A value made of digits, a dash and digits is rewritten with ``--``, whatever
    dash and spacing it used. Anything else, such as ``{e12--e19}`` or a single
    page, is left untouched.

    .. code-block:: bibtex

       @article{k, pages = {4101-4105}}

    pybtex: nothing, typography of the rendered reference.
    """
    findings: list[Finding] = []
    for entry in ctx.entries():
        if ctx.is_excluded(entry):
            continue
        for field in _fields_named(entry, "pages"):
            text = _single_text(field.value)
            if text is None:
                continue
            match = _RANGE.fullmatch(text)
            if match is None:
                continue
            target = f"{match[1]}--{match[2]}"
            if text == target:
                continue
            field.value = Value([Part("braced", target)])
            message = f"page range '{text}' should use '--'"
            findings.append(Finding(field.start, message, True))
    return findings
