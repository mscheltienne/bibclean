from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bibclean._commands.main import run

if TYPE_CHECKING:
    from pathlib import Path

    from click.testing import CliRunner

CLEAN = "@misc{k,\n  title = {A}\n}\n"
DIRTY = "@Misc{k, Title = {A}}\n"
UNFIXABLE = "@article{k,\n  title = {A}\n}\n"


def _write(directory: Path, name: str, text: str) -> Path:
    """Write a file with line feed endings."""
    path = directory / name
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def test_check_clean_file(tmp_path: Path, runner: CliRunner) -> None:
    """Test that a canonical file reports nothing and exits 0."""
    path = _write(tmp_path, "a.bib", CLEAN)
    result = runner.invoke(run, ["check", "--isolated", str(path)])
    assert result.exit_code == 0
    assert result.stdout == ""


def test_check_dirty_file(tmp_path: Path, runner: CliRunner) -> None:
    """Test that a violation exits 1 and prints a summary."""
    path = _write(tmp_path, "a.bib", DIRTY)
    result = runner.invoke(run, ["check", "--isolated", str(path)])
    assert result.exit_code == 1
    assert "file is not formatted" in result.stdout
    assert result.stdout.endswith("Found 1 violation (1 fixable).\n")


def test_check_missing_file(tmp_path: Path, runner: CliRunner) -> None:
    """Test that an unreadable file exits 2 with an error line on stderr."""
    result = runner.invoke(run, ["check", "--isolated", str(tmp_path / "absent.bib")])
    assert result.exit_code == 2
    assert result.stdout == ""
    assert "error: cannot read file:" in result.stderr


def test_check_bad_encoding(tmp_path: Path, runner: CliRunner) -> None:
    """Test the error line of a file that cannot be decoded."""
    path = tmp_path / "a.bib"
    path.write_bytes("@misc{k,\n  title = {é}\n}\n".encode("latin-1"))
    result = runner.invoke(run, ["check", "--isolated", str(path)])
    assert result.exit_code == 2
    assert "error: cannot decode file with encoding 'utf-8'" in result.stderr


def test_encoding_option(tmp_path: Path, runner: CliRunner) -> None:
    """Test that a non-UTF-8 file round trips with --encoding."""
    path = tmp_path / "a.bib"
    path.write_bytes("@misc{k,\n  title = {é}\n}\n".encode("latin-1"))
    result = runner.invoke(
        run, ["check", "--isolated", "--encoding", "latin-1", str(path)]
    )
    assert result.exit_code == 0
    assert result.stdout == ""


def test_unknown_encoding(tmp_path: Path, runner: CliRunner) -> None:
    """Test that an unknown encoding name is a usage error."""
    path = _write(tmp_path, "a.bib", CLEAN)
    result = runner.invoke(run, ["check", "--encoding", "utf-9", str(path)])
    assert result.exit_code == 2
    assert "unknown encoding 'utf-9'" in result.stderr


def test_batch_continues_after_an_error(tmp_path: Path, runner: CliRunner) -> None:
    """Test that one unreadable file does not stop the others."""
    good = _write(tmp_path, "a.bib", DIRTY)
    missing = tmp_path / "absent.bib"
    other = _write(tmp_path, "b.bib", DIRTY)
    result = runner.invoke(
        run, ["check", "--isolated", str(good), str(missing), str(other)]
    )
    assert result.exit_code == 2
    assert result.stdout.count("file is not formatted") == 2
    assert result.stdout.endswith("Found 2 violations (2 fixable).\n")
    assert result.stderr.count("error: cannot read file:") == 1


def test_batch_mixed_results(tmp_path: Path, runner: CliRunner) -> None:
    """Test that one dirty file among clean ones exits 1."""
    clean = _write(tmp_path, "a.bib", CLEAN)
    dirty = _write(tmp_path, "b.bib", DIRTY)
    result = runner.invoke(run, ["check", "--isolated", str(clean), str(dirty)])
    assert result.exit_code == 1
    assert result.stdout.count("\n") == 2


def test_repeated_file_is_processed_once(tmp_path: Path, runner: CliRunner) -> None:
    """Test that the same path given twice yields one set of diagnostics."""
    path = _write(tmp_path, "a.bib", DIRTY)
    result = runner.invoke(run, ["check", "--isolated", str(path), str(path)])
    assert result.exit_code == 1
    assert result.stdout.count("file is not formatted") == 1


def test_fix_writes_and_exits_one(tmp_path: Path, runner: CliRunner) -> None:
    """Test that 'fix' rewrites a file and exits 1."""
    path = _write(tmp_path, "a.bib", DIRTY)
    result = runner.invoke(run, ["fix", "--isolated", str(path)])
    assert result.exit_code == 1
    assert path.read_bytes() == CLEAN.encode("utf-8")
    assert result.stdout == "Fixed 1 violation, wrote 1 file.\n"


def test_fix_diff_writes_nothing(tmp_path: Path, runner: CliRunner) -> None:
    """Test that --diff prints the change and leaves the file alone."""
    path = _write(tmp_path, "a.bib", DIRTY)
    result = runner.invoke(run, ["fix", "--isolated", "--diff", str(path)])
    assert result.exit_code == 1
    assert path.read_text(encoding="utf-8") == DIRTY
    assert f"--- a/{path}" in result.stdout
    assert f"+++ b/{path}" in result.stdout
    assert result.stdout.endswith("Fixed 1 violation, would write 1 file.\n")


def test_fix_reports_unfixable(tmp_path: Path, runner: CliRunner) -> None:
    """Test that 'fix' prints what it could not fix."""
    path = _write(tmp_path, "a.bib", UNFIXABLE)
    result = runner.invoke(run, ["fix", "--isolated", str(path)])
    assert result.exit_code == 1
    assert "required-field" in result.stdout
    assert result.stdout.endswith("Fixed 0 violations, wrote 0 files.\n")


def test_ignore_option(tmp_path: Path, runner: CliRunner) -> None:
    """Test that --ignore disables a rule."""
    path = _write(tmp_path, "a.bib", UNFIXABLE)
    assert runner.invoke(run, ["check", "--isolated", str(path)]).exit_code == 1
    result = runner.invoke(
        run, ["check", "--isolated", "--ignore", "required-field", str(path)]
    )
    assert result.exit_code == 0
    assert result.stdout == ""


def test_ignore_unknown_rule(tmp_path: Path, runner: CliRunner) -> None:
    """Test that an unknown rule name is a usage error."""
    path = _write(tmp_path, "a.bib", CLEAN)
    result = runner.invoke(run, ["check", "--ignore", "no-such-rule", str(path)])
    assert result.exit_code == 2
    assert "--ignore" in result.stderr


def test_quiet(tmp_path: Path, runner: CliRunner) -> None:
    """Test that --quiet prints the summary only."""
    path = _write(tmp_path, "a.bib", DIRTY)
    result = runner.invoke(run, ["check", "--isolated", "-q", str(path)])
    assert result.exit_code == 1
    assert result.stdout == "Found 1 violation (1 fixable).\n"


def test_verbose(tmp_path: Path, runner: CliRunner) -> None:
    """Test that --verbose reports the version and the per-file outcome."""
    path = _write(tmp_path, "a.bib", DIRTY)
    result = runner.invoke(run, ["check", "--isolated", "-v", str(path)])
    assert result.exit_code == 1
    lines = result.stderr.splitlines()
    assert lines[0].startswith("bibclean ")
    assert lines[1] == f"{path}: configuration defaults"
    assert lines[2] == f"{path}: 1 violation"


def test_verbose_fix(tmp_path: Path, runner: CliRunner) -> None:
    """Test the per-file outcome reported by 'fix'."""
    path = _write(tmp_path, "a.bib", UNFIXABLE)
    result = runner.invoke(run, ["fix", "--isolated", "-v", str(path)])
    assert (
        result.stderr.splitlines()[-1] == f"{path}: unchanged, 3 unfixable violations"
    )


def test_verbose_and_quiet_are_exclusive(tmp_path: Path, runner: CliRunner) -> None:
    """Test that --verbose and --quiet cannot be combined."""
    path = _write(tmp_path, "a.bib", CLEAN)
    result = runner.invoke(run, ["check", "-v", "-q", str(path)])
    assert result.exit_code == 2
    assert "--verbose and --quiet are mutually exclusive" in result.stderr


def test_config_and_isolated_are_exclusive(tmp_path: Path, runner: CliRunner) -> None:
    """Test that --config and --isolated cannot be combined."""
    path = _write(tmp_path, "a.bib", CLEAN)
    config = _write(tmp_path, "bibclean.toml", "indent = 4\n")
    result = runner.invoke(run, ["check", "--isolated", "-c", str(config), str(path)])
    assert result.exit_code == 2
    assert "--config and --isolated are mutually exclusive" in result.stderr


def test_isolated_ignores_a_discovered_configuration(
    tmp_path: Path, runner: CliRunner
) -> None:
    """Test that --isolated bypasses the configuration file next to the input."""
    path = _write(tmp_path, "a.bib", CLEAN)
    _write(tmp_path, "bibclean.toml", "indent = 4\n")
    assert runner.invoke(run, ["check", str(path)]).exit_code == 1
    assert runner.invoke(run, ["check", "--isolated", str(path)]).exit_code == 0


def test_configuration_is_discovered_per_directory(
    tmp_path: Path, runner: CliRunner
) -> None:
    """Test that two files in different trees pick different configurations."""
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    _write(left, "bibclean.toml", "indent = 4\n")
    _write(right, "bibclean.toml", "indent = 2\n")
    first = _write(left, "a.bib", CLEAN)
    second = _write(right, "b.bib", CLEAN)
    result = runner.invoke(run, ["check", str(first), str(second)])
    assert result.exit_code == 1
    assert result.stdout.count("file is not formatted") == 1
    assert str(first) in result.stdout


def test_invalid_configuration(tmp_path: Path, runner: CliRunner) -> None:
    """Test that an unknown configuration key exits 2 with a suggestion."""
    path = _write(tmp_path, "a.bib", CLEAN)
    _write(tmp_path, "bibclean.toml", "exclude_type = []\n")
    result = runner.invoke(run, ["check", str(path)])
    assert result.exit_code == 2
    assert "unknown key 'exclude_type'" in result.stderr
    assert "did you mean 'exclude-types'?" in result.stderr


def test_invalid_configuration_override(tmp_path: Path, runner: CliRunner) -> None:
    """Test that an invalid --config file is reported once."""
    path = _write(tmp_path, "a.bib", CLEAN)
    other = _write(tmp_path, "b.bib", CLEAN)
    config = _write(tmp_path, "custom.toml", "indent = 0\n")
    result = runner.invoke(run, ["check", "-c", str(config), str(path), str(other)])
    assert result.exit_code == 2
    assert result.stderr.count("error:") == 1
    assert "must be a positive integer" in result.stderr


def test_crlf_and_bom_are_rewritten(tmp_path: Path, runner: CliRunner) -> None:
    """Test that a file with CRLF endings and a BOM is rewritten without them."""
    path = tmp_path / "a.bib"
    path.write_bytes("﻿@misc{k,\r\n  title = {A}\r\n}\r\n".encode())
    result = runner.invoke(run, ["check", "--isolated", str(path)])
    assert result.exit_code == 1
    assert "file is not formatted" in result.stdout
    assert runner.invoke(run, ["fix", "--isolated", str(path)]).exit_code == 1
    assert path.read_bytes() == CLEAN.encode("utf-8")


@pytest.mark.parametrize("no_color", ["", "1"])
def test_output_is_plain_without_a_terminal(
    tmp_path: Path, runner: CliRunner, monkeypatch: pytest.MonkeyPatch, no_color: str
) -> None:
    """Test that the output carries no escape code when stdout is not a terminal."""
    monkeypatch.setenv("NO_COLOR", no_color)
    path = _write(tmp_path, "a.bib", DIRTY)
    result = runner.invoke(run, ["check", "--isolated", str(path)])
    assert "\x1b[" not in result.stdout
    assert result.stdout.endswith("Found 1 violation (1 fixable).\n")
