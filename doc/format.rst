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
   * - Outer whitespace stripped, except in ``@string`` values
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
     - macros and preambles in source order, then entries
     - fixed
   * - Comments
     - ``% x`` above an entry
     - still above it after sorting, no blank line between
     - fixed
   * - Blank lines
     - any number, anywhere
     - exactly one between blocks, at most one inside free text
     - fixed
   * - Delimiters
     - ``@article(K, )``
     - ``@article{K, }``
     - fixed
   * - Unparsable block
     - ``@article{K, title = {A}``
     - the whole file unchanged until the block is repaired
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
``@preamble`` blocks and the free text between them, ``@comment`` included.
Nothing is dropped.

Blocks are grouped into units before they are ordered: a unit is one block
together with the comments and free text written directly above it, so an
annotation travels with the entry it describes. Units are then emitted as macro
definitions and preambles, in the order of the source since a preamble may use a
macro defined above it, and finally entries, sorted by cite key. Inside free text,
every run of blank lines is reduced to one.

Reading conventions
-------------------

**Every @ starts a block.** Like BibTeX and `pybtex`_, every ``@`` outside a block
starts a block, wherever it is. ``%`` is not a comment character for BibTeX, so an
``@`` in a ``%`` line starts a block too: an e-mail address there is a syntax error
that also breaks a pybtex or Sphinx build, and a ``%``-commented entry is a live
entry. To disable an entry, delete its ``@``. ``@comment`` must be followed by
``{`` or ``(``, then by plain text up to the next ``@``:

.. code-block:: bibtex

    % write to me@example.org                    <- syntax error at '@example.org'
    % @article{old, title = {Still an entry}}    <- a live entry
    % article{old, title = {Disabled}}           <- free text
    @comment{ unbalanced { braces are fine here

After a block that cannot be parsed, reading resumes at the next ``@``. Since the
broken block swallows the text up to there, a file with a syntax error is never
rewritten: every violation is still reported, none of them as fixable.

**Braces are counted as BibTeX counts them.** A backslash has no special meaning
to the parser: ``\{`` opens a brace and ``\"`` closes a quoted value. A value such
as ``{a \{ b}`` or ``"Schr\"odinger"`` is a syntax error, as it is for BibTeX and
pybtex; write ``{\"o}`` for the umlaut and pair every ``\{`` with a ``\}``.

Encoding and line endings
-------------------------

Files are read and written as UTF-8 unless ``--encoding`` says otherwise. The
output always uses line feeds and ends with exactly one newline, and never starts
with a UTF-8 byte order mark, even with ``--encoding utf-8-sig``. A file with
carriage returns or a byte order mark is therefore reported as not formatted, and
rewritten once.
