from unittest import mock

import pytest

from pip_lock import (
    check_requirements,
    get_mismatches,
    get_package_versions,
    print_errors,
    read_pip,
)


def create_file(tmpdir, name, text):
    t = tmpdir.join(name)
    t.write(text)
    return str(t)


class TestReadPip:
    def test_read(self, tmpdir):
        path = create_file(tmpdir, "requirements.txt", "package1==1.0\npackage2==1.1")
        assert read_pip(path) == ["package1==1.0", "package2==1.1"]

    def test_include(self, tmpdir):
        inc_path = create_file(tmpdir, "requirements_inc.txt", "other-package==1.0")
        path = create_file(tmpdir, "requirements.txt", "-r {}".format(inc_path))

        assert read_pip(path) == ["-r {}".format(inc_path), "other-package==1.0"]

    def test_empty(self, tmpdir):
        path = create_file(tmpdir, "requirements.txt", "")
        assert read_pip(path) == [""]


class TestGetPackageVersion:
    def test_version(self):
        assert get_package_versions(["package1==1.0", "package2==1.1"]) == {
            "package1": "1.0",
            "package2": "1.1",
        }

    def test_ignore_empty(self):
        assert get_package_versions([""]) == {}

    def test_ignore_comments(self):
        assert get_package_versions(["# Comment"]) == {}

    def test_ignore_includes(self):
        assert get_package_versions(["-r example.txt"]) == {}

    def test_ignore_urls(self):
        assert get_package_versions(["https://www.google.com"]) == {}


class TestGetMismatches:
    def setUp(self, tmpdir):
        super().setUp()
        self.requirements_path = create_file(
            tmpdir, "requirements.txt", "package1==1.1\npackage2==1.2"
        )

    @mock.patch("pip_lock.pip_freeze")
    def test_relative_requirements_file(self, pip_freeze, tmpdir):
        pip_freeze.return_value = ["package==1.1"]
        create_file(tmpdir, "requirements.txt", "package==1.2")
        with tmpdir.as_cwd():
            assert get_mismatches("requirements.txt") == {"package": ("1.2", "1.1")}

    @mock.patch("pip_lock.pip_freeze")
    def test_version_mismatch(self, pip_freeze, tmpdir):
        pip_freeze.return_value = ["package==1.1"]
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.2")

        assert get_mismatches(requirements_path) == {"package": ("1.2", "1.1")}

    @mock.patch("pip_lock.pip_freeze")
    def test_missing(self, pip_freeze, tmpdir):
        pip_freeze.return_value = [""]
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.1")

        assert get_mismatches(requirements_path) == {"package": ("1.1", None)}

    @mock.patch("pip_lock.pip_freeze")
    def test_no_mismatches(self, pip_freeze, tmpdir):
        pip_freeze.return_value = ["package==1.1"]
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.1")

        assert get_mismatches(requirements_path) == {}

    @mock.patch("pip_lock.pip_freeze")
    def test_no_mismatches_case_insensitive(self, pip_freeze, tmpdir):
        pip_freeze.return_value = ["Package==1.1"]
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.1")

        assert get_mismatches(requirements_path) == {}

    @mock.patch("pip_lock.pip_freeze")
    def test_empty(self, pip_freeze, tmpdir):
        pip_freeze.return_value = [""]
        requirements_path = create_file(tmpdir, "requirements.txt", "")

        assert get_mismatches(requirements_path) == {}

    @mock.patch("pip_lock.pip_freeze")
    def test_editable_packages_ignored(self, pip_freeze, tmpdir):
        pip_freeze.return_value = [
            (
                "-e git+git@github.com:adamchainz/pip-lock.git@"
                + "efac0eef8072d73b001b1bae0731c1d58790ac4b#egg=pip-lock"
            ),
            "package==1.1",
        ]
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.1")

        assert get_mismatches(requirements_path) == {}

    @mock.patch("pip_lock.pip_freeze")
    def test_at_packages_ignored(self, pip_freeze, tmpdir):
        pip_freeze.return_value = [
            "pip @ file:///tmp/pip-20.1.1-py2.py3-none-any.whl",
            "package==1.1",
        ]
        requirements_path = create_file(tmpdir, "requirements.txt", "package==1.1")

        assert get_mismatches(requirements_path) == {}

    @mock.patch("pip_lock.pip_freeze")
    def test_package_with_extra(self, pip_freeze, tmpdir):
        pip_freeze.return_value = ["package==1.1"]
        requirements_path = create_file(
            tmpdir, "requirements.txt", "package[anextra]==1.1"
        )

        assert get_mismatches(requirements_path) == {}


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

    @mock.patch("pip_lock.pip_freeze")
    def test_relative_requirements_file(self, pip_freeze, tmpdir):
        pip_freeze.return_value = ["package==1.2"]
        create_file(tmpdir, "requirements.txt", "package==1.2")
        with tmpdir.as_cwd():
            check_requirements("requirements.txt")
