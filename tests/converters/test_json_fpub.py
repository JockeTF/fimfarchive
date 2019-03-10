"""
JSON to FPUB converter tests.
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
from copy import deepcopy
from io import BytesIO
from typing import Any, Dict, Iterator, List
from zipfile import ZipFile

import pytest

from fimfarchive.converters import JsonFpubConverter
from fimfarchive.fetchers import Fimfiction2Fetcher
from fimfarchive.flavors import DataFormat, MetaFormat
from fimfarchive.stories import Story
from fimfarchive.utils import JayWalker


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


class JsonFpubConverterSampler:
    """
    Generates sample conversions for tests.

    Samples must be manually inspected for correctness.
    """

    def __init__(self, token: str, *keys: int) -> None:
        """
        Constructor.

        Args:
            token: Fimfiction APIv2 access token.
            keys: Stories to generate samples for.
        """
        self.keys = sorted(int(key) for key in keys)
        self.fetcher = Fimfiction2Fetcher(token)
        self.convert = JsonFpubConverter()
        self.redactor = Redactor()

    def sample(self, key: int) -> Dict[str, Any]:
        """
        Generates a sample conversion.
        """
        story = self.fetcher.fetch(key)
        redacted = self.redact(story)
        converted = self.convert(redacted)

        return {
            'key': int(key),
            'meta': redacted.meta,
            'json': json.loads(redacted.data.decode()),
            'fpub': self.extract(converted.data),
        }

    def redact(self, story: Story) -> Story:
        """
        Redacts a story.
        """
        meta = deepcopy(story.meta)
        data = json.loads(story.data.decode())

        self.redactor.walk(meta)
        self.redactor.walk(data)

        raw_data = json.dumps(data).encode()

        return story.merge(meta=meta, data=raw_data)

    def extract(self, data: bytes) -> List[Dict[str, Any]]:
        """
        Lists the contents of a ZIP-file.
        """
        output: List[Dict[str, Any]] = []
        zobj = ZipFile(BytesIO(data))

        for info in zobj.infolist():
            output.append({
                'name': info.filename,
                'text': zobj.read(info).decode(),
            })

        return output

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """
        Yields all samples.
        """
        for key in self.keys:
            yield self.sample(key)

    def __str__(self) -> str:
        """
        Serializes all samples.
        """
        return json.dumps(
            obj={'pairs': list(self)},
            ensure_ascii=False,
            sort_keys=True,
            indent=4,
        )


class TestJsonFpubConverter:
    """
    JsonFpubConverter tests.
    """

    @pytest.fixture
    def converter(self):
        """
        Returns a JSON to FPUB converter instance.
        """
        return JsonFpubConverter()

    @pytest.fixture(params=range(1))
    def pair(self, request, data):
        """
        Returns test data pairs.
        """
        return data['pairs'][request.param]

    @pytest.fixture
    def json_story(self, pair):
        """
        Returns a story in the JSON data format.
        """
        return Story(
            key=pair['key'],
            meta=deepcopy(pair['meta']),
            data=json.dumps(pair['json']).encode(),
            flavors={MetaFormat.BETA, DataFormat.JSON},
        )

    @pytest.fixture
    def fpub_story(self, pair):
        """
        Returns a story in the FPUB data format.
        """
        stream = BytesIO()

        with ZipFile(stream, 'w') as zobj:
            for info in pair['fpub']:
                zobj.writestr(info['name'], info['text'])

        return Story(
            key=pair['key'],
            meta=deepcopy(pair['meta']),
            data=stream.getvalue(),
            flavors={MetaFormat.BETA, DataFormat.FPUB},
        )

    def test_conversion(self, converter, json_story, fpub_story):
        """
        Tests conversion of story data from JSON to FPUB format.
        """
        converted = converter(json_story)

        exp = ZipFile(BytesIO(fpub_story.data))
        act = ZipFile(BytesIO(converted.data))

        for einfo, ainfo in zip(exp.infolist(), act.infolist()):
            assert einfo.filename == ainfo.filename
            assert exp.read(einfo) == act.read(ainfo)

    def test_mimetype(self, converter, json_story):
        """
        Tests mimetype is included correctly.
        """
        converted = converter(json_story)

        zobj = ZipFile(BytesIO(converted.data))
        info = zobj.infolist()[0]
        read = zobj.read(info).decode()

        assert 0 == info.compress_type
        assert 'mimetype' == info.filename
        assert 'application/epub+zip' == read

    def test_immutablilty(self, converter, json_story):
        """
        Tests converter doesn't modify original.
        """
        clone = deepcopy(json_story)
        converter(json_story)

        for attr in ('key', 'fetcher', 'meta', 'data', 'flavors'):
            assert getattr(clone, attr) == getattr(json_story, attr)
