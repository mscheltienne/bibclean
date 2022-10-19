.. include:: ./links.inc

Configuration
=============

``bibclean`` commands can be configured in a TOML file, usually the
``pyproject.toml`` file. The configuration is defined in sections heading
with ``tool.bibclean`` and defines for each
:ref:`entry-type <bibtex:entry-type>`:

- under ``required``, which :ref:`fields <bibtex:fields>` are required when
  checking a BibTex with :func:`~bibclean.check_bib_database`.
- under ``keep``, which :ref:`fields <bibtex:fields>` are kept when cleaning a
  BibTex with :func:`~bibclean.clean_bib_database`.

Default
-------

The default configuration of ``bibclean`` can be found
`here <default config_>`_.

.. code-block:: toml

    [tool.bibclean]
    exclude = []

    [tool.bibclean.article]
    required = [
        'author',
        'journal',
        'title',
        'year',
    ]
    keep = [
        'author',
        'journal',
        'month',
        'number',
        'pages',
        'title',
        'volume',
        'year',
    ]

    [tool.bibclean.book]
    required = [
        'author',
        'publisher',
        'title',
        'year',
    ]
    keep = [
        'author',
        'publisher',
        'title',
        'year',
    ]

Each :ref:`entry-type <bibtex:entry-type>` is defined in its own section. The
configuration of an :ref:`entry-type <bibtex:entry-type>` is complete only when
both ``required`` and ``keep`` are defined for this
:ref:`entry-type <bibtex:entry-type>`.

``bibclean`` will only process the entry-types that are defined in the loaded
configuration. The loaded configuration is either the default configuration, or
a merge between the user-defined and the default configuration.

Example
-------

``exclude`` defines the :ref:`cite-key <bibtex:cite-key>` ignored and
``exclude_type`` defines the :ref:`entry-type <bibtex:entry-type>` ignored.
``required`` defines the :ref:`fields <bibtex:fields>` that any entry of a
given type should have. ``keep`` defines the :ref:`fields <bibtex:fields>` that
are kept when auto-formating entries of a given type. For all parameters, the
TOML configuration uses an array of strings.

Consider the following BibTex file with an entry for ``numpy`` and an entry for
``scipy``:

.. code-block:: bibtex

    @article{virtanen_scipy_2020,
    	title = {{SciPy} 1.0: fundamental algorithms for scientific computing in {Python}},
    	volume = {17},
    	issn = {1548-7091, 1548-7105},
    	shorttitle = {{SciPy} 1.0},
    	url = {http://www.nature.com/articles/s41592-019-0686-2},
    	doi = {10.1038/s41592-019-0686-2},
    	number = {3},
    	urldate = {2022-10-12},
    	journal = {Nature Methods},
    	author = {Virtanen, Pauli and Gommers, Ralf and Oliphant, Travis E. and Haberland, Matt and Reddy, Tyler and Cournapeau, David and Burovski, Evgeni and Peterson, Pearu and Weckesser, Warren and Bright, Jonathan and van der Walt, Stéfan J. and Brett, Matthew and Wilson, Joshua and Millman, K. Jarrod and Mayorov, Nikolay and Nelson, Andrew R. J. and Jones, Eric and Kern, Robert and Larson, Eric and Carey, C J and Polat, İlhan and Feng, Yu and Moore, Eric W. and VanderPlas, Jake and Laxalde, Denis and Perktold, Josef and Cimrman, Robert and Henriksen, Ian and Quintero, E. A. and Harris, Charles R. and Archibald, Anne M. and Ribeiro, Antônio H. and Pedregosa, Fabian and van Mulbregt, Paul and {SciPy 1.0 Contributors} and Vijaykumar, Aditya and Bardelli, Alessandro Pietro and Rothberg, Alex and Hilboll, Andreas and Kloeckner, Andreas and Scopatz, Anthony and Lee, Antony and Rokem, Ariel and Woods, C. Nathan and Fulton, Chad and Masson, Charles and Häggström, Christian and Fitzgerald, Clark and Nicholson, David A. and Hagen, David R. and Pasechnik, Dmitrii V. and Olivetti, Emanuele and Martin, Eric and Wieser, Eric and Silva, Fabrice and Lenders, Felix and Wilhelm, Florian and Young, G. and Price, Gavin A. and Ingold, Gert-Ludwig and Allen, Gregory E. and Lee, Gregory R. and Audren, Hervé and Probst, Irvin and Dietrich, Jörg P. and Silterra, Jacob and Webber, James T and Slavič, Janko and Nothman, Joel and Buchner, Johannes and Kulick, Johannes and Schönberger, Johannes L. and de Miranda Cardoso, José Vinícius and Reimer, Joscha and Harrington, Joseph and Rodríguez, Juan Luis Cano and Nunez-Iglesias, Juan and Kuczynski, Justin and Tritz, Kevin and Thoma, Martin and Newville, Matthew and Kümmerer, Matthias and Bolingbroke, Maximilian and Tartre, Michael and Pak, Mikhail and Smith, Nathaniel J. and Nowaczyk, Nikolai and Shebanov, Nikolay and Pavlyk, Oleksandr and Brodtkorb, Per A. and Lee, Perry and McGibbon, Robert T. and Feldbauer, Roman and Lewis, Sam and Tygier, Sam and Sievert, Scott and Vigna, Sebastiano and Peterson, Stefan and More, Surhud and Pudlik, Tadeusz and Oshima, Takuya and Pingel, Thomas J. and Robitaille, Thomas P. and Spura, Thomas and Jones, Thouis R. and Cera, Tim and Leslie, Tim and Zito, Tiziano and Krauss, Tom and Upadhyay, Utkarsh and Halchenko, Yaroslav O. and Vázquez-Baeza, Yoshiki},
    	month = mar,
    	year = {2020},
    	pages = {261--272},
    	file = {Virtanen et al. - 2020 - SciPy 1.0 fundamental algorithms for scientific c.pdf:C\:\\Users\\Mathieu\\Zotero\\storage\\5ST4PLCB\\Virtanen et al. - 2020 - SciPy 1.0 fundamental algorithms for scientific c.pdf:application/pdf},
    }

    @article{harris_array_2020,
    	title = {Array programming with {NumPy}},
    	volume = {585},
    	issn = {0028-0836, 1476-4687},
    	url = {https://www.nature.com/articles/s41586-020-2649-2},
    	doi = {10.1038/s41586-020-2649-2},
    	number = {7825},
    	urldate = {2022-10-12},
    	journal = {Nature},
    	author = {Harris, Charles R. and Millman, K. Jarrod and van der Walt, Stéfan J. and Gommers, Ralf and Virtanen, Pauli and Cournapeau, David and Wieser, Eric and Taylor, Julian and Berg, Sebastian and Smith, Nathaniel J. and Kern, Robert and Picus, Matti and Hoyer, Stephan and van Kerkwijk, Marten H. and Brett, Matthew and Haldane, Allan and del Río, Jaime Fernández and Wiebe, Mark and Peterson, Pearu and Gérard-Marchant, Pierre and Sheppard, Kevin and Reddy, Tyler and Weckesser, Warren and Abbasi, Hameer and Gohlke, Christoph and Oliphant, Travis E.},
    	month = sep,
    	year = {2020},
    	pages = {357--362},
    	file = {Harris et al. - 2020 - Array programming with NumPy.pdf:C\:\\Users\\Mathieu\\Zotero\\storage\\5H7ZM23G\\Harris et al. - 2020 - Array programming with NumPy.pdf:application/pdf},
    }

Exclude an entry
~~~~~~~~~~~~~~~~

To ignore processing of the entry for ``scipy``, the following TOML
configuration is required:

.. code-block:: toml

    [tool.bibclean]
    exclude = ['virtanen_scipy_2020']

.. note::

    Note that excluded entries will still have their fields sorted
    alphabetically and will still be positioned in an alphabetical order
    in the cleaned BibTex file.

The processing of the BibTex file above with the configuration above results
in:

.. code-block:: bibtex

    @article{harris_array_2020,
     author = {Harris, Charles R. and Millman, K. Jarrod and van der Walt, Stéfan J. and Gommers, Ralf and Virtanen, Pauli and Cournapeau, David and Wieser, Eric and Taylor, Julian and Berg, Sebastian and Smith, Nathaniel J. and Kern, Robert and Picus, Matti and Hoyer, Stephan and van Kerkwijk, Marten H. and Brett, Matthew and Haldane, Allan and del Río, Jaime Fernández and Wiebe, Mark and Peterson, Pearu and Gérard-Marchant, Pierre and Sheppard, Kevin and Reddy, Tyler and Weckesser, Warren and Abbasi, Hameer and Gohlke, Christoph and Oliphant, Travis E.},
     doi = {10.1038/s41586-020-2649-2},
     journal = {Nature},
     month = {September},
     number = {7825},
     pages = {357--362},
     title = {Array programming with {NumPy}},
     volume = {585},
     year = {2020}
    }

    @article{virtanen_scipy_2020,
     author = {Virtanen, Pauli and Gommers, Ralf and Oliphant, Travis E. and Haberland, Matt and Reddy, Tyler and Cournapeau, David and Burovski, Evgeni and Peterson, Pearu and Weckesser, Warren and Bright, Jonathan and van der Walt, Stéfan J. and Brett, Matthew and Wilson, Joshua and Millman, K. Jarrod and Mayorov, Nikolay and Nelson, Andrew R. J. and Jones, Eric and Kern, Robert and Larson, Eric and Carey, C J and Polat, İlhan and Feng, Yu and Moore, Eric W. and VanderPlas, Jake and Laxalde, Denis and Perktold, Josef and Cimrman, Robert and Henriksen, Ian and Quintero, E. A. and Harris, Charles R. and Archibald, Anne M. and Ribeiro, Antônio H. and Pedregosa, Fabian and van Mulbregt, Paul and {SciPy 1.0 Contributors} and Vijaykumar, Aditya and Bardelli, Alessandro Pietro and Rothberg, Alex and Hilboll, Andreas and Kloeckner, Andreas and Scopatz, Anthony and Lee, Antony and Rokem, Ariel and Woods, C. Nathan and Fulton, Chad and Masson, Charles and Häggström, Christian and Fitzgerald, Clark and Nicholson, David A. and Hagen, David R. and Pasechnik, Dmitrii V. and Olivetti, Emanuele and Martin, Eric and Wieser, Eric and Silva, Fabrice and Lenders, Felix and Wilhelm, Florian and Young, G. and Price, Gavin A. and Ingold, Gert-Ludwig and Allen, Gregory E. and Lee, Gregory R. and Audren, Hervé and Probst, Irvin and Dietrich, Jörg P. and Silterra, Jacob and Webber, James T and Slavič, Janko and Nothman, Joel and Buchner, Johannes and Kulick, Johannes and Schönberger, Johannes L. and de Miranda Cardoso, José Vinícius and Reimer, Joscha and Harrington, Joseph and Rodríguez, Juan Luis Cano and Nunez-Iglesias, Juan and Kuczynski, Justin and Tritz, Kevin and Thoma, Martin and Newville, Matthew and Kümmerer, Matthias and Bolingbroke, Maximilian and Tartre, Michael and Pak, Mikhail and Smith, Nathaniel J. and Nowaczyk, Nikolai and Shebanov, Nikolay and Pavlyk, Oleksandr and Brodtkorb, Per A. and Lee, Perry and McGibbon, Robert T. and Feldbauer, Roman and Lewis, Sam and Tygier, Sam and Sievert, Scott and Vigna, Sebastiano and Peterson, Stefan and More, Surhud and Pudlik, Tadeusz and Oshima, Takuya and Pingel, Thomas J. and Robitaille, Thomas P. and Spura, Thomas and Jones, Thouis R. and Cera, Tim and Leslie, Tim and Zito, Tiziano and Krauss, Tom and Upadhyay, Utkarsh and Halchenko, Yaroslav O. and Vázquez-Baeza, Yoshiki},
     doi = {10.1038/s41592-019-0686-2},
     file = {Virtanen et al. - 2020 - SciPy 1.0 fundamental algorithms for scientific c.pdf:C\:\\Users\\Mathieu\\Zotero\\storage\\5ST4PLCB\\Virtanen et al. - 2020 - SciPy 1.0 fundamental algorithms for scientific c.pdf:application/pdf},
     issn = {1548-7091, 1548-7105},
     journal = {Nature Methods},
     month = {March},
     number = {3},
     pages = {261--272},
     shorttitle = {{SciPy} 1.0},
     title = {{SciPy} 1.0: fundamental algorithms for scientific computing in {Python}},
     url = {http://www.nature.com/articles/s41592-019-0686-2},
     urldate = {2022-10-12},
     volume = {17},
     year = {2020}
    }

Set fields to keep
~~~~~~~~~~~~~~~~~~

To set different fields to keep for ``article`` entries, the following TOML
configuration is required:

.. code-block:: toml

    [tool.bibclean.article]
    keep = [
        'author',
        'title',
        'year',
    ]

The processing of the BibTex file above with the configuration above results
in:

.. code-block:: bibtex

    @article{harris_array_2020,
     author = {Harris, Charles R. and Millman, K. Jarrod and van der Walt, Stéfan J. and Gommers, Ralf and Virtanen, Pauli and Cournapeau, David and Wieser, Eric and Taylor, Julian and Berg, Sebastian and Smith, Nathaniel J. and Kern, Robert and Picus, Matti and Hoyer, Stephan and van Kerkwijk, Marten H. and Brett, Matthew and Haldane, Allan and del Río, Jaime Fernández and Wiebe, Mark and Peterson, Pearu and Gérard-Marchant, Pierre and Sheppard, Kevin and Reddy, Tyler and Weckesser, Warren and Abbasi, Hameer and Gohlke, Christoph and Oliphant, Travis E.},
     doi = {10.1038/s41586-020-2649-2},
     title = {Array programming with {NumPy}},
     year = {2020}
    }

    @article{virtanen_scipy_2020,
     author = {Virtanen, Pauli and Gommers, Ralf and Oliphant, Travis E. and Haberland, Matt and Reddy, Tyler and Cournapeau, David and Burovski, Evgeni and Peterson, Pearu and Weckesser, Warren and Bright, Jonathan and van der Walt, Stéfan J. and Brett, Matthew and Wilson, Joshua and Millman, K. Jarrod and Mayorov, Nikolay and Nelson, Andrew R. J. and Jones, Eric and Kern, Robert and Larson, Eric and Carey, C J and Polat, İlhan and Feng, Yu and Moore, Eric W. and VanderPlas, Jake and Laxalde, Denis and Perktold, Josef and Cimrman, Robert and Henriksen, Ian and Quintero, E. A. and Harris, Charles R. and Archibald, Anne M. and Ribeiro, Antônio H. and Pedregosa, Fabian and van Mulbregt, Paul and {SciPy 1.0 Contributors} and Vijaykumar, Aditya and Bardelli, Alessandro Pietro and Rothberg, Alex and Hilboll, Andreas and Kloeckner, Andreas and Scopatz, Anthony and Lee, Antony and Rokem, Ariel and Woods, C. Nathan and Fulton, Chad and Masson, Charles and Häggström, Christian and Fitzgerald, Clark and Nicholson, David A. and Hagen, David R. and Pasechnik, Dmitrii V. and Olivetti, Emanuele and Martin, Eric and Wieser, Eric and Silva, Fabrice and Lenders, Felix and Wilhelm, Florian and Young, G. and Price, Gavin A. and Ingold, Gert-Ludwig and Allen, Gregory E. and Lee, Gregory R. and Audren, Hervé and Probst, Irvin and Dietrich, Jörg P. and Silterra, Jacob and Webber, James T and Slavič, Janko and Nothman, Joel and Buchner, Johannes and Kulick, Johannes and Schönberger, Johannes L. and de Miranda Cardoso, José Vinícius and Reimer, Joscha and Harrington, Joseph and Rodríguez, Juan Luis Cano and Nunez-Iglesias, Juan and Kuczynski, Justin and Tritz, Kevin and Thoma, Martin and Newville, Matthew and Kümmerer, Matthias and Bolingbroke, Maximilian and Tartre, Michael and Pak, Mikhail and Smith, Nathaniel J. and Nowaczyk, Nikolai and Shebanov, Nikolay and Pavlyk, Oleksandr and Brodtkorb, Per A. and Lee, Perry and McGibbon, Robert T. and Feldbauer, Roman and Lewis, Sam and Tygier, Sam and Sievert, Scott and Vigna, Sebastiano and Peterson, Stefan and More, Surhud and Pudlik, Tadeusz and Oshima, Takuya and Pingel, Thomas J. and Robitaille, Thomas P. and Spura, Thomas and Jones, Thouis R. and Cera, Tim and Leslie, Tim and Zito, Tiziano and Krauss, Tom and Upadhyay, Utkarsh and Halchenko, Yaroslav O. and Vázquez-Baeza, Yoshiki},
     doi = {10.1038/s41592-019-0686-2},
     title = {{SciPy} 1.0: fundamental algorithms for scientific computing in {Python}},
     year = {2020}
    }

.. note::

    Note that ``doi`` is preserved. ``bibclean`` was designed with
    ``sphinxcontrib-bibtex`` in mind where a DOI (preferred) or a URL yields
    a cross-ref link to the reference on the build documentation. Thus,
    ``bibclean`` will always keep at least one of those 2 fields if it is
    present.

Enhancement
-----------

Please contact the developer on `GitHub <project github_>`_ to propose
modifications to the :ref:`default TOML configuration <configuration:default>`.
At term, it should include a sensible default for most entry-types.
