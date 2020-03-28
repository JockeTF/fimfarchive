"""
Utility tests.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2019  Joakim Soderlund
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
from pathlib import Path
from unittest.mock import call, patch

import pytest

from fimfarchive import utils
from fimfarchive.flavors import DataFormat, MetaFormat, MetaPurity
from fimfarchive.utils import (
    find_flavor, get_path, is_blacklisted,
    Empty, JayWalker, PersistedDict,
)


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
        extra = {'key': object()}
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


class TestJayWalker:
    """
    JayWalker tests.
    """

    @pytest.fixture
    def walker(self):
        """
        Returns a walker instance.
        """
        walker = JayWalker()

        with patch.object(walker, 'handle', wraps=walker.handle):
            yield walker

    @pytest.mark.parametrize('obj', [None, 'alpaca', 42])
    def test_ignored_walk(self, walker, obj):
        """
        Tests walker ignores plain values.
        """
        walker.walk(obj)
        walker.handle.assert_not_called()

    def test_list_walk(self, walker):
        """
        Tests walker can walk lists.
        """
        data = ['a', 'b', 'c']
        walker.walk(data)

        assert walker.handle.mock_calls == [
            call(data, 0, 'a'),
            call(data, 1, 'b'),
            call(data, 2, 'c'),
        ]

    def test_dict_walk(self, walker):
        """
        Tests walker can walk dicts.
        """
        data = {0: 'a', 1: 'b', 2: 'c'}
        walker.walk(data)

        assert walker.handle.mock_calls == [
            call(data, 0, 'a'),
            call(data, 1, 'b'),
            call(data, 2, 'c'),
        ]

    def test_nested_walk(self, walker):
        """
        Tests walker can walk nested objects.
        """
        data = {
            'a': ['b', 'c'],
            'd': {'e': 'f'},
        }

        walker.walk([data])

        assert walker.handle.mock_calls == [
            call([data], 0, data),
            call(data, 'a', data['a']),
            call(data['a'], 0, 'b'),
            call(data['a'], 1, 'c'),
            call(data, 'd', data['d']),
            call(data['d'], 'e', 'f'),
        ]


class TestFindFlavor:
    """
    find_flavor tests.
    """

    @pytest.fixture
    def story(self, story):
        """
        Returns a meta-flavored story.
        """
        return story.merge(flavors=[
            MetaFormat.BETA,
            MetaPurity.CLEAN,
        ])

    def test_present_flavor(self, story):
        """
        Tests flavor is returned when present.
        """
        found = find_flavor(story, MetaFormat)
        assert found is MetaFormat.BETA

    def test_missing_flavor(self, story):
        """
        Tests None is returned when flavor is missing.
        """
        found = find_flavor(story, DataFormat)
        assert found is None


class TestGetPath:
    """
    get_path tests.
    """

    @pytest.mark.parametrize('source,target', (
        (None, None),
        ('', Path().resolve()),
        ('alpaca', Path('alpaca').resolve()),
        (Path('alpaca'), Path('alpaca').resolve()),
    ))
    def test_return_values(self, source, target):
        """
        Tests function returns the correct value.
        """
        assert target == get_path(source)


class TestIsBlacklisted:
    """
    is_blacklisted tests.
    """
    BLACKLISTED_AUTHOR = 1
    BLACKLISTED_STORY = 2
    WHITELISTED_STORY = 3
    UNLISTED_AUTHOR = 4
    UNLISTED_STORY = 5

    COMBINATIONS = [
        (BLACKLISTED_STORY, BLACKLISTED_AUTHOR, True),
        (BLACKLISTED_STORY, UNLISTED_AUTHOR, True),
        (UNLISTED_STORY, BLACKLISTED_AUTHOR, True),
        (UNLISTED_STORY, UNLISTED_AUTHOR, False),
        (WHITELISTED_STORY, BLACKLISTED_AUTHOR, False),
        (WHITELISTED_STORY, UNLISTED_AUTHOR, False),
    ]

    @pytest.fixture
    def utils(self):
        """
        Patches the blacklists and whitelists.
        """
        ab = patch.object(utils, 'AUTHOR_BLACKLIST', {self.BLACKLISTED_AUTHOR})
        sb = patch.object(utils, 'STORY_BLACKLIST', {self.BLACKLISTED_STORY})
        sw = patch.object(utils, 'STORY_WHITELIST', {self.WHITELISTED_STORY})

        with ab, sb, sw:
            yield utils

    @pytest.mark.parametrize('key,author,result', COMBINATIONS)
    def test_blacklisted(self, utils, story, key, author, result):
        """
        Tests the various blacklist combinations.
        """
        meta = {'id': key, 'author': {'id': author}}
        story = story.merge(key=key, meta=meta)

        assert result is is_blacklisted(story)

    @pytest.mark.parametrize('key,author,result', COMBINATIONS)
    def test_blacklisted_string(self, utils, story, key, author, result):
        """
        Tests the various blacklist combinations when IDs are strings.
        """
        meta = {'id': str(key), 'author': {'id': str(author)}}
        story = story.merge(key=key, meta=meta)

        assert result is is_blacklisted(story)
