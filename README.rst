========
pip-lock
========

.. image:: https://img.shields.io/pypi/v/pip-lock.svg
        :target: https://pypi.python.org/pypi/pip-lock

.. image:: https://img.shields.io/travis/YPlan/pip-lock/master.svg
        :target: https://travis-ci.org/YPlan/pip-lock

Check for differences between requirements.txt files and your environment.

At YPlan, we automatically call ``check_requirements()`` during development and testing to provide developers instant
feedback if their environment is out of sync with the current requirements.txt. This ensures that developers do
not experience unexpected behaviour or errors related to out of sync requirements.


Installation
============

Install with **pip**:

.. code-block:: python

    pip install pip-lock

Example usage
=============

.. code-block:: python

    from pip_lock import check_requirements

    # Check requirements and if there are any mismatches, print a message and die with exit code 1
    check_requirements('requirements.txt')


.. code-block:: python

    from pip_lock import get_mismatches

    # Get mismatches as a dictionary of package names to tuples (expected_version, actual_version)
    # e.g. {'django': ('1.10.2', None), 'requests': ('2.11.1', '2.9.2')}
    mismatches = get_mismatches('requirements.txt')


At YPlan, we call ``check_requirements()`` within our Django ``manage.py`` which checks the requirements every time
Django starts or tests are run. We recommend checking the environment to ensure it is not run in a production
environment, to avoid slowing down application startup.

API
===

``check_requirements(requirements_file_path, post_text='')``
------------------------------------------------------------

Exit with exit code 1 and output to stderr if there are mismatches between the environment and requirements file.

``requirements_file_path`` is the path to the ``requirements.txt`` file - we recommend using an absolute file path.

``post_text`` is optional text which is displayed after the stderr message. This can be used to display instructions
on how to update the requirements.

Example:

.. code-block:: python

    check_requirements(
        'requirements.txt',
        post_text='\nRun the following on your host machine: \n\n    vagrant provision\n'
    )

.. code-block:: bash

    There are requirement mismatches with requirements.txt:
        * Package Django has version 1.9.10 but you have version 1.9.0 installed.
        * Package requests has version 2.11.1 but you have version 2.11.0 installed.
        * Package requests-oauthlib is in requirements.txt but not in virtualenv

    Run the following on your host machine:

        vagrant provision

``get_mismatches(requirements_file_path, post_text='')``
--------------------------------------------------------

Return a dictionary of package names to tuples of ``(expected_version, actual_version)`` for mismatched packages.

``requirements_file_path`` is the path to the ``requirements.txt`` file - we recommend using an absolute file path.

Example:

.. code-block:: python

    >>> get_mismatches('requirements.txt')
    {'django': ('1.10.2', '1.9.0'), 'requests': ('2.11.1', '2.9.2'), 'request-oauthlib': ('0.7.0', None)}
