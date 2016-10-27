# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys

from pip.operations.freeze import freeze as pip_freeze

__version__ = '1.0.0'


def lines_from_file(filename):
    with open(filename) as f:
        return f.read().split("\n")


def read_pip(filename):
    """Return lines in pip file, concatenating included requirement files."""
    lines = lines_from_file(filename)
    for line in lines:
        if line.startswith('-r '):
            orig_dirpath = os.path.dirname(os.path.realpath(filename))
            sub_filename = line.split(' ')[1]
            sub_filepath = os.path.join(orig_dirpath, sub_filename)
            lines.extend(read_pip(sub_filepath))
    return lines


def get_package_versions(lines):
    """Return a dictionary of package versions."""
    versions = {}
    for line in lines:
        line = line.strip()

        if len(line) == 0 or line.startswith('#') or line.startswith('-r '):
            continue

        if line.startswith('https://'):
            continue

        name, version_plus = line.split('==', 1)
        versions[name] = version_plus.split(' ', 1)[0]

    return versions


def get_mismatches(requirements_file):
    """Return a dictionary of requirement mismatches."""
    requirements_path = os.path.join(os.path.dirname(__file__), requirements_file)
    pip_lines = read_pip(requirements_path)

    expected = get_package_versions(pip_lines)
    actual = get_package_versions(pip_freeze())

    mismatches = {}
    for name, version in expected.items():
        if name not in actual:
            mismatches[name] = (version, None)
            continue

        if version != actual[name]:
            mismatches[name] = (version, actual[name])

    return mismatches


def print_errors(errors, pre_text=None, post_text=None):
    """Print list of errors to stderr with optional pre_text and post_text."""
    sys.stderr.write("\033[91m")  # red text
    if pre_text:
        sys.stderr.write(pre_text + "\n")
    for message in errors:
        sys.stderr.write("        * {0}\n".format(message))
    if post_text:
        sys.stderr.write(post_text)
    sys.stderr.write("\033[0m")


def check_requirements(requirements_file, post_text=None):
    """Print errors and exit program if there are mismatches with the requirements file."""
    mismatches = get_mismatches(requirements_file)
    if mismatches:
        errors = []
        for name, (expected, actual) in mismatches.items():
            if actual is None:
                errors.append("Package {0} is in {1} but not in virtualenv".format(name, requirements_file))
                continue

            if expected != actual:
                errors.append(
                    "Package {0} has version {1} but you have version {2} installed.".format(
                        name,
                        expected,
                        actual,
                    )
                )

        print_errors(
            errors,
            "There are requirement mistmatches with {0}".format(requirements_file),
            post_text,
        )
        sys.exit(1)
