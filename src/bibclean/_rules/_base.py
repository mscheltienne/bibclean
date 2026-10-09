from __future__ import annotations

import inspect
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from bibclean._formatter import collapse_whitespace, render_fields
from bibclean._model import Entry, entry_type

if TYPE_CHECKING:
    from bibclean._config import Config, FormatOptions, TypeRules
    from bibclean._model import Block, Field, Position, Value

Fixability = Literal["no", "partial", "yes"]
Scope = Literal["block", "file", "entry", "field", "value"]

_NAME = re.compile(r"^[a-z]+(-[a-z]+)*$")


@dataclass(slots=True, frozen=True)
class Finding:
    """One violation reported by a rule.

    Parameters
    ----------
    position : Position | None
        Where the violation is, None for a file-level finding.
    message : str
        Description of the violation.
    fixable : bool
        True when the rule changed the working model to resolve the violation.
    """

    position: Position | None
    message: str
    fixable: bool


@dataclass(slots=True)
class Context:
    """State shared by the rules running over one file.

    Parameters
    ----------
    path : str
        File being linted, as typed on the command line.
    blocks : list of Block
        The working model, mutated by the rules that fix.
    config : Config
        Effective configuration of the file.
    """

    path: str
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

    def remove(self, block: Block) -> None:
        """Remove a block from the working model.

        Parameters
        ----------
        block : Block
            Block to remove, identified by identity.
        """
        for index, item in enumerate(self.blocks):
            if item is block:
                del self.blocks[index]
                return


RuleFunction = Callable[[Context], list[Finding]]


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
        Function running the rule over a context and returning its findings.
    doc : str
        Cleaned docstring of the function.
    """

    name: str
    fixable: Fixability
    scope: Scope
    check: RuleFunction
    doc: str


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

    Raises
    ------
    ValueError
        If the name is not kebab-case or the function has no docstring.
    """
    if _NAME.fullmatch(name) is None:
        raise ValueError(f"invalid rule name '{name}'")

    def decorator(function: RuleFunction) -> Rule:
        doc = inspect.cleandoc(function.__doc__ or "")
        if not doc:
            raise ValueError(f"rule '{name}' has no docstring")
        return Rule(name=name, fixable=fixable, scope=scope, check=function, doc=doc)

    return decorator


def signature(entry: Entry, options: FormatOptions) -> tuple[str, str]:
    """Build the comparison signature of an entry.

    Parameters
    ----------
    entry : Entry
        Entry to describe.
    options : FormatOptions
        Formatting options used to render the fields.

    Returns
    -------
    tuple of str
        The lowercased entry type and the rendered field lines. The cite key is
        not part of the signature.
    """
    return (entry_type(entry), render_fields(entry, options))


def _fields_named(entry: Entry, name: str) -> list[Field]:
    """Return the fields of an entry with a given name, case-insensitively."""
    lowered = name.lower()
    return [field for field in entry.fields if field.key.lower() == lowered]


def _has_field(entry: Entry, name: str) -> bool:
    """Check whether an entry has a field with a given name."""
    lowered = name.lower()
    return any(field.key.lower() == lowered for field in entry.fields)


def _single_text(value: Value) -> str | None:
    """Return the collapsed text of a value made of one braced or quoted part."""
    if len(value.parts) != 1:
        return None
    part = value.parts[0]
    if part.kind == "bare":
        return None
    return collapse_whitespace(part.text).strip()


def _remove_field(entry: Entry, field: Field) -> None:
    """Remove a field from an entry, identified by identity."""
    for index, item in enumerate(entry.fields):
        if item is field:
            del entry.fields[index]
            return
