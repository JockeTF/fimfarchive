"""
Directory fetcher tests.
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
import pytest
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.fetchers import DirectoryFetcher


NONE_KEY = 1
META_KEY = 3
DATA_KEY = 5
BOTH_KEY = 7


class TestDirectoryFetcher:
    """
    DirectoryFetcher tests.
    """

    def make_meta(self, key: int) -> Dict[str, Any]:
        """
        Returns generated story meta for the key.
        """
        return {'id': key}

    @pytest.fixture
    def metadir(self, tmpdir) -> Path:
        """
        Returns a temporary meta directory path.
        """
        subdir = tmpdir.mkdir('meta')

        for key in (META_KEY, BOTH_KEY):
            meta = self.make_meta(key)
            path = subdir.join(str(key))
            path.write(json.dumps(meta))

        return Path(str(subdir))

    def make_data(self, key: int) -> bytes:
        """
        Returns generated story data for the key.
        """
        return f'STORY {key}'.encode()

    @pytest.fixture
    def datadir(self, tmpdir) -> Path:
        """
        Returns a temporary data directory path.
        """
        subdir = tmpdir.mkdir('data')

        for key in (DATA_KEY, BOTH_KEY):
            data = self.make_data(key)
            path = subdir.join(str(key))
            path.write(data)

        return Path(str(subdir))

    @pytest.fixture
    def fetcher(self, metadir, datadir, flavor) -> DirectoryFetcher:
        """
        Returns a directory fetcher instance with prefetch disabled.
        """
        fetcher = DirectoryFetcher(metadir, datadir, [flavor])

        fetcher.prefetch_meta = False
        fetcher.prefetch_data = False

        return fetcher

    def test_complete_fetch(self, fetcher):
        """
        Tests stories can be successfully fetched.
        """
        story = fetcher.fetch(BOTH_KEY)
        meta = self.make_meta(BOTH_KEY)
        data = self.make_data(BOTH_KEY)

        assert meta == story.meta
        assert data == story.data

    def test_partial_meta_fetch(self, fetcher):
        """
        Tests stories with only meta can be partially fetched.
        """
        story = fetcher.fetch(META_KEY)
        meta = self.make_meta(META_KEY)

        assert meta == story.meta

        with pytest.raises(InvalidStoryError):
            story.data

    def test_partial_data_fetch(self, fetcher):
        """
        Tests stories with only data can be partially fetched.
        """
        story = fetcher.fetch(DATA_KEY)
        data = self.make_data(DATA_KEY)

        assert data == story.data

        with pytest.raises(InvalidStoryError):
            story.meta

    def test_missing_fetch(self, fetcher):
        """
        Tests `InvalidStoryError` is raised for missing stories.
        """
        story = fetcher.fetch(NONE_KEY)

        with pytest.raises(InvalidStoryError):
            story.meta

        with pytest.raises(InvalidStoryError):
            story.data

    @pytest.mark.parametrize('key', (NONE_KEY, META_KEY, DATA_KEY, BOTH_KEY))
    def test_flavors(self, fetcher, flavor, key):
        """
        Tests flavors are added to stories.
        """
        story = fetcher.fetch(key)
        assert {flavor} == set(story.flavors)

    def test_len(self, fetcher):
        """
        Tests len returns the total number of available stories.
        """
        assert 3 == len(fetcher)

    def test_len_caching(self, fetcher):
        """
        Tests len is only calculated once.
        """
        with patch.object(fetcher, 'list_keys', wraps=fetcher.list_keys) as m:
            assert 3 == len(fetcher)
            assert 3 == len(fetcher)
            assert 1 == len(m.mock_calls)

    def test_iter(self, fetcher):
        """
        Tests iter yields all available stories, ordered by key.
        """
        expected = sorted((META_KEY, DATA_KEY, BOTH_KEY))
        actual = list(story.key for story in fetcher)

        assert expected == actual
