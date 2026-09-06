.. NOTE: we use cross-references to highlight new functions and classes.
   Please follow the examples below, so the changelog page will have a link to
   the function/class documentation.

.. NOTE: there are 3 separate sections for changes, based on type:
   - "Enhancements" for new features
   - "Bugs" for bug fixes
   - "API changes" for backward-incompatible changes

.. NOTE: You can use the :pr:`xx` and :issue:`xx` role to x-ref to a GitHub PR
   or issue from this project.

.. include:: ./authors.inc

.. _latest:

Version 1.0
===========

.. warning::

   The hook ``bibclean-fix`` no longer accepts ``--exit-non-zero-on-fix``: exiting
   with a non-zero code after writing a file is now the default. A
   ``.pre-commit-config.yaml`` pinning ``rev: 0.8.0`` with
   ``args: [--exit-non-zero-on-fix]`` fails with a usage error after
   ``pre-commit autoupdate`` until the ``args`` line is removed. The check hook is
   renamed from ``bibclean`` to ``bibclean-check``.

bibclean 1.0 is a rewrite. It is a linter and formatter for BibTeX files, with its
own lossless parser, a canonical format, thirteen rules and automatic
configuration discovery. There is no public Python API.

Enhancements
------------

- New ``bibclean check`` and ``bibclean fix`` commands, accepting any number of
  files. A file that cannot be read is reported and the batch continues.
- Files are parsed by ``bibclean`` itself. Comments, ``@string`` macros,
  ``@preamble`` blocks and unknown entry types are preserved, and a block that
  cannot be parsed is kept verbatim and reported at its position.
- One canonical format, with a two-space indent, braced values, sorted entries and
  sorted fields, described in :doc:`../format`.
- Thirteen rules, each disabled by name with ``ignore`` or ``--ignore``, described
  in :doc:`../rules`: :ref:`rule-syntax-error`, :ref:`rule-duplicate-key`,
  :ref:`rule-duplicate-doi`, :ref:`rule-duplicate-field`, :ref:`rule-empty-field`,
  :ref:`rule-strip-field`, :ref:`rule-url-with-doi`, :ref:`rule-doi-prefix`,
  :ref:`rule-month-format`, :ref:`rule-pages-range`,
  :ref:`rule-unescaped-percent`, :ref:`rule-undefined-string` and
  :ref:`rule-required-field`.
- The configuration is discovered from ``pyproject.toml``, ``bibclean.toml`` or
  ``.bibclean.toml`` next to the files, described in :doc:`../configuration`.
  ``--config`` overrides it and ``--isolated`` ignores it.
- New options ``--diff``, ``--ignore``, ``--isolated``, ``--verbose`` and
  ``--quiet``. Violations are reported one per line with their position, followed
  by a summary line, in colour on a terminal and honouring ``NO_COLOR``.
- Two pre-commit hooks, ``bibclean-check`` and ``bibclean-fix``, running on the
  ``pre-commit``, ``pre-merge-commit``, ``pre-push`` and ``manual`` stages.
- Faster startup: the runtime dependencies are ``click`` and ``packaging``.
  ``bibtexparser``, ``numpy`` and ``toml`` are gone, and ``psutil`` is optional and
  used by ``bibclean sys-info`` only.

Bugs
----

- ``--exit-non-zero-on-fix`` never fired, because it compared a value with itself.
  Exiting with a non-zero code after writing a file is now the default behaviour.
- Non-standard entry types such as ``@software`` and ``@online``, ``@string``
  macros, ``@preamble`` blocks and comments were dropped or inlined; they are now
  preserved.

API and behavior changes
------------------------

- The hook ``bibclean`` is renamed ``bibclean-check``, and the hook
  ``bibclean-fix`` no longer takes ``--exit-non-zero-on-fix``.
- ``bibclean FILE [-o OUT] [--overwrite] [-c CFG] [--exit-non-zero-on-fix]``
  becomes ``bibclean fix FILES... [-c CFG] [--diff]``; the files are always
  rewritten in place.
- ``bibclean-check FILE`` becomes ``bibclean check FILES...`` and
  ``bibclean-sys_info`` becomes ``bibclean sys-info``. The console scripts
  ``bibclean-check`` and ``bibclean-sys_info`` are removed.
- Exit codes are now 0 for a clean run, 1 for a violation or a written file, and 2
  for a configuration error, an unreadable file or a usage error. A syntax error
  in a ``.bib`` file exits 1, not 2.
- The configuration key ``exclude_type`` is renamed ``exclude-types``, and the
  configuration is discovered instead of requiring ``-c``.
- The Python API ``check_bib_database``, ``clean_bib_database``, ``load_bib`` and
  ``save_bib`` is removed.
- Entries are written with a two-space indent instead of one space, and months
  with the macro ``feb`` instead of ``{February}``. The first ``bibclean fix``
  after upgrading therefore rewrites the whole file once.
- The minimum supported Python version is 3.11.

Authors
-------

* `Mathieu Scheltienne`_
