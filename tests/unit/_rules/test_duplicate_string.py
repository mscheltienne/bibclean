from __future__ import annotations

from bibclean._config import default_config
from bibclean._engine import process
from tests.helpers import apply_rule

NAME = "duplicate-string"
SOURCE = (
    "@string{v = {A}}\n@misc{a, title = v}\n@string{V = {B}}\n@misc{b, title = v}\n"
)


def test_detection() -> None:
    """Test that a redefinition is reported against the first one."""
    rows, _ = apply_rule(NAME, SOURCE)
    assert rows == [(3, 1, "string 'V' is already defined as 'v' at line 1", False)]
    assert apply_rule(NAME, "@string{v = {A}}\n@string{w = {A}}\n")[0] == []


def test_file_is_never_rewritten() -> None:
    """Test that a file redefining a macro is reported but never rewritten."""
    report = process(SOURCE.encode(), "utf-8", default_config())
    assert report.output is None
    assert [(item.rule, item.fixable) for item in report.diagnostics] == [(NAME, False)]
