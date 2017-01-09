"""
Utility tests.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2015  Joakim Soderlund
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import json
import os

import pytest

from fimfarchive.utils import Empty, PersistedDict


class TestEmpty:
    """
    Empty tests.
    """

    def test_empty_class_is_not_none(self):
        """
        Tests `Empty` class is different from `None`.
        """
        assert Empty is not None
        assert Empty != None  # noqa

    def test_empty_class_evaluates_to_false(self):
        """
        Tests `Empty` class evaluates to `False`.
        """
        assert not Empty

    def test_empty_class_is_empty(self):
        """
        Tests `Empty` class can be identified.
        """
        assert Empty is Empty
        assert Empty == Empty

    def test_empty_instance_evaluates_to_false(self):
        """
        Tests `Empty` instance evaulates to `False`
        """
        assert not Empty()

    def test_empty_instance_is_unique(self):
        """
        Tests `Empty` instances are unique.
        """
        empty = Empty()

        assert isinstance(empty, Empty)
        assert empty is not Empty
        assert empty != Empty
        assert empty is not Empty()
        assert empty != Empty()
        assert empty is empty
        assert empty == empty


class TestPersistedDict:
    """
    PersistedDict tests.
    """

    @pytest.fixture
    def sample(self):
        """
        Returns a sample dictionary.
        """
        return {'key': 'value'}

    @pytest.fixture
    def tmppath(self, tmpdir):
        """
        Returns a temporary file path to nothing.
        """
        return str(tmpdir.join('sample.json'))

    @pytest.fixture
    def tmpfile(self, tmppath, sample):
        """
        Returns a temporary file path to sample data.
        """
        with open(tmppath, 'wt') as fobj:
            json.dump(sample, fobj)

        return tmppath

    def test_saves_data(self, tmppath, sample):
        """
        Tests data is saved to file.
        """
        data = PersistedDict(tmppath)
        data.update(sample)

        assert not os.path.exists(tmppath)

        data.save()

        with open(tmppath, 'rt') as fobj:
            saved = json.load(fobj)

        assert dict(data) == saved

    def test_loads_values(self, tmpfile, sample):
        """
        Tests data is loaded from file.
        """
        data = PersistedDict(tmpfile)

        assert dict(data) == sample

    def test_load_replaces_data(self, tmpfile, sample):
        """
        Tests data is replaced on load.
        """
        extra = {object(): object()}
        data = PersistedDict(tmpfile)
        data.update(extra)
        data.load()

        assert dict(data) == sample

    def test_load_empty_replaces_data(self, tmppath, sample):
        """
        Tests data is replaced on load if file does not exist.
        """
        data = PersistedDict(tmppath)
        data.update(sample)
        data.load()

        assert dict(data) == dict()

    def test_load_restores_defaults(self, tmpfile, sample):
        """
        Tests defaults are restored on load.
        """
        extra = {object(): object()}
        data = PersistedDict(tmpfile, default=extra)
        data.clear()

        assert dict(data) == dict()

        data.load()

        assert dict(data) == {**sample, **extra}

    def test_default_in_empty(self, tmppath, sample):
        """
        Tests defaults are inserted when data is empty.
        """
        data = PersistedDict(tmppath, default=sample)

        assert dict(data) == sample

    def test_default_in_mixed(self, tmpfile, sample):
        """
        Tests defaults are inserted alongside loaded data.
        """
        extra = {object(): object()}
        data = PersistedDict(tmpfile, default=extra)

        assert dict(data) == {**sample, **extra}

    def test_default_does_not_override(self, tmpfile, sample):
        """
        Tests defaults do not override loaded data.
        """
        extra = {k: object() for k in sample.keys()}
        data = PersistedDict(tmpfile, default=extra)

        assert dict(data) == sample