[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![codecov](https://codecov.io/gh/mscheltienne/bibclean/branch/main/graph/badge.svg?token=RX2lXKFDUn)](https://codecov.io/gh/mscheltienne/bibclean)
[![tests](https://github.com/mscheltienne/bibclean/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/mscheltienne/bibclean/actions/workflows/pytest.yml)
[![build](https://github.com/mscheltienne/bibclean/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/mscheltienne/bibclean/actions/workflows/build.yml)
[![doc](https://github.com/mscheltienne/bibclean/actions/workflows/doc.yml/badge.svg?branch=main)](https://github.com/mscheltienne/bibclean/actions/workflows/doc.yml)
[![PyPI version](https://badge.fury.io/py/bibclean.svg)](https://badge.fury.io/py/bibclean)
[![Downloads](https://pepy.tech/badge/bibclean)](https://pepy.tech/project/bibclean)

# BibClean

A simple BibTex file checker and cleaner. It focuses on ``article`` entries and
on ``.bib`` files which will be fed to ``sphinxcontrib-bibtex``.

After installation via ``pip``, it can be used via CLI:

```
# to list the arguments
bibclean --help
# to clean in-place
bibclean references.bib
# to clean and output in a different file
bibclean references.bib -o references-clean.bib
```
