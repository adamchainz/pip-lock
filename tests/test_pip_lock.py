import sys
from contextlib import contextmanager
from typing import Dict, Generator
from unittest import mock

import pytest

from pip_lock import (
    check_requirements,
    get_mismatches,
    get_package_versions,
    print_errors,
    read_pip,
)

if sys.version_info >= (3, 8):
    from importlib.metadata import PackageNotFoundError
else:
    from importlib_metadata import PackageNotFoundError


def create_file(tmpdir, name, text):
    t = tmpdir.join(name)
    t.write(text)
    return str(t)


@contextmanager
def mock_get_version(versions: Dict[str, str]) -> Generator[None, None, None]:
    # importlib.metadata.version is case insensitive, so duplicate that here
    versions = {name.lower(): version for name, version in versions.items()}

    def fake_get_version(name: str) -> str:
        try:
            return versions[name.lower()]
        except KeyError:
            raise PackageNotFoundError from None

    with mock.patch("pip_lock.get_version", fake_get_version):
        yield


class TestReadPip:
    def test_read(self, tmpdir):
        path = create_file(tmpdir, "requirements.txt", "package1==1.0\npackage2==1.1")
        assert read_pip(path) == ["package1==1.0", "package2==1.1"]

    def test_include(self, tmpdir):
        inc_path = create_file(tmpdir, "requirements_inc.txt", "other-package==1.0")
        path = create_file(tmpdir, "requirements.txt", f"-r {inc_path}")

        assert read_pip(path) == [f"-r {inc_path}", "other-package==1.0"]

    def test_empty(self, tmpdir):
        path = create_file(tmpdir, "requirements.txt", "")
        assert read_pip(path) == [""]


class TestGetPackageVersion:
    def test_version(self):
        assert get_package_versions(["package1==1.0", "package2==1.1"]) == {
            "package1": "1.0",
            "package2": "1.1",
        }

    def test_normalize_dashes(self):
        assert get_package_versions(["package_1==1.0"]) == {
            "package-1": "1.0",
        }

    def test_ignore_empty(self):
        assert get_package_versions([""]) == {}

    def test_ignore_comments(self):
        assert get_package_versions(["# Comment"]) == {}

    def test_ignore_includes(self):
        assert get_package_versions(["-r example.txt"]) == {}

    def test_ignore_arguments(self):
        assert get_package_versions(["--find-links file:./wheels"]) == {}

    def test_ignore_urls(self):
        assert get_package_versions(["https://www.google.com"]) == {}


class TestGetMismatches:
    def test_relative_requirements_file(self, tmpdir):
        create_file(tmpdir, "requirements.txt", "package==1.2")

        with tmpdir.as_cwd(), mock_get_version({"package": "1.1"}):
            result = get_mismatches("requirements.txt")

        assert result == {"package": ("1.2", "1.1")}

    def test_version_mismatch(self, tmpdir):
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.2")

        with tmpdir.as_cwd(), mock_get_version({"package": "1.1"}):
            result = get_mismatches(requirements_path)

        assert result == {"package": ("1.2", "1.1")}

    def test_missing(self, tmpdir):
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.1")

        with mock_get_version({}):
            result = get_mismatches(requirements_path)

        assert result == {"package": ("1.1", None)}

    def test_no_mismatches(self, tmpdir):
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.1")

        with mock_get_version({"package": "1.1"}):
            result = get_mismatches(requirements_path)

        assert result == {}

    def test_no_mismatches_case_insensitive(self, tmpdir):
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.1")

        with mock_get_version({"Package": "1.1"}):
            result = get_mismatches(requirements_path)

        assert result == {}

    def test_empty(self, tmpdir):
        requirements_path = create_file(tmpdir, "requirements.txt", "")

        with mock_get_version({}):
            result = get_mismatches(requirements_path)

        assert result == {}

    def test_package_with_extra(self, tmpdir):
        requirements_path = create_file(
            tmpdir, "requirements.txt", "package[anextra]==1.1"
        )

        with mock_get_version({"package": "1.1"}):
            result = get_mismatches(requirements_path)

        assert result == {}


class TestPrintErrors:
    def test_errors(self, capsys):
        print_errors(["error message 1", "error message 2"])
        _, err = capsys.readouterr()
        assert "error message 1" in err
        assert "error message 2" in err

    def test_pre_post_text(self, capsys):
        print_errors(["error message"], "pre text", "post text")
        _, err = capsys.readouterr()
        assert "error message" in err
        assert "pre text" in err
        assert "post text" in err


class TestCheckRequirements:
    @mock.patch("pip_lock.get_mismatches")
    def test_no_mismatches(self, get_mismatches):
        get_mismatches.return_value = {}
        check_requirements("requirements.txt")

    @mock.patch("pip_lock.get_mismatches")
    def test_mismatches(self, get_mismatches, capsys):
        get_mismatches.return_value = {
            "package1": ("1.1", "1.0"),
            "package2": ("1.0", None),
        }
        with pytest.raises(SystemExit):
            check_requirements("requirements.txt")

        _, err = capsys.readouterr()
        assert "package1 has version 1.1 but you have version 1.0 installed" in err
        assert "package2 is in requirements.txt but not in virtualenv" in err

    def test_relative_requirements_file(self, tmpdir):
        create_file(tmpdir, "requirements.txt", "package==1.2")
        with tmpdir.as_cwd(), mock_get_version({"package": "1.2"}):
            check_requirements("requirements.txt")
