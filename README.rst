========
pip-lock
========

.. image:: https://img.shields.io/pypi/v/pip-lock.svg
        :target: https://pypi.python.org/pypi/pip-lock

.. image:: https://img.shields.io/travis/YPlan/pip-lock/master.svg
        :target: https://travis-ci.org/YPlan/pip-lock

Check for differences between requirements.txt files and your environment.


Install
-------

Install with **pip**:

.. code-block:: python

    pip install pip-lock

Example usage
-------------

.. code-block:: python

    from pip_lock import check_requirements

    # Check requirements and exit with exit code 1 if there are mismatches
    check_requirements('requirements.txt')


.. code-block:: python

    from pip_lock import get_mismatches

    # Get mistmatches as a dictionary of tuples (expected, actual)
    # e.g. {'django': ('1.10.2', None), 'requests': ('2.11.1', '2.9.2')}
    mismatches = get_mismatches('requirements.txt')
