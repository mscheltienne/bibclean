from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._commands.fix import run

if TYPE_CHECKING:
    from pathlib import Path

    from click.testing import CliRunner

CLEAN = "@misc{k,\n  title = {A}\n}\n"
DIRTY = "@Misc{k, Title = {A}}\n"


def _write(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def test_help(runner: CliRunner) -> None:
    """Test that the fixer documents --diff on top of the shared options."""
    result = runner.invoke(run, ["--help"])
    assert result.exit_code == 0
    assert "--diff" in result.stdout
    for option in (
        "--config",
        "--isolated",
        "--ignore",
        "--encoding",
        "--verbose",
        "--quiet",
    ):
        assert option in result.stdout


def test_exit_code_zero(tmp_path: Path, runner: CliRunner) -> None:
    """Test the exit code when nothing is written."""
    path = _write(tmp_path, "a.bib", CLEAN)
    assert runner.invoke(run, ["--isolated", str(path)]).exit_code == 0


def test_exit_code_one(tmp_path: Path, runner: CliRunner) -> None:
    """Test the exit code when a file is written."""
    path = _write(tmp_path, "a.bib", DIRTY)
    assert runner.invoke(run, ["--isolated", str(path)]).exit_code == 1
    assert path.read_text(encoding="utf-8") == CLEAN


def test_exit_code_two(tmp_path: Path, runner: CliRunner) -> None:
    """Test the exit code of a file that cannot be read."""
    assert runner.invoke(run, ["--isolated", str(tmp_path / "a.bib")]).exit_code == 2


def test_diff_does_not_write(tmp_path: Path, runner: CliRunner) -> None:
    """Test that --diff reports the change without applying it."""
    path = _write(tmp_path, "a.bib", DIRTY)
    result = runner.invoke(run, ["--isolated", "--diff", str(path)])
    assert result.exit_code == 1
    assert path.read_text(encoding="utf-8") == DIRTY
    assert "would write 1 file" in result.stdout


def test_encoding_round_trip(tmp_path: Path, runner: CliRunner) -> None:
    """Test that the file is rewritten with the requested encoding."""
    path = tmp_path / "a.bib"
    path.write_bytes("@Misc{k, Title = {é}}\n".encode("latin-1"))
    assert (
        runner.invoke(run, ["--isolated", "--encoding", "latin-1", str(path)]).exit_code
        == 1
    )
    assert path.read_bytes() == "@misc{k,\n  title = {é}\n}\n".encode("latin-1")
