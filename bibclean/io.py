from pathlib import Path
from typing import Union

from bibtexparser import load
from bibtexparser.bibdatabase import BibDatabase

from .utils._checks import _check_type


def load_bib(file: Union[str, Path], encoding: str = "utf-8") -> BibDatabase:
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
    bib_database : BibDatabase
        BibTex database.
    """
    _check_type(file, (str, Path), "file")
    file = Path(file) if isinstance(file, str) else file
    if file.suffix != ".bib":
        raise ValueError("The provided file extensioon is not '.bib'.")
    if not file.exists():
        raise ValueError("The provided file does not exist.")

    with open(file, encoding=encoding) as bibtex_file:
        bib_database = load(bibtex_file)
    return bib_database