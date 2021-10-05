========
pip-lock
========

.. image:: https://img.shields.io/github/workflow/status/adamchainz/pip-lock/CI/main?style=for-the-badge
   :target: https://github.com/adamchainz/pip-lock/actions?workflow=CI

.. image:: https://img.shields.io/pypi/v/pip-lock.svg?style=for-the-badge
   :target: https://pypi.org/project/pip-lock/

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=for-the-badge
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit

Check for differences between requirements.txt files and the current environment.

Installation
============

Install with ``python -m pip install pip-lock``.

Python 3.6 to 3.10 supported.

----

**Working on a Django project?**
Check out my book `Speed Up Your Django Tests <https://gumroad.com/l/suydt>`__ which covers loads of best practices so you can write faster, more accurate tests.

----

Example usage
=============

Call ``pip_lock.check_requirements()`` at your application startup to verify that the current virtual environment matches your requirements file.
This gives instant feedback to developers changing branches etc. who would otherwise experience unexpected behaviour or errors due to out of sync requirements.

In a Django project, it makes sense to add the check inside the ``manage.py`` file, which is the project’s main entrypoint.
You can add a call to ``pip_lock.check_requirements()`` after the first import of Django.
For example:

.. code-block:: python

    #!/usr/bin/env python
    import os
    import sys
    from pathlib import Path


    def main():
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example.settings")

        try:
            from django.core.management import execute_from_command_line
        except ImportError as exc:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            ) from exc

        try:
            import pip_lock
        except ImportError:
            raise ImportError(
                "Couldn't import pip-lock. Are you on the right virtualenv and up "
                + "to date?"
            )

        requirements_path = str(Path(__file__).parent / "requirements.txt")
        pip_lock.check_requirements(
            requirements_path,
            post_text="\nRun the following:\n\npython -m pip install -r requirements.txt\n",
        )

        execute_from_command_line(sys.argv)


    if __name__ == "__main__":
        main()

API
===

``check_requirements(requirements_file_path: str, post_text: str='') -> None``
------------------------------------------------------------------------------

Exit with exit code 1 and output to stderr if there are mismatches between the environment and requirements file.

``requirements_file_path`` is the path to the ``requirements.txt`` file - we recommend using an absolute file path.

``post_text`` is optional text which is displayed after the stderr message. This can be used to display instructions
on how to update the requirements.

Example:

.. code-block:: python

    check_requirements(
        "requirements.txt",
        post_text="\nRun the following on your host machine: \n\n    vagrant provision\n",
    )

.. code-block:: bash

    There are requirement mismatches with requirements.txt:
        * Package Django has version 1.9.10 but you have version 1.9.0 installed.
        * Package requests has version 2.11.1 but you have version 2.11.0 installed.
        * Package requests-oauthlib is in requirements.txt but not in virtualenv

    Run the following on your host machine:

        vagrant provision

``get_mismatches(requirements_file_path: str) -> dict[str, tuple[str, str | None]]``
------------------------------------------------------------------------------------

Return a dictionary of package names to tuples of ``(expected_version, actual_version)`` for mismatched packages.

``requirements_file_path`` is the path to the ``requirements.txt`` file - we recommend using an absolute file path.

Example:

.. code-block:: pycon

    >>> get_mismatches("requirements.txt")
    {'django': ('1.10.2', '1.9.0'), 'requests': ('2.11.1', '2.9.2'), 'request-oauthlib': ('0.7.0', None)}
