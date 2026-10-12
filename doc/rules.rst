.. include:: ./links.inc

Rules
=====

Fourteen rules run over every file, in the order below. The rules repairing a value
run before the rules comparing fields and entries, so that a single ``fix`` merges
the repeats that only become identical once repaired. ``bibclean check`` and
``bibclean fix`` report the same violations; only ``fix`` writes the result.

Reading a rule section
----------------------

``Fix: yes`` means the rule always repairs what it reports, ``Fix: partial`` that
it repairs some cases only, and ``Fix: no`` that the repair needs a human
decision. ``bibclean check`` marks the violations that ``fix`` repairs with
``[*]``.

``Scope`` says what the rule looks at: a whole ``file``, one ``block``, one
``entry``, one ``field`` or one ``value``.

The ``pybtex:`` paragraph of each rule says what `pybtex`_ does with the
construct, which is what a `sphinxcontrib-bibtex`_ documentation build sees.

Turning a rule off
------------------

A rule can be disabled by name, either for a project with ``ignore`` in the
configuration file, or for one run with ``--ignore``:

.. code-block:: toml

    [tool.bibclean]
    ignore = ["strip-field"]

.. code-block:: bash

    bibclean check --ignore strip-field doc/references.bib

Individual entries are exempted from every rule by cite key with ``exclude``, and
whole entry types with ``exclude-types``. Exempted entries are still formatted.
See :doc:`configuration`.

Formatting itself is not a rule and cannot be disabled: a file whose layout
differs from the canonical style is reported once, without a position, by a
``file is not formatted`` line. See :doc:`format`.

.. include:: generated/rules.inc
