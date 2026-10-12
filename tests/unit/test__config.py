from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import pytest

from bibclean._config import (
    ConfigError,
    default_config,
    find_config,
    load_config,
    parse_config,
)
from bibclean._defaults import TYPES

if TYPE_CHECKING:
    from pathlib import Path

RULES = ("doi-prefix", "duplicate-key", "url-with-doi")


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def test_default_config() -> None:
    """Test the shipped defaults."""
    config = default_config()
    assert config.source is None
    assert config.format.indent == 2
    assert config.format.align_values is False
    assert config.format.trailing_comma is False
    assert config.format.sort_entries is True
    assert config.format.sort_fields is True
    assert config.lint.ignore == frozenset()
    assert config.lint.exclude == frozenset()
    assert config.lint.exclude_types == frozenset()
    assert config.lint.month == "abbreviation"
    assert set(config.lint.types) == set(TYPES)
    assert config.lint.types["article"].required == TYPES["article"][0]
    assert "author" in config.lint.types["article"].keep


def test_parse_config_values() -> None:
    """Test that every known key reaches the right option."""
    config = parse_config(
        {
            "indent": "tab",
            "align-values": True,
            "trailing-comma": True,
            "sort-entries": False,
            "sort-fields": ["Year", "Author", "year"],
            "month": "number",
            "ignore": ["doi-prefix"],
            "exclude": ["Smith2020"],
            "exclude-types": ["Software"],
        },
        path=None,
        known_rules=RULES,
    )
    assert config.format.indent == "tab"
    assert config.format.align_values is True
    assert config.format.trailing_comma is True
    assert config.format.sort_entries is False
    assert config.format.sort_fields == ("year", "author", "year")
    assert config.lint.month == "number"
    assert config.lint.ignore == frozenset({"doi-prefix"})
    assert config.lint.exclude == frozenset({"Smith2020"})
    assert config.lint.exclude_types == frozenset({"software"})


@pytest.mark.parametrize(
    ("table", "message"),
    [
        (
            {"exclude_type": ["a"]},
            "unknown key 'exclude_type' in [tool.bibclean], "
            "did you mean 'exclude-types'?",
        ),
        ({"zzzzzzz": 1}, "unknown key 'zzzzzzz' in [tool.bibclean]"),
        (
            {"indent": True},
            "'indent' in [tool.bibclean] must be a positive integer or \"tab\", "
            "got True",
        ),
        (
            {"indent": 0},
            "'indent' in [tool.bibclean] must be a positive integer or \"tab\", got 0",
        ),
        (
            {"indent": "four"},
            "'indent' in [tool.bibclean] must be a positive integer or \"tab\", "
            "got 'four'",
        ),
        (
            {"align-values": 1},
            "'align-values' in [tool.bibclean] must be a boolean, got 1",
        ),
        (
            {"sort-fields": [1, 2]},
            "'sort-fields' in [tool.bibclean] must be a boolean or an array of "
            "strings, got [1, 2]",
        ),
        (
            {"month": "preserve"},
            '\'month\' in [tool.bibclean] must be one of "abbreviation", "name", '
            "\"number\", got 'preserve'",
        ),
        (
            {"strip-fields": False},
            "unknown key 'strip-fields' in [tool.bibclean], "
            "did you mean 'sort-fields'?",
        ),
        (
            {"exclude": [1, 2]},
            "'exclude' in [tool.bibclean] must be an array of strings, got [1, 2]",
        ),
        (
            {"ignore": ["doi-prefixes"]},
            "unknown rule 'doi-prefixes' in 'ignore', did you mean 'doi-prefix'?",
        ),
        ({"ignore": ["zzzzzzz"]}, "unknown rule 'zzzzzzz' in 'ignore'"),
        (
            {"article": {"require": ["author"]}},
            "unknown key 'require' in [tool.bibclean.article], "
            "did you mean 'required'?",
        ),
        ({"article": {"zzzzzzz": ["a"]}}, "unknown key 'zzzzzzz' in "),
        (
            {"article": {"keep": "author"}},
            "'keep' in [tool.bibclean.article] must be an array of strings, "
            "got 'author'",
        ),
        (
            {"InProceeding": {"keep": ["doi"]}},
            "unknown entry type 'inproceeding' in [tool.bibclean.inproceeding], did "
            "you mean 'inproceedings'? (a new entry type must declare 'required')",
        ),
    ],
)
def test_validation_messages(table: dict[str, Any], message: str) -> None:
    """Test the exact text of every validation error."""
    with pytest.raises(ConfigError, match=re.escape(message)):
        parse_config(table, path=None, known_rules=RULES)


def test_validation_stops_at_the_first_problem() -> None:
    """Test that keys are validated in document order."""
    with pytest.raises(ConfigError, match=re.escape("'month' in")):
        parse_config({"month": "names", "indent": 0}, path=None, known_rules=RULES)


def test_merge_types() -> None:
    """Test the merge of the user tables with the shipped defaults."""
    config = parse_config(
        {
            "Article": {"required": ["author", "title", "year", "doi"]},
            "book": {"keep": ["Address"]},
            "custom": {"required": ["title"]},
            "other": {"required": [], "keep": ["note"]},
        },
        path=None,
        known_rules=RULES,
    )
    types = config.lint.types
    assert types["article"].required == ("author", "title", "year", "doi")
    assert types["article"].keep == frozenset(
        {"author", "title", "year", "doi", "month", "number", "pages", "url", "volume"}
    )
    assert types["book"].required == TYPES["book"][0]
    assert types["book"].keep == frozenset(
        {"address", "author", "editor", "publisher", "title", "year"}
    )
    assert types["custom"].required == ("title",)
    assert types["custom"].keep is None
    assert types["other"].required == ()
    assert types["other"].keep == frozenset({"note"})


def test_exclude_types_keeps_the_tables() -> None:
    """Test that an excluded type keeps its table and is skipped by the rules."""
    config = parse_config({"exclude-types": ["article"]}, path=None, known_rules=RULES)
    assert "article" in config.lint.types
    assert config.lint.exclude_types == frozenset({"article"})


def test_load_config_top_level(tmp_path: Path) -> None:
    """Test a dedicated file using top-level keys."""
    path = _write(tmp_path / "bibclean.toml", 'indent = 4\n[Book]\nkeep = ["note"]\n')
    config = load_config(path, known_rules=RULES)
    assert config.format.indent == 4
    assert "note" in config.lint.types["book"].keep
    assert config.source == path
    assert load_config(path, known_rules=RULES) is config


def test_load_config_tool_table_in_dedicated_file(tmp_path: Path) -> None:
    """Test that a dedicated file cannot use a [tool.bibclean] table."""
    path = _write(tmp_path / "bibclean.toml", "[tool.bibclean]\nindent = 4\n")
    with pytest.raises(ConfigError, match=re.escape("[tool] tables are read from")):
        load_config(path, known_rules=RULES)


def test_load_config_extra_ignore(tmp_path: Path) -> None:
    """Test that extra rule names are added to the ignore set."""
    path = _write(tmp_path / "bibclean.toml", 'ignore = ["doi-prefix"]\n')
    config = load_config(path, known_rules=RULES, extra_ignore=("duplicate-key",))
    assert config.lint.ignore == frozenset({"doi-prefix", "duplicate-key"})
    config = load_config(None, known_rules=RULES, extra_ignore=("duplicate-key",))
    assert config.source is None
    assert config.lint.ignore == frozenset({"duplicate-key"})


@pytest.mark.parametrize("text", ["[project]\nname = 'x'\n", "[tool]\nbibclean = 1\n"])
def test_load_config_pyproject_without_table(tmp_path: Path, text: str) -> None:
    """Test that a pyproject.toml must hold a [tool.bibclean] table."""
    path = _write(tmp_path / "pyproject.toml", text)
    with pytest.raises(ConfigError, match=re.escape("no [tool.bibclean] table")):
        load_config(path, known_rules=RULES)


def test_load_config_invalid_toml(tmp_path: Path) -> None:
    """Test the message of a TOML syntax error."""
    path = _write(tmp_path / "bibclean.toml", "indent = \n")
    with pytest.raises(ConfigError, match="invalid TOML"):
        load_config(path, known_rules=RULES)


def test_load_config_missing_file(tmp_path: Path) -> None:
    """Test the message of an unreadable file."""
    with pytest.raises(ConfigError, match="cannot read file"):
        load_config(tmp_path / "absent.toml", known_rules=RULES)


def test_config_error_attributes(tmp_path: Path) -> None:
    """Test that the error carries the path and names the dedicated file."""
    path = _write(tmp_path / "bibclean.toml", "unknown-key = 1\n")
    for _ in range(2):  # failures are not memoized
        with pytest.raises(ConfigError) as excinfo:
            load_config(path, known_rules=RULES)
    assert excinfo.value.path == path
    assert str(excinfo.value) == "unknown key 'unknown-key' in bibclean.toml"


def test_find_config_precedence(tmp_path: Path) -> None:
    """Test the precedence of the three file names inside one directory."""
    _write(tmp_path / "pyproject.toml", "[tool.bibclean]\nindent = 8\n")
    assert find_config(tmp_path) == tmp_path / "pyproject.toml"
    _write(tmp_path / "bibclean.toml", "indent = 4\n")
    find_config.cache_clear()
    assert find_config(tmp_path) == tmp_path / "bibclean.toml"
    _write(tmp_path / ".bibclean.toml", "indent = 3\n")
    find_config.cache_clear()
    assert find_config(tmp_path) == tmp_path / ".bibclean.toml"


def test_find_config_walks_up(tmp_path: Path) -> None:
    """Test that the walk goes up until a file is found."""
    _write(tmp_path / "bibclean.toml", "indent = 4\n")
    deep = tmp_path / "a" / "b"
    deep.mkdir(parents=True)
    assert find_config(deep) == tmp_path / "bibclean.toml"


def test_find_config_skips_pyproject_without_table(tmp_path: Path) -> None:
    """Test that a pyproject.toml without the table is not a match."""
    _write(tmp_path / "a" / "pyproject.toml", "[project]\nname = 'x'\n")
    _write(tmp_path / "bibclean.toml", "indent = 4\n")
    assert find_config(tmp_path / "a") == tmp_path / "bibclean.toml"


def test_find_config_invalid_pyproject(tmp_path: Path) -> None:
    """Test that an unparsable pyproject.toml is an error."""
    _write(tmp_path / "pyproject.toml", "[tool\n")
    with pytest.raises(ConfigError, match="invalid TOML"):
        find_config(tmp_path)


def test_find_config_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that the walk returns None when nothing is found."""
    monkeypatch.setattr(
        "bibclean._config._pyproject_has_table",
        lambda path: False,  # noqa: ARG005
    )
    assert find_config(tmp_path) is None


def test_sort_fields_boolean() -> None:
    """Test that sort-fields also accepts a boolean."""
    config = parse_config({"sort-fields": False}, path=None, known_rules=RULES)
    assert config.format.sort_fields is False
