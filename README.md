[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![codecov](https://codecov.io/gh/mscheltienne/bibclean/branch/main/graph/badge.svg?token=RX2lXKFDUn)](https://codecov.io/gh/mscheltienne/bibclean)
[![tests](https://github.com/mscheltienne/bibclean/actions/workflows/pytest.yaml/badge.svg?branch=main)](https://github.com/mscheltienne/bibclean/actions/workflows/pytest.yaml)
[![doc](https://github.com/mscheltienne/bibclean/actions/workflows/doc.yaml/badge.svg?branch=main)](https://github.com/mscheltienne/bibclean/actions/workflows/doc.yaml)
[![PyPI version](https://badge.fury.io/py/bibclean.svg)](https://badge.fury.io/py/bibclean)
[![Downloads](https://static.pepy.tech/badge/bibclean)](https://pepy.tech/project/bibclean)

# bibclean

A simple BibTeX file checker and cleaner, available as a command-line tool and as
pre-commit hooks. The documentation can be found
[here](https://mscheltienne.github.io/bibclean/dev/index.html).

```bash
pip install bibclean
bibclean check doc/references.bib   # exit 1 if the file is not clean
bibclean fix doc/references.bib     # clean it in place
```
