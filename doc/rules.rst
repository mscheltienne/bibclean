.. include:: ./links.inc

Rules
=====

Thirteen rules run over every file, always in the order below. Each one reports
what it found and, when it can, repairs the model before the next rule sees it.
``bibclean check`` and ``bibclean fix`` run exactly the same pipeline, so both
report the same violations; only ``fix`` writes the result.

Reading a rule section
----------------------

``Fix: yes`` means the rule always repairs what it reports, ``Fix: partial`` that
it repairs some cases only, and ``Fix: no`` that the repair needs a human
decision. A violation that was repaired is marked ``[*]`` in the output, and is
counted by the summary line of ``bibclean fix``.

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
