.. include:: ./links.inc

Command-lines
=============

``bibclean`` has 2 CLI entry-points: :ref:`cli:bibclean` and
:ref:`cli:bibclean-check`.

bibclean
--------

``bibclean`` process a single ``.bib`` file, checks it with
:func:`bibclean.check_bib_database` and cleans it with
:func:`bibclean.clean_bib_database`.
Details about the arguments can be retrieved with ``bibclean --help``.

.. code-block:: bash

    usage: bibclean [-h] [-o path] [-e str] [--overwrite] [-c path] path

    cleans a .bib file.

    positional arguments:
      path                     path to the .bib file to clean. If an output is not provided, this file is overwritten.

    optional arguments:
      -h, --help               show this help message and exit
      -o path, --output path   path to the output .bib file.
      -e str, --encoding str   encoding of the .bib file.
      --overwrite              overwrite the file provided in --output if it exists.
      -c path, --config path   path to the TOML configuration.

To clean the file ``bib/references.bib`` in place, use:

.. code-block:: bash

    bibclean bib/references.bib

To prevent overwriting the existing file, an output path must be provided:

.. code-block:: bash

    bibclean bib/references.bib --output bib/references-clean.bib

The :ref:`default TOML configuration <configuration:default>`.
can be overwritten with ``-c`` or ``--config``:

.. code-block:: bash

    bibclean bib/references.bib --config pyproject.toml

bibclean-check
--------------

``bibclean-check`` is designed for use in CIs. It will exit with the code ``0``
if the provided ``.bib`` file is already processed, with the exit code ``1`` if
a violation has been found, and with the exit code ``2`` if the provided
configuration/paths are invalid.
Details about the arguments can be retrieved with ``bibclean-check --help``.

.. code-block:: bash

    usage: bibclean-check [-h] [-c path] path

    confirms that a .bib file is processed.

    positional arguments:
      path                     path to the .bib file to clean. If an output is not provided, this file is overwritten.

    optional arguments:
      -h, --help               show this help message and exit
      -c path, --config path   path to the TOML configuration.

GitHub action CI
~~~~~~~~~~~~~~~~

Below is an example of GitHub action workflow configuration to confirm
that the file ``doc/references.bib`` used by a sphinx documentation build is
cleaned.

.. code-block:: yaml

    name: code-style
    concurrency:
      group: ${{ github.workflow }}-${{ github.event.number }}-${{ github.event.ref }}
      cancel-in-progress: true
    on:
      push:
        branches: [main]

    jobs:
      style:
        timeout-minutes: 10
        runs-on: ubuntu-latest
        steps:
          - name: Checkout repository
            uses: actions/checkout@v3
          - name: Setup Python 3.9
            uses: actions/setup-python@v4
            with:
              python-version: '3.9'
              architecture: 'x64'
          - name: Install dependencies
            run: |
              python -m pip install --progress-bar off --upgrade pip setuptools wheel
              python -m pip install --progress-bar off bibclean
              python -m pip install --progress-bar off .
          - name: Run bibclean
            run: bibclean-check doc/references.bib
