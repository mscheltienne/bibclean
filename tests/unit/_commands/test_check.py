from pathlib import Path

from bibclean.commands.bibclean_check import ReturnCode, _run


def test_run():
    """Test the exit code returned by _run."""
    directory = Path(__file__).parent / "data"

    # already valid
    exit_code = _run(directory / "zotero-clean.bib", None)
    assert exit_code == ReturnCode.no_violations_found

    # in-existant config file
    exit_code = _run(directory / "zotero-clean.bib", config="101.toml")
    assert exit_code == ReturnCode.invalid_options

    # invalid
    exit_code = _run(directory / "zotero-articles.bib", None)
    assert exit_code == ReturnCode.violations_found
    exit_code = _run(directory / "zotero-duplicates.bib", None)
    assert exit_code == ReturnCode.violations_found_unfixable

    # invalid but with excluded elements, thus valid
    exit_code = _run(
        directory / "zotero-duplicates.bib",
        str(directory / "zotero-duplicates.toml"),
    )
    assert exit_code == ReturnCode.no_violations_found
