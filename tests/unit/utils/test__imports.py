from __future__ import annotations

import pytest

from bibclean.utils._imports import import_optional_dependency


def test_import_optional_dependency() -> None:
    """Test the import of optional dependencies."""
    # Test import of present package
    click = import_optional_dependency("click")
    assert click.__name__ == "click"

    # Test import of absent package
    with pytest.raises(ImportError, match="Missing optional dependency"):
        import_optional_dependency("non_existing_pkg", raise_error=True)

    # Test import of absent package without raise
    pkg = import_optional_dependency("non_existing_pkg", raise_error=False)
    assert pkg is None

    # Test extra
    with pytest.raises(ImportError, match="blabla"):
        import_optional_dependency("non_existing_pkg", extra="blabla")
