from __future__ import annotations

from bibclean._defaults import TYPES


def test_types_invariants() -> None:
    """Test that the tables are lowercase, keep sorted and required disjoint from it."""
    for name, (required, keep) in TYPES.items():
        assert name == name.lower()
        assert list(keep) == sorted(keep)
        assert all(item == item.lower() for item in (*required, *keep))
        names = {part for item in required for part in item.split("|")}
        assert names.isdisjoint(keep)
