from __future__ import annotations

import random
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import click
import pytest

from bibclean._commands._common import format_diagnostic
from bibclean._config import Config, default_config, load_config
from bibclean._engine import NOT_FORMATTED_MESSAGE, lint, process, unified_diff
from bibclean._parser import parse
from bibclean._rules import RULE_NAMES
from bibclean._rules._base import Context
from tests.helpers import assert_converged

ASSETS = Path(__file__).parents[1] / "assets"
CASES = sorted(
    path.stem for path in ASSETS.glob("*.bib") if not path.name.endswith(".fixed.bib")
)
CLEAN = b"@misc{k,\n  title = {A}\n}\n"
# Pieces of BibTeX glued at random by the property test.
ATOMS = (
    "@article{", "@string{", "@preamble{", "@comment{", "@misc(", "k", ",", " ", "\n",
    "=", "{", "}", '"', "#", "%", "\\", "a", "1", "title", "doi", "month = jan", "(",
    ")", "\t", "@", "x = {y}", "\r\n", "\n\n\n", " \n \n", "@string{s = {S}}",
    "@preamble{s # {x}}", "doi = {https://doi.org/10.1/x}", "pages = {1-2}",
    "\N{BYTE ORDER MARK}", "me@example.org", "% @misc{x, a = {1}}", "@comment{ a { b ",
)  # fmt: skip

_HEAVY = ("numpy", "psutil", "packaging", "bibtexparser", "click")
_STARTUP = (
    "import sys\n"
    "import bibclean._engine\n"
    "import bibclean._config\n"
    "heavy = [name for name in {names!r} if name in sys.modules]\n"
    "raise SystemExit('imported ' + ', '.join(heavy) if heavy else 0)\n"
)


def _config(case: str) -> Config:
    toml = ASSETS / f"{case}.toml"
    if toml.exists():
        return load_config(toml, known_rules=RULE_NAMES)
    return default_config()


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
    data = (ASSETS / f"{case}.bib").read_bytes()
    fixed = ASSETS / f"{case}.fixed.bib"
    expected = fixed.read_bytes() if fixed.exists() else data
    report = process(data, "utf-8", _config(case))
    assert report.output == (None if expected == data else expected)
    lines = (ASSETS / f"{case}.check.txt").read_text(encoding="utf-8").splitlines()
    rendered = [
        click.unstyle(format_diagnostic(f"{case}.bib", item))
        for item in report.diagnostics
    ]
    assert rendered == lines[:-1]
    assert_converged(data, _config(case))


@pytest.mark.parametrize("case", CASES)
def test_golden_on_the_fixed_file(case: str) -> None:
    """Test that a canonical file only keeps the unfixable findings of its case."""
    fixed = ASSETS / f"{case}.fixed.bib"
    data = (fixed if fixed.exists() else ASSETS / f"{case}.bib").read_bytes()
    report = process(data, "utf-8", _config(case))
    assert report.output is None
    assert all(not item.fixable for item in report.diagnostics)
    expected = [
        line.split(": ", 1)[1].split(" ", 1)[0]
        for line in (ASSETS / f"{case}.check.txt").read_text("utf-8").splitlines()[:-1]
        if not line.endswith(" [*]")
    ]
    assert [item.rule for item in report.diagnostics] == expected


def test_fix_converges_on_random_input() -> None:
    """Test that fixing random BibTeX-like text converges in one pass."""
    rng = random.Random(0)
    base = default_config()
    alt = replace(
        base,
        format=replace(
            base.format, align_values=True, trailing_comma=True, sort_fields=False
        ),
    )
    for _ in range(3000):
        text = "".join(rng.choice(ATOMS) for _ in range(rng.randint(1, 20)))
        assert_converged(text.encode("utf-8"), rng.choice((base, alt)))


@pytest.mark.parametrize(
    "source",
    [
        "@misc{a, title = {T}}\n\n@misc{A, title = {T}, file = {f}}\n",
        "@misc{a, doi = {10.1/x}, doi = {https://doi.org/10.1/x}}\n",
    ],
)
def test_fix_merges_values_identical_once_fixed(source: str) -> None:
    """Test that entries or fields only identical once fixed are merged in one fix."""
    report = process(source.encode(), "utf-8", default_config())
    assert report.output is not None
    assert report.output.count(b"@misc") == 1
    assert report.output.count(b"doi") <= 1
    assert_converged(source.encode(), default_config())


def test_not_formatted_finding() -> None:
    """Test the file-level finding, sorted after the positioned ones."""
    data = b"@misc{k, title = {1}, title = {1}}\n"
    report = process(data, "utf-8", default_config())
    assert report.diagnostics[-1].rule is None
    assert report.diagnostics[-1].message == NOT_FORMATTED_MESSAGE
    assert report.diagnostics[-1].fixable is True
    assert report.diagnostics[-1].position is None
    assert report.diagnostics[0].rule == "duplicate-field"


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_bom_is_removed(encoding: str) -> None:
    """Test that a byte order mark makes the file not canonical and is never written."""
    report = process(b"\xef\xbb\xbf" + CLEAN, encoding, default_config())
    assert report.output == CLEAN
    assert [item.message for item in report.diagnostics] == [NOT_FORMATTED_MESSAGE]
    assert process(CLEAN, encoding, default_config()).output is None


def test_crlf_is_not_formatted() -> None:
    """Test that carriage returns make the file not canonical."""
    report = process(CLEAN.replace(b"\n", b"\r\n"), "utf-8", default_config())
    assert report.output == CLEAN
    assert [item.message for item in report.diagnostics] == [NOT_FORMATTED_MESSAGE]


def test_syntax_error_is_never_fixed() -> None:
    """Test that a file with a syntax error is reported but never rewritten."""
    data = b"@Misc{k, Title = {A}, doi = {https://doi.org/10.1/x}}\n@misc{broken,\n"
    report = process(data, "utf-8", default_config())
    assert report.output is None
    assert [item.rule for item in report.diagnostics] == ["doi-prefix", "syntax-error"]
    assert not any(item.fixable for item in report.diagnostics)


def test_encoding() -> None:
    """Test that the content is decoded and the output encoded with the encoding."""
    data = "@Misc{k, Title = {é}}\n".encode("latin-1")
    report = process(data, "latin-1", default_config())
    assert report.output == "@misc{k,\n  title = {é}\n}\n".encode("latin-1")
    with pytest.raises(UnicodeDecodeError):
        process(data, "utf-8", default_config())


def test_lint_honours_ignore() -> None:
    """Test that an ignored rule never runs."""
    source = "@article{k, doi = {https://doi.org/10.1/x}}\n"
    base = default_config()
    ignored = replace(base, lint=replace(base.lint, ignore=frozenset({"doi-prefix"})))
    assert "doi-prefix" in [item.rule for item in lint(Context(parse(source), base))]
    assert "doi-prefix" not in [
        item.rule for item in lint(Context(parse(source), ignored))
    ]


def test_unified_diff() -> None:
    """Test the headers of the unified diff."""
    diff = unified_diff("doc/a.bib", "a\n", "b\n")
    assert diff.startswith("--- a/doc/a.bib\n+++ b/doc/a.bib\n")
    assert "-a\n" in diff
    assert unified_diff("a.bib", "a\n", "a\n") == ""


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
