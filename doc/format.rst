.. include:: ./links.inc

Canonical format
================

``bibclean fix`` rewrites a file into one canonical style. A file that already
matches it is left alone; a file that does not is reported by ``bibclean check``
with a single line, without a position:

.. code-block:: text

    doc/references.bib: file is not formatted, run `bibclean fix` [*]

Formatting is independent of the rules: it never removes a field and never
changes what a value means. A few points of the style are configurable, the rest
is fixed. See :doc:`configuration` for the options.

Before and after
----------------

.. tab-set::

    .. tab-item:: Before

        .. literalinclude:: ../tests/assets/blocks.bib
           :language: bibtex

    .. tab-item:: After

        .. literalinclude:: ../tests/assets/blocks.fixed.bib
           :language: bibtex

The style
---------

.. list-table::
   :header-rows: 1
   :widths: 30 25 25 20

   * - Rewrite
     - Before
     - After
     - Option
   * - Indentation
     - ``\ttitle = {A},``
     - ``  title = {A},``
     - ``indent``
   * - Entry type lowercased
     - ``@Article{K,``
     - ``@article{K,``
     - fixed
   * - Field name lowercased
     - ``Author = {X}``
     - ``author = {X}``
     - fixed
   * - Cite key preserved
     - ``@article{Smith2020,``
     - unchanged
     - fixed
   * - Textual values braced
     - ``title = "A"``
     - ``title = {A}``
     - fixed
   * - Numbers braced
     - ``year = 2014``
     - ``year = {2014}``
     - fixed
   * - Macros left bare
     - ``month = jan``
     - unchanged
     - fixed
   * - Concatenation spacing
     - ``acm#" Press"``
     - ``acm # { Press}``
     - fixed
   * - Inner whitespace collapsed
     - ``{A  {Title}   here}``
     - ``{A {Title} here}``
     - fixed
   * - Outer whitespace stripped
     - ``{ A }``
     - ``{A}``
     - fixed
   * - Value alignment
     - ``author = {X}``
     - unchanged, or padded so the ``=`` align
     - ``align-values``
   * - Comma after the last field
     - ``year = {2014},``
     - ``year = {2014}``
     - ``trailing-comma``
   * - Field order
     - ``year, title, author``
     - ``author, title, year``
     - ``sort-fields``
   * - Entry order
     - keys ``b, A, a``
     - ``A, a, b``
     - ``sort-entries``
   * - Block order
     - any
     - preambles, then macros, then entries
     - fixed
   * - Comments
     - ``% x`` above an entry
     - still above it after sorting, no blank line between
     - fixed
   * - Blank lines
     - any number, anywhere
     - exactly one between blocks
     - fixed
   * - Delimiters
     - ``@article(K, )``
     - ``@article{K, }``
     - fixed
   * - Unparsable block
     - verbatim
     - verbatim, at its original position among the entries
     - fixed
   * - Line endings and final newline
     - ``\r\n``, missing
     - ``\n``, exactly one
     - fixed

An entry rendered with the defaults:

.. code-block:: bibtex

    @article{Gramfort2014,
      author = {Gramfort, Alexandre and Luessi, Martin},
      doi = {10.1016/j.neuroimage.2013.10.027},
      journal = {NeuroImage},
      month = feb,
      pages = {446--460},
      title = {{MNE} software for processing {MEG} and {EEG} data},
      volume = {86},
      year = {2014}
    }

Braces are used everywhere because `pybtex`_ treats ``{...}`` and ``"..."``
identically and braces need no escaping of inner quotes. Bare macros are the one
exception: ``month = jan`` refers to a macro that pybtex substitutes, while
``month = {jan}`` is the literal text ``jan``. Rewriting one into the other would
change the file, so macros are never touched, and only bare numbers are braced.

Blocks and ordering
-------------------

A file is read as a sequence of blocks: entries, ``@string`` macro definitions,
``@preamble`` blocks, ``@comment`` blocks and the free text between them. Nothing
is dropped.

Blocks are grouped into units before they are ordered: a unit is one block
together with the comments and free text written directly above it, so an
annotation travels with the entry it describes. Units are then emitted as
preambles, macro definitions, and finally entries, sorted by cite key. A block
that could not be parsed stays at the position it had among the entries.

Reading conventions
-------------------

Two details of how a file is read are worth knowing, because they decide whether
a line is data or text.

**A block starts only at the beginning of a line.** An ``@`` is read as the start
of a block when it is the first non-blank character of its line. Anywhere else it
is free text, so a commented-out entry and an e-mail address survive untouched
instead of becoming a syntax error:

.. code-block:: bibtex

    % write to me@example.org
    % @article{old_entry, title = {Not an entry any more}}

**A backslash escapes the next character.** Braces are counted so that ``\{``,
``\}`` and ``\\`` never open or close a value, which is what makes a Zotero
``file`` field parse:

.. code-block:: bibtex

    @article{k,
      file = {Paper.pdf:C\:\\Users\\me\\Zotero\\storage\\Paper.pdf:application/pdf}
    }

BibTeX itself counts braces without looking at backslashes. A value that relies on
``\{`` to balance its braces is therefore read differently by ``bibclean`` and by
pybtex, and should be rewritten with balanced braces.

Encoding and line endings
-------------------------

Files are read and written as UTF-8 unless ``--encoding`` says otherwise. The
output always uses line feeds and ends with exactly one newline, and a byte order
mark is removed. A file with carriage returns or a byte order mark is therefore
reported as not formatted, and rewritten once.
