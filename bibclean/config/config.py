from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Set, Tuple


def _load_default_config() -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """Load the default config from 'default.ini'."""
    config = ConfigParser()
    config.optionxform = str
    config.read(Path(__file__).parent / "default.ini")

    required_fields = dict()
    keep_fields = dict()
    for key in config.keys():
        if key == "DEFAULT":
            continue

        try:
            req = config[key]["required"]
        except KeyError:  # sanity-check
            raise KeyError(
                "'.ini' default file is invalid. The 'required' key is "
                "missing. Please contact the developers on GitHub."
            )

        try:
            keep = config[key]["keep"]
        except KeyError:  # sanity-check
            raise KeyError(
                "'.ini' default file is invalid. The 'keep' key is "
                "missing. Please contact the developers on GitHub."
            )

        req = [elt for elt in req.split("\n") if len(elt) != 0]
        keep = [elt for elt in keep.split("\n") if len(elt) != 0]
        if len(req) != len(set(req)) or len(keep) != len(set(keep)):
            raise ValueError(
                "'.ini' default file is invalid. Some fields are present "
                "multiple times for the same entry type. Please contact the "
                "developers on GitHub."
            )

        required_fields[key] = set(req)
        keep_fields[key] = set(keep)

    return required_fields, keep_fields
