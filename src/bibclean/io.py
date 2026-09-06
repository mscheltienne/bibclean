from __future__ import annotations

from pathlib import Path

from bibtexparser import dump, load
from bibtexparser.bibdatabase import BibDatabase

from bibclean.utils._checks import check_type
from bibclean.utils.logs import logger


def load_bib(file: str | Path, encoding: str = "utf-8") -> BibDatabase:
    """Load a BibTex file.

    Parameters
    ----------
    file : str | Path
        Path to the ``.bib`` file to load.
    encoding : str
        Encoding used to read the file. The provided encoding is forwarded to
        :func:`open`.

    Returns
    -------
    bib_database : ``BibDatabase``
        BibTex database loaded.
    """
    check_type(file, (str, Path), "file")
    file = Path(file) if isinstance(file, str) else file
    if file.suffix != ".bib":
        raise OSError(
            f"The provided file extension is not '.bib'. '{file.suffix}' is invalid."
        )
    if not file.exists():
        raise OSError("The provided file does not exist.")

    logger.info("Loading file %s", file)
    with open(file, encoding=encoding) as bibtex_file:
        bib_database = load(bibtex_file)
    return bib_database


def save_bib(
    bib_database: BibDatabase,
    file: str | Path,
    encoding: str = "utf-8",
    overwrite: bool = False,
) -> None:
    """Save a BibTex file.

    Parameters
    ----------
    bib_database : ``BibDatabase``
        BibTex database to save.
    file : str | Path
        Path to the ``.bib`` file to save.
    encoding : str
        Encoding used to write the file. The provided encoding is forwarded to
        :func:`open`.
    overwrite : bool
        If True, an existing file will be overwritten.
    """
    check_type(bib_database, (BibDatabase,), "bib_database")
    check_type(file, (str, Path), "file")
    file = Path(file) if isinstance(file, str) else file
    if file.suffix != ".bib":
        raise OSError(
            f"The provided file extension is not '.bib'. '{file.suffix}' is invalid."
        )
    check_type(overwrite, (bool,), "overwrite")
    if file.exists() and not overwrite:
        raise OSError(
            "The provided file already exist. Set overwrite to True if you "
            "want to overwrite the file."
        )

    logger.info("Saving to file %s", file)
    with open(file, "w", encoding=encoding) as bibtex_file:
        dump(bib_database, bibtex_file)
