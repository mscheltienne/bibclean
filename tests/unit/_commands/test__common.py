from __future__ import annotations

import io

import click
import pytest

from bibclean._commands._common import format_diagnostic, use_color
from bibclean._model import Position
from bibclean._rules._base import Diagnostic


class _Tty(io.StringIO):
    """Text stream reporting whether it is a terminal."""

    def __init__(self, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        """Report whether the stream is a terminal."""
        return self._tty


def test_format_diagnostic() -> None:
    """Test that a diagnostic renders as a line carrying ANSI escape codes."""
    line = format_diagnostic("a.bib", Diagnostic(Position(3, 5), "boom", True, "x"))
    assert "\x1b[" in line
    assert click.unstyle(line) == "a.bib:3:5: x boom [*]"


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
