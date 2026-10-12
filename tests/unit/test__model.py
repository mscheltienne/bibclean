from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bibclean._model import Part

if TYPE_CHECKING:
    from bibclean._model import Kind


@pytest.mark.parametrize(
    ("kind", "text", "expected"),
    [
        ("bare", "acm", True),
        ("bare", "jan2", True),
        ("bare", "2024", False),
        ("bare", "²", True),
        ("braced", "acm", False),
        ("quoted", "acm", False),
    ],
)
def test_part_is_macro(kind: Kind, text: str, expected: bool) -> None:
    """Test that only a bare part not made of ASCII digits is a macro."""
    assert Part(kind, text).is_macro is expected
