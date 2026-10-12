from __future__ import annotations

from bibclean._rules._base import Rule
from bibclean._rules.author_format import author_format
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

# The rules fixing a value run before the rules comparing values, so that two fields
# or entries that only become identical once fixed are merged by a single fix.
RULES: tuple[Rule, ...] = (
    syntax_error,
    doi_prefix,
    empty_field,
    strip_field,
    url_with_doi,
    month_format,
    pages_range,
    unescaped_percent,
    duplicate_field,
    duplicate_key,
    duplicate_doi,
    undefined_string,
    author_format,
    required_field,
)

RULE_NAMES: tuple[str, ...] = tuple(item.name for item in RULES)
