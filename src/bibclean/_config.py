from __future__ import annotations

import difflib
import tomllib
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Literal

from bibclean._defaults import TYPES

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from pathlib import Path

Month = Literal["abbreviation", "name", "number", "preserve"]

_MONTHS: tuple[str, ...] = ("abbreviation", "name", "number", "preserve")
_KNOWN_KEYS: dict[str, str] = {
    "indent": 'an integer or "tab"',
    "align-values": "a boolean",
    "trailing-comma": "a boolean",
    "sort-entries": "a boolean",
    "sort-fields": "a boolean or an array of strings",
    "month": "a string",
    "ignore": "an array of strings",
    "exclude": "an array of strings",
    "exclude-types": "an array of strings",
    "strip-fields": "a boolean",
}
_TYPE_KEYS: tuple[str, ...] = ("required", "keep")
_TOP = "[tool.bibclean]"


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
    strip_fields : bool
        Master switch of the ``strip-field`` rule.
    month : str
        Target form of the ``month`` field, ``'preserve'`` disabling the rule.
    types : dict of str to TypeRules
        Per-type field requirements, keyed by lowercased entry type.
    """

    ignore: frozenset[str] = frozenset()
    exclude: frozenset[str] = frozenset()
    exclude_types: frozenset[str] = frozenset()
    strip_fields: bool = True
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
    source : Path | None
        File the configuration was read from, None for the defaults.
    """

    format: FormatOptions
    lint: LintOptions
    source: Path | None


def default_config() -> Config:
    """Build the configuration used when no file applies.

    Returns
    -------
    Config
        The shipped defaults, with ``source`` set to None.
    """
    return parse_config({}, path=None, known_rules=())


def parse_config(
    table: Mapping[str, Any], *, path: Path | None, known_rules: Collection[str]
) -> Config:
    """Validate a configuration table and build the configuration it describes.

    Parameters
    ----------
    table : dict
        Content of the ``[tool.bibclean]`` table.
    path : Path | None
        File the table was read from, used in error messages.
    known_rules : collection of str
        Rule names accepted by the ``ignore`` key.

    Returns
    -------
    Config
        The validated configuration.

    Raises
    ------
    ConfigError
        If a key is unknown or a value has the wrong type or an invalid value.
        Keys are validated in document order and the first problem raises.
    """
    values: dict[str, Any] = {}
    user_types: dict[str, dict[str, tuple[str, ...]]] = {}
    for key, value in table.items():
        if key in _KNOWN_KEYS:
            values[key] = _parse_value(key, value, path, known_rules)
        elif isinstance(value, dict):
            user_types[key.lower()] = _parse_type_table(key, value, path)
        else:
            raise ConfigError(
                path,
                f"unknown key {key!r} in {_TOP}" + _did_you_mean(key, _KNOWN_KEYS),
            )
    format_options = FormatOptions(
        indent=values.get("indent", 2),
        align_values=values.get("align-values", False),
        trailing_comma=values.get("trailing-comma", False),
        sort_entries=values.get("sort-entries", True),
        sort_fields=values.get("sort-fields", True),
    )
    lint_options = LintOptions(
        ignore=values.get("ignore", frozenset()),
        exclude=values.get("exclude", frozenset()),
        exclude_types=values.get("exclude-types", frozenset()),
        strip_fields=values.get("strip-fields", True),
        month=values.get("month", "abbreviation"),
        types=_merge_types(user_types),
    )
    return Config(format=format_options, lint=lint_options, source=path)


def load_config(
    path: Path, *, known_rules: Collection[str], extra_ignore: Collection[str] = ()
) -> Config:
    """Read and validate one configuration file.

    Parameters
    ----------
    path : Path
        File to read. A ``pyproject.toml`` must hold a ``[tool.bibclean]`` table;
        any other file may hold one or use top-level keys.
    known_rules : collection of str
        Rule names accepted by the ``ignore`` key.
    extra_ignore : collection of str
        Rule names added to the ``ignore`` set of the file.

    Returns
    -------
    Config
        The validated configuration, with ``source`` set to ``path``.

    Raises
    ------
    ConfigError
        If the file cannot be read, is not valid TOML, holds no table, or fails
        validation.
    """
    document = _read_toml(path)
    config = parse_config(
        _select_table(document, path), path=path, known_rules=known_rules
    )
    return _with_extra_ignore(config, extra_ignore)


def find_config(directory: Path) -> Path | None:
    """Walk up from a directory looking for a configuration file.

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
        If a candidate ``pyproject.toml`` is not valid TOML.
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


class ConfigResolver:
    """Configuration lookup for a batch of files.

    Parameters
    ----------
    known_rules : collection of str
        Rule names accepted by the ``ignore`` key.
    override : Path | None
        File used for every input instead of the discovered one.
    isolated : bool
        Ignore every configuration file and use the defaults.
    extra_ignore : collection of str
        Rule names added to the ``ignore`` set of whichever configuration applies.
    """

    def __init__(
        self,
        *,
        known_rules: Collection[str],
        override: Path | None = None,
        isolated: bool = False,
        extra_ignore: Collection[str] = (),
    ) -> None:
        self._known_rules = tuple(known_rules)
        self._override = override
        self._isolated = isolated
        self._extra_ignore = tuple(extra_ignore)
        self._directories: dict[Path, Path | None] = {}
        self._files: dict[Path, Config] = {}
        self._default: Config | None = None

    def for_file(self, file: Path) -> Config:
        """Return the configuration applying to one input file.

        Parameters
        ----------
        file : Path
            Input file, which need not exist.

        Returns
        -------
        Config
            The configuration to use, cached per directory and per file.

        Raises
        ------
        ConfigError
            If the applicable configuration file is invalid. Failures are not
            cached, so every input using that file reports the problem.
        """
        if self._isolated:
            return self._defaults()
        if self._override is not None:
            path: Path | None = self._override
        else:
            directory = file.resolve().parent
            if directory in self._directories:
                path = self._directories[directory]
            else:
                path = find_config(directory)
                self._directories[directory] = path
        if path is None:
            return self._defaults()
        if path in self._files:
            return self._files[path]
        config = load_config(
            path, known_rules=self._known_rules, extra_ignore=self._extra_ignore
        )
        self._files[path] = config
        return config

    def _defaults(self) -> Config:
        if self._default is None:
            self._default = _with_extra_ignore(default_config(), self._extra_ignore)
        return self._default


def _with_extra_ignore(config: Config, extra_ignore: Collection[str]) -> Config:
    """Add rule names to the ignore set of a configuration."""
    if not extra_ignore:
        return config
    lint = replace(config.lint, ignore=config.lint.ignore | frozenset(extra_ignore))
    return replace(config, lint=lint)


def _read_toml(path: Path) -> dict[str, Any]:
    """Read a TOML document, turning every failure into a ConfigError."""
    try:
        with path.open("rb") as fid:
            return tomllib.load(fid)
    except OSError as exc:
        raise ConfigError(path, f"cannot read file: {exc.strerror or exc}")
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(path, f"invalid TOML: {exc}")


def _select_table(document: Mapping[str, Any], path: Path | None) -> Mapping[str, Any]:
    """Extract the bibclean table out of a TOML document."""
    tool = document.get("tool")
    nested = isinstance(tool, dict) and "bibclean" in tool
    if path is not None and path.name == "pyproject.toml":
        if not nested:
            raise ConfigError(path, "missing [tool.bibclean] table")
        table = tool["bibclean"]
    elif nested:
        table = tool["bibclean"]
    else:
        table = document
    if not isinstance(table, dict):
        raise ConfigError(path, f"{_TOP} must be a table")
    return table


def _pyproject_has_table(path: Path) -> bool:
    """Check whether a pyproject.toml holds a [tool.bibclean] table."""
    try:
        with path.open("rb") as fid:
            document = tomllib.load(fid)
    except OSError:
        return False
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(path, f"invalid TOML: {exc}")
    tool = document.get("tool")
    return isinstance(tool, dict) and "bibclean" in tool


def _did_you_mean(name: str, candidates: Collection[str]) -> str:
    """Build the suffix suggesting the closest known name, if any."""
    matches = difflib.get_close_matches(name, sorted(candidates), n=1, cutoff=0.6)
    return f", did you mean {matches[0]!r}?" if matches else ""


def _is_string_array(value: Any) -> bool:
    """Check whether a value is a list of strings."""
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _parse_value(
    key: str, value: Any, path: Path | None, known_rules: Collection[str]
) -> Any:
    """Validate one top-level key and return the value to store."""
    if key == "indent":
        if isinstance(value, bool) or not isinstance(value, int | str):
            raise ConfigError(
                path, f"'indent' in {_TOP} must be {_KNOWN_KEYS[key]}, got {value!r}"
            )
        if (isinstance(value, int) and value < 1) or (
            isinstance(value, str) and value != "tab"
        ):
            raise ConfigError(
                path,
                f"'indent' in {_TOP} must be a positive integer or \"tab\", "
                f"got {value!r}",
            )
        return value
    if key in ("align-values", "trailing-comma", "sort-entries", "strip-fields"):
        if not isinstance(value, bool):
            raise ConfigError(
                path, f"'{key}' in {_TOP} must be a boolean, got {value!r}"
            )
        return value
    if key == "sort-fields":
        if isinstance(value, bool):
            return value
        if _is_string_array(value):
            return tuple(item.lower() for item in value)
        raise ConfigError(
            path, f"'sort-fields' in {_TOP} must be {_KNOWN_KEYS[key]}, got {value!r}"
        )
    if key == "month":
        if not isinstance(value, str) or isinstance(value, bool):
            raise ConfigError(
                path, f"'month' in {_TOP} must be a string, got {value!r}"
            )
        if value not in _MONTHS:
            allowed = ", ".join(f'"{name}"' for name in _MONTHS)
            raise ConfigError(
                path, f"'month' in {_TOP} must be one of {allowed}, got {value!r}"
            )
        return value
    if not _is_string_array(value):
        raise ConfigError(
            path,
            f"'{key}' in {_TOP} must be an array of strings, got {value!r}",
        )
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
    return frozenset(item.lower() for item in value)


def _parse_type_table(
    name: str, table: Mapping[str, Any], path: Path | None
) -> dict[str, tuple[str, ...]]:
    """Validate one per-type table and return the field lists it defines."""
    where = f"[tool.bibclean.{name.lower()}]"
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
    """Combine the required names and the keep list into one lowercased set."""
    names = {name.lower() for item in required for name in item.split("|")}
    return frozenset(names | {name.lower() for name in keep})


def _merge_types(
    user_types: Mapping[str, Mapping[str, tuple[str, ...]]],
) -> dict[str, TypeRules]:
    """Merge the user per-type tables into the shipped defaults."""
    merged: dict[str, tuple[tuple[str, ...] | None, tuple[str, ...] | None]] = {
        name: (required, keep) for name, (required, keep) in TYPES.items()
    }
    for name, table in user_types.items():
        required, keep = merged.get(name, (None, None))
        if "required" in table:
            required = table["required"]
        if "keep" in table:
            keep = table["keep"]
        merged[name] = (required, keep)
    return {
        name: TypeRules(
            required=tuple(required or ()),
            keep=None if keep is None else _effective_keep(required or (), keep),
        )
        for name, (required, keep) in merged.items()
    }
