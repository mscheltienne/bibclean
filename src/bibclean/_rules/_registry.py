from __future__ import annotations

from bibclean._rules._base import Rule
from bibclean._rules.doi_prefix import doi_prefix
from bibclean._rules.duplicate_doi import duplicate_doi
from bibclean._rules.duplicate_field import duplicate_field
from bibclean._rules.duplicate_key import duplicate_key
from bibclean._rules.empty_field import empty_field
from bibclean._rules.month_format import month_format
from bibclean._rules.pages_range import pages_range
from bibclean._rules.required_field import required_field
from bibclean._rules.strip_field import strip_field
from bibclean._rules.syntax_error import syntax_error
from bibclean._rules.undefined_string import undefined_string
from bibclean._rules.unescaped_percent import unescaped_percent
from bibclean._rules.url_with_doi import url_with_doi

RULES: tuple[Rule, ...] = (
    syntax_error,
    duplicate_key,
    duplicate_doi,
    duplicate_field,
    empty_field,
    strip_field,
    url_with_doi,
    doi_prefix,
    month_format,
    pages_range,
    unescaped_percent,
    undefined_string,
    required_field,
)

RULE_NAMES: tuple[str, ...] = tuple(item.name for item in RULES)

_BY_NAME: dict[str, Rule] = {item.name: item for item in RULES}

if len(_BY_NAME) != len(RULES):  # pragma: no cover
    raise RuntimeError("the rule registry holds duplicate rule names")


def get_rule(name: str) -> Rule:
    """Look up a rule by name.

    Parameters
    ----------
    name : str
        Kebab-case name of the rule.

    Returns
    -------
    Rule
        The rule with that name.

    Raises
    ------
    KeyError
        If no rule has that name.
    """
    try:
        return _BY_NAME[name]
    except KeyError:
        raise KeyError(f"unknown rule '{name}'")
