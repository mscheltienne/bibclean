from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote

from bibclean._engine import process

if TYPE_CHECKING:
    from bibclean._config import Config

ASSETS = Path(__file__).parent / "assets"


def assert_converged(data: bytes, config: Config) -> None:
    """Check that one fix leaves a fixed point with nothing left to fix.

    Parameters
    ----------
    data : bytes
        Content of a UTF-8 file. A file with a syntax error is exempt, as it is never
        rewritten.
    config : Config
        Configuration used by both passes.
    """
    report = process(data, "utf-8", config)
    if any(item.rule == "syntax-error" for item in report.diagnostics):
        return
    fixed = data if report.output is None else report.output
    again = process(fixed, "utf-8", config)
    assert again.output is None, data
    assert not any(item.fixable for item in again.diagnostics), data
    assert not any(item.rule == "syntax-error" for item in again.diagnostics), data


def corpus_manifest() -> dict[str, tuple[str, str]]:
    """Read the manifest of the external corpus.

    Returns
    -------
    dict
        Maps the name ``<owner>/<repo>/<path>`` of every file to its download URL
        and its SHA-256 digest.
    """
    manifest = json.loads((ASSETS / "corpus.json").read_text(encoding="utf-8"))
    return {
        "/".join(base.split("/")[3:5]) + "/" + unquote(path): (base + path, digest)
        for base, group in manifest.items()
        for path, digest in group["files"].items()
    }
