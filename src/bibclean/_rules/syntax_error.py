from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._model import Malformed
from bibclean._rules._base import Diagnostic, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context


@rule(name="syntax-error", fixable="no", scope="block")
def syntax_error(ctx: Context) -> list[Diagnostic]:
    """Report a block that could not be read.

    The block is reported once, at the ``@`` that opens it, with the reason and the
    position at which reading failed. A file with a syntax error is never rewritten:
    every rule still reports its violations, but none of them is fixable, as the
    text swallowed by the broken block cannot be reordered safely.

    Like BibTeX, every ``@`` starts a block, so an e-mail address in a ``%`` line is
    a syntax error too.

    .. code-block:: bibtex

       % write to me@example.org

       @article{broken,
         title = {Missing closing brace,
         year = {2002}
       }

    pybtex: the documentation build fails on the file.
    """
    return [
        Diagnostic(block.start, block.message, False)
        for block in ctx.blocks
        if isinstance(block, Malformed)
    ]
