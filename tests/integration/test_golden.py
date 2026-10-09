from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from bibclean._commands.main import run

if TYPE_CHECKING:
    from click.testing import CliRunner

ASSETS = Path(__file__).parents[1] / "assets"
CASES = sorted(
    path.stem for path in ASSETS.glob("*.bib") if not path.name.endswith(".fixed.bib")
)


def _args(case: str) -> list[str]:
    """Build the configuration arguments of a case."""
    if (ASSETS / f"{case}.toml").exists():
        return ["--config", f"{case}.toml"]
    return ["--isolated"]


def _check_lines(directory: Path, case: str) -> list[str]:
    """Read the expected output of ``check`` for a case."""
    return (directory / f"{case}.check.txt").read_text(encoding="utf-8").splitlines()


def _unfixable(lines: list[str]) -> list[str]:
    """Keep the diagnostic lines that ``fix`` cannot resolve."""
    return [line for line in lines[:-1] if not line.endswith(" [*]")]


def _rules(lines: list[str]) -> list[str]:
    """Extract the rule name of each diagnostic line."""
    return [line.split(": ", 1)[1].split(" ", 1)[0] for line in lines]


def test_cases_are_discovered() -> None:
    """Test that the golden corpus holds the expected cases."""
    assert CASES == [
        "blocks",
        "clean",
        "configured",
        "duplicates",
        "malformed",
        "pybtex-compat",
        "zotero-export",
    ]


@pytest.mark.parametrize("case", CASES)
def test_check(case: str, case_dir: Path, runner: CliRunner) -> None:
    """Test that 'check' reproduces the expected report of a case."""
    expected = (case_dir / f"{case}.check.txt").read_text(encoding="utf-8")
    result = runner.invoke(
        run, ["check", *_args(case), f"{case}.bib"], catch_exceptions=False
    )
    assert result.stdout == expected
    assert result.stderr == ""
    assert result.exit_code == (1 if expected else 0)


@pytest.mark.parametrize("case", CASES)
def test_fix(case: str, case_dir: Path, runner: CliRunner) -> None:
    """Test that 'fix' reproduces the expected file and reports what is left."""
    expected = (case_dir / f"{case}.fixed.bib").read_bytes()
    original = (case_dir / f"{case}.bib").read_bytes()
    unfixable = _unfixable(_check_lines(case_dir, case))
    result = runner.invoke(
        run, ["fix", *_args(case), f"{case}.bib"], catch_exceptions=False
    )
    assert (case_dir / f"{case}.bib").read_bytes() == expected
    assert result.stdout.splitlines()[:-1] == unfixable
    assert result.exit_code == (1 if expected != original or unfixable else 0)


@pytest.mark.parametrize("case", CASES)
def test_fix_is_idempotent(case: str, case_dir: Path, runner: CliRunner) -> None:
    """Test that a second 'fix' leaves the file alone."""
    expected = (case_dir / f"{case}.fixed.bib").read_bytes()
    unfixable = _unfixable(_check_lines(case_dir, case))
    runner.invoke(run, ["fix", *_args(case), f"{case}.bib"], catch_exceptions=False)
    result = runner.invoke(
        run, ["fix", *_args(case), f"{case}.bib"], catch_exceptions=False
    )
    assert (case_dir / f"{case}.bib").read_bytes() == expected
    assert _rules(result.stdout.splitlines()[:-1]) == _rules(unfixable)
    assert result.exit_code == (1 if unfixable else 0)
    assert "wrote 0 files" in result.stdout or result.stdout == ""


@pytest.mark.parametrize("case", CASES)
def test_check_on_the_fixed_file(case: str, case_dir: Path, runner: CliRunner) -> None:
    """Test that a canonical file only keeps the unfixable rules of its case."""
    expected = _rules(_unfixable(_check_lines(case_dir, case)))
    result = runner.invoke(
        run, ["check", *_args(case), f"{case}.fixed.bib"], catch_exceptions=False
    )
    got = _rules(result.stdout.splitlines()[:-1])
    assert got == expected
    assert result.exit_code == (1 if got else 0)
