"""Exercise bibclean on an external corpus of real-world and parser test files.

The corpus is downloaded at test time by the ``corpus`` fixture into the ``corpus``
folder of the user cache directory of ``bibclean`` (``platformdirs.user_cache_dir``),
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

import pytest
from pybtex.database.input.bibtex import Parser

from bibclean._config import default_config
from bibclean._engine import decode
from bibclean._formatter import format_blocks
from bibclean._model import Malformed
from bibclean._parser import parse
from tests.helpers import assert_converged, corpus_manifest

if TYPE_CHECKING:
    from pathlib import Path

NAMES = sorted(corpus_manifest())


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
    """Test a corpus file: round-trip, convergence of fix and readability by pybtex.

    The file round-trips through the parser and fixing it converges. The formatted file
    reads the same as the original in pybtex, when pybtex accepts the original. The
    fixed file is accepted by pybtex when it holds no violation.
    """
    if corpus[name] is None:
        pytest.skip("file not downloaded")
    data = corpus[name].read_bytes()
    try:
        text = decode(data, "utf-8")
    except UnicodeDecodeError:
        pytest.skip("file not encoded in UTF-8")
    blocks = parse(text)
    assert "".join(block.raw for block in blocks) == text
    config = default_config()
    fixed, again = assert_converged(data, config)
    try:
        before = _pybtex(text)
    except Exception:  # pybtex rejects the original, nothing to compare to
        pass
    else:
        if not any(isinstance(block, Malformed) for block in blocks):
            assert _pybtex(format_blocks(blocks, config.format)) == before
    if not again.diagnostics:
        _pybtex(fixed.decode("utf-8"))
