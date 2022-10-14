from pathlib import Path

from bibclean.commands.bibclean_check import _run


def test_run():
    """Test the exit code returned by _run."""
    directory = Path(__file__).parent / "data"

    # already valid
    exit_code = _run(directory / "zotero-clean.bib", None)
    assert exit_code == 0

    # in-existant config file
    exit_code = _run(directory / "zotero-clean.bib", config="101.toml")
    assert exit_code == 2

    # invalid
    exit_code = _run(directory / "zotero-articles.bib", None)
    assert exit_code == 1
    exit_code = _run(directory / "zotero-duplicates.bib", None)
    assert exit_code == 1

    # invalid but with excluded elements, thus valid
    exit_code = _run(
        directory / "zotero-duplicates.bib",
        str(directory / "zotero-duplicates.toml"),
    )
    assert exit_code == 0
