# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from unittest.mock import patch

import pytest
from pip_lock import check_requirements, get_mismatches, get_package_versions, print_errors, read_pip


def create_file(tmpdir, name, text):
    t = tmpdir.join(name)
    t.write(text)
    return str(t)


class TestReadPip(object):

    def test_read(self, tmpdir):
        path = create_file(tmpdir, 'requirements.txt', 'package1==1.0\npackage2==1.1')
        assert read_pip(path) == ['package1==1.0', 'package2==1.1']

    def test_include(self, tmpdir):
        inc_path = create_file(tmpdir, 'requirements_inc.txt', 'other-package==1.0')
        path = create_file(tmpdir, 'requirements.txt', '-r {0}'.format(inc_path))

        assert read_pip(path) == [
            '-r {0}'.format(inc_path),
            'other-package==1.0',
        ]

    def test_empty(self, tmpdir):
        path = create_file(tmpdir, 'requirements.txt', '')
        assert read_pip(path) == ['']


class TestGetPackageVersion(object):

    def test_version(self):
        assert get_package_versions(['package1==1.0', 'package2==1.1']) == {'package1': '1.0', 'package2': '1.1'}

    def test_ignore_empty(self):
        assert get_package_versions(['']) == {}

    def test_ignore_comments(self):
        assert get_package_versions(['# Comment']) == {}

    def test_ignore_includes(self):
        assert get_package_versions(['-r example.txt']) == {}

    def test_ignore_urls(self):
        assert get_package_versions(['https://www.google.com']) == {}


class TestGetMismatches(object):

    def setUp(self, tmpdir):
        super(TestGetMismatches, self).setUp()
        self.requirements_path = create_file(
            tmpdir,
            'requirements.txt',
            'package1==1.1\npackage2==1.2',
        )

    @patch('pip_lock.pip_freeze')
    def test_relative_requirements_file(self, pip_freeze, tmpdir):
        pip_freeze.return_value = ['package==1.1']
        assert get_mismatches('test_requirements.txt') == {'package': ('1.2', '1.1')}

    @patch('pip_lock.pip_freeze')
    def test_version_mismatch(self, pip_freeze, tmpdir):
        pip_freeze.return_value = ['package==1.1']
        requirements_path = create_file(tmpdir, 'requirements.txt', 'package==1.2')

        assert get_mismatches(requirements_path) == {'package': ('1.2', '1.1')}

    @patch('pip_lock.pip_freeze')
    def test_missing(self, pip_freeze, tmpdir):
        pip_freeze.return_value = ['']
        requirements_path = create_file(tmpdir, 'requirements.txt', 'package==1.1')

        assert get_mismatches(requirements_path) == {'package': ('1.1', None)}

    @patch('pip_lock.pip_freeze')
    def test_no_mismatches(self, pip_freeze, tmpdir):
        pip_freeze.return_value = ['package==1.1']
        requirements_path = create_file(tmpdir, 'requirements.txt', 'package==1.1')

        assert get_mismatches(requirements_path) == {}

    @patch('pip_lock.pip_freeze')
    def test_empty(self, pip_freeze, tmpdir):
        pip_freeze.return_value = ['']
        requirements_path = create_file(tmpdir, 'requirements.txt', '')

        assert get_mismatches(requirements_path) == {}


class TestPrintErrors(object):

    def test_errors(self, capsys):
        print_errors(['error message 1', 'error message 2'])
        _, err = capsys.readouterr()
        assert 'error message 1' in err
        assert 'error message 2' in err

    def test_pre_post_text(self, capsys):
        print_errors(['error message'], 'pre text', 'post text')
        _, err = capsys.readouterr()
        assert 'error message' in err
        assert 'pre text' in err
        assert 'post text' in err


class TestCheckRequirements(object):

    @patch('pip_lock.get_mismatches')
    def test_no_mismatches(self, get_mismatches):
        get_mismatches.return_value = {}
        check_requirements('requirements.txt')

    @patch('pip_lock.get_mismatches')
    def test_mismatches(self, get_mismatches, capsys):
        get_mismatches.return_value = {'package1': ('1.1', '1.0'), 'package2': ('1.0', None)}
        with pytest.raises(SystemExit):
            check_requirements('requirements.txt')

        _, err = capsys.readouterr()
        assert 'package1 has version 1.1 but you have version 1.0 installed' in err
        assert 'package2 is in requirements.txt but not in virtualenv' in err
