from __future__ import annotations


class DuplicateEntry(Exception):
    """Error raised when an entry is present multiple times in the same DB."""


class MissingReqField(Exception):
    """Error raised when a required field is missing from an entry."""
