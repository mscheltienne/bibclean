class DuplicateEntry(Exception):
    """Error raised when an entry is present multiple times in the same DB."""

    pass


class MissingReqField(Exception):
    """Error raised when a required field is missing from an entry."""

    pass
