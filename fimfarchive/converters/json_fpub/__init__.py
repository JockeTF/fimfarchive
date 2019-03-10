"""
JSON to FPUB converter for story data.
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
from typing import Any, Dict, Iterator, Optional, Tuple
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

import arrow
from jinja2 import Environment, PackageLoader

from fimfarchive.flavors import DataFormat, MetaFormat
from fimfarchive.stories import Story
from fimfarchive.utils import JayWalker

from fimfarchive.fetchers.fimfiction2 import BetaFormatVerifier

from ..base import Converter


__all__ = (
    'JsonFpubConverter',
)


MIMETYPE = 'application/epub+zip'
PACKAGE = __package__.rsplit('.', 1)


class DateNormalizer(JayWalker):
    """
    Normalizes timezones of date values to UTC.
    """

    def handle(self, data, key, value) -> None:
        if str(key).startswith('date_'):
            data[key] = self.normalize(value)
        else:
            self.walk(value)

    def normalize(self, value: Optional[str]) -> Optional[str]:
        """
        Normalizes a single date value.
        """
        parsed = arrow.get(value or 0)

        if parsed.timestamp == 0:
            return None

        return parsed.to('utc').isoformat()


class StoryRenderer:
    """
    Renders story data.
    """

    def __init__(self) -> None:
        env = Environment(
            autoescape=True,
            keep_trailing_newline=True,
            loader=PackageLoader(*PACKAGE),
        )

        self.container_xml = env.get_template('container.xml')
        self.chapter_html = env.get_template('chapter.html')
        self.book_opf = env.get_template('book.opf')
        self.book_ncx = env.get_template('book.ncx')

        self.date_normalizer = DateNormalizer()
        self.verify_meta = BetaFormatVerifier.from_meta_params()
        self.verify_data = BetaFormatVerifier.from_data_params()

    def fix_authors_note_position(self, data: Dict[str, Any]) -> None:
        """
        Clears author's note position if author's note is missing.
        """
        authors_note = data['authors_note_html']

        if not authors_note or len(authors_note.strip()) < 10:
            data['authors_note_position'] = None

    def fix_local_href_attributes(self, data: Dict[str, Any]) -> None:
        """
        Replaces local href attributes with global ones.
        """
        source = ' href="/'
        target = ' href="https://www.fimfiction.net/'

        for key in ('authors_note_html', 'content_html'):
            data[key] = data[key].replace(source, target)

    def fix_local_src_attributes(self, data: Dict[str, Any]) -> None:
        """
        Replaces local src attributes with global ones.
        """
        source = ' src="/'
        target = ' src="https://www.fimfiction.net/'

        for key in ('authors_note_html', 'content_html'):
            data[key] = data[key].replace(source, target)

    def verify_index(self, expected, actual):
        """
        Raises an exception if the index values differ.
        """
        if expected != actual:
            raise ValueError(f"Expected index {expected}, was {actual}.")

    def iter_chapters(self, story: Story) -> Iterator[Dict[str, Any]]:
        """
        Yields chapter meta and data, combined into one.
        """
        self.verify_meta(story.meta)

        meta_chapters = story.meta['chapters']
        data_chapters = json.loads(story.data.decode())
        zipped = zip(meta_chapters, data_chapters)

        for index, chapter in enumerate(zipped, 1):
            meta, data = chapter

            self.verify_data(data)
            self.verify_index(index, meta['chapter_number'])
            self.verify_index(index, data['chapter_number'])

            yield {**meta, **data}

    def iter_content(self, story: Story) -> Iterator[Tuple[str, str]]:
        """
        Yields EPUB file paths and content for a story.
        """
        yield 'META-INF/container.xml', self.container_xml.render()

        for chapter in self.iter_chapters(story):
            number = chapter['chapter_number']
            path = f"Chapter{number}.html"

            self.fix_authors_note_position(chapter)
            self.fix_local_href_attributes(chapter)
            self.fix_local_src_attributes(chapter)

            yield path, self.chapter_html.render(chapter)

        meta = deepcopy(story.meta)
        self.date_normalizer.walk(meta)

        yield 'book.opf', self.book_opf.render(meta)
        yield 'book.ncx', self.book_ncx.render(meta)

    def __call__(self, story: Story) -> bytes:
        """
        Renders the EPUB file contents as bytes.
        """
        fobj = BytesIO()

        with ZipFile(fobj, 'w') as archive:
            archive.writestr('mimetype', MIMETYPE, ZIP_STORED)

            for path, data in self.iter_content(story):
                archive.writestr(path, data, ZIP_DEFLATED)

        return fobj.getvalue()


class JsonFpubConverter(Converter):
    """
    Converts story data from JSON to FPUB format.
    """

    def __init__(self) -> None:
        self.render = StoryRenderer()

    def __call__(self, story: Story) -> Story:
        if DataFormat.JSON not in story.flavors:
            raise ValueError(f"Missing flavor: {DataFormat.JSON}")

        if MetaFormat.BETA not in story.flavors:
            raise ValueError(f"Missing flavor: {MetaFormat.BETA}")

        data = self.render(story)

        flavors = set(story.flavors)
        flavors.remove(DataFormat.JSON)
        flavors.add(DataFormat.FPUB)

        return story.merge(data=data, flavors=flavors)
