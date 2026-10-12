from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Literal

from bibclean._formatter import render_entry
from bibclean._model import Entry, entry_type

if TYPE_CHECKING:
    from collections.abc import Iterator

    from bibclean._config import Config, FormatOptions, TypeRules
    from bibclean._model import Block, Position

Fixability = Literal["no", "partial", "yes"]
Scope = Literal["block", "file", "entry", "field", "value"]


@dataclass(slots=True, frozen=True)
class Diagnostic:
    """One reported violation.

    Parameters
    ----------
    position : Position | None
        Where the violation is, None for a file-level violation.
    message : str
        Description of the violation.
    fixable : bool
        True when running ``bibclean fix`` resolves the violation.
    rule : str | None
        Name of the rule, filled in by the engine; None for a file-level violation.
    """

    position: Position | None
    message: str
    fixable: bool
    rule: str | None = None


@dataclass(slots=True)
class Context:
    """State shared by the rules running over one file.

    Parameters
    ----------
    blocks : list of Block
        The working model, mutated by the rules that fix.
    config : Config
        Effective configuration of the file.
    """

    blocks: list[Block]
    config: Config

    def entries(self) -> list[Entry]:
        """Return the entries of the working model.

        Returns
        -------
        list of Entry
            The entries, in their current order.
        """
        return [block for block in self.blocks if isinstance(block, Entry)]

    def checked_entries(self) -> Iterator[Entry]:
        """Yield the entries of the working model that the rules inspect.

        Yields
        ------
        Entry
            The entries that are not excluded, in their current order. The list is
            taken before the first one is yielded, so a rule may mutate the blocks.
        """
        for entry in self.entries():
            if not self.is_excluded(entry):
                yield entry

    def is_excluded(self, entry: Entry) -> bool:
        """Check whether an entry is exempt from the rules.

        Parameters
        ----------
        entry : Entry
            Entry to inspect.

        Returns
        -------
        bool
            True when the cite key is listed in ``exclude`` or the entry type in
            ``exclude-types``.
        """
        lint = self.config.lint
        return entry.key in lint.exclude or entry_type(entry) in lint.exclude_types

    def type_rules(self, entry: Entry) -> TypeRules | None:
        """Return the field requirements of the type of an entry.

        Parameters
        ----------
        entry : Entry
            Entry to inspect.

        Returns
        -------
        TypeRules | None
            The rules of the entry type, None when the type is unknown.
        """
        return self.config.lint.types.get(entry_type(entry))


RuleFunction = Callable[[Context], list[Diagnostic]]


@dataclass(slots=True, frozen=True)
class Rule:
    """One lint rule.

    Parameters
    ----------
    name : str
        Kebab-case name used by ``ignore`` and ``--ignore``.
    fixable : str
        One of ``'no'``, ``'partial'`` or ``'yes'``.
    scope : str
        One of ``'block'``, ``'file'``, ``'entry'``, ``'field'`` or ``'value'``.
    check : callable
        Function running the rule over a context and returning its diagnostics. The
        summary and extended summary of its docstring document the rule.
    """

    name: str
    fixable: Fixability
    scope: Scope
    check: RuleFunction


def rule(
    *, name: str, fixable: Fixability, scope: Scope
) -> Callable[[RuleFunction], Rule]:
    """Turn a rule function into a :class:`Rule`.

    Parameters
    ----------
    name : str
        Kebab-case name of the rule.
    fixable : str
        One of ``'no'``, ``'partial'`` or ``'yes'``.
    scope : str
        One of ``'block'``, ``'file'``, ``'entry'``, ``'field'`` or ``'value'``.

    Returns
    -------
    callable
        A decorator replacing the function by the corresponding rule.
    """

    def decorator(function: RuleFunction) -> Rule:
        """Build the rule of a function.

        Parameters
        ----------
        function : callable
            Function running the rule over a context and returning its diagnostics.

        Returns
        -------
        Rule
            The rule.
        """
        return Rule(name=name, fixable=fixable, scope=scope, check=function)

    return decorator


def signature(entry: Entry, options: FormatOptions) -> str:
    """Build the comparison signature of an entry.

    Parameters
    ----------
    entry : Entry
        Entry to describe.
    options : FormatOptions
        Formatting options used to render the entry.

    Returns
    -------
    str
        The canonical rendering of the entry with its cite key blanked, so that the
        cite key is not part of the signature.
    """
    return render_entry(replace(entry, key=""), options)
