"""Exercise bibclean on an external corpus of real-world and parser test files.

The corpus is downloaded at test time by the ``corpus`` fixture into the pytest cache,
from the raw URLs pinned to a commit in ``tests/assets/corpus.json``, which maps each
base URL to the license of the repository and the SHA-256 digest of every file. A file
that cannot be downloaded or does not match its digest is skipped. It gathers the test
files of pybtex, bibtexparser, biber, btparse, BibTool, typst/biblatex, bibtex-tidy,
citation-js, retorquere/bibtex-parser and nickng/bibtex, and the bibliographies of the
documentation of scientific Python projects. To refresh it, point a base URL at a new
commit and recompute the digests of its files, e.g. with ``sha256sum``.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

import pybtex.errors
import pytest
from pybtex.database.input.bibtex import Parser

from bibclean._config import FormatOptions, default_config
from bibclean._engine import process
from bibclean._formatter import format_blocks
from bibclean._model import Malformed
from bibclean._parser import parse
from tests.helpers import assert_converged, corpus_manifest

if TYPE_CHECKING:
    from pathlib import Path

NAMES = sorted(corpus_manifest())
pybtex.errors.set_strict_mode(True)


def _read(corpus: dict[str, Path | None], name: str) -> tuple[bytes, str]:
    """Read one corpus file, skipping the test when it is not available.

    Parameters
    ----------
    corpus : dict
        The corpus fixture.
    name : str
        Name of the file in the corpus.

    Returns
    -------
    data : bytes
        Content of the file.
    text : str
        Decoded content, without byte order mark.
    """
    if corpus[name] is None:
        pytest.skip("file not downloaded")
    data = corpus[name].read_bytes()
    try:
        return data, data.decode("utf-8").removeprefix("\N{BYTE ORDER MARK}")
    except UnicodeDecodeError:
        pytest.skip("file not encoded in UTF-8")


def _pybtex(text: str) -> tuple[dict[str, tuple[str, dict[str, str]]], list[str]]:
    """Read a text with pybtex in strict mode.

    Parameters
    ----------
    text : str
        BibTeX source.

    Returns
    -------
    entries : dict
        Maps every case-folded cite key to its case-folded type and its fields, the
        persons included, with whitespace-normalised values.
    preambles : list of str
        Whitespace-normalised preambles.
    """
    data = Parser("utf-8").parse_stream(io.StringIO(text))
    entries = {}
    for key, entry in data.entries.items():
        fields = {k.lower(): " ".join(str(v).split()) for k, v in entry.fields.items()}
        for role, persons in entry.persons.items():
            fields[role.lower()] = " and ".join(str(person) for person in persons)
        entries[key.lower()] = (entry.type.lower(), fields)
    return entries, [" ".join(preamble.split()) for preamble in data.preamble_list]


@pytest.mark.parametrize("name", NAMES)
def test_corpus(name: str, corpus: dict[str, Path | None]) -> None:
    """Test that a corpus file round-trips and that fixing it converges."""
    data, text = _read(corpus, name)
    assert "".join(block.raw for block in parse(text)) == text
    assert_converged(data, default_config())


@pytest.mark.parametrize("name", NAMES)
def test_corpus_pybtex(name: str, corpus: dict[str, Path | None]) -> None:
    """Test that formatting and fixing a corpus file keep it readable by pybtex.

    The formatted file reads the same as the original in pybtex, when pybtex accepts the
    original. The fixed file is accepted by pybtex when it holds no violation.
    """
    data, text = _read(corpus, name)
    blocks = parse(text.replace("\r\n", "\n").replace("\r", "\n"))
    checked = False
    try:
        before = _pybtex(text)
    except Exception:  # pybtex rejects the original, nothing to compare to
        pass
    else:
        if not any(isinstance(block, Malformed) for block in blocks):
            assert _pybtex(format_blocks(blocks, FormatOptions())) == before
            checked = True
    config = default_config()
    report = process(data, "utf-8", config)
    fixed = data if report.output is None else report.output
    if not process(fixed, "utf-8", config).diagnostics:
        _pybtex(fixed.decode("utf-8"))
        checked = True
    if not checked:
        pytest.skip("pybtex rejects the file and fix leaves violations")
