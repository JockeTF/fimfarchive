"""
Alpha to beta converter tests.
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
from typing import Any, Dict

import arrow
import pytest

from fimfarchive.converters import AlphaBetaConverter
from fimfarchive.flavors import MetaFormat


def to_null(data: Dict[str, Any], *keys: str) -> None:
    """
    Nulls the requested keys.
    """
    for key in keys:
        data[key] = None


def to_utc(data: Dict[str, Any], *keys: str) -> None:
    """
    Converts the requested keys to UTC time strings.
    """
    for key in keys:
        value = data.get(key)

        if value is None:
            continue

        time = arrow.get(value).to('utc')
        data[key] = time.isoformat()


@pytest.fixture(scope='module')
def data():
    """
    Returns test data from JSON.
    """
    path = f'{__file__[:-3]}.json'

    with open(path, 'rt') as fobj:
        return json.load(fobj)


class TestAlphaBetaConverter:
    """
    AlphaBetaConverter tests.
    """

    @pytest.fixture
    def converter(self):
        """
        Returns an alpha beta converter instance.
        """
        return AlphaBetaConverter()

    @pytest.fixture(params=range(1))
    def pair(self, request, data):
        """
        Returns meta test data pairs.
        """
        return data['pairs'][request.param]

    @pytest.fixture
    def alpha(self, pair):
        """
        Returns meta in alpha format.
        """
        return deepcopy(pair['alpha'])

    @pytest.fixture
    def beta(self, pair):
        """
        Returns meta in beta format.
        """
        return deepcopy(pair['beta'])

    @pytest.fixture
    def expected(self, beta):
        """
        Returns the expected meta result.
        """
        data = deepcopy(beta)

        data['archive'] = {
            'date_checked': None,
            'date_created': None,
            'date_fetched': None,
            'date_updated': None,
            'path': None,
        }

        to_null(data, 'color', 'date_published')
        to_utc(data, 'date_modified', 'date_updated')

        to_null(data['author'], *(
            'avatar',
            'bio_html',
            'date_joined',
            'num_blog_posts',
            'num_followers',
            'num_stories',
        ))

        for chapter in data['chapters']:
            to_null(chapter, 'date_published')
            to_utc(chapter, 'date_modified')

        data['tags'] = [
            tag for tag in data['tags']
            if tag['type'] in {'content', 'genre', 'series'}
        ]

        return data

    def test_conversion(self, converter, story, expected, alpha):
        """
        Tests conversion of story meta from alpha to beta format.
        """
        story = story.merge(flavors=[MetaFormat.ALPHA], meta=alpha)
        converted = converter(story)

        assert MetaFormat.BETA in converted.flavors
        assert expected == converted.meta
