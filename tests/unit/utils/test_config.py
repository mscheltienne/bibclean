from __future__ import annotations

from importlib.util import find_spec
from io import StringIO

import pytest

from bibclean.utils.config import sys_info


def test_sys_info() -> None:
    """Test info-showing utility."""
    out = StringIO()
    sys_info(fid=out)
    value = out.getvalue()
    out.close()
    assert "Platform:" in value
    assert "Executable:" in value
    assert "CPU:" in value

    hardware = ("Physical cores:", "Logical cores", "RAM:", "SWAP:")
    if find_spec("psutil") is None:
        assert all(line not in value for line in hardware)
    else:
        assert all(line in value for line in hardware)

    assert "bibtexparser" in value
    assert "click" in value
    assert "packaging" in value

    assert "style" not in value
    assert "test" not in value

    out = StringIO()
    sys_info(fid=out, developer=True)
    value = out.getvalue()
    out.close()

    assert "style" in value
    assert "test" in value


def test_sys_info_without_psutil(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that the hardware lines are skipped when psutil is not installed."""
    monkeypatch.setattr(
        "bibclean.utils.config.import_optional_dependency", lambda *args, **kwargs: None
    )
    out = StringIO()
    sys_info(fid=out)
    value = out.getvalue()
    out.close()
    assert "CPU:" in value
    assert "Physical cores:" not in value
    assert "RAM:" not in value


def test_sys_info_invalid() -> None:
    """Test getting information on package without requirements."""
    out = StringIO()
    with pytest.raises(RuntimeError, match="could not be retrieved"):
        sys_info(fid=out, package="packaging")
    out.close()


def test_sys_info_other_package() -> None:
    """Test getting information on another package."""
    out = StringIO()
    sys_info(fid=out, package="bibtexparser")
    value = out.getvalue()
    out.close()
    assert "bibtexparser" in value


def test_sys_info_other_package_dev() -> None:
    """Test getting developer information on another package."""
    out = StringIO()
    with pytest.raises(RuntimeError, match="from source in an editable install"):
        sys_info(fid=out, package="bibtexparser", developer=True)
    out.close()
