"""
Mappers for Fimfarchive.
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


import string
from abc import abstractmethod
from html import unescape
from io import BytesIO
from pathlib import Path
from typing import Dict, Generic, Optional, Set, TypeVar, Union
from zipfile import ZipFile

from arrow import api as arrow, Arrow

from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.flavors import DataFormat, MetaFormat
from fimfarchive.stories import Story
from fimfarchive.utils import find_flavor


__all__ = (
    'Mapper',
    'StaticMapper',
    'DataFormatMapper',
    'MetaFormatMapper',
    'StoryDateMapper',
    'StoryPathMapper',
    'StorySlugMapper',
)


T = TypeVar('T')


class Mapper(Generic[T]):
    """
    Callable which maps stories to something else.
    """

    @abstractmethod
    def __call__(self, story: Story) -> T:
        """
        Applies the mapper.

        Args:
            story: The story to map.

        Returns:
            A mapped object.
        """


class StaticMapper(Mapper[T]):
    """
    Returns the supplied value for any call.
    """

    def __init__(self, value: T) -> None:
        self.value = value

    def __call__(self, story: Story) -> T:
        return self.value


class StoryDateMapper(Mapper[Optional[Arrow]]):
    """
    Returns the latest timestamp in a story, or None.
    """

    def __call__(self, story: Story) -> Optional[Arrow]:
        try:
            meta = getattr(story, 'meta', None)
        except InvalidStoryError:
            return None

        if not meta:
            return None

        dates = {
            meta.get('date_modified'),
        }

        for chapter in meta.get('chapters') or tuple():
            dates.add(chapter.get('date_modified'))

        dates.discard(None)

        if dates:
            return max(arrow.get(date) for date in dates)
        else:
            return None


class StoryPathMapper(Mapper[Path]):
    """
    Returns a key-based file path for a story.
    """

    def __init__(self, directory: Union[Path, str]) -> None:
        """
        Constructor.

        Args:
            directory: The directory for the path.
        """
        self.directory = Path(directory)

    def __call__(self, story: Story) -> Path:
        return self.directory / str(story.key)


class StorySlugMapper(Mapper[str]):
    """
    Returns a slug-based file path for a story.
    """

    def __init__(self, template: str = None) -> None:
        """
        Constructor.

        Args:
            template: Format string for the path.
        """
        self.template = '{extension}/{group}/{author}/{story}.{extension}'
        self.whitelist = set(string.ascii_letters + string.digits)
        self.groupings = set(string.ascii_lowercase)
        self.ignore = {'\''}
        self.spacing = '_'
        self.part_limit = 112
        self.slug_limit = 255

        if template is not None:
            self.template = template

    def slugify(self, text: str) -> str:
        """
        Creates a slug from any text.

        Args:
            text: The text to slufigy.

        Returns:
            A slugified version of the text.
        """
        chars = [self.spacing]

        for char in unescape(str(text)):
            if char in self.whitelist:
                chars.append(char)
            elif char not in self.ignore and chars[-1] != self.spacing:
                chars.append(self.spacing)

        slug = ''.join(chars).strip(self.spacing)

        if self.part_limit < len(slug):
            limit = self.part_limit + 1
            chars = slug[:limit].split(self.spacing)
            slug = self.spacing.join(chars[:-1])

        return slug.lower()

    def join(self, key: int, slug: Optional[str]) -> str:
        """
        Appends a key to a slug.

        Args:
            key: The key to append.
            slug: The target slug.

        Returns:
            A string with both slug and key.
        """
        key = int(key)

        if key < 0:
            raise ValueError("Key must not be negative.")

        if slug:
            return f'{slug}-{key}'
        else:
            return f'{key}'

    def group(self, slug: str) -> str:
        """
        Returns the group for part of a path.

        Args:
            slug: The slug to group.

        Return:
            A group for the slug.
        """
        path = slug[:1]

        if path not in self.groupings:
            path = self.spacing

        return path

    def classify(self, story: Story) -> str:
        """
        Returns a file extension for the story.

        Args:
            story: The story to classify.

        Returns:
            A file extension.
        """
        for flavor in story.flavors:
            if isinstance(flavor, DataFormat):
                return flavor.name.lower()

        return 'data'

    def generate(self, story: Story) -> Dict[str, Union[int, str]]:
        """
        Returns the parts of a path.

        Args:
            story: The story to generate parts from.

        Returns:
            The parts of the path.
        """
        story_meta = story.meta
        author_meta = story.meta['author']

        story_slug = self.slugify(story_meta['title'])
        author_slug = self.slugify(author_meta['name'])
        story_path = self.join(story_meta['id'], story_slug)
        author_path = self.join(author_meta['id'], author_slug)
        group_path = self.group(author_path)
        extension = self.classify(story)

        return {
            'group': group_path,
            'author': author_path,
            'author_key': author_meta['id'],
            'author_slug': author_path,
            'story': story_path,
            'story_key': story_meta['id'],
            'story_slug': story_slug,
            'extension': extension,
        }

    def __call__(self, story: Story) -> str:
        parts = self.generate(story)
        path = self.template.format(**parts)

        if self.slug_limit < len(path):
            raise ValueError("Path too long: {}".format(path))

        return path


class MetaFormatMapper(Mapper[Optional[MetaFormat]]):
    """
    Guesses the meta format of stories.
    """
    spec: Dict[MetaFormat, Set[str]] = {
        MetaFormat.ALPHA: {'likes', 'dislikes', 'words'},
        MetaFormat.BETA: {'num_likes', 'num_dislikes', 'num_words'},
    }

    def __call__(self, story: Story) -> Optional[MetaFormat]:
        flavor = find_flavor(story, MetaFormat)

        if flavor is not None:
            return flavor

        items = self.spec.items()
        meta = set(story.meta.keys())
        matches = [fmt for fmt, spec in items if spec & meta]

        if len(matches) == 1:
            return matches[0]
        else:
            return None


class DataFormatMapper(Mapper[Optional[DataFormat]]):
    """
    Guesses the data format of stories.
    """
    spec: Dict[DataFormat, Set[str]] = {
        DataFormat.EPUB: {'content.opf', 'mimetype', 'toc.ncx'},
        DataFormat.FPUB: {'book.ncx', 'book.opf', 'mimetype'},
    }

    zip_magic: Set[bytes] = {
        b'PK\x03\x04',
        b'PK\x05\x06',
        b'PK\x07\x08',
    }

    def __call__(self, story: Story) -> Optional[DataFormat]:
        flavor = find_flavor(story, DataFormat)

        if flavor is not None:
            return flavor

        data = story.data.rstrip()

        if data and data[0] == 123 and data[-1] == 125:
            return DataFormat.JSON

        if data[:4] not in self.zip_magic:
            return None

        with ZipFile(BytesIO(data)) as zobj:
            names = set(zobj.namelist())

        items = self.spec.items()
        matches = [fmt for fmt, spec in items if spec <= names]

        if len(matches) == 1:
            return matches[0]
        else:
            return None
