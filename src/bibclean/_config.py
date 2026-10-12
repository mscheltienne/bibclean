from __future__ import annotations

import difflib
import tomllib
from dataclasses import dataclass, field, fields, replace
from functools import cache
from typing import TYPE_CHECKING, Any, Literal, get_args

from bibclean._defaults import TYPES

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from pathlib import Path

Month = Literal["abbreviation", "name", "number"]

_KNOWN_KEYS: dict[str, str] = {
    "indent": 'a positive integer or "tab"',
    "align-values": "a boolean",
    "trailing-comma": "a boolean",
    "sort-entries": "a boolean",
    "sort-fields": "a boolean or an array of strings",
    "month": 'one of "abbreviation", "name", "number"',
    "ignore": "an array of strings",
    "exclude": "an array of strings",
    "exclude-types": "an array of strings",
}
_TYPE_KEYS: tuple[str, ...] = ("required", "keep")


class ConfigError(Exception):
    """Invalid or unreadable configuration file.

    Parameters
    ----------
    path : Path | None
        File the error comes from, None for a configuration built in memory.
    message : str
        Description of the problem.
    """

    def __init__(self, path: Path | None, message: str) -> None:
        super().__init__(message)
        self.path = path
        self.message = message


@dataclass(slots=True, frozen=True)
class FormatOptions:
    """Options driving the canonical rendering of a file.

    Parameters
    ----------
    indent : int | str
        Number of spaces of the field indent, or ``'tab'``.
    align_values : bool
        Pad field names so that the ``'='`` signs align inside an entry.
    trailing_comma : bool
        Emit a comma after the last field of an entry.
    sort_entries : bool
        Sort entries by cite key, case-insensitively and stably.
    sort_fields : bool | tuple of str
        Sort fields alphabetically, preserve their order, or place the listed
        names first and sort the remaining ones alphabetically.
    """

    indent: int | Literal["tab"] = 2
    align_values: bool = False
    trailing_comma: bool = False
    sort_entries: bool = True
    sort_fields: bool | tuple[str, ...] = True


@dataclass(slots=True, frozen=True)
class TypeRules:
    """Field requirements of one entry type.

    Parameters
    ----------
    required : tuple of str
        Required field names as written, an alternative being spelled
        ``'author|editor'``.
    keep : frozenset of str | None
        Field names kept by the ``strip-field`` rule, required names included.
        None means that entries of this type are never stripped.
    """

    required: tuple[str, ...]
    keep: frozenset[str] | None


@dataclass(slots=True, frozen=True)
class LintOptions:
    """Options driving the lint rules.

    Parameters
    ----------
    ignore : frozenset of str
        Names of the rules that never run.
    exclude : frozenset of str
        Cite keys exempt from every rule.
    exclude_types : frozenset of str
        Lowercased entry types exempt from every rule.
    month : str
        Target form of the ``month`` field.
    types : dict of str to TypeRules
        Per-type field requirements, keyed by lowercased entry type.
    """

    ignore: frozenset[str] = frozenset()
    exclude: frozenset[str] = frozenset()
    exclude_types: frozenset[str] = frozenset()
    month: Month = "abbreviation"
    types: Mapping[str, TypeRules] = field(default_factory=lambda: _merge_types({}))


@dataclass(slots=True, frozen=True)
class Config:
    """Effective configuration for one file.

    Parameters
    ----------
    format : FormatOptions
        Formatting options.
    lint : LintOptions
        Linting options.
    """

    format: FormatOptions
    lint: LintOptions


def default_config() -> Config:
    """Build the configuration used when no file applies.

    Returns
    -------
    Config
        The shipped defaults.
    """
    return parse_config({}, path=None, known_rules=())


def parse_config(
    table: Mapping[str, Any], *, path: Path | None, known_rules: Collection[str]
) -> Config:
    """Validate a configuration table and build the configuration it describes.

    Parameters
    ----------
    table : dict
        Content of the ``[tool.bibclean]`` table of a ``pyproject.toml``, or the
        whole document of a dedicated file.
    path : Path | None
        File the table was read from, used in error messages. A dedicated file is
        any file not named ``pyproject.toml``; None stands for a
        ``[tool.bibclean]`` table.
    known_rules : collection of str
        Rule names accepted by the ``ignore`` key.

    Returns
    -------
    Config
        The validated configuration.

    Raises
    ------
    ConfigError
        If a key is unknown, a value has the wrong type or an invalid value, or a
        table names an entry type without shipped defaults and declares no
        ``required``. Keys are validated in document order and the first problem
        raises.
    """
    nested = path is None or path.name == "pyproject.toml"
    top = "[tool.bibclean]" if nested else path.name
    values: dict[str, Any] = {}
    user_types: dict[str, dict[str, tuple[str, ...]]] = {}
    for key, value in table.items():
        if key in _KNOWN_KEYS:
            values[key.replace("-", "_")] = _parse_value(
                key, value, path, top, known_rules
            )
            continue
        if not isinstance(value, dict):
            raise ConfigError(
                path, f"unknown key {key!r} in {top}" + _did_you_mean(key, _KNOWN_KEYS)
            )
        name = key.lower()
        where = f"[tool.bibclean.{name}]" if nested else f"[{name}]"
        user_types[name] = _parse_type_table(value, path, where)
        if name not in TYPES and "required" not in user_types[name]:
            raise ConfigError(
                path,
                f"unknown entry type {name!r} in {where}"
                + _did_you_mean(name, TYPES)
                + " (a new entry type must declare 'required')",
            )
    format_names = {item.name for item in fields(FormatOptions)}
    format_options = FormatOptions(
        **{key: value for key, value in values.items() if key in format_names}
    )
    lint_options = LintOptions(
        **{key: value for key, value in values.items() if key not in format_names},
        types=_merge_types(user_types),
    )
    return Config(format=format_options, lint=lint_options)


@cache
def load_config(
    path: Path | None,
    *,
    known_rules: tuple[str, ...],
    extra_ignore: tuple[str, ...] = (),
) -> Config:
    """Read and validate one configuration file, memoized.

    Parameters
    ----------
    path : Path | None
        File to read, None for the shipped defaults. A ``pyproject.toml`` must
        hold a ``[tool.bibclean]`` table; any other file uses top-level keys.
    known_rules : tuple of str
        Rule names accepted by the ``ignore`` key.
    extra_ignore : tuple of str
        Rule names added to the ``ignore`` set of the configuration.

    Returns
    -------
    Config
        The validated configuration.

    Raises
    ------
    ConfigError
        If the file cannot be read, is not valid TOML, lacks its table, or fails
        validation. Failures are not memoized, so every input using an invalid
        file reports it.
    """
    if path is None:
        config = default_config()
    else:
        document = _read_toml(path)
        if path.name == "pyproject.toml":
            tool = document.get("tool")
            document = tool.get("bibclean") if isinstance(tool, dict) else None
            if not isinstance(document, dict):
                raise ConfigError(path, "no [tool.bibclean] table")
        elif "tool" in document:
            raise ConfigError(
                path,
                f"[tool] tables are read from pyproject.toml only, write the keys "
                f"at the top level of {path.name}",
            )
        config = parse_config(document, path=path, known_rules=known_rules)
    lint = replace(config.lint, ignore=config.lint.ignore | frozenset(extra_ignore))
    return replace(config, lint=lint)


@cache
def find_config(directory: Path) -> Path | None:
    """Walk up from a directory looking for a configuration file, memoized.

    Parameters
    ----------
    directory : Path
        Directory to start from.

    Returns
    -------
    Path | None
        The first file found, None when the filesystem root is reached. Inside
        one directory, ``.bibclean.toml`` wins over ``bibclean.toml``, which wins
        over a ``pyproject.toml`` holding a ``[tool.bibclean]`` table.

    Raises
    ------
    ConfigError
        If a candidate ``pyproject.toml`` cannot be read or is not valid TOML.
    """
    directory = directory.resolve()
    for parent in [directory, *directory.parents]:
        for name in (".bibclean.toml", "bibclean.toml"):
            candidate = parent / name
            if candidate.is_file():
                return candidate
        candidate = parent / "pyproject.toml"
        if candidate.is_file() and _pyproject_has_table(candidate):
            return candidate
    return None


def _read_toml(path: Path) -> dict[str, Any]:
    """Read a TOML document, turning every failure into a ConfigError.

    Parameters
    ----------
    path : Path
        File to read.

    Returns
    -------
    dict
        The parsed document.

    Raises
    ------
    ConfigError
        If the file cannot be read or is not valid TOML.
    """
    try:
        with path.open("rb") as fid:
            return tomllib.load(fid)
    except OSError as exc:
        raise ConfigError(path, f"cannot read file: {exc.strerror or exc}")
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(path, f"invalid TOML: {exc}")


def _pyproject_has_table(path: Path) -> bool:
    """Check whether a pyproject.toml holds a [tool.bibclean] table.

    Parameters
    ----------
    path : Path
        Candidate ``pyproject.toml``.

    Returns
    -------
    bool
        True when the file holds a ``bibclean`` key under ``[tool]``.

    Raises
    ------
    ConfigError
        If the file cannot be read or is not valid TOML.
    """
    tool = _read_toml(path).get("tool")
    return isinstance(tool, dict) and "bibclean" in tool


def _did_you_mean(name: str, candidates: Collection[str]) -> str:
    """Build the suffix suggesting the closest known name, if any.

    Parameters
    ----------
    name : str
        Unknown name.
    candidates : collection of str
        Known names.

    Returns
    -------
    str
        ``", did you mean '...'?"``, or an empty string when nothing is close.
    """
    matches = difflib.get_close_matches(name, sorted(candidates), n=1, cutoff=0.6)
    return f", did you mean {matches[0]!r}?" if matches else ""


def _is_string_array(value: Any) -> bool:
    """Check whether a value is a list of strings.

    Parameters
    ----------
    value : Any
        Value to check.

    Returns
    -------
    bool
        True for a list whose items are all strings.
    """
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _parse_value(
    key: str, value: Any, path: Path | None, where: str, known_rules: Collection[str]
) -> Any:
    """Validate one top-level key and return the value to store.

    Parameters
    ----------
    key : str
        Known key, as written in the file.
    value : Any
        Value read from the file.
    path : Path | None
        File the value was read from, used in error messages.
    where : str
        Location of the key, used in error messages.
    known_rules : collection of str
        Rule names accepted by the ``ignore`` key.

    Returns
    -------
    Any
        The value converted to the type of its option.

    Raises
    ------
    ConfigError
        If the value has the wrong type, an invalid value, or names an unknown
        rule.
    """
    if key == "indent":
        valid = value == "tab" or (type(value) is int and value > 0)
    elif key in ("align-values", "trailing-comma", "sort-entries"):
        valid = isinstance(value, bool)
    elif key == "sort-fields":
        valid = isinstance(value, bool) or _is_string_array(value)
    elif key == "month":
        valid = value in get_args(Month)
    else:
        valid = _is_string_array(value)
    if not valid:
        raise ConfigError(
            path, f"'{key}' in {where} must be {_KNOWN_KEYS[key]}, got {value!r}"
        )
    if key == "sort-fields" and not isinstance(value, bool):
        return tuple(item.lower() for item in value)
    if key == "ignore":
        for name in value:
            if name not in known_rules:
                raise ConfigError(
                    path,
                    f"unknown rule {name!r} in 'ignore'"
                    + _did_you_mean(name, known_rules),
                )
        return frozenset(value)
    if key == "exclude":
        return frozenset(value)
    if key == "exclude-types":
        return frozenset(item.lower() for item in value)
    return value


def _parse_type_table(
    table: Mapping[str, Any], path: Path | None, where: str
) -> dict[str, tuple[str, ...]]:
    """Validate one per-type table and return the field lists it defines.

    Parameters
    ----------
    table : dict
        Content of the per-type table.
    path : Path | None
        File the table was read from, used in error messages.
    where : str
        Name of the table, used in error messages.

    Returns
    -------
    dict of str to tuple of str
        The ``required`` and ``keep`` lists present in the table.

    Raises
    ------
    ConfigError
        If a key is unknown or a value is not an array of strings.
    """
    parsed: dict[str, tuple[str, ...]] = {}
    for key, value in table.items():
        if key not in _TYPE_KEYS:
            raise ConfigError(
                path,
                f"unknown key {key!r} in {where}" + _did_you_mean(key, _TYPE_KEYS),
            )
        if not _is_string_array(value):
            raise ConfigError(
                path,
                f"'{key}' in {where} must be an array of strings, got {value!r}",
            )
        parsed[key] = tuple(value)
    return parsed


def _effective_keep(required: tuple[str, ...], keep: tuple[str, ...]) -> frozenset[str]:
    """Combine the required names and the keep list into one lowercased set.

    Parameters
    ----------
    required : tuple of str
        Required field names, alternatives spelled ``'author|editor'``.
    keep : tuple of str
        Kept field names.

    Returns
    -------
    frozenset of str
        Every name of both lists, alternatives split, in lower case.
    """
    names = {name.lower() for item in required for name in item.split("|")}
    return frozenset(names | {name.lower() for name in keep})


def _merge_types(
    user_types: Mapping[str, Mapping[str, tuple[str, ...]]],
) -> dict[str, TypeRules]:
    """Merge the user per-type tables into the shipped defaults.

    Parameters
    ----------
    user_types : dict of str to dict
        Validated per-type tables, keyed by lowercased entry type. A type without
        shipped defaults always declares ``required``.

    Returns
    -------
    dict of str to TypeRules
        Field requirements of every shipped or user type. A user key replaces the
        shipped one; a type without any ``keep`` list is never stripped.
    """
    merged: dict[str, tuple[tuple[str, ...], tuple[str, ...] | None]] = dict(TYPES)
    for name, table in user_types.items():
        required, keep = merged.get(name, ((), None))
        merged[name] = (table.get("required", required), table.get("keep", keep))
    return {
        name: TypeRules(
            required=required,
            keep=None if keep is None else _effective_keep(required, keep),
        )
        for name, (required, keep) in merged.items()
    }
