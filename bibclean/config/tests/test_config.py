import re
from pathlib import Path

import pytest

from bibclean.config import _load_default_config, load_config

directory = Path(__file__).parent / "data"


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
    req_def, keep_def = _load_default_config()

    # valid
    req, keep, exclude = load_config(directory / "valid.toml")
    assert len(req) == len(keep) == len(req_def) == len(keep_def)
    assert req["article"] == {"author", "journal", "title", "year"}
    assert req["book"] == {"author", "publisher", "title", "year"}
    assert keep["article"] == {"author", "journal", "title", "issn", "year"}
    assert keep["book"] == keep_def["book"]
    assert exclude == ["test"]

    # valid with minimal overwrite
    req, keep, exclude = load_config(directory / "valid-2.toml")
    assert len(req) == len(keep) == len(req_def) == len(keep_def)
    assert req["article"] == req_def["article"]
    assert req["book"] == req_def["book"]
    assert keep["article"] == {"author", "journal", "title", "issn", "year"}
    assert keep["book"] == keep_def["book"]
    assert exclude == ["test"]

    # valid-no-book
    req, keep, exclude = load_config(directory / "valid-no-book.toml")
    assert len(req) == len(keep) == 1
    assert req["article"] == {"author", "journal", "title", "year"}
    assert keep["article"] == {"author", "journal", "title", "issn", "year"}
    assert "book" not in req
    assert "book" not in keep
    assert exclude == ["test"]

    # valid-exclude-type
    req, keep, exclude = load_config(directory / "valid-exclude-type.toml")
    assert len(req) == len(keep) == len(req_def) == len(keep_def)
    assert req["article"] == {"author", "journal", "title", "year"}
    assert req["book"] == {"author", "publisher", "title", "year"}
    assert keep["article"] == {"author", "journal", "title", "issn", "year"}
    assert keep["book"] == keep_def["book"]
    assert len(exclude) == 0
    assert "test" not in req
    assert "test" not in keep


def test_load_invalid_config():
    """Test loading an invalid TOML configuration."""
    # missing section(s)
    with pytest.raises(
        RuntimeError,
        match="TOML file is invalid. The section 'tool' is missing.",
    ):
        load_config(directory / "invalid-missing-tool.toml")
    with pytest.raises(
        RuntimeError,
        match=re.escape("invalid. The section(s) 'tool.bibclean' are missing."),
    ):
        load_config(directory / "invalid-missing-section.toml")

    # invalid keys
    with pytest.raises(KeyError, match=re.escape("invalid. Unexpected ['author'] key")):
        load_config(directory / "invalid-keys-singular.toml")
    with pytest.raises(
        KeyError,
        match=re.escape("invalid. Unexpected ['author', 'year'] keys"),
    ):
        load_config(directory / "invalid-keys-plural.toml")

    # wrong format
    with pytest.raises(
        TypeError,
        match="excluded entries must be provided as cite-keys in str format",
    ):
        load_config(directory / "invalid-exclude.toml")
    with pytest.raises(
        TypeError, match="The excluded types must be provided in str format"
    ):
        load_config(directory / "invalid-exclude-type.toml")

    # duplicated fields
    with pytest.raises(
        ValueError, match="invalid. Some fields are present multiple times"
    ):
        load_config(directory / "invalid-duplicate-fields.toml")


def test_invalid_merge():
    """Test invalid merge when default configuration is absent."""
    with pytest.raises(
        RuntimeError,
        match="'tool.bibclean.test' does not have a 'required' default.",
    ):
        load_config(directory / "invalid-missing-req-def.toml")

    with pytest.raises(
        RuntimeError,
        match="'tool.bibclean.test' does not have a 'keep' default.",
    ):
        load_config(directory / "invalid-missing-keep-def.toml")
