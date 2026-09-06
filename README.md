[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/mscheltienne/bibclean/branch/main/graph/badge.svg?token=RX2lXKFDUn)](https://codecov.io/gh/mscheltienne/bibclean)
[![tests](https://github.com/mscheltienne/bibclean/actions/workflows/pytest.yaml/badge.svg?branch=main)](https://github.com/mscheltienne/bibclean/actions/workflows/pytest.yaml)
[![doc](https://github.com/mscheltienne/bibclean/actions/workflows/doc.yaml/badge.svg?branch=main)](https://github.com/mscheltienne/bibclean/actions/workflows/doc.yaml)
[![PyPI version](https://badge.fury.io/py/bibclean.svg)](https://badge.fury.io/py/bibclean)
[![Downloads](https://static.pepy.tech/badge/bibclean)](https://pepy.tech/project/bibclean)

# bibclean

A linter and formatter for BibTeX files, available as a command-line tool and as
pre-commit hooks. It rewrites a `.bib` file into a canonical style and reports what
it cannot rewrite, so that a bibliography stays readable in review and builds
without surprises with pybtex and sphinxcontrib-bibtex. Comments, `@string` macros,
`@preamble` blocks and unknown entry types are preserved, and a block that cannot
be parsed is kept verbatim and reported.

```bash
pip install bibclean
bibclean check doc/references.bib   # report violations, never write
bibclean fix doc/references.bib     # rewrite it in place
```

```
doc/references.bib:14:3: strip-field field 'abstract' is not kept for @article [*]
doc/references.bib:27:1: duplicate-key cite key 'smith2020' is already defined as 'Smith2020' at line 3
doc/references.bib: file is not formatted, run `bibclean fix` [*]
Found 3 violations (2 fixable).
```

Two pre-commit hooks are available: `bibclean-check` reports and never writes,
`bibclean-fix` rewrites and fails when it did.

```yaml
repos:
  - repo: https://github.com/mscheltienne/bibclean
    rev: 1.0.0
    hooks:
      - id: bibclean-fix
```

The documentation, including the canonical format, the thirteen rules and the
configuration reference, is available
[here](https://mscheltienne.github.io/bibclean/dev/index.html).
