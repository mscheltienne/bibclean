.. include:: ./links.inc

**bibclean**
============

.. toctree::
   :hidden:

   format.rst
   rules.rst
   configuration.rst
   cli.rst
   bibtex.rst
   changes/index

``bibclean`` is a linter and formatter for BibTeX files. It rewrites a ``.bib``
file into a canonical style and reports what it cannot rewrite, so that a
bibliography stays readable in review and builds without surprises with `pybtex`_
and `sphinxcontrib-bibtex`_.

- one canonical style, described in :doc:`format`;
- thirteen rules, described in :doc:`rules`;
- configuration discovered from ``pyproject.toml``, ``bibclean.toml`` or
  ``.bibclean.toml``, described in :doc:`configuration`;
- comments, ``@string`` macros, ``@preamble`` blocks and unknown entry types are
  preserved, and a block that cannot be parsed is kept verbatim and reported.

Install
-------

.. tab-set::

    .. tab-item:: pip

        .. code-block:: bash

            pip install bibclean

    .. tab-item:: uv

        .. code-block:: bash

            uv tool install bibclean

    .. tab-item:: Source

        .. code-block:: bash

            pip install git+https://github.com/mscheltienne/bibclean

Quick start
-----------

``bibclean check`` reports violations without touching the files, ``bibclean fix``
rewrites them in place. Both accept any number of files.

.. code-block:: bash

    bibclean check doc/*.bib
    bibclean fix doc/references.bib

.. code-block:: text

    doc/references.bib:14:3: strip-field field 'abstract' is not kept for @article [*]
    doc/references.bib:27:1: duplicate-key cite key 'smith2020' is already defined as 'Smith2020' at line 3
    doc/references.bib: file is not formatted, run `bibclean fix` [*]
    Found 3 violations (2 fixable).

The lines marked ``[*]`` are the ones ``bibclean fix`` resolves. See :doc:`cli`
for the options, the exit codes and the output format.

pre-commit
----------

Two `pre-commit`_ hooks are available: ``bibclean-check`` reports and never writes,
``bibclean-fix`` rewrites and exits with a non-zero code when it did.

.. code-block:: yaml

    repos:
      - repo: https://github.com/mscheltienne/bibclean
        rev: 1.0.0
        hooks:
          - id: bibclean-fix

Changelog
---------

The list of changes of each release is in the :doc:`changes/index`.

License
-------

``bibclean`` is licensed under the `MIT license`_. A full copy of the license can
be found `on GitHub <project license_>`_.
