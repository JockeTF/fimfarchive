"""
Fimfiction APIv2 fetcher.
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
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from copy import deepcopy
from typing import Any, Dict, Iterator, Optional, Set
from urllib.parse import urlencode

from jsonapi_client import Filter, Session
from jsonapi_client.document import Document
from jsonapi_client.exceptions import DocumentError
from jsonapi_client.resourceobject import ResourceObject

from fimfarchive import __version__ as version
from fimfarchive.flavors import DataFormat, MetaFormat, MetaPurity, StorySource

from fimfarchive.exceptions import (
    FimfarchiveError,
    InvalidStoryError,
    StorySourceError,
)

from .base import Fetcher


__all__ = (
    'BetaFormatVerifier',
    'Fimfiction2Fetcher',
)


QueryParams = Dict[str, Set[str]]


ROOT = 'root'
AUTHOR = 'author'
CHAPTERS = 'chapters'
PREQUEL = 'prequel'
TAGS = 'tags'


DATA_PARAMS: QueryParams = {
    'include': {
        'chapters',
    },
    'fields[chapter]': {
        'authors_note_html',
        'authors_note_position',
        'chapter_number',
        'content_html',
        'title',
    },
    'fields[story]': {
        'chapters',
    },
}


META_PARAMS: QueryParams = {
    'include': {
        'author',
        'chapters',
        'tags',
    },
    'fields[chapter]': {
        'chapter_number',
        'date_modified',
        'date_published',
        'num_views',
        'num_words',
        'published',
        'title',
    },
    'fields[story]': {
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
    },
    'fields[story_tag]': {
        'name',
        'type',
    },
    'fields[user]': {
        'avatar',
        'bio_html',
        'date_joined',
        'name',
        'num_blog_posts',
        'num_followers',
        'num_stories',
    },
}


class ApiClient:
    """
    Performs API requests.
    """

    def __init__(self, token: str) -> None:
        """
        Constructor.

        Args:
            token: Fimfiction authorization bearer.
        """
        self.token = token

    def create_session(self, token: str) -> Session:
        """
        Creates a jsonapi session with authorization.

        Args:
            token: Fimfiction authorization bearer.

        Returns:
            A jsonapi session containing the token.
        """
        headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Authorization': f'Bearer {token}',
            'User-Agent': f'fimfarchive/{version}',
        }

        return Session(
            server_url='https://www.fimfiction.net/api/v2/',
            request_kwargs={'headers': headers},
        )

    def create_filter(self, params: QueryParams) -> Filter:
        """
        Creates a jsonapi filter from query parameters.

        Args:
            params: Parameters to create a filter for.

        Returns:
            A jsonapi filter matching the parameters.
        """
        joined: Dict[str, str] = OrderedDict()

        for key, value in sorted(params.items()):
            joined[key] = ','.join(sorted(value))

        return Filter(urlencode(joined))

    def get(self, path: str, params: QueryParams = dict()) -> Document:
        """
        Performs a jsonapi request.

        Args:
            resource: Path to the resource.
            params: Parameters for the request.

        Returns:
            A jsonapi response document.
        """
        query = self.create_filter(params)
        session = self.create_session(self.token)

        return session.get(path, query)


class Requester(ABC):
    """
    Performs Fimfiction APIv2 requests.
    """

    @abstractmethod
    def get_meta(self, key: int) -> ResourceObject:
        """
        Performs an API request for story meta.

        Args:
            key: Primary key of the story.

        Returns:
            A resource object containing story meta.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If source does not return valid data.
        """

    @abstractmethod
    def get_data(self, key: int) -> Iterator[ResourceObject]:
        """
        Performs an API request for story data.

        Args:
            key: Primary key of the story.

        Returns:
            Resource objects containing story chapters.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If source does not return valid data.
        """


class SingleRequester(Requester):
    """
    Requests stories one by one.
    """

    def __init__(self, client: ApiClient) -> None:
        """
        Constructor.

        Args:
            client: Client to use for queries.
        """
        self.client = client

    def error(self, key: int, status: int) -> FimfarchiveError:
        """
        Creates an exception for the status.

        Args:
            key: Primary key of the story.
            status: Status code of the response.

        Returns:
            A fimfarchive exception instance.
        """
        if status == 403:
            return InvalidStoryError(f"Private story: {key}")
        elif status == 404:
            return InvalidStoryError(f"Missing story: {key}")
        else:
            return StorySourceError(f"Bad HTTP status for {key}: {status}")

    def get(self, key: int, path: str, params: QueryParams) -> Document:
        """
        Performs a Fimfiction APIv2 request.

        Args:
            key: Primary key of the story.
            path: Resource to query.
            params: Query parameters.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If source does not return valid data.
        """
        try:
            return self.client.get(path, params)
        except DocumentError as e:
            raise self.error(key, e.response.status_code) from e
        except Exception as e:
            raise StorySourceError("Unknown error for {key}.") from e

    def get_meta(self, key: int) -> ResourceObject:
        path = f'stories/{key}'
        response = self.get(key, path, META_PARAMS)
        return response.resource

    def get_data(self, key: int) -> Iterator[ResourceObject]:
        path = f'stories/{key}/chapters'
        response = self.get(key, path, DATA_PARAMS)
        return response.resources


class BulkRequester(Requester):
    """
    Requests stories in bulk.
    """
    response: Optional[Document]
    resources: Dict[int, Optional[ResourceObject]]

    def __init__(
            self,
            client: ApiClient,
            bulk_meta: bool = True,
            bulk_data: bool = True,
            bulk_size: int = 16,
            ) -> None:
        """
        Constructor.

        Args:
            client: Client to use for queries.
            bulk_meta: Toggles bulk fetching of meta.
            bulk_data: Toggles bulk fetching of data.
            bulk_size: Number of items to request per batch.
        """
        self.client = client
        self.bulk_meta = bulk_meta
        self.bulk_data = bulk_data
        self.bulk_size = bulk_size

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Resets the requester when necessary.
        """
        try:
            super().__setattr__(name, value)
        finally:
            if name in ('bulk_meta', 'bulk_data'):
                self.reset()

    def reset(self) -> None:
        """
        Drops the currently cached story batch.
        """
        self.response = None
        self.resources = dict()

    def create_params(self) -> QueryParams:
        """
        Creates general query parameters for a request.
        """
        params: QueryParams = defaultdict(set)

        if self.bulk_meta:
            for key, value in META_PARAMS.items():
                params[key].update(value)

        if self.bulk_data:
            for key, value in DATA_PARAMS.items():
                params[key].update(value)

        return dict(params)

    def cache(self, key: int) -> None:
        """
        Caches a story batch from Fimfiction.

        Args:
            key: Primary key of the story.
        """
        count = int(self.bulk_size)
        lower = key - (key % count)
        upper = lower + count

        keys = range(lower, upper)
        params = self.create_params()
        params['page[size]'] = {str(len(keys) + 4)}
        params['filter[ids]'] = {str(i) for i in keys}

        self.response = self.client.get('stories', params)
        self.resources = {key: None for key in keys}

        for resource in self.response.resources:
            self.resources[int(resource.id)] = resource

    def fetch(self, key: int) -> ResourceObject:
        """
        Fetches a resource from either cache or Fimfiction.

        Args:
            key: Primary key of the story.

        Returns:
            A resource object containing the story.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If source does not return valid data.
        """
        if key not in self.resources:
            try:
                self.cache(key)
            except Exception as e:
                self.reset()
                raise StorySourceError("Unable to fetch.") from e

        resource = self.resources[key]

        if resource is None:
            raise InvalidStoryError("Invalid story ID.")

        return resource

    def get_meta(self, key: int) -> ResourceObject:
        if not self.bulk_meta:
            raise StorySourceError("Bulk meta not enabled.")

        return self.fetch(key)

    def get_data(self, key: int) -> Iterator[ResourceObject]:
        if not self.bulk_data:
            raise StorySourceError("Bulk data not enabled.")

        return self.fetch(key).chapters


class RoutedRequester(Requester):
    """
    Routes between single and bulk requesters.
    """

    def __init__(
            self,
            client: ApiClient,
            bulk_meta: bool,
            bulk_data: bool,
            ) -> None:
        """
        Constructor.

        Args:
            client: Client to use for queries.
            bulk_meta: Toggles bulk fetching of meta.
            bulk_data: Toggles bulk fetching of data.
        """
        self.single = SingleRequester(client)
        self.bulk = BulkRequester(client, bulk_meta, bulk_data)

    def get_meta(self, key: int) -> ResourceObject:
        if self.bulk.bulk_meta:
            return self.bulk.get_meta(key)
        else:
            return self.single.get_meta(key)

    def get_data(self, key: int) -> Iterator[ResourceObject]:
        if self.bulk.bulk_data:
            return self.bulk.get_data(key)
        else:
            return self.single.get_data(key)


class Documentifier:
    """
    Converts a resource into a dictionary.
    """

    def merge(self, target: Dict, source: Dict) -> None:
        """
        Copies items from source into target.

        Args:
            target: Dictionary to copy to.
            source: Dictionary to copy from.
        """
        for key, value in deepcopy(source).items():
            assert key not in target
            target[key] = value

    def flatten(self, resource: ResourceObject) -> Dict[str, Any]:
        """
        Flattens the resource into a dictionary.

        Args:
            resource: Resource to flatten.

        Returns:
            A dictionary representation.
        """
        document: Dict[str, Any] = {
            'id': int(resource.id),
        }

        self.merge(document, resource.json['attributes'])
        self.merge(document, resource.meta.meta)

        return document

    def __call__(self, resource: ResourceObject) -> Dict[str, Any]:
        """
        Applies the documentifier.

        Args:
            resource: Resource to documentify.

        Returns:
            A dictionary representation.
        """
        return self.flatten(resource)


class MetaDocumentifier(Documentifier):
    """
    Converts a resource into a story meta dictionary.
    """
    fill = (
        'cover_image',
        'date_published',
    )

    remove = (
        'content_html',
        'authors_note_html',
        'authors_note_position',
    )

    def fill_keys(self, meta: Dict[str, Any]) -> None:
        """
        Fills keys that may be left out by Fimfiction.

        Args:
            meta: Dictionary to fill.
        """
        for key in self.fill:
            if key not in meta:
                meta[key] = None

    def remove_data(self, meta: Dict[str, Any]) -> None:
        """
        Removes keys that may be left in by the bulk fetcher.

        Args:
            meta: Dictionary to clean.
        """
        for chapter in meta['chapters']:
            for key in self.remove:
                if key in chapter:
                    del chapter[key]

    def __call__(self, resource: ResourceObject) -> Dict[str, Any]:
        meta = self.flatten(resource)

        assert AUTHOR not in meta
        meta[AUTHOR] = self.flatten(resource.author)

        assert CHAPTERS not in meta
        chapters = [self.flatten(chapter) for chapter in resource.chapters]
        chapters.sort(key=lambda chapter: chapter['chapter_number'])
        meta[CHAPTERS] = chapters

        assert PREQUEL not in meta
        prequel = getattr(resource.relationships, PREQUEL, None)

        if prequel:
            value = prequel._resource_identifier.id
            meta[PREQUEL] = int(value)
        else:
            meta[PREQUEL] = None

        assert TAGS not in meta
        tags = [self.flatten(tag) for tag in resource.tags]
        tags.sort(key=lambda tag: (tag['type'], tag['name']))
        meta[TAGS] = tags

        self.fill_keys(meta)
        self.remove_data(meta)

        return meta


class BetaFormatVerifier:
    """
    Verifies that required keys are present in a dictionary.
    """

    def __init__(self, requirements: Dict[str, Set[str]]) -> None:
        """
        Constructor.

        Args:
            requirements: Specifies the required keys.
        """
        self.requirements: Dict[str, Set[str]] = requirements

    @classmethod
    def from_params(
            cls,
            params: QueryParams,
            mapping: Dict[str, str],
            ) -> 'BetaFormatVerifier':
        """
        Constructor, using query parameters.

        Args:
            params: Query parameters to base the requirements on.
            mapping: Mapping from document keys to resource types.
        """
        requirements = dict()

        for key, resource in mapping.items():
            param = f'fields[{resource}]'
            fields = deepcopy(params[param])
            fields.update(('id', 'url'))
            requirements[key] = fields

        return cls(requirements)

    @classmethod
    def from_meta_params(cls) -> 'BetaFormatVerifier':
        """
        Constructor, for creating a meta verifier.
        """
        return cls.from_params(META_PARAMS, {
            ROOT: 'story',
            AUTHOR: 'user',
            CHAPTERS: 'chapter',
            TAGS: 'story_tag',
        })

    @classmethod
    def from_data_params(cls) -> 'BetaFormatVerifier':
        """
        Constructor, for creating a chapter verifier.
        """
        return cls.from_params(DATA_PARAMS, {
            ROOT: 'chapter',
        })

    def check(self, key: str, required: Set[str], data: Any) -> None:
        """
        Checks dictionaries against a set of required keys.

        Args:
            key: Document key being checked.
            required: Set of required keys.
            data: Dictionaries to check.

        Raises:
            StorySourceError: If a dictionary is invalid.
        """
        if isinstance(data, dict):
            data = (data,)

        for obj in data:
            if obj.keys() < required:
                missing = ", ".join(required - obj.keys())
                message = f"Missing from {key}: {missing}"
                raise StorySourceError(message)

    def __call__(self, data: Dict[str, Any]) -> None:
        """
        Applies the verifier to a dictionary.

        Args:
            data: Dictionary to check.

        Raises:
            StorySourceError: If a dictionary is invalid.
        """
        for key, required in self.requirements.items():
            if key == ROOT:
                self.check(key, required, data)
            else:
                self.check(key, required, data[key])


class Fimfiction2Fetcher(Fetcher):
    """
    Fetcher for Fimfiction APIv2.
    """
    prefetch_meta = True
    prefetch_data = False

    flavors = frozenset((
        StorySource.FIMFICTION,
        DataFormat.JSON,
        MetaFormat.BETA,
        MetaPurity.DIRTY,
    ))

    def __init__(self, token: str, bulk_meta=False, bulk_data=False) -> None:
        """
        Constructor.

        Args:
            token: Authentication token for Fimfiction.
            bulk_meta: Toggles bulk fetching of story meta.
            bulk_data: Toggles bulk fetching of story data.
        """
        client = ApiClient(token)
        self.extract_meta = MetaDocumentifier()
        self.extract_chapter = Documentifier()
        self.verify_meta = BetaFormatVerifier.from_meta_params()
        self.verify_chapter = BetaFormatVerifier.from_data_params()
        self.requester = RoutedRequester(client, bulk_meta, bulk_data)

    def fetch_meta(self, key: int) -> Dict[str, Any]:
        resource = self.requester.get_meta(int(key))
        meta = self.extract_meta(resource)
        self.verify_meta(meta)

        return meta

    def fetch_data(self, key: int) -> bytes:
        resource = self.requester.get_data(int(key))
        chapters = [self.extract_chapter(chapter) for chapter in resource]

        if not chapters:
            raise InvalidStoryError("Missing chapters.")

        for chapter in chapters:
            self.verify_chapter(chapter)

        chapters.sort(key=lambda chapter: chapter['chapter_number'])

        data = json.dumps(
            chapters,
            indent=4,
            ensure_ascii=False,
            sort_keys=True
        )

        return data.encode()
