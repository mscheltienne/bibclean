from pathlib import Path
from typing import Dict, List, Set, Tuple, Union

from toml import load

from ..utils._docs import fill_doc


@fill_doc
def load_config(
    file: Union[str, Path]
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], List[str]]:
    """Load the ``bibclean`` configuration form a TOML file.

    The loaded configuration is merged with the
    :ref:`default TOML configuration <configuration:default>`, overwriting
    the defaults with the provided configuration.

    Parameters
    ----------
    file : str | Path
        Path to the TOML file containing the ``tool.bibclean`` and
        ``'tool.bibclean.entry_type'`` sections.

    Returns
    -------
    %(required_fields)s
    %(keep_fields)s
    %(exclude)s
    """
    required_fields_def, keep_fields_def = _load_default_config()
    required_fields, keep_fields, exclude, exclude_type = _load_config(file)

    # merge both
    for key, value in required_fields_def.items():
        if key not in required_fields:
            required_fields[key] = required_fields_def[key]
    for key, value in keep_fields_def.items():
        if key not in keep_fields:
            keep_fields[key] = keep_fields_def[key]

    for key, value in required_fields.items():
        if len(value) == 0 and key in required_fields_def:  # absent from TOML
            required_fields[key] = required_fields_def[key]
        elif len(value) == 0 and key not in required_fields_def:
            raise RuntimeError(
                f"The section 'tool.bibclean.{key}' does not have a "
                "'required' default. Please provide the required fields in "
                "your configuration. You can propose a default by creating "
                "an issue on GitHub."
            )
    for key, value in keep_fields.items():
        if len(value) == 0 and key in keep_fields_def:  # absent from TOML
            keep_fields[key] = keep_fields_def[key]
        elif len(value) == 0 and key not in keep_fields_def:
            raise RuntimeError(
                f"The section 'tool.bibclean.{key}' does not have a "
                "'keep' default. Please provide the fields to keep in "
                "your configuration. You can propose a default by creating "
                "an issue on GitHub."
            )

    # exclude by type
    try:
        for exc_type in exclude_type:
            del required_fields[exc_type]
            del keep_fields[exc_type]
    except KeyError:
        pass

    return required_fields, keep_fields, exclude


def _load_config(
    file: Union[str, Path]
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], List[str], List[str]]:
    """Load a configuration from a TOML file."""
    config = load(file)
    if "tool" not in config:
        raise RuntimeError("TOML file is invalid. The section 'tool' is missing.")

    if "bibclean" not in config["tool"]:
        raise RuntimeError(
            "TOML file is invalid. The section(s) 'tool.bibclean' are missing."
        )

    config = config["tool"]["bibclean"]

    required_fields = dict()
    keep_fields = dict()
    exclude = list()
    exclude_type = list()
    for key in config:
        if key == "exclude":
            exclude = config[key]
            for exc in exclude:
                if not isinstance(exc, str):
                    raise TypeError(
                        "TOML file is invalid. The excluded entries must be "
                        "provided as cite-keys in str format. e.g. "
                        "exclude = ['example', 'example_2']."
                    )
            continue
        elif key == "exclude_type":
            exclude_type = config[key]
            for exc in exclude_type:
                if not isinstance(exc, str):
                    raise TypeError(
                        "TOML file is invalid. The excluded types must be "
                        "provided in str format. e.g. "
                        "exclude_type = ['article', 'book']."
                    )
            continue

        # check that TOML is valid
        invalid = sorted(set(config[key].keys()) - {"keep", "required"})
        if len(invalid) != 0:
            plural = "" if len(invalid) == 1 else "s"
            raise KeyError(
                f"TOML file is invalid. Unexpected {invalid} key{plural} in "
                f"section 'bibclean.{key}'."
            )

        try:
            req = config[key]["required"]
        except KeyError:
            req = set()
        try:
            keep = config[key]["keep"]
        except KeyError:
            keep = set()

        if len(req) != len(set(req)) or len(keep) != len(set(keep)):
            raise ValueError(
                "TOML file is invalid. Some fields are present multiple "
                f"times for the same key in section 'bibclean.{key}'."
            )

        required_fields[key] = set(req)
        keep_fields[key] = set(keep)

    return required_fields, keep_fields, exclude, exclude_type


def _load_default_config() -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """Load the default config from 'default.toml'."""
    required_fields, keep_fields, _, _ = _load_config(
        Path(__file__).parent / "default.toml"
    )
    return required_fields, keep_fields
