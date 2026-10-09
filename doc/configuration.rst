.. include:: ./links.inc

Configuration
=============

``bibclean`` runs without any configuration. Every option below changes either the
canonical style or the rules, and lives in a TOML table.

Discovery
---------

For each input file, ``bibclean`` walks up from the directory of that file to the
root of the filesystem and stops at the first directory holding one of:

1. ``.bibclean.toml``
2. ``bibclean.toml``
3. ``pyproject.toml`` containing a ``[tool.bibclean]`` table

A dedicated file wins over ``pyproject.toml`` in the same directory. The result is
cached per directory, so a batch of files in one folder walks the tree once, and
two files in different projects each use their own configuration.

In ``pyproject.toml`` the table must be ``[tool.bibclean]``. In a dedicated file,
and in a file passed to ``--config``, the keys may be written either under
``[tool.bibclean]`` or at the top level.

.. code-block:: toml

    # bibclean.toml
    indent = 4
    exclude = ["ignored_entry"]

``-c, --config PATH`` replaces the discovered file for every input, and
``--isolated`` ignores every file and runs with the defaults. The two are mutually
exclusive. ``--ignore`` adds rule names to whichever configuration applies,
including the defaults.

An unknown key, a value of the wrong type and an unknown rule name in ``ignore``
are errors: the run stops with exit code 2 and a message naming the key, with a
suggestion when a known key is close enough.

Options
-------

.. code-block:: toml

    [tool.bibclean]
    # formatting
    indent = 2                   # a positive integer, or "tab"
    align-values = false
    trailing-comma = false
    sort-entries = true
    sort-fields = true           # true | false | ["author", "title", "year"]
    month = "abbreviation"       # "abbreviation" | "name" | "number" | "preserve"

    # linting
    ignore = []                  # rule names disabled everywhere
    exclude = []                 # cite keys exempt from the rules
    exclude-types = []           # entry types exempt from the rules
    strip-fields = true          # master switch of the strip-field rule

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Key
     - Type and default
     - Meaning
   * - ``indent``
     - integer or ``"tab"``, ``2``
     - Indentation of the field lines of an entry.
   * - ``align-values``
     - boolean, ``false``
     - Pad the field names so that the ``=`` signs align inside an entry.
   * - ``trailing-comma``
     - boolean, ``false``
     - Emit a comma after the last field of an entry.
   * - ``sort-entries``
     - boolean, ``true``
     - Sort the entries by cite key, case-insensitively and stably.
   * - ``sort-fields``
     - boolean or array of strings, ``true``
     - ``true`` sorts the fields alphabetically, ``false`` preserves their order,
       an array places those names first, in that order, and sorts the rest
       alphabetically.
   * - ``month``
     - string, ``"abbreviation"``
     - Target form of the ``month`` field: the macro ``feb``, the name
       ``{February}``, the number ``{2}``, or ``"preserve"`` to disable the
       :ref:`rule-month-format` rule.
   * - ``ignore``
     - array of strings, ``[]``
     - Names of the rules that never run. See :doc:`rules`.
   * - ``exclude``
     - array of strings, ``[]``
     - Cite keys exempt from every rule, compared exactly as written. Excluded
       entries are still formatted, and still count as the first occurrence for
       :ref:`rule-duplicate-key` and :ref:`rule-duplicate-doi`.
   * - ``exclude-types``
     - array of strings, ``[]``
     - Entry types exempt from every rule, compared in lower case. Excluded
       entries are still formatted.
   * - ``strip-fields``
     - boolean, ``true``
     - Master switch of the :ref:`rule-strip-field` rule.

Per entry type
--------------

Each entry type has a table listing the fields it requires and the fields it
keeps.

.. code-block:: toml

    [tool.bibclean.article]
    required = ["author", "journal", "title", "year"]
    keep = ["doi", "month", "number", "pages", "url", "volume"]

``required`` drives :ref:`rule-required-field`. A name written with a bar, such as
``"author|editor"``, is satisfied when at least one of the alternatives is
present, and is reported as written when none is.

``keep`` drives :ref:`rule-strip-field`. The effective list always contains the
required names on top of the names listed, and ``doi`` and ``url`` are never
stripped, so a citation keeps its link.

The shipped tables below are the base. A user table overrides ``required`` and
``keep`` independently: a key left out keeps its default. A type that has no
shipped table and no ``keep`` is never stripped; one with no ``required`` has no
required field. Type names and field names are compared in lower case.

Default tables
--------------

.. include:: generated/defaults.inc
