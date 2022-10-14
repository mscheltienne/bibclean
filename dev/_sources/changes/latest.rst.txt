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

Version 0.4
===========

Enhancements
------------

- Add support for configuration via ``pyproject.toml`` in the sections ``'tool.bibclean.entry_type'``

Bugs
----

- Fix exit code returned by ``bibclean-check`` when a duplicate is found

API and behavior changes
------------------------

- Replace ``.ini`` configuration file with TOML

Authors
-------

* `Mathieu Scheltienne`_
