from pathlib import Path
from typing import Dict, List, Set, Tuple, Union

from toml import load

from ..utils._docs import fill_doc


@fill_doc
def load_config(
    file: Union[str, Path]
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], List[str]]:
    """Load the bibclean configuration form a TOML file.

    Parameters
    ----------
    file : str | Path
        Path to the TOML file containing the ``'tool.bibclean.entry_type'``
        sections.

    Returns
    -------
    %(required_fields)s
    %(keep_fields)s
    %(exclude)s
    """
    config = load(file)
    if "tool" not in config:
        raise RuntimeError(
            "TOML file is invalid. The section 'tool' is missing."
        )

    if "bibclean" not in config["tool"]:
        raise RuntimeError(
            "TOML file is invalid. The section(s) 'tool.bibclean' are missing."
        )

    config = config["tool"]["bibclean"]

    required_fields = dict()
    keep_fields = dict()
    exclude = list()
    for key in config:

        if key == "exclude":
            exclude = config[key]
            continue

        try:
            req = config[key]["required"]
        except KeyError:
            raise KeyError(
                "TOML file is invalid. The 'required' key is missing from "
                f"entry-type '{key}'."
            )

        try:
            keep = config[key]["keep"]
        except KeyError:
            raise KeyError(
                "'.toml' file is invalid. The 'keep' key is missing from "
                f"entry-type '{key}'."
            )

        if len(req) != len(set(req)) or len(keep) != len(set(keep)):
            raise ValueError(
                "TOML file is invalid. Some fields are present multiple "
                "times for the same entry type."
            )

        required_fields[key] = set(req)
        keep_fields[key] = set(keep)

    return required_fields, keep_fields, exclude


def _load_default_config() -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """Load the default config from 'default.toml'."""
    required_fields, keep_fields, _ = load_config(
        Path(__file__).parent / "default.toml"
    )
    return required_fields, keep_fields
