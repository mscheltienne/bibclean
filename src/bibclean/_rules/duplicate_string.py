from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._model import StringDef
from bibclean._rules._base import Diagnostic, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context


@rule(name="duplicate-string", fixable="no", scope="file")
def duplicate_string(ctx: Context) -> list[Diagnostic]:
    """Report a ``@string`` macro that is already defined, case-insensitively.

    The canonical format writes every ``@string`` before the entries, which changes
    the value of a redefined macro in the entries written between two definitions.
    A file redefining a macro is therefore never rewritten: every rule still reports
    its violations, but none of them is fixable. A third definition is reported
    against the first.

    .. code-block:: bibtex

       @string{venue = {NeurIPS}}
       @inproceedings{a, booktitle = venue}
       @string{Venue = {ICML}}
       @inproceedings{b, booktitle = venue}

    pybtex: a macro takes its latest definition at each point of the file, so
    reordering the blocks changes the values of the entries.

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
    seen: dict[str, StringDef] = {}
    for block in ctx.blocks:
        if not isinstance(block, StringDef):
            continue
        first = seen.setdefault(block.key.lower(), block)
        if first is not block:
            message = (
                f"string '{block.key}' is already defined as '{first.key}' "
                f"at line {first.start.line}"
            )
            findings.append(Diagnostic(block.start, message, False))
    return findings
