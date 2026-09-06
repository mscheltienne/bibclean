from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._model import Malformed
from bibclean._rules._base import Finding, rule

if TYPE_CHECKING:
    from bibclean._rules._base import Context


@rule(name="syntax-error", fixable="no", scope="block")
def syntax_error(ctx: Context) -> list[Finding]:
    """Report a block that could not be read.

    The block is kept verbatim at its position and reported once, at the ``@``
    that opens it, with the reason and the position at which reading failed.

    .. code-block:: bibtex

       @article{broken,
         title = {Missing closing brace,
         year = {2002}
       }

    pybtex: the documentation build fails on the file.
    """
    return [
        Finding(block.start, block.message, False)
        for block in ctx.blocks
        if isinstance(block, Malformed)
    ]
