from configparser import ConfigParser
from pathlib import Path
from typing import Dict, Set


def _load_default_config() -> Dict[str, Set[str]]:
    """Load the default config from 'default.ini'."""
    config = ConfigParser()
    config.optionxform = str
    config.read(Path(__file__).parent / "default.ini")

    required_fields = dict()
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

        req = [elt for elt in req.split("\n") if len(elt) != 0]
        if len(req) != len(set(req)):  # sanity-check
            raise ValueError(
                "'.ini' default file is invalid. Some fields are present "
                "multiple times for the same entry type. Please contact the "
                "developers on GitHub."
            )
        required_fields[key] = set(req)

    return required_fields
