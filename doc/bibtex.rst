.. include:: ./links.inc

BibTeX format
=============

The messages and the options of ``bibclean`` use the vocabulary of the BibTeX
format, defined `here <bibtex format_>`_ on the `bibtex website`_. This page
recalls the terms that appear in the documentation.

Entry type
----------

The entry type says what kind of work the entry describes. It follows the ``@``:
an article is written ``@article{...}``, a book ``@book{...}``. The type decides
which fields are required and which are kept, see :doc:`configuration`.

``bibclean`` lowercases the entry type and preserves types it has no table for,
such as ``@software`` or ``@dataset``.

Cite key
--------

The cite key follows the entry type and identifies the entry uniquely; it is what
a document cites.

.. code-block:: bibtex

    @book{MyUniqueCiteKey,
      title = {Title of the book}
    }

Its case is preserved, because a citation elsewhere spells it as written. Two keys
that differ only by case are still a duplicate, since BibTeX compares them without
case.

Fields
------

The bibliographic data follows the cite key, as a list of ``name = value`` pairs
separated by commas. The name of a pair is the field.

.. code-block:: bibtex

    @book{MyUniqueCiteKey,
      author = {Author, An},
      title = {Title of the book},
      year = {2020}
    }

Field names are lowercased and compared without case.

Values
------

A value takes one of four forms: braced ``{2014}``, quoted ``"2014"``, a bare
number ``2014``, or a bare macro ``jan``. The first three mean the same thing and
are all written with braces by ``bibclean``.

A bare macro is different: it is a name that BibTeX substitutes. Twelve month
macros, ``jan`` to ``dec``, are always defined, and more can be defined in the
file itself.

Macros and other blocks
-----------------------

Besides entries, a file may hold three other kinds of block, all preserved by
``bibclean``.

``@string`` defines a macro, which entries below it can then use as a value:

.. code-block:: bibtex

    @string{jneuro = {Journal of Neuroscience}}

    @article{k,
      journal = jneuro,
      month = feb
    }

``@preamble`` holds LaTeX inserted at the top of the generated bibliography, and
``@comment`` holds text that BibTeX ignores. Free text outside any block, such as
lines starting with ``%``, is kept as well.

Concatenation
-------------

Values can be concatenated with ``#``, which is how a macro is combined with
literal text:

.. code-block:: bibtex

    @string{acm = {ACM}}

    @book{k,
      publisher = acm # { Press}
    }
