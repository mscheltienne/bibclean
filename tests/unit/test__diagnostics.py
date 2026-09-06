from __future__ import annotations

import io

import pytest

from bibclean._diagnostics import (
    Diagnostic,
    format_diagnostic,
    pluralize,
    sort_diagnostics,
    summary_check,
    summary_fix,
    use_color,
)

POSITIONED = Diagnostic("a.bib", 3, 5, "doi-prefix", "boom", True)
UNFIXABLE = Diagnostic("a.bib", 1, 1, "required-field", "missing", False)
FILE_LEVEL = Diagnostic("a.bib", None, None, None, "file is not formatted", True)


class _Tty(io.StringIO):
    def __init__(self, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


@pytest.mark.parametrize(
    ("count", "expected"),
    [(0, "0 violations"), (1, "1 violation"), (2, "2 violations")],
)
def test_pluralize(count: int, expected: str) -> None:
    """Test the singular and plural forms."""
    assert pluralize(count, "violation") == expected


def test_pluralize_irregular() -> None:
    """Test an explicit plural form."""
    assert pluralize(2, "entry", "entries") == "2 entries"


@pytest.mark.parametrize(
    ("diagnostic", "expected"),
    [
        (POSITIONED, "a.bib:3:5: doi-prefix boom [*]"),
        (UNFIXABLE, "a.bib:1:1: required-field missing"),
        (FILE_LEVEL, "a.bib: file is not formatted [*]"),
    ],
)
def test_format_diagnostic(diagnostic: Diagnostic, expected: str) -> None:
    """Test the plain rendering of a diagnostic."""
    assert format_diagnostic(diagnostic, color=False) == expected


@pytest.mark.parametrize("diagnostic", [POSITIONED, UNFIXABLE, FILE_LEVEL])
def test_format_diagnostic_color(diagnostic: Diagnostic) -> None:
    """Test that the coloured rendering only adds escape codes."""
    import click

    colored = format_diagnostic(diagnostic, color=True)
    assert "\x1b[" in colored
    assert click.unstyle(colored) == format_diagnostic(diagnostic, color=False)


def test_sort_diagnostics() -> None:
    """Test the ordering by file, then position, with file-level findings last."""
    other = Diagnostic("b.bib", 1, 1, "empty-field", "empty", True)
    ordered = sort_diagnostics(
        [FILE_LEVEL, other, POSITIONED, UNFIXABLE], ["a.bib", "b.bib"]
    )
    assert ordered == [UNFIXABLE, POSITIONED, FILE_LEVEL, other]


def test_sort_diagnostics_is_stable() -> None:
    """Test that two findings at one position keep the pipeline order."""
    first = Diagnostic("a.bib", 2, 2, "empty-field", "one", True)
    second = Diagnostic("a.bib", 2, 2, "strip-field", "two", True)
    assert sort_diagnostics([first, second], ["a.bib"]) == [first, second]


def test_sort_diagnostics_unknown_file() -> None:
    """Test that a file outside the argument order sorts last."""
    stray = Diagnostic("z.bib", 1, 1, "empty-field", "empty", True)
    assert sort_diagnostics([stray, POSITIONED], ["a.bib"]) == [POSITIONED, stray]


@pytest.mark.parametrize(
    ("diagnostics", "expected"),
    [
        ([], "Found 0 violations (0 fixable)."),
        ([POSITIONED], "Found 1 violation (1 fixable)."),
        ([POSITIONED, UNFIXABLE], "Found 2 violations (1 fixable)."),
    ],
)
def test_summary_check(diagnostics: list[Diagnostic], expected: str) -> None:
    """Test the summary line of check."""
    assert summary_check(diagnostics) == expected


@pytest.mark.parametrize(
    ("fixed", "written", "diff", "expected"),
    [
        (0, 0, False, "Fixed 0 violations, wrote 0 files."),
        (3, 1, False, "Fixed 3 violations, wrote 1 file."),
        (1, 1, True, "Fixed 1 violation, would write 1 file."),
    ],
)
def test_summary_fix(fixed: int, written: int, diff: bool, expected: str) -> None:
    """Test the summary line of fix."""
    assert summary_fix(fixed, written, diff=diff) == expected


def test_use_color(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the colour detection."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    assert use_color(_Tty(True)) is True
    assert use_color(_Tty(False)) is False
    monkeypatch.setenv("TERM", "dumb")
    assert use_color(_Tty(True)) is False
    monkeypatch.setenv("TERM", "xterm")
    monkeypatch.setenv("NO_COLOR", "1")
    assert use_color(_Tty(True)) is False
    monkeypatch.setenv("NO_COLOR", "")
    assert use_color(_Tty(True)) is True
