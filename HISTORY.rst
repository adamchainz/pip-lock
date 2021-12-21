=======
History
=======

2.6.0 (2021-12-21)
------------------

* Make the package much faster by using ``importlib.metadata`` to get installed
  versions, rather than ``pip freeze``. This saves most of the import time
  (local benchmark: 200ms down to 10ms) and halves the run time (230ms to
  100ms).

2.5.0 (2021-10-05)
------------------

* Support Python 3.10.

2.4.0 (2021-08-13)
------------------

* Add type hints.

2.3.0 (2021-07-25)
------------------

* Normalize package names from underscores to hyphens, just like pip does.

* Stop distributing tests to reduce package size. Tests are not intended to be
  run outside of the tox setup in the repository. Repackagers can use GitHub's
  tarballs per tag.

2.2.1 (2021-01-22)
------------------

* Fix to ignore lines that represent arguments to pip, such as
  ``--find-links``.

2.2.0 (2020-12-13)
------------------

* Drop Python 3.5 support.
* Support Python 3.9.
* Move license from ISC to MIT License.

2.1.1 (2020-08-11)
------------------

* Fix to ignore packages installed directly from wheels, for example pip itself
  on Heroku, which will output its location in ``pip freeze`` as
  ``pip @ file:///tmp/pip-20.1.1-py2.py3-none-any.whl``.

2.1.0 (2019-12-19)
------------------

* Update Python support to 3.5-3.8, as 3.4 has reached its end of life.
* Converted setuptools metadata to configuration file. This meant removing the
  ``__version__`` attribute from the package. If you want to inspect the
  installed version, use
  ``importlib.metadata.version("pip-lock")``
  (`docs <https://docs.python.org/3.8/library/importlib.metadata.html#distribution-versions>`__ /
  `backport <https://pypi.org/project/importlib-metadata/>`__).
* Fix parsing of package names featuring extras e.g. ``package[extra1]``.
* Require Pip 10+.

2.0.0 (2019-02-28)
------------------

* Drop Python 2 support, only Python 3.4+ is supported now.

1.2.0 (2018-07-25)
------------------

* Ignore installed external (``-e``) packages.

1.1.1 (2018-04-15)
------------------

* Fix for pip 10 move of import to ``pip._internal``

1.1.0 (2016-08-18)
------------------

* Remove logic that made relative file paths relative to the path of the
  calling code's file. It's now the standard behaviour of relative to the
  current working directory. Passing an absolute path is recommended.
* Make comparison of package names case-insensitive to work with
  ``requirements.txt`` files that use a different case to the canoncial package
  name. This can happen with ``pip-compile`` that always outputs lowercase
  names.
* Fix 'mismatches' typo
* Only indent mismatch list by 4 spaces in error message

1.0.2 (2016-10-28)
------------------

* Fix relative paths for all environments

1.0.1 (2016-10-28)
------------------

* Support relative requirements.txt paths

1.0.0 (2016-10-27)
------------------

* First release on PyPI.
