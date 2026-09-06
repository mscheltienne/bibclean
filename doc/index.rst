.. include:: ./links.inc

**BibClean**
============

.. toctree::
   :hidden:

   bibtex.rst
   cli.rst
   configuration.rst
   api/index
   changes/index

``bibclean`` is a simple auto-formatter for BibTeX files. It was designed to
clean ``.bib`` files provided to sphinx documentation build using
`sphinxcontrib-bibtex`_.

Install
-------

BibClean is available on `Pypi <project pypi_>`_.

.. tab-set::

    .. tab-item:: Pypi

        .. code-block:: bash

            pip install bibclean

    .. tab-item:: Source

        .. code-block:: bash

            pip install git+https://github.com/mscheltienne/bibclean

Usage
-----

BibClean is a single command-line tool, ``bibclean``, with two sub-commands:
:ref:`bibclean fix <cli:bibclean fix>` (auto-format) and
:ref:`bibclean check <cli:bibclean check>` (check in CIs). Both accept ``-c`` or
``--config`` to overwrite the :ref:`default TOML configuration <configuration:default>`
with a different :ref:`TOML configuration <configuration:configuration>`, e.g.
``pyproject.toml``.

.. tab-set::

    .. tab-item:: bibclean fix

        ``bibclean fix`` processes a single file in place. See
        :ref:`here <cli:bibclean fix>` for additional information.

        .. code-block:: bash

            # clean the file references.bib in-place
            bibclean fix references.bib
            # clean the file references.bib with the configuration in pyproject.toml
            bibclean fix references.bib -c pyproject.toml

    .. tab-item:: bibclean check

        ``bibclean check`` exits with the exit-code ``0`` if the file is already
        processed, with the exit-code ``1`` if violations have been found and with the
        exit-code ``2`` if unfixable violations have been found. See
        :ref:`here <cli:bibclean check>` for additional information.

        .. code-block:: bash

            # check if the file references.bib is already processed
            bibclean check references.bib
            # same, with the configuration in pyproject.toml
            bibclean check references.bib -c pyproject.toml

    .. tab-item:: pre-commit

        .. code-block:: yaml

            repos:
              - repo: https://github.com/mscheltienne/bibclean
                rev: 1.0.0
                hooks:
                  - id: bibclean-fix
                    files: doc/references.bib

License
-------

BibClean is licensed under the `MIT license`_.
A full copy of the license can be found `on GitHub <project license_>`_.
