"""
Fimfarchive fetcher tests.
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
from io import BytesIO
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock
from zipfile import ZipFile

import arrow
import pytest

from fimfarchive.exceptions import InvalidStoryError, StorySourceError
from fimfarchive.fetchers import fimfarchive, Fetcher, FimfarchiveFetcher
from fimfarchive.stories import Story
from fimfarchive.utils import JayWalker


VALID_STORY_KEY = 9
INVALID_STORY_KEY = 7


@pytest.fixture(scope='module')
def data():
    """
    Returns test data from JSON.
    """
    path = f'{__file__[:-3]}.json'

    with open(path, 'rt') as fobj:
        return json.load(fobj)


class Redactor(JayWalker):
    """
    Redacts samples.
    """

    def handle(self, data, key, value) -> None:
        if str(key).endswith('_html'):
            data[key] = '<p>REDACTED<p>'
        elif key == 'short_description':
            data[key] = "REDACTED"
        else:
            self.walk(value)


class FimfarchiveFetcherSampler:
    """
    Generates a sample archive for tests.

    Samples must be manually inspected for correctness.
    """

    def __init__(self, fetcher: Fetcher, *keys: int) -> None:
        """
        Constructor.

        Args:
            fetcher: The fetcher to fetch from.
            *keys: The stories to sample.
        """
        self.redactor = Redactor()
        self.stories = [self.sample(fetcher, key) for key in keys]

    def sample(self, fetcher: Fetcher, key: int) -> Story:
        """
        Returns a redacted story sample.
        """
        story = fetcher.fetch(key)
        story = story.merge(data=b'REDACTED')
        self.redactor.walk(story.meta)

        return story

    @property
    def files(self) -> List[Dict[str, str]]:
        """
        Returns a list of story data files.
        """
        files = []

        for story in self.stories:
            files.append({
                'name': story.meta['archive']['path'],
                'text': story.data.decode(),
            })

        return files

    @property
    def about(self) -> Dict[str, str]:
        """
        Returns the about file dictionary.
        """
        today = arrow.utcnow()
        fmt = 'YYYYMMDD'

        return {
            'version': today.shift(days=-1).format(fmt),
            'start': today.shift(days=-9).format(fmt),
            'end': today.shift(days=-2).format(fmt),
        }

    @property
    def index(self) -> Dict[int, Any]:
        """
        Returns the index file dictionary.
        """
        return {
            story.key: story.meta
            for story in self.stories
        }

    @property
    def archive(self) -> Dict[str, Any]:
        """
        Returns all the sample content.
        """
        return {
            'about': self.about,
            'files': self.files,
            'index': self.index,
        }

    def __str__(self) -> str:
        """
        Serializes all samples.
        """
        return json.dumps(
            {'archive': self.archive},
            ensure_ascii=False,
            sort_keys=True,
            indent=4,
        )


def serialize(obj: Dict) -> str:
    """
    Serializes into JSON readable by the fetcher.
    """
    entries = []

    for key, value in obj.items():
        data = json.dumps(value, sort_keys=True)
        entries.append(f'"{key}": {data}')

    joined = ',\n'.join(entries)
    output = '\n'.join(('{', joined, '}', ''))

    return output


class PoolMock(MagicMock):
    """
    Mocks the multiprocessing pool.
    """

    @staticmethod
    def imap(func, iterable, chunksize):
        yield from map(func, iterable)


class TestFimfarchiveFetcher:
    """
    FimfarchiveFetcher tests.
    """

    @pytest.fixture(scope='module')
    def archive(self, data):
        """
        Returns the archive as a byte stream.
        """
        stream = BytesIO()

        zobj = ZipFile(stream, 'w')
        archive = data['archive']

        for entry in archive['files']:
            zobj.writestr(entry['name'], entry['text'])

        zobj.writestr('readme.pdf', 'REDACTED')
        zobj.writestr('about.json', serialize(archive['about']))
        zobj.writestr('index.json', serialize(archive['index']))
        zobj.close()

        return stream

    @pytest.fixture
    def pool(self):
        """
        Yields a multiprocessing pool mock.
        """
        with patch.object(fimfarchive, 'Pool', PoolMock) as mock:
            yield mock

    @pytest.fixture()
    def fetcher(self, archive, pool):
        """
        Returns the fetcher instance to test.
        """
        with FimfarchiveFetcher(archive) as fetcher:
            yield fetcher

    def test_closed_fetcher_raises_exception(self, fetcher):
        """
        Tests `StorySourceError` is raised when fetcher is closed.
        """
        fetcher.close()

        with pytest.raises(StorySourceError):
            fetcher.fetch_meta(VALID_STORY_KEY)

    def test_fetch_meta_for_valid_story(self, fetcher):
        """
        Tests meta is returned if story is valid
        """
        meta = fetcher.fetch_meta(VALID_STORY_KEY)
        assert meta['id'] == VALID_STORY_KEY

    def test_fetch_meta_for_invalid_story(self, fetcher):
        """
        Tests `InvalidStoryError` is raised if story is invalid.
        """
        with pytest.raises(InvalidStoryError):
            fetcher.fetch_meta(INVALID_STORY_KEY)

    def test_fetch_data_for_valid_story(self, fetcher):
        """
        Tests data is returned if story is valid.
        """
        data = fetcher.fetch_data(VALID_STORY_KEY)
        assert len(data) != 0

    def test_fetch_data_for_invalid_story(self, fetcher):
        """
        Tests `InvalidStoryError` is raised if story is invalid.
        """
        with pytest.raises(InvalidStoryError):
            fetcher.fetch_data(INVALID_STORY_KEY)

    @pytest.mark.parametrize('attr', ('archive', 'index', 'paths'))
    def test_close_when_missing_attribute(self, fetcher, attr):
        """
        Tests close works even after partial initialization.
        """
        delattr(fetcher, attr)
        fetcher.close()
