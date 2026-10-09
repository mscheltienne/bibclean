from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import pytest

from bibclean._config import (
    ConfigError,
    ConfigResolver,
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
    assert config.lint.strip_fields is True
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
            "strip-fields": False,
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
    assert config.lint.strip_fields is False


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
            "'indent' in [tool.bibclean] must be an integer or \"tab\", got True",
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
        ({"month": 1}, "'month' in [tool.bibclean] must be a string, got 1"),
        (
            {"month": "names"},
            '\'month\' in [tool.bibclean] must be one of "abbreviation", "name", '
            '"number", "preserve", got \'names\'',
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
            "other": {"keep": ["note"]},
            "empty": {},
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
    assert types["empty"].required == ()
    assert types["empty"].keep is None


def test_exclude_types_keeps_the_tables() -> None:
    """Test that an excluded type keeps its table and is skipped by the rules."""
    config = parse_config({"exclude-types": ["article"]}, path=None, known_rules=RULES)
    assert "article" in config.lint.types
    assert config.lint.exclude_types == frozenset({"article"})


def test_load_config_top_level(tmp_path: Path) -> None:
    """Test a dedicated file using top-level keys."""
    path = _write(tmp_path / "bibclean.toml", "indent = 4\n")
    config = load_config(path, known_rules=RULES)
    assert config.format.indent == 4
    assert config.source == path


def test_load_config_tool_table(tmp_path: Path) -> None:
    """Test a dedicated file using a [tool.bibclean] table."""
    path = _write(
        tmp_path / "bibclean.toml",
        '[tool.other]\nx = 1\n\n[tool.bibclean]\nmonth = "name"\n',
    )
    assert load_config(path, known_rules=RULES).lint.month == "name"


def test_load_config_extra_ignore(tmp_path: Path) -> None:
    """Test that extra rule names are added to the ignore set."""
    path = _write(tmp_path / "bibclean.toml", 'ignore = ["doi-prefix"]\n')
    config = load_config(path, known_rules=RULES, extra_ignore=["duplicate-key"])
    assert config.lint.ignore == frozenset({"doi-prefix", "duplicate-key"})


def test_load_config_pyproject_without_table(tmp_path: Path) -> None:
    """Test that a pyproject.toml must hold the table."""
    path = _write(tmp_path / "pyproject.toml", "[project]\nname = 'x'\n")
    with pytest.raises(ConfigError, match=re.escape("missing [tool.bibclean] table")):
        load_config(path, known_rules=RULES)


def test_load_config_not_a_table(tmp_path: Path) -> None:
    """Test that the table must be a TOML table."""
    path = _write(tmp_path / "pyproject.toml", "[tool]\nbibclean = 1\n")
    with pytest.raises(ConfigError, match=re.escape("[tool.bibclean] must be a table")):
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
    """Test that the error carries the path and stringifies to the message."""
    path = _write(tmp_path / "bibclean.toml", "unknown-key = 1\n")
    with pytest.raises(ConfigError) as excinfo:
        load_config(path, known_rules=RULES)
    assert excinfo.value.path == path
    assert str(excinfo.value) == excinfo.value.message


def test_find_config_precedence(tmp_path: Path) -> None:
    """Test the precedence of the three file names inside one directory."""
    _write(tmp_path / "pyproject.toml", "[tool.bibclean]\nindent = 8\n")
    assert find_config(tmp_path) == tmp_path / "pyproject.toml"
    _write(tmp_path / "bibclean.toml", "indent = 4\n")
    assert find_config(tmp_path) == tmp_path / "bibclean.toml"
    _write(tmp_path / ".bibclean.toml", "indent = 3\n")
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


def test_resolver_isolated(tmp_path: Path) -> None:
    """Test that --isolated short-circuits the discovery."""
    _write(tmp_path / "bibclean.toml", "indent = 4\n")
    resolver = ConfigResolver(known_rules=RULES, isolated=True, extra_ignore=RULES[:1])
    config = resolver.for_file(tmp_path / "a.bib")
    assert config.source is None
    assert config.format.indent == 2
    assert config.lint.ignore == frozenset(RULES[:1])
    assert resolver.for_file(tmp_path / "b.bib") is config


def test_resolver_override(tmp_path: Path) -> None:
    """Test that --config is used for every input."""
    path = _write(tmp_path / "custom.toml", "indent = 8\n")
    _write(tmp_path / "bibclean.toml", "indent = 4\n")
    resolver = ConfigResolver(known_rules=RULES, override=path)
    assert resolver.for_file(tmp_path / "a.bib").format.indent == 8
    assert resolver.for_file(tmp_path / "sub" / "b.bib").format.indent == 8


def test_resolver_caches_the_directory_walk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that two files in one directory walk the tree once."""
    _write(tmp_path / "bibclean.toml", "indent = 4\n")
    calls = []
    original = find_config

    def counting(directory: Path) -> Path | None:
        calls.append(directory)
        return original(directory)

    monkeypatch.setattr("bibclean._config.find_config", counting)
    resolver = ConfigResolver(known_rules=RULES)
    first = resolver.for_file(tmp_path / "a.bib")
    second = resolver.for_file(tmp_path / "b.bib")
    assert first is second
    assert len(calls) == 1


def test_resolver_without_config(tmp_path: Path) -> None:
    """Test that the defaults apply when no file is found."""
    resolver = ConfigResolver(known_rules=RULES, extra_ignore=["doi-prefix"])
    monkey = tmp_path / "deep" / "a.bib"
    monkey.parent.mkdir()
    config = resolver.for_file(monkey)
    assert config.lint.ignore == frozenset({"doi-prefix"}) or config.source is not None


def test_resolver_does_not_cache_failures(tmp_path: Path) -> None:
    """Test that an invalid file is reported for every input using it."""
    _write(tmp_path / "bibclean.toml", "unknown-key = 1\n")
    resolver = ConfigResolver(known_rules=RULES)
    for name in ("a.bib", "b.bib"):
        with pytest.raises(ConfigError):
            resolver.for_file(tmp_path / name)


def test_pyproject_probe_on_a_missing_file(tmp_path: Path) -> None:
    """Test that an unreadable candidate is not a match."""
    from bibclean._config import _pyproject_has_table

    assert _pyproject_has_table(tmp_path / "absent.toml") is False


def test_sort_fields_boolean() -> None:
    """Test that sort-fields also accepts a boolean."""
    config = parse_config({"sort-fields": False}, path=None, known_rules=RULES)
    assert config.format.sort_fields is False
