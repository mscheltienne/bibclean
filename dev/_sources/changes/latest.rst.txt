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

    This release is API-breaking. The pre-commit hook ``bibclean-fix`` no longer accepts
    ``--exit-non-zero-on-fix``: remove the ``args`` line from your
    ``.pre-commit-config.yaml`` after ``pre-commit autoupdate``. The hook ``bibclean``
    is renamed ``bibclean-check``.

Enhancements
------------

- New unified command-line interface ``bibclean`` with the sub-commands ``check``,
  ``fix`` and ``sys-info``, built with ``click``.
- Two pre-commit hooks, ``bibclean-check`` and ``bibclean-fix``, running on the
  ``pre-commit``, ``pre-merge-commit``, ``pre-push`` and ``manual`` stages.
- Fewer runtime dependencies: ``numpy``, ``psutil`` and ``toml`` are no longer required
  (``psutil`` is optional and only used by ``bibclean sys-info``).

API and behavior changes
------------------------

- The console scripts ``bibclean-check`` and ``bibclean-sys_info`` are removed; use
  ``bibclean check`` and ``bibclean sys-info``.
- ``bibclean FILE`` becomes ``bibclean fix FILE``. The options ``-o/--output``,
  ``--overwrite`` and ``--exit-non-zero-on-fix`` are removed; the file is always cleaned
  in place.
- The minimum supported Python version is 3.11.
- The package is now versioned from git tags (``setuptools_scm``) and uses a ``src``
  layout.

Authors
-------

* `Mathieu Scheltienne`_
