from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from bibclean._config import Config, default_config, load_config
from bibclean._diagnostics import format_diagnostic, sort_diagnostics, summary_check
from bibclean._engine import (
    NOT_FORMATTED_MESSAGE,
    ReadError,
    Report,
    Source,
    lint,
    normalize_newlines,
    process,
    read_source,
    unified_diff,
    write_source,
)
from bibclean._parser import parse
from bibclean._rules import RULE_NAMES
from bibclean._rules._base import Context, Finding, rule

if TYPE_CHECKING:
    pass

ASSETS = Path(__file__).parents[1] / "assets"
CASES = sorted(
    path.stem for path in ASSETS.glob("*.bib") if not path.name.endswith(".fixed.bib")
)

_HEAVY = ("numpy", "psutil", "packaging", "bibtexparser", "click")
_STARTUP = (
    "import sys\n"
    "import bibclean._engine\n"
    "import bibclean._config\n"
    "heavy = [name for name in {names!r} if name in sys.modules]\n"
    "raise SystemExit('imported ' + ', '.join(heavy) if heavy else 0)\n"
)


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def _config(case: str) -> Config:
    toml = ASSETS / f"{case}.toml"
    if toml.exists():
        return load_config(toml, known_rules=RULE_NAMES)
    return default_config()


def _rendered(report: Report, path: str) -> str:
    lines = [
        format_diagnostic(item, color=False)
        for item in sort_diagnostics(report.diagnostics, [path])
    ]
    if lines:
        lines.append(summary_check(report.diagnostics))
    return "".join(line + "\n" for line in lines)


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
def test_golden(case: str) -> None:
    """Test that the pipeline reproduces the output and the report of a case."""
    path = f"{case}.bib"
    text = _read(ASSETS / path)
    report = process(path, Source(text=text, had_bom=False), _config(case))
    fixed = ASSETS / f"{case}.fixed.bib"
    expected_output = _read(fixed) if fixed.exists() else text
    assert report.output == expected_output
    assert _rendered(report, path) == _read(ASSETS / f"{case}.check.txt")
    assert report.changed == (expected_output != text)


@pytest.mark.parametrize("case", CASES)
def test_golden_on_the_fixed_file(case: str) -> None:
    """Test that a canonical file only keeps the unfixable findings of its case."""
    fixed = ASSETS / f"{case}.fixed.bib"
    path = fixed.name if fixed.exists() else f"{case}.bib"
    text = _read(ASSETS / path)
    report = process(path, Source(text=text, had_bom=False), _config(case))
    assert report.output == text
    assert report.changed is False
    assert all(not item.fixable for item in report.diagnostics)
    expected = [
        line.split(": ", 1)[1].split(" ", 1)[0]
        for line in _read(ASSETS / f"{case}.check.txt").splitlines()[:-1]
        if not line.endswith(" [*]")
    ]
    assert [item.rule for item in report.diagnostics] == expected


def test_not_formatted_finding() -> None:
    """Test the file-level finding and its message."""
    report = process(
        "t.bib", Source(text="@misc{k, a = {1}}\n", had_bom=False), default_config()
    )
    assert report.diagnostics[-1].rule is None
    assert report.diagnostics[-1].message == NOT_FORMATTED_MESSAGE
    assert report.diagnostics[-1].fixable is True
    assert report.diagnostics[-1].line is None


def test_bom_is_not_formatted() -> None:
    """Test that a byte order mark makes the file not canonical."""
    text = "@misc{k,\n  a = {1}\n}\n"
    report = process("t.bib", Source(text=text, had_bom=True), default_config())
    assert report.changed is True
    assert report.diagnostics[-1].message == NOT_FORMATTED_MESSAGE


def test_crlf_is_not_formatted() -> None:
    """Test that carriage returns make the file not canonical."""
    text = "@misc{k,\r\n  title = {1}\r\n}\r\n"
    report = process("t.bib", Source(text=text, had_bom=False), default_config())
    assert report.output == "@misc{k,\n  title = {1}\n}\n"
    assert report.changed is True


@pytest.mark.parametrize(
    ("text", "expected"),
    [("a\r\nb", "a\nb"), ("a\rb", "a\nb"), ("a\nb", "a\nb")],
)
def test_normalize_newlines(text: str, expected: str) -> None:
    """Test the normalisation of the three line ending conventions."""
    assert normalize_newlines(text) == expected


def test_read_source(tmp_path: Path) -> None:
    """Test reading a plain file."""
    path = tmp_path / "a.bib"
    path.write_bytes(b"@misc{k}\r\n")
    source = read_source(path, "utf-8")
    assert source.text == "@misc{k}\r\n"
    assert source.had_bom is False


def test_read_source_bom(tmp_path: Path) -> None:
    """Test that a byte order mark is stripped and reported."""
    path = tmp_path / "a.bib"
    path.write_bytes("﻿@misc{k}\n".encode())
    source = read_source(path, "utf-8")
    assert source.text == "@misc{k}\n"
    assert source.had_bom is True


def test_read_source_missing(tmp_path: Path) -> None:
    """Test the message of an unreadable file."""
    with pytest.raises(ReadError, match="cannot read file:"):
        read_source(tmp_path / "absent.bib", "utf-8")


def test_read_source_bad_encoding(tmp_path: Path) -> None:
    """Test the message of a decoding failure."""
    path = tmp_path / "a.bib"
    path.write_bytes(b"@misc{k, a = {\xe9}}\n")
    with pytest.raises(
        ReadError, match=r"cannot decode file with encoding 'utf-8': .* at byte 14"
    ):
        read_source(path, "utf-8")


def test_write_source(tmp_path: Path) -> None:
    """Test that the output always uses line feeds."""
    path = tmp_path / "a.bib"
    write_source(path, "@misc{k,\n  a = {1}\n}\n", "utf-8")
    assert path.read_bytes() == b"@misc{k,\n  a = {1}\n}\n"


def test_write_source_encoding(tmp_path: Path) -> None:
    """Test that the encoding is honoured."""
    path = tmp_path / "a.bib"
    write_source(path, "@misc{k, a = {é}}\n", "latin-1")
    assert read_source(path, "latin-1").text == "@misc{k, a = {é}}\n"


def test_lint_honours_ignore() -> None:
    """Test that an ignored rule never runs."""
    from dataclasses import replace

    source = "@article{k, doi = {https://doi.org/10.1/x}}\n"
    base = default_config()
    ignored = replace(base, lint=replace(base.lint, ignore=frozenset({"doi-prefix"})))
    assert "doi-prefix" in [
        item.rule for item in lint(Context("t.bib", parse(source), base))
    ]
    assert "doi-prefix" not in [
        item.rule for item in lint(Context("t.bib", parse(source), ignored))
    ]


def test_unified_diff() -> None:
    """Test the headers of the unified diff."""
    diff = unified_diff("doc/a.bib", "a\n", "b\n")
    assert diff.startswith("--- a/doc/a.bib\n+++ b/doc/a.bib\n")
    assert "-a\n" in diff
    assert unified_diff("a.bib", "a\n", "a\n") == ""


def test_convergence_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a rule reporting a fix that changes nothing is an internal error."""

    @rule(name="never-done", fixable="yes", scope="entry")
    def never_done(ctx: Context) -> list[Finding]:
        """Report a fix that never happens.

        .. code-block:: bibtex

           @misc{k}

        pybtex: nothing, this rule only exists to exercise the guard.
        """
        return [Finding(ctx.entries()[0].start, "boom", True)]

    monkeypatch.setattr("bibclean._engine.RULES", (never_done,))
    with pytest.raises(RuntimeError, match="fixes did not converge"):
        process(
            "t.bib",
            Source(text="@misc{k,\n  a = {1}\n}\n", had_bom=False),
            default_config(),
        )


def test_heavy_modules_not_imported() -> None:
    """Test that the engine imports nothing outside of the standard library."""
    code = _STARTUP.format(names=_HEAVY)
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
