.. include:: ./links.inc

Command-line
============

``bibclean`` is a single command with 3 sub-commands: :ref:`cli:bibclean fix`,
:ref:`cli:bibclean check` and :ref:`cli:bibclean sys-info`. Details about the arguments
of each sub-command can be retrieved with ``--help``.

.. note::

    Each sub-command processes exactly one ``.bib`` file per invocation in this
    version. Support for several files in one call is planned for the next release.

bibclean fix
------------

``bibclean fix`` processes a single ``.bib`` file in place: it checks it with
:func:`bibclean.check_bib_database` and cleans it with
:func:`bibclean.clean_bib_database`.

.. code-block:: bash

    Usage: bibclean fix [OPTIONS] FILE

      Check and clean a .bib file in place.

    Options:
      -c, --config PATH  Path to the TOML configuration.
      --encoding TEXT    Encoding of the .bib file.  [default: utf-8]
      --help             Show this message and exit.

To clean the file ``bib/references.bib`` in place, use:

.. code-block:: bash

    bibclean fix bib/references.bib

The :ref:`default TOML configuration <configuration:default>` can be overwritten with
``-c`` or ``--config``:

.. code-block:: bash

    bibclean fix bib/references.bib --config pyproject.toml

Exit codes: ``0`` on success, ``2`` if unfixable violations were found (duplicate
entries, missing required fields; the file is left untouched), ``3`` if the file or the
configuration is invalid, ``4`` if the cleaned file could not be written.

bibclean check
--------------

``bibclean check`` is designed for use in CIs. It will exit with the code ``0`` if the
provided ``.bib`` file is already processed, with the exit code ``1`` if a violation has
been found, with the exit code ``2`` if an unfixable violation has been found, and with
the exit code ``3`` if the provided configuration/paths are invalid.

.. code-block:: bash

    Usage: bibclean check [OPTIONS] FILE

      Check that a .bib file is already processed.

    Options:
      -c, --config PATH  Path to the TOML configuration.
      --help             Show this message and exit.

bibclean sys-info
-----------------

``bibclean sys-info`` prints the platform, Python and dependency versions, for bug
reports. ``--developer`` adds the development dependency groups (editable install only).

pre-commit
----------

Two hooks are provided: ``bibclean-check`` (read-only) and ``bibclean-fix`` (rewrites
the file). The example below runs the fixer on the bibliography of a sphinx build:

.. code-block:: yaml

    repos:
      - repo: https://github.com/mscheltienne/bibclean
        rev: 1.0.0
        hooks:
          - id: bibclean-fix
            files: doc/references.bib

GitHub action CI
~~~~~~~~~~~~~~~~

Below is an example of GitHub action workflow configuration to confirm that the file
``doc/references.bib`` used by a sphinx documentation build is cleaned.

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
          - uses: astral-sh/setup-uv@v7
          - run: uvx bibclean check doc/references.bib
