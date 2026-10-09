from __future__ import annotations

from typing import TYPE_CHECKING

import click
import pytest

from bibclean._commands._common import _dedupe, _validate_encoding, execute

if TYPE_CHECKING:
    from pathlib import Path

CLEAN = "@misc{k,\n  title = {A}\n}\n"
DIRTY = "@Misc{k, Title = {A}}\n"


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
        "verbose": False,
        "quiet": False,
        "diff": False,
    }
    defaults.update(kwargs)
    return execute(files, **defaults)


def test_dedupe() -> None:
    """Test that repeated paths are dropped in first-occurrence order."""
    assert _dedupe(("b.bib", "a.bib", "b.bib")) == ["b.bib", "a.bib"]
    assert _dedupe(()) == []


def test_validate_encoding() -> None:
    """Test the encoding callback."""
    assert _validate_encoding(None, None, "latin-1") == "latin-1"
    with pytest.raises(click.BadParameter, match="unknown encoding 'utf-9'"):
        _validate_encoding(None, None, "utf-9")


def test_mutually_exclusive_options(tmp_path: Path) -> None:
    """Test the two pairs of options that cannot be combined."""
    config = _write(tmp_path, "bibclean.toml", "indent = 4\n")
    with pytest.raises(click.UsageError, match="--config and --isolated"):
        _execute(("a.bib",), config=config)
    with pytest.raises(click.UsageError, match="--verbose and --quiet"):
        _execute(("a.bib",), verbose=True, quiet=True)


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

    monkeypatch.setattr("bibclean._commands._common.write_source", _fail)
    assert _execute((str(dirty),), mode="fix") == 2
    assert "error: cannot write file: Permission denied" in capsys.readouterr().err


def test_convergence_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Test that an internal error is one line on stderr and exit code 2."""
    dirty = _write(tmp_path, "a.bib", DIRTY)

    def _fail(path: str, *args: object, **kwargs: object) -> None:
        raise RuntimeError(f"{path}: internal error, fixes did not converge")

    monkeypatch.setattr("bibclean._commands._common.process", _fail)
    assert _execute((str(dirty),)) == 2
    err = capsys.readouterr().err
    assert err == f"{dirty}: error: internal error, fixes did not converge\n"


def test_quiet_prints_the_summary_only(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test the quiet mode."""
    dirty = _write(tmp_path, "a.bib", DIRTY)
    assert _execute((str(dirty),), quiet=True) == 1
    assert capsys.readouterr().out == "Found 1 violation (1 fixable).\n"


def test_verbose_lines(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Test the verbose lines of a run without violation."""
    clean = _write(tmp_path, "a.bib", CLEAN)
    assert _execute((str(clean),), verbose=True) == 0
    lines = capsys.readouterr().err.splitlines()
    assert lines[0].startswith("bibclean ")
    assert lines[1] == f"{clean}: configuration defaults"
    assert lines[2] == f"{clean}: ok"


def test_verbose_reports_the_configuration_file(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test that the discovered configuration file is named."""
    config = _write(tmp_path, "bibclean.toml", "indent = 2\n")
    clean = _write(tmp_path, "a.bib", CLEAN)
    assert _execute((str(clean),), isolated=False, verbose=True) == 0
    assert f"{clean}: configuration {config}" in capsys.readouterr().err


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


def test_verbose_fix_reports_a_written_file(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test the verbose line of a file that was rewritten."""
    dirty = _write(tmp_path, "a.bib", DIRTY)
    assert _execute((str(dirty),), mode="fix", verbose=True) == 1
    assert capsys.readouterr().err.splitlines()[-1] == f"{dirty}: written"


def test_verbose_fix_reports_a_diff(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Test the verbose line of a file that --diff would rewrite."""
    dirty = _write(tmp_path, "a.bib", DIRTY)
    assert _execute((str(dirty),), mode="fix", verbose=True, diff=True) == 1
    captured = capsys.readouterr()
    assert captured.err.splitlines()[-1] == f"{dirty}: would write"
    assert captured.out.startswith(f"--- a/{dirty}")
