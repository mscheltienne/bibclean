from __future__ import annotations

from typing import TYPE_CHECKING

from bibclean._commands.check import run

if TYPE_CHECKING:
    from pathlib import Path

    from click.testing import CliRunner

CLEAN = "@misc{k,\n  title = {A}\n}\n"


def _write(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def test_help(runner: CliRunner) -> None:
    """Test that every shared option is documented."""
    result = runner.invoke(run, ["--help"])
    assert result.exit_code == 0
    assert "FILES..." in result.stdout
    for option in (
        "--config",
        "--isolated",
        "--ignore",
        "--encoding",
        "--verbose",
        "--quiet",
    ):
        assert option in result.stdout
    assert "--diff" not in result.stdout


def test_files_are_required(runner: CliRunner) -> None:
    """Test that at least one file must be given."""
    result = runner.invoke(run, [])
    assert result.exit_code == 2
    assert "Missing argument" in result.stderr


def test_missing_configuration_file(tmp_path: Path, runner: CliRunner) -> None:
    """Test that --config rejects a path that does not exist."""
    path = _write(tmp_path, "a.bib", CLEAN)
    result = runner.invoke(run, ["-c", str(tmp_path / "absent.toml"), str(path)])
    assert result.exit_code == 2
    assert "does not exist" in result.stderr


def test_exit_code_zero(tmp_path: Path, runner: CliRunner) -> None:
    """Test the exit code of a canonical file."""
    path = _write(tmp_path, "a.bib", CLEAN)
    assert runner.invoke(run, ["--isolated", str(path)]).exit_code == 0


def test_exit_code_one(tmp_path: Path, runner: CliRunner) -> None:
    """Test the exit code of a file with a violation."""
    path = _write(tmp_path, "a.bib", "@Misc{k, Title = {A}}\n")
    assert runner.invoke(run, ["--isolated", str(path)]).exit_code == 1


def test_exit_code_two(tmp_path: Path, runner: CliRunner) -> None:
    """Test the exit code of a file that cannot be read."""
    assert runner.invoke(run, ["--isolated", str(tmp_path / "a.bib")]).exit_code == 2


def test_check_never_writes(tmp_path: Path, runner: CliRunner) -> None:
    """Test that 'check' leaves the file untouched."""
    path = _write(tmp_path, "a.bib", "@Misc{k, Title = {A}}\n")
    runner.invoke(run, ["--isolated", str(path)])
    assert path.read_text(encoding="utf-8") == "@Misc{k, Title = {A}}\n"
