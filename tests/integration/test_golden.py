from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from bibclean._commands.main import run
from bibclean._config import default_config, load_config
from bibclean._rules import RULE_NAMES
from tests.helpers import ASSETS, assert_converged

if TYPE_CHECKING:
    from click.testing import CliRunner

CASES = sorted(
    path.name.removesuffix(".check.txt") for path in ASSETS.glob("*.check.txt")
)


@pytest.fixture(params=CASES)
def case(
    request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> str:
    """Copy the files of one golden case into the working directory, return its name."""
    for path in ASSETS.glob(f"{request.param}.*"):
        shutil.copy(path, tmp_path)
    monkeypatch.chdir(tmp_path)
    return request.param


def _args(case: str) -> list[str]:
    """Build the configuration arguments of a case."""
    return (
        ["--config", f"{case}.toml"]
        if Path(f"{case}.toml").exists()
        else ["--isolated"]
    )


def _unfixable(case: str) -> list[str]:
    """Read the diagnostic lines of a case that ``fix`` cannot resolve."""
    lines = Path(f"{case}.check.txt").read_text(encoding="utf-8").splitlines()
    return [line for line in lines[:-1] if not line.endswith(" [*]")]


def _rules(lines: list[str]) -> list[str]:
    """Extract the rule name of each diagnostic line."""
    return [line.split(": ", 1)[1].split(" ", 1)[0] for line in lines]


def test_check(case: str, runner: CliRunner) -> None:
    """Test that 'check' reproduces the expected report of a case."""
    expected = Path(f"{case}.check.txt").read_text(encoding="utf-8")
    result = runner.invoke(
        run, ["check", *_args(case), f"{case}.bib"], catch_exceptions=False
    )
    assert result.stdout == expected
    assert result.stderr == ""
    assert result.exit_code == (1 if expected else 0)


def test_fix(case: str, runner: CliRunner) -> None:
    """Test that 'fix' writes the expected fixed point and reports what is left."""
    original = Path(f"{case}.bib").read_bytes()
    expected = Path(f"{case}.fixed.bib").read_bytes()
    unfixable = _unfixable(case)
    result = runner.invoke(
        run, ["fix", *_args(case), f"{case}.bib"], catch_exceptions=False
    )
    assert Path(f"{case}.bib").read_bytes() == expected
    assert result.stdout.splitlines()[:-1] == unfixable
    assert result.exit_code == (1 if expected != original or unfixable else 0)
    toml = ASSETS / f"{case}.toml"
    config = (
        load_config(toml, known_rules=RULE_NAMES) if toml.exists() else default_config()
    )
    assert_converged(original, config)


def test_check_on_the_fixed_file(case: str, runner: CliRunner) -> None:
    """Test that a canonical file only keeps the unfixable rules of its case."""
    expected = _rules(_unfixable(case))
    result = runner.invoke(
        run, ["check", *_args(case), f"{case}.fixed.bib"], catch_exceptions=False
    )
    got = _rules(result.stdout.splitlines()[:-1])
    assert got == expected
    assert result.exit_code == (1 if got else 0)
