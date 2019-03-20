"""
Local timezone to UTC converter tests.
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
import pytest
from copy import deepcopy

from fimfarchive.converters import LocalUtcConverter


class TestLocalUtcConverter:
    """
    LocalUtcConverter tests.
    """

    @pytest.fixture(params=[
        ('2019-03-20T11:27:58+00:00', '2019-03-20T11:27:58+00:00'),
        ('2019-03-20T12:29:15+01:00', '2019-03-20T11:29:15+00:00'),
        ('1970-01-01T00:00:00+00:00', None),
        ('1970-01-01T01:00:00+01:00', None),
        (None, None),
    ])
    def date_pair(self, request):
        """
        Returns a date pair.
        """
        local, utc = request.param

        return local, utc

    @pytest.fixture(params=[
        '{"a":{"b":{"c":{"d":"e"}}}}',
        '{"a":{"b":{"c":{"date_x":?}}}}',
        '{"a":{"b":{"c":{"date_x":?,"date_y":?}}}}',
        '{"a":{"b":{"c":{"date_x":?},"date_y":?}}}',
        '{"a":{"b":{"c":{"date_x":?}},"date_y":?}}',
        '{"date_x":?,"kittens":"2019-03-20T13:06:13+01:00","a":{"date_x":?}}',
        '{"date_x":?,"kittens":"2019-03-20T13:06:13+01:00","date_y":?}',
    ])
    def meta_pair(self, request, date_pair):
        """
        Returns a meta pair.
        """
        template = request.param
        local_date, utc_date = date_pair

        local_value = json.dumps(local_date)
        local_json = template.replace('?', local_value)
        local_meta = json.loads(local_json)

        utc_value = json.dumps(utc_date)
        utc_json = template.replace('?', utc_value)
        utc_meta = json.loads(utc_json)

        return local_meta, utc_meta

    @pytest.fixture
    def converter(self):
        """
        Returns a converter instance.
        """
        return LocalUtcConverter()

    def test_conversion(self, converter, story, meta_pair):
        """
        Tests local to UTC conversion.
        """
        local_meta, utc_meta = meta_pair

        local_story = story.merge(meta=local_meta)
        utc_story = story.merge(meta=utc_meta)

        clone = deepcopy(local_story)
        converted = converter(local_story)

        assert clone.meta == local_story.meta
        assert utc_story.meta == converted.meta
