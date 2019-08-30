"""
Alpha to beta converter for story meta.
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
from copy import deepcopy
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple
from urllib.parse import quote_plus as urlquote

import arrow
import bbcode
from jmespath import compile as jmes
from jmespath.parser import ParsedResult

from fimfarchive.flavors import MetaFormat
from fimfarchive.stories import Story
from fimfarchive.utils import ResourceLoader

from ..base import Converter


__all__ = (
    'AlphaBetaConverter',
)


load = ResourceLoader(__package__)


HOST = 'https://www.fimfiction.net'
TAGS = json.loads(load('tags.json'))
EPOCH = arrow.get(0).isoformat()


class Handler(Iterable[Tuple[str, Any]]):
    """
    Maps story meta to another style.
    """
    attrs: Iterable[str] = tuple()
    static: Dict[str, Any] = dict()
    paths: Dict[str, ParsedResult] = dict()

    def __init__(self, meta: Dict[str, Any]) -> None:
        """
        Constructor.

        Args:
            meta: The story meta to map.
        """
        self.meta = meta

    def __getattr__(self, key: str) -> Any:
        """
        Returns values from indirect sources.
        """
        if key in self.static:
            return self.static[key]

        if key in self.paths:
            meta = self.meta
            path = self.paths[key]
            return path.search(meta)

        return self.meta.get(key)

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """
        Yields all story meta items.
        """
        for attr in self.attrs:
            value = getattr(self, attr)
            yield attr, value


class ArchiveHandler(Handler):
    """
    Maps an archive meta dict from root.
    """
    attrs = (
        'date_checked',
        'date_created',
        'date_fetched',
        'date_updated',
        'path',
    )

    paths = {
        'date_checked': jmes('archive.date_checked'),
        'date_created': jmes('archive.date_created'),
        'date_fetched': jmes('archive.date_fetched'),
        'date_updated': jmes('archive.date_updated'),
        'path': jmes('archive.path || path'),
    }


class AuthorHandler(Handler):
    """
    Maps an author meta dict.
    """
    attrs = (
        'avatar',
        'bio_html',
        'date_joined',
        'id',
        'name',
        'num_blog_posts',
        'num_followers',
        'num_stories',
        'url',
    )

    @property
    def id(self):
        return int(self.meta['id'])

    @property
    def url(self):
        uid = self.id
        name = urlquote(str(self.name))
        return f'{HOST}/user/{uid}/{name}'


class ChapterHandler(Handler):
    """
    Maps a chapter meta dict.
    """
    attrs = (
        'chapter_number',
        'date_modified',
        'date_published',
        'id',
        'num_views',
        'num_words',
        'published',
        'title',
        'url',
    )

    static = {
        'published': True,
    }

    paths = {
        'url': jmes('link'),
        'num_views': jmes('views'),
        'num_words': jmes('words'),
    }

    def __init__(self, meta: Dict[str, Any], index: int) -> None:
        """
        Constructor.

        Args:
            meta: The chapter meta to map.
            index: The current chapter index.
        """
        self.meta = meta
        self.chapter_number = int(index) + 1

    @property
    def date_modified(self) -> Optional[str]:
        timestamp = self.meta.get('date_modified')

        if timestamp is None:
            return None

        return arrow.get(timestamp).isoformat()


class RootHandler(Handler):
    """
    Maps a root meta dict.
    """
    attrs = (
        'archive',
        'author',
        'chapters',
        'color',
        'completion_status',
        'content_rating',
        'cover_image',
        'date_modified',
        'date_published',
        'date_updated',
        'description_html',
        'id',
        'num_chapters',
        'num_comments',
        'num_dislikes',
        'num_likes',
        'num_views',
        'num_words',
        'prequel',
        'published',
        'rating',
        'short_description',
        'status',
        'submitted',
        'tags',
        'title',
        'total_num_views',
        'url',
    )

    static = {
        'date_modified': EPOCH,
        'published': True,
        'status': 'visible',
        'submitted': True,
    }

    paths = {
        'num_chapters': jmes('chapter_count'),
        'num_comments': jmes('comments'),
        'num_dislikes': jmes('dislikes'),
        'num_likes': jmes('likes'),
        'num_views': jmes('views'),
        'num_words': jmes('words'),
        'total_num_views': jmes('total_views'),
    }

    @property
    def archive(self) -> Dict[str, Any]:
        handler = ArchiveHandler(self.meta)
        return dict(iter(handler))

    @property
    def author(self) -> Dict[str, Any]:
        author = self.meta.get('author') or dict()
        handler = AuthorHandler(author)
        return dict(iter(handler))

    @property
    def chapters(self) -> List[Dict[str, Any]]:
        items = enumerate(self.meta.get('chapters') or list())
        handlers = (ChapterHandler(c, i) for i, c in items)
        return [dict(iter(handler)) for handler in handlers]

    @property
    def completion_status(self) -> Optional[str]:
        status = self.meta.get('status')

        if status == 'On Hiatus':
            return 'hiatus'

        return status and status.strip().lower()

    @property
    def content_rating(self) -> Optional[str]:
        rating = self.meta.get('content_rating_text')
        return rating and rating.strip().lower()

    @property
    def cover_image(self) -> Optional[Dict[str, Any]]:
        image = self.meta.get('image')

        if image is None:
            return None

        base = image.rsplit("-", 1)[0]
        assert base.startswith('http')

        return {
            'full': f'{base}-full',
            'large': f'{base}-large',
            'medium': f'{base}-medium',
            'thumbnail': f'{base}-tiny',
        }

    @property
    def date_updated(self) -> Optional[str]:
        timestamp = self.meta.get('date_modified')

        if timestamp is None:
            return None

        return arrow.get(timestamp).isoformat()

    @property
    def description_html(self) -> Optional[str]:
        desc = self.meta.get('description')

        if desc is None:
            return None

        html = bbcode.render_html(desc)
        return f'<p>{html.strip()}</p>'

    @property
    def rating(self) -> Optional[int]:
        likes = self.num_likes
        dislikes = self.num_dislikes

        if None in (likes, dislikes):
            return None

        try:
            return round(likes / (likes + dislikes) * 100)
        except ZeroDivisionError:
            return 50

    @property
    def tags(self) -> List[Dict[str, Any]]:
        cats = self.meta.get('categories') or dict()
        tags = [TAGS[k] for k, v in cats.items() if v]
        return deepcopy(tags)


class AlphaBetaConverter(Converter):
    """
    Converts story meta from alpha to beta format.
    """

    def __call__(self, story: Story) -> Story:
        if MetaFormat.ALPHA not in story.flavors:
            raise ValueError(f"Missing flavor: {MetaFormat.ALPHA}")

        handler = RootHandler(story.meta)
        meta = dict(iter(handler))

        flavors = set(story.flavors)
        flavors.remove(MetaFormat.ALPHA)
        flavors.add(MetaFormat.BETA)

        return story.merge(meta=meta, flavors=flavors)
