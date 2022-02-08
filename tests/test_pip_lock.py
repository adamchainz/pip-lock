from __future__ import annotations

from contextlib import contextmanager
from email.message import EmailMessage
from types import SimpleNamespace
from typing import Generator
from unittest import mock

import pytest

from pip_lock import (
    check_requirements,
    get_installed,
    get_mismatches,
    parse_pip,
    print_errors,
    read_pip,
)


def create_file(tmpdir, name, text):
    t = tmpdir.join(name)
    t.write(text)
    return str(t)


@contextmanager
def mock_get_distributions(versions: dict[str, str]) -> Generator[None, None, None]:
    def fake_get_distributions():
        dists = []
        for name, version in versions.items():
            metadata = EmailMessage()
            metadata["Name"] = name
            dists.append(SimpleNamespace(metadata=metadata, version=version))
        return iter(dists)

    with mock.patch("pip_lock.get_distributions", fake_get_distributions):
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


class TestParsePip:
    def test_version(self):
        assert parse_pip(["package1==1.0", "package2==1.1"]) == {
            "package1": "1.0",
            "package2": "1.1",
        }

    def test_normalize_dashes(self):
        assert parse_pip(["package_one==1.0"]) == {
            "package-one": "1.0",
        }

    def test_normalize_dots(self):
        assert parse_pip(["foo.bar==1.0"]) == {
            "foo-bar": "1.0",
        }

    def test_ignore_empty(self):
        assert parse_pip([""]) == {}

    def test_ignore_comments(self):
        assert parse_pip(["# Comment"]) == {}

    def test_ignore_includes(self):
        assert parse_pip(["-r example.txt"]) == {}

    def test_ignore_arguments(self):
        assert parse_pip(["--find-links file:./wheels"]) == {}

    def test_ignore_urls(self):
        assert parse_pip(["https://www.google.com"]) == {}

    def test_ignore_at_urls(self):
        assert parse_pip(["foo @ git+ssh://example.com"]) == {}


class TestGetInstalled:
    def test_single(self):
        with mock_get_distributions({"package": "1.0.0"}):
            result = get_installed()

        assert result == {"package": "1.0.0"}

    def test_several(self):
        versions = {"package-one": "1.0.0", "package-two": "2.0.0"}
        with mock_get_distributions(versions):
            result = get_installed()

        assert result == {"package-one": "1.0.0", "package-two": "2.0.0"}

    def test_normalize_case(self):
        # importlib.metadata should already lowercase names, but we do so to
        # be sure
        with mock_get_distributions({"Package": "1.0.0"}):
            result = get_installed()

        assert result == {"package": "1.0.0"}

    def test_normalize_underscore(self):
        with mock_get_distributions({"package_one": "1.0.0"}):
            result = get_installed()

        assert result == {"package-one": "1.0.0"}

    def test_normalize_dots(self):
        with mock_get_distributions({"package.one": "1.0.0"}):
            result = get_installed()

        assert result == {"package-one": "1.0.0"}


class TestGetMismatches:
    def test_relative_requirements_file(self, tmpdir):
        create_file(tmpdir, "requirements.txt", "package==1.2")

        with tmpdir.as_cwd(), mock_get_distributions({"package": "1.1"}):
            result = get_mismatches("requirements.txt")

        assert result == {"package": ("1.2", "1.1")}

    def test_version_mismatch(self, tmpdir):
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.2")

        with tmpdir.as_cwd(), mock_get_distributions({"package": "1.1"}):
            result = get_mismatches(requirements_path)

        assert result == {"package": ("1.2", "1.1")}

    def test_missing(self, tmpdir):
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.1")

        with mock_get_distributions({}):
            result = get_mismatches(requirements_path)

        assert result == {"package": ("1.1", None)}

    def test_no_mismatches(self, tmpdir):
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.1")

        with mock_get_distributions({"package": "1.1"}):
            result = get_mismatches(requirements_path)

        assert result == {}

    def test_no_mismatches_case_insensitive(self, tmpdir):
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.1")

        with mock_get_distributions({"Package": "1.1"}):
            result = get_mismatches(requirements_path)

        assert result == {}

    def test_empty(self, tmpdir):
        requirements_path = create_file(tmpdir, "requirements.txt", "")

        with mock_get_distributions({}):
            result = get_mismatches(requirements_path)

        assert result == {}

    def test_package_with_extra(self, tmpdir):
        requirements_path = create_file(
            tmpdir, "requirements.txt", "package[anextra]==1.1"
        )

        with mock_get_distributions({"package": "1.1"}):
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
        with tmpdir.as_cwd(), mock_get_distributions({"package": "1.2"}):
            check_requirements("requirements.txt")
