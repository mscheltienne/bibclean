.. include:: ./links.inc

Command-line
============

``bibclean`` is a single command with three sub-commands. ``--help`` on any of
them lists its arguments.

.. code-block:: text

    bibclean --version
    bibclean check    [OPTIONS] FILES...
    bibclean fix      [OPTIONS] FILES...
    bibclean sys-info [--developer]

bibclean check
--------------

``bibclean check`` reads the files, reports every violation and never writes.
It accepts any number of files; a file that cannot be read is reported and the
others are still processed.

.. code-block:: bash

    bibclean check doc/references.bib doc/software.bib

bibclean fix
------------

``bibclean fix`` runs the same analysis, applies every fixable rule, rewrites the
canonical text of the files that changed and reports what is left. A file is
rewritten as soon as its canonical text differs from what is on disk, even when
unfixable violations remain. A file with a syntax error is never rewritten: its
violations are all reported as unfixable until the error is repaired.

.. code-block:: bash

    bibclean fix doc/references.bib

``--diff`` prints the unified diff of what would be written and writes nothing.
The exit code is the same with and without it.

.. code-block:: bash

    bibclean fix --diff doc/references.bib

Options
-------

``check`` and ``fix`` share the following options; ``--diff`` is specific to
``fix``.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Option
     - Meaning
   * - ``-c, --config FILE``
     - Use this TOML file instead of the discovered configuration, for every input
       file. See :doc:`configuration`.
   * - ``--isolated``
     - Ignore every configuration file and run with the defaults. Mutually
       exclusive with ``--config``.
   * - ``--ignore RULE``
     - Disable a rule by name, repeatable. Adds to the ``ignore`` list of the
       configuration that applies.
   * - ``--encoding NAME``
     - Encoding used to read and write the files, ``utf-8`` by default.
   * - ``-q, --quiet``
     - Print only the summary line, not the violations.
   * - ``--diff``
     - ``fix`` only: print the changes instead of applying them.

Exit codes
----------

.. list-table::
   :header-rows: 1
   :widths: 10 45 45

   * - Code
     - ``check``
     - ``fix``
   * - 0
     - No violation, every file is already canonical.
     - Nothing written and no violation left.
   * - 1
     - At least one violation, or a file that is not canonical.
     - At least one file written, or an unfixable violation left.
   * - 2
     - Configuration error, unreadable file, bad encoding or usage error.
     - Same.

A syntax error inside a ``.bib`` file is a violation, not an error: it exits 1, and
``fix`` leaves that file untouched.

Output
------

Every violation is one line on the standard output, sorted by file in the order
the files were given, then by position. A summary line closes the report.

.. code-block:: text

    doc/references.bib:14:3: strip-field field 'abstract' is not kept for @article [*]
    doc/references.bib:27:1: duplicate-key cite key 'smith2020' is already defined as 'Smith2020' at line 3
    doc/references.bib: file is not formatted, run `bibclean fix` [*]
    Found 3 violations (2 fixable).

A positioned line reads ``<path>:<line>:<column>: <rule> <message>``. Field
violations point at the first character of the field name, entry violations at
the ``@`` that opens the entry. A line without a position is about the file as a
whole. The trailing ``[*]`` marks a violation that ``bibclean fix`` resolves.

``bibclean fix`` prints the same lines for the violations it could not resolve,
followed by ``Fixed N violations, wrote M files.``, or ``Would fix N violations,
would write M files.`` with ``--diff``. Paths are printed exactly as they were
typed on the command line; a file named twice is processed once, under its first
spelling.

Nothing is printed when there is nothing to report. Errors go to the error stream.
The output is coloured on a terminal, unless ``NO_COLOR`` is set or ``TERM`` is
``dumb``.

bibclean sys-info
-----------------

``bibclean sys-info`` prints the platform, the Python and the dependency versions,
for bug reports. ``--developer`` adds the development dependency groups, only for
an editable install.

pre-commit
----------

Two `pre-commit`_ hooks are available.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Hook
     - Behaviour
   * - ``bibclean-check``
     - Runs ``bibclean check``, never writes, fails on any violation.
   * - ``bibclean-fix``
     - Runs ``bibclean fix``, rewrites the files and fails when it did.

.. code-block:: yaml

    repos:
      - repo: https://github.com/mscheltienne/bibclean
        rev: 1.0.0
        hooks:
          - id: bibclean-fix
            files: doc/references.bib

Both hooks run on the ``pre-commit``, ``pre-merge-commit``, ``pre-push`` and
``manual`` stages.

GitHub action
-------------

Below is a workflow checking the bibliography of a documentation build.

.. code-block:: yaml

    name: bibclean
    on:
      pull_request:
      push:
        branches: [main]

    jobs:
      check:
        timeout-minutes: 10
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v7
          - uses: astral-sh/setup-uv@v10.3.0
          - run: uvx bibclean check doc/references.bib
