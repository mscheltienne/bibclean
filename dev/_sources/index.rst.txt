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

``bibclean`` is a simple auto-formater for BibTex file. It was designed to
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

BibClean can be used from 2 CLI entry-points: :ref:`cli:bibclean` (to
auto-format) and :ref:`cli:bibclean-check` (to check in CIs). Both entry-points
can be configured with the ``-c`` or ``--config`` flag which overwrite the
:ref:`default TOML configuration <configuration:default>` with a different
:ref:`TOML configuration <configuration:configuration>`, e.g.
``pyproject.toml``.

.. tab-set::

    .. tab-item:: bibclean

        ``bibclean`` process a single file. See :ref:`here <cli:bibclean>` for
        additional information.

        .. code-block:: bash

            # clean the file references.bib in-place
            bibclean references.bib
            # clean the file references.bib and output in references-clean.bib
            bibclean references.bib -o references-clean.bib
            # clean the file references.bib in-place with the configuration in pyproject.toml
            bibclean references.bib -c pyproject.toml

    .. tab-item:: bibclean-check

        ``bibclean-check`` exits with the exit-code ``0`` if the file is
        already processed, with the exit-code ``1`` if violations have been
        found and with the exit-code ``2`` if the configuration or the paths
        are invalid. See :ref:`here <cli:bibclean-check>` for additional
        information.

        .. code-block:: bash

            # check if the file references.bib is already processed
            bibclean-check references.bib

License
-------

BibClean is licensed under the `MIT license`_.
A full copy of the license can be found `on GitHub <project license_>`_.
