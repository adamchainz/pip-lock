from __future__ import annotations

from contextlib import contextmanager
from email.message import EmailMessage
from types import SimpleNamespace
from typing import Generator
from unittest import mock

import pytest

from pip_lock import check_requirements
from pip_lock import get_installed
from pip_lock import get_mismatches
from pip_lock import parse_pip
from pip_lock import print_errors
from pip_lock import read_pip


@contextmanager
def mock_get_distributions(versions: dict[str, str]) -> Generator[None]:
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
    def test_read(self, tmp_path):
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("package1==1.0\npackage2==1.1\n")
        assert read_pip(str(requirements)) == ["package1==1.0", "package2==1.1"]

    def test_include(self, tmp_path):
        requirements_inc = tmp_path / "requirements_inc.txt"
        requirements_inc.write_text("other-package==1.0\n")
        requirements = tmp_path / "requirements.txt"
        requirements.write_text(f"-r {requirements_inc}\n")

        assert read_pip(str(requirements)) == [
            f"-r {requirements_inc}",
            "other-package==1.0",
        ]

    def test_empty(self, tmp_path):
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("\n")
        assert read_pip(str(requirements)) == [""]


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

    def test_ignore_http_urls(self):
        assert parse_pip(["http://www.google.com"]) == {}

    def test_ignore_https_urls(self):
        assert parse_pip(["https://www.google.com"]) == {}

    def test_ignore_bzr_http_urls(self):
        url = "bzr+http://bzr.example.com"
        assert parse_pip([url]) == {}

    def test_ignore_git_https_urls(self):
        url = "git+https://git@github.com/adamchainz/pip-lock.git@80361b8#egg=pip-lock"
        assert parse_pip([url]) == {}

    def test_ignore_at_git_ssh_urls(self):
        assert parse_pip(["foo @ git+ssh://example.com"]) == {}

    def test_ignore_at_https_urls(self):
        assert parse_pip(["foo @ https://example.com"]) == {}


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
    def test_relative_requirements_file(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("package==1.2\n")

        with mock_get_distributions({"package": "1.1"}):
            result = get_mismatches("requirements.txt")

        assert result == {"package": ("1.2", "1.1")}

    def test_version_mismatch(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("package==1.2\n")

        with mock_get_distributions({"package": "1.1"}):
            result = get_mismatches("requirements.txt")

        assert result == {"package": ("1.2", "1.1")}

    def test_missing(self, tmp_path):
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("package==1.1\n")

        with mock_get_distributions({}):
            result = get_mismatches(str(requirements))

        assert result == {"package": ("1.1", None)}

    def test_no_mismatches(self, tmp_path):
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("package==1.1\n")

        with mock_get_distributions({"package": "1.1"}):
            result = get_mismatches(str(requirements))

        assert result == {}

    def test_no_mismatches_case_insensitive(self, tmp_path):
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("package==1.1\n")

        with mock_get_distributions({"Package": "1.1"}):
            result = get_mismatches(str(requirements))

        assert result == {}

    def test_empty(self, tmp_path):
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("\n")

        with mock_get_distributions({}):
            result = get_mismatches(str(requirements))

        assert result == {}

    def test_package_with_extra(self, tmp_path):
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("package[anextra]==1.1\n")

        with mock_get_distributions({"package": "1.1"}):
            result = get_mismatches(str(requirements))

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

    def test_relative_requirements_file(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("package==1.2\n")
        with mock_get_distributions({"package": "1.2"}):
            check_requirements("requirements.txt")
