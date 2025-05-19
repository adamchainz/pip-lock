from __future__ import annotations

import os
import re
import sys
from collections.abc import Iterable
from importlib.metadata import distributions as get_distributions


def read_pip(filename: str) -> list[str]:
    """Return lines in pip file, concatenating included requirement files."""
    with open(filename) as f:
        lines = [line.strip() for line in f.readlines()]
    for line in lines:
        if line.startswith("-r "):
            orig_dirpath = os.path.dirname(os.path.realpath(filename))
            sub_filename = line.split(" ")[1]
            sub_filepath = os.path.join(orig_dirpath, sub_filename)
            lines.extend(read_pip(sub_filepath))
    return lines


VCS_RE = re.compile(r"(|[^ ]+ @ )[\w+]+://")


def parse_pip(lines: Iterable[str]) -> dict[str, str]:
    """Return a dictionary of package versions."""
    versions = {}
    for line in lines:
        line = line.strip()

        if len(line) == 0 or line.startswith(("#", "-")):
            continue

        if line.startswith(("http://", "https://")):
            continue

        if VCS_RE.match(line):
            continue

        full_name, version_and_extras = line.split("==", 1)
        # Strip extras and normalize
        name = normalize_name(full_name.split("[", 1)[0])
        version = version_and_extras.split(" ", 1)[0]
        versions[name] = version

    return versions


def get_installed() -> dict[str, str]:
    return {normalize_name(d.metadata["Name"]): d.version for d in get_distributions()}


def normalize_name(name: str) -> str:
    return name.lower().replace("_", "-").replace(".", "-")


def get_mismatches(requirements_file_path: str) -> dict[str, tuple[str, str | None]]:
    """Return a dictionary of requirement mismatches."""
    pip_lines = read_pip(requirements_file_path)
    expected = parse_pip(pip_lines)
    installed = get_installed()

    mismatches: dict[str, tuple[str, str | None]] = {}
    for name, expected_version in expected.items():
        installed_version = installed.get(name)
        if installed_version is None:
            mismatches[name] = (expected_version, None)
        elif installed_version != expected_version:
            mismatches[name] = (expected_version, installed_version)

    return mismatches


def print_errors(
    errors: list[str],
    pre_text: str | None = None,
    post_text: str | None = None,
) -> None:
    """Print list of errors to stderr with optional pre_text and post_text."""
    sys.stderr.write("\033[91m")  # red text
    if pre_text:
        sys.stderr.write(pre_text + "\n")
    for message in errors:
        sys.stderr.write(f"    * {message}\n")
    if post_text:
        sys.stderr.write(post_text)
    sys.stderr.write("\033[0m")


def check_requirements(requirements_file_path: str, post_text: str = "") -> None:
    """
    Print errors and exit program if there are mismatches with the requirements
    file.
    """
    mismatches = get_mismatches(requirements_file_path)
    if mismatches:
        errors = []
        for name, (expected, actual) in mismatches.items():
            if actual is None:
                errors.append(
                    f"Package {name} is in {requirements_file_path} but not in virtualenv"
                )
                continue

            if expected != actual:
                msg = (
                    "Package {0} has version {1} but you have version {2} "
                    + "installed."
                ).format(name, expected, actual)
                errors.append(msg)

        print_errors(
            errors,
            f"There are requirement mismatches with {requirements_file_path}",
            post_text,
        )
        sys.exit(1)
