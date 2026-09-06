from __future__ import annotations

from bibclean._defaults import DOI_PREFIXES, MONTH_MACROS, MONTHS, TYPES

_EXPECTED_TYPES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "article": (
        ("author", "journal", "title", "year"),
        ("doi", "month", "number", "pages", "url", "volume"),
    ),
    "book": (
        ("author|editor", "publisher", "title", "year"),
        ("address", "doi", "edition", "month", "series", "url", "volume"),
    ),
    "booklet": (
        ("title",),
        ("address", "author", "howpublished", "month", "url", "year"),
    ),
    "inbook": (
        ("author|editor", "chapter|pages", "publisher", "title", "year"),
        ("address", "doi", "edition", "month", "series", "url", "volume"),
    ),
    "incollection": (
        ("author", "booktitle", "publisher", "title", "year"),
        (
            "address",
            "chapter",
            "doi",
            "edition",
            "editor",
            "month",
            "pages",
            "series",
            "url",
            "volume",
        ),
    ),
    "inproceedings": (
        ("author", "booktitle", "title", "year"),
        (
            "address",
            "doi",
            "editor",
            "month",
            "organization",
            "pages",
            "publisher",
            "series",
            "url",
            "volume",
        ),
    ),
    "conference": (
        ("author", "booktitle", "title", "year"),
        (
            "address",
            "doi",
            "editor",
            "month",
            "organization",
            "pages",
            "publisher",
            "series",
            "url",
            "volume",
        ),
    ),
    "manual": (
        ("title",),
        ("address", "author", "edition", "month", "organization", "url", "year"),
    ),
    "mastersthesis": (
        ("author", "school", "title", "year"),
        ("address", "doi", "month", "type", "url"),
    ),
    "phdthesis": (
        ("author", "school", "title", "year"),
        ("address", "doi", "month", "type", "url"),
    ),
    "misc": (
        (),
        ("author", "doi", "howpublished", "month", "note", "title", "url", "year"),
    ),
    "proceedings": (
        ("title", "year"),
        (
            "address",
            "doi",
            "editor",
            "month",
            "organization",
            "publisher",
            "series",
            "url",
            "volume",
        ),
    ),
    "techreport": (
        ("author", "institution", "title", "year"),
        ("address", "doi", "month", "number", "type", "url"),
    ),
    "unpublished": (
        ("author", "note", "title"),
        ("doi", "month", "url", "year"),
    ),
    "online": (
        ("title",),
        ("author", "doi", "month", "publisher", "url", "version", "year"),
    ),
    "software": (
        ("title",),
        ("author", "doi", "month", "publisher", "url", "version", "year"),
    ),
    "dataset": (
        ("title",),
        ("author", "doi", "month", "publisher", "url", "version", "year"),
    ),
}


def test_types() -> None:
    """Test that the shipped tables match the documented ones exactly."""
    assert TYPES == _EXPECTED_TYPES


def test_types_are_lowercase_and_sorted() -> None:
    """Test that every table name and field name is lowercase and sorted."""
    for name, (required, keep) in TYPES.items():
        assert name == name.lower()
        assert list(keep) == sorted(keep)
        assert all(item == item.lower() for item in required)
        assert all(item == item.lower() for item in keep)
        names = {part for item in required for part in item.split("|")}
        assert names.isdisjoint(keep)


def test_months() -> None:
    """Test the month table and the derived macro set."""
    assert len(MONTHS) == 12
    assert MONTHS[0] == ("jan", "January")
    assert MONTHS[8] == ("sep", "September")
    assert MONTHS[11] == ("dec", "December")
    assert MONTH_MACROS == frozenset(
        {
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
        }
    )


def test_doi_prefixes() -> None:
    """Test the DOI resolver prefixes."""
    assert DOI_PREFIXES == (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "https://www.doi.org/",
        "doi:",
    )
    assert all(prefix == prefix.lower() for prefix in DOI_PREFIXES)
