from __future__ import annotations

import pytest

from tests.helpers import apply_rule

NAME = "url-with-doi"


def test_detection() -> None:
    """Test that every url field is removed when a doi is present."""
    source = (
        "@article{k,\n  doi = {10.1/x},\n  url = {https://a},\n  URL = {https://b}\n}\n"
    )
    rows, output = apply_rule(NAME, source)
    assert rows == [
        (3, 3, "field 'url' is redundant with 'doi'", True),
        (4, 3, "field 'url' is redundant with 'doi'", True),
    ]
    assert "url" not in output
    assert "doi = {10.1/x}" in output


@pytest.mark.parametrize(
    "source", ["@article{k, url = {https://a}}\n", "@article{k, doi = {10.1/x}}\n"]
)
def test_no_finding(source: str) -> None:
    """Test that a url or a doi alone is kept and not reported."""
    rows, output = apply_rule(NAME, source)
    assert rows == []
    assert output.count(" = ") == 1
