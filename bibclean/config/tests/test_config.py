import re
from pathlib import Path

import pytest

from bibclean.config import _load_default_config, load_config


def _check_config(required_fields, keep_fields):
    """Check the returned config types."""
    for fields in (required_fields, keep_fields):
        assert isinstance(fields, dict)
        assert all(isinstance(elt, str) for elt in fields.keys())
        for field in fields.values():
            assert isinstance(field, set)
            assert all(isinstance(elt, str) for elt in field)


def test_load_default_config():
    """Test loading of the default configuration."""
    required_fields, keep_fields = _load_default_config()
    _check_config(required_fields, keep_fields)


def test_load_config():
    """Test loading of a TOML configuration."""
    directory = Path(__file__).parent / "data"

    required_fields, keep_fields, exclude = load_config(
        directory / "valid.toml"
    )
    _check_config(required_fields, keep_fields)
    assert isinstance(exclude, list)
    assert len(exclude) == 0
    required_fields, keep_fields, exclude = load_config(
        directory / "valid-exclusion.toml"
    )
    _check_config(required_fields, keep_fields)
    assert exclude == ["test", "101"]

    with pytest.raises(
        RuntimeError,
        match="TOML file is invalid. The section 'tool' is missing.",
    ):
        load_config(directory / "tool-missing.toml")

    with pytest.raises(
        RuntimeError,
        match=re.escape("file is invalid. The section(s) 'tool.bibclean'"),
    ):
        load_config(directory / "bibclean-missing.toml")

    with pytest.raises(
        KeyError, match="TOML file is invalid. The 'required' key is missing"
    ):
        load_config(directory / "required-missing.toml")

    with pytest.raises(
        KeyError, match="'.toml' file is invalid. The 'keep' key is missing"
    ):
        load_config(directory / "keep-missing.toml")

    with pytest.raises(
        ValueError,
        match="TOML file is invalid. Some fields are present multiple times",
    ):
        load_config(directory / "duplicates.toml")
