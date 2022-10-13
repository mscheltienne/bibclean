from pathlib import Path
from typing import Union

from bibtexparser import dump, load
from bibtexparser.bibdatabase import BibDatabase

from .utils._checks import _check_type
from .utils._docs import fill_doc
from .utils._logs import logger


@fill_doc
def load_bib(file: Union[str, Path], encoding: str = "utf-8") -> BibDatabase:
    """Load a BibTex file.

    Parameters
    ----------
    file : str | Path
        Path to the ``.bib`` file to load.
    %(encoding)s

    Returns
    -------
    bib_database : BibDatabase
        BibTex database loaded.
    """
    _check_type(file, (str, Path), "file")
    file = Path(file) if isinstance(file, str) else file
    if file.suffix != ".bib":
        raise IOError(
            "The provided file extension is not '.bib'. "
            f"'{file.suffix}' is invalid."
        )
    if not file.exists():
        raise IOError("The provided file does not exist.")

    logger.info("Loading file %s", file)
    with open(file, "r", encoding=encoding) as bibtex_file:
        bib_database = load(bibtex_file)
    return bib_database


@fill_doc
def save_bib(
    bib_database: BibDatabase,
    file: Union[str, Path],
    encoding: str = "utf-8",
    overwrite: bool = False,
) -> None:
    """Save a BibTex file.

    Parameters
    ----------
    bib_database : BibDatabase
        BibTex database to save.
    file : str | Path
        Path to the ``.bib`` file to save.
    %(encoding)s
    overwrite : bool
        If True, an existing file will be overwritten.
    """
    _check_type(bib_database, (BibDatabase,), "bib_database")
    _check_type(file, (str, Path), "file")
    file = Path(file) if isinstance(file, str) else file
    if file.suffix != ".bib":
        raise IOError(
            "The provided file extension is not '.bib'. "
            f"'{file.suffix}' is invalid."
        )
    _check_type(overwrite, (bool,), "overwrite")
    if file.exists() and not overwrite:
        raise IOError(
            "The provided file already exist. Set overwrite to True if you "
            "want to overwrite the file."
        )

    logger.info("Saving to file %s", file)
    with open(file, "w", encoding=encoding) as bibtex_file:
        dump(bib_database, bibtex_file)
