from __future__ import annotations

TYPES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
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

MONTHS: tuple[tuple[str, str], ...] = (
    ("jan", "January"),
    ("feb", "February"),
    ("mar", "March"),
    ("apr", "April"),
    ("may", "May"),
    ("jun", "June"),
    ("jul", "July"),
    ("aug", "August"),
    ("sep", "September"),
    ("oct", "October"),
    ("nov", "November"),
    ("dec", "December"),
)

MONTH_MACROS: frozenset[str] = frozenset(macro for macro, _ in MONTHS)

DOI_PREFIXES: tuple[str, ...] = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
    "https://www.doi.org/",
    "doi:",
)
