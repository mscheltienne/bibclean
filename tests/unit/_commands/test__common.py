from __future__ import annotations

import io
from typing import TYPE_CHECKING

import click
import pytest

from bibclean._commands._common import (
    _validate_encoding,
    execute,
    format_diagnostic,
    pluralize,
    use_color,
)
from bibclean._model import Position
from bibclean._rules._base import Diagnostic

if TYPE_CHECKING:
    from pathlib import Path

CLEAN = "@misc{k,\n  title = {A}\n}\n"
DIRTY = "@Misc{k, Title = {A}}\n"
POSITIONED = Diagnostic(Position(3, 5), "boom", True, "doi-prefix")
UNFIXABLE = Diagnostic(Position(1, 1), "missing", False, "required-field")
FILE_LEVEL = Diagnostic(None, "file is not formatted", True)


class _Tty(io.StringIO):
    def __init__(self, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def _write(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _execute(files: tuple[str, ...], **kwargs: object) -> int:
    defaults = {
        "mode": "check",
        "config": None,
        "isolated": True,
        "ignore": (),
        "encoding": "utf-8",
        "quiet": False,
        "diff": False,
    }
    defaults.update(kwargs)
    return execute(files, **defaults)


@pytest.mark.parametrize(
    ("count", "expected"),
    [(0, "0 violations"), (1, "1 violation"), (2, "2 violations")],
)
def test_pluralize(count: int, expected: str) -> None:
    """Test the singular and plural forms."""
    assert pluralize(count, "violation") == expected


@pytest.mark.parametrize(
    ("diagnostic", "expected"),
    [
        (POSITIONED, "a.bib:3:5: doi-prefix boom [*]"),
        (UNFIXABLE, "a.bib:1:1: required-field missing"),
        (FILE_LEVEL, "a.bib: file is not formatted [*]"),
    ],
)
def test_format_diagnostic(diagnostic: Diagnostic, expected: str) -> None:
    """Test that a diagnostic renders as a styled line."""
    line = format_diagnostic("a.bib", diagnostic)
    assert "\x1b[" in line
    assert click.unstyle(line) == expected


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


def test_validate_encoding() -> None:
    """Test the encoding callback."""
    assert _validate_encoding(None, None, "latin-1") == "latin-1"
    with pytest.raises(click.BadParameter, match="unknown encoding 'utf-9'"):
        _validate_encoding(None, None, "utf-9")


def test_config_and_isolated_are_exclusive(tmp_path: Path) -> None:
    """Test that --config and --isolated cannot be combined."""
    config = _write(tmp_path, "bibclean.toml", "indent = 4\n")
    with pytest.raises(click.UsageError, match="--config and --isolated"):
        _execute(("a.bib",), config=config)


def test_check_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test the exit codes of the check mode."""
    clean = _write(tmp_path, "a.bib", CLEAN)
    dirty = _write(tmp_path, "b.bib", DIRTY)
    assert _execute((str(clean),)) == 0
    assert capsys.readouterr().out == ""
    assert _execute((str(dirty),)) == 1
    assert _execute((str(tmp_path / "absent.bib"),)) == 2


def test_fix_writes(tmp_path: Path) -> None:
    """Test that the fix mode rewrites a file and counts it."""
    dirty = _write(tmp_path, "a.bib", DIRTY)
    assert _execute((str(dirty),), mode="fix") == 1
    assert dirty.read_text(encoding="utf-8") == CLEAN
    assert _execute((str(dirty),), mode="fix") == 0


def test_error_does_not_stop_the_batch(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test that a file that cannot be read is skipped, not fatal."""
    dirty = _write(tmp_path, "a.bib", DIRTY)
    code = _execute((str(tmp_path / "absent.bib"), str(dirty)), mode="fix")
    captured = capsys.readouterr()
    assert code == 2
    assert dirty.read_text(encoding="utf-8") == CLEAN
    assert "error: cannot read file:" in captured.err
    assert "wrote 1 file" in captured.out


def test_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that a file that cannot be written is reported."""
    dirty = _write(tmp_path, "a.bib", DIRTY)

    def _fail(*args: object, **kwargs: object) -> None:
        raise OSError(13, "Permission denied")

    monkeypatch.setattr("pathlib.Path.write_bytes", _fail)
    assert _execute((str(dirty),), mode="fix") == 2
    assert "error: cannot write file: Permission denied" in capsys.readouterr().err


def test_quiet_prints_the_summary_only(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test the quiet mode."""
    dirty = _write(tmp_path, "a.bib", DIRTY)
    assert _execute((str(dirty),), quiet=True) == 1
    assert capsys.readouterr().out == "Found 1 violation (1 fixable).\n"


def test_invalid_configuration_override(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test that an invalid --config file is reported once for the whole batch."""
    config = _write(tmp_path, "custom.toml", "indent = 0\n")
    first = _write(tmp_path, "a.bib", CLEAN)
    second = _write(tmp_path, "b.bib", CLEAN)
    code = _execute((str(first), str(second)), isolated=False, config=config)
    err = capsys.readouterr().err
    assert code == 2
    assert err.count("error:") == 1
    assert err.startswith(f"{config}: error:")


def test_fix_diff(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test that --diff prints the change and writes nothing."""
    dirty = _write(tmp_path, "a.bib", DIRTY)
    assert _execute((str(dirty),), mode="fix", diff=True) == 1
    assert capsys.readouterr().out.startswith(f"--- a/{dirty}")
    assert dirty.read_text(encoding="utf-8") == DIRTY
