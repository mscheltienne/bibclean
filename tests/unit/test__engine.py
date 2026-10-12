from __future__ import annotations

import random
from dataclasses import replace

import pytest

from bibclean._config import default_config
from bibclean._engine import NOT_FORMATTED_MESSAGE, process, unified_diff
from tests.helpers import assert_converged

CLEAN = b"@misc{k,\n  title = {A}\n}\n"
# Pieces of BibTeX glued at random by the property test.
ATOMS = (
    "@article{", "@string{", "@preamble{", "@comment{", "@misc(", "k", ",", " ", "\n",
    "=", "{", "}", '"', "#", "%", "\\", "a", "1", "title", "doi", "month = jan", "(",
    ")", "\t", "@", "x = {y}", "\r\n", "\n\n\n", " \n \n", "@string{s = {S}}",
    "@preamble{s # {x}}", "doi = {https://doi.org/10.1/x}", "pages = {1-2}",
    "\N{BYTE ORDER MARK}", "me@example.org", "% @misc{x, a = {1}}", "@comment{ a { b ",
)  # fmt: skip


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
        "@misc{a, title={A}} @misc{b, title={B}}\n",
        "@comment{x}@string{s={S}}\n@misc{k, title = s}\n",
    ],
)
def test_fix_splits_blocks_on_one_line(source: str) -> None:
    """Test that blocks sharing a line are split in one fix."""
    assert process(source.encode(), "utf-8", default_config()).output is not None
    assert_converged(source.encode(), default_config())


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


def test_unified_diff_is_a_valid_patch() -> None:
    """Test the marker of a missing final newline and the header of an absolute path."""
    assert unified_diff("/abs/a.bib", "x", "y\n") == (
        "--- a/abs/a.bib\n+++ b/abs/a.bib\n@@ -1 +1 @@\n"
        "-x\n\\ No newline at end of file\n+y\n"
    )


def test_crlf_is_not_formatted() -> None:
    """Test that carriage returns make the file not canonical."""
    report = process(CLEAN.replace(b"\n", b"\r\n"), "utf-8", default_config())
    assert report.output == CLEAN
    assert [item.message for item in report.diagnostics] == [NOT_FORMATTED_MESSAGE]
