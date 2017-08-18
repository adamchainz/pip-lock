.. :changelog:

History
=======

Pending release
---------------

* New release notes go here

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
