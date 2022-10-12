"""Test utils.py"""

from bibtexparser.bibdatabase import BibDatabase

from bibclean.utils import get_entry_types


def test_get_entry_types():
    """Test retrieval of entry types."""
    bib_database = BibDatabase()
    bib_database.entries = [
        {
            "author": "Christoph M. Michel and Thomas Koenig",
            "doi": "10.1016/j.neuroimage.2017.11.062",
            "issn": "1053-8119",
            "note": "Brain Connectivity Dynamics",
            "year": "2018",
            "pages": "577-593",
            "volume": "180",
            "journal": "NeuroImage",
            "title": "EEG microstates as a tool for studying the temporal dynamics of whole-brain neuronal networks: A review",  # noqa: E501
            "ENTRYTYPE": "article",
            "ID": "MICHEL2018577",
        }
    ]
    assert get_entry_types(bib_database) == {"MICHEL2018577": "article"}

    bib_database.entries.append(
        {
            "ENTRYTYPE": "book",
            "year": "1987",
            "edition": "2",
            "publisher": "Wiley Edition",
            "ID": "Bird1987",
            "volume": "1",
            "title": "Dynamics of Polymeric Liquid",
            "author": "Bird, R.B. and Armstrong, R.C. and Hassager, O.",
        }
    )
    assert get_entry_types(bib_database) == {
        "MICHEL2018577": "article",
        "Bird1987": "book",
    }
