"""
Web to local resource converter.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2021  Joakim Soderlund
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


import imghdr
from hashlib import sha1
from io import BytesIO
from typing import Dict, Iterator, Tuple
from urllib.parse import unquote
from zipfile import ZipFile

import requests
from bs4 import BeautifulSoup, Tag

from fimfarchive.exceptions import StorySourceError
from fimfarchive.stories import Story

from .base import Converter


class ImageLoader:
    cache: Dict[str, str]
    images: Dict[str, bytes]
    source: ZipFile

    def __init__(self, source: ZipFile) -> None:
        self.cache = dict()
        self.images = dict()
        self.source = source

    def fetch(self, url) -> str:
        response = requests.get(url, timeout=60)

        if not response.ok:
            raise StorySourceError("Could not fetch image")

        data = response.content
        digest = sha1(data).hexdigest()
        extension = imghdr.what(BytesIO(data))

        if not extension:
            raise StorySourceError("Could not parse image")

        name = "images/{}.{}".format(digest, extension)

        self.cache[url] = name
        self.images[name] = data

        return name

    def parse(self, data: bytes) -> bytes:
        dom = BeautifulSoup(data, features='html.parser')

        for tag in dom.find_all('img'):
            src = tag.attrs['src']
            url = unquote(src.split('?url=')[1])

            if url in self.cache:
                tag.attrs['src'] = self.cache[url]
            else:
                tag.attrs['src'] = self.fetch(url)

            tag.wrap(Tag(name='center'))

        return dom.decode_contents().encode()

    def entries(self) -> Iterator[Tuple[str, bytes]]:
        source = self.source

        for info in source.infolist():
            data = source.read(info)
            name = info.filename

            if name.endswith('.html'):
                yield name, self.parse(data)
            else:
                yield name, data

        yield from self.images.items()


class WebLocalConverter(Converter):
    """
    Converts web resources to local.
    """

    def __call__(self, story: Story) -> Story:
        source = ZipFile(BytesIO(story.data))
        loader = ImageLoader(source)
        repack = BytesIO()

        with ZipFile(repack, 'w') as target:
            for info, data in loader.entries():
                target.writestr(info, data)

        return story.merge(data=repack.getvalue())
