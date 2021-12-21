import os
import sys
from typing import Dict, Iterable, List, Optional, Tuple

if sys.version_info >= (3, 8):
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as get_version
else:
    from importlib_metadata import PackageNotFoundError
    from importlib_metadata import version as get_version


def lines_from_file(filename: str) -> List[str]:
    with open(filename) as f:
        return f.read().split("\n")


def read_pip(filename: str) -> List[str]:
    """Return lines in pip file, concatenating included requirement files."""
    lines = lines_from_file(filename)
    for line in lines:
        if line.startswith("-r "):
            orig_dirpath = os.path.dirname(os.path.realpath(filename))
            sub_filename = line.split(" ")[1]
            sub_filepath = os.path.join(orig_dirpath, sub_filename)
            lines.extend(read_pip(sub_filepath))
    return lines


def get_package_versions(lines: Iterable[str]) -> Dict[str, str]:
    """Return a dictionary of package versions."""
    versions = {}
    for line in lines:
        line = line.strip()

        if len(line) == 0 or line.startswith(("#", "-")):
            continue

        if line.startswith("https://"):
            continue

        full_name, version_and_extras = line.split("==", 1)
        # Strip extras
        name = full_name.split("[", 1)[0].lower().replace("_", "-")
        version = version_and_extras.split(" ", 1)[0]
        versions[name] = version

    return versions


def get_mismatches(requirements_file_path: str) -> Dict[str, Tuple[str, Optional[str]]]:
    """Return a dictionary of requirement mismatches."""
    pip_lines = read_pip(requirements_file_path)

    expected = get_package_versions(pip_lines)

    mismatches: Dict[str, Tuple[str, Optional[str]]] = {}
    for name, version in expected.items():
        try:
            actual_version = get_version(name)
        except PackageNotFoundError:
            mismatches[name] = (version, None)
        else:
            if version != actual_version:
                mismatches[name] = (version, actual_version)

    return mismatches


def print_errors(
    errors: List[str],
    pre_text: Optional[str] = None,
    post_text: Optional[str] = None,
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
                    "Package {} is in {} but not in virtualenv".format(
                        name, requirements_file_path
                    )
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
