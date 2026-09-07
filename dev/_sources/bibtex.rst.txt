.. include:: ./links.inc

BibTex format
=============

To understand the BibTex format and the configuration of ``bibclean``, some
terminology is required. The format is defined `here <bibtex format_>`_ on the
`bibtex website`_.

Entry-type
----------

The entry-type defines the content type. It follows the ``@``. For instance, an
article is defined with ``@article{}`` and a book with ``@book{}``.

Cite-key
--------

The cite-key follows the entry-type and is a unique identifier of the entry.
For instance, ``@book{MyUniqueCitekey, ... }``.

Fields
------

The bibliographic data follows the cite-key as a list of key-value pairs.

.. code-block:: bibtex

    @book{MyUniqueCitekey,
     title = "Title of the book",
    }

The key is called ``field``.
