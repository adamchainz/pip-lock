#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re
import sys

from setuptools import setup


def get_version(module_file):
    """
    Return package version as listed in `__version__` in `__init__.py`.
    """
    with open(module_file, 'r') as f:
        init_py = f.read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('pip_lock.py')


if sys.argv[-1] == 'publish':
    if os.system("pip freeze | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("rm -rf .eggs/ build/ dist/")
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload dist/*")
    print("You probably want to also tag the version now:")
    print("  git tag -a v%s -m 'Version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()


setup(
    name='pip-lock',
    version=version,
    description="Check for differences between requirements.txt files and your environment.",
    long_description=readme + '\n\n' + history,
    author="YPlan",
    author_email='aaron@yplanapp.com',
    url='https://github.com/YPlan/pip-lock',
    py_modules=['pip_lock'],
    include_package_data=True,
    license="ISCL",
    zip_safe=False,
    keywords='pip, requirements, YPlan',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
)
