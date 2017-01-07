"""
Mapper tests.
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


import os
from unittest.mock import MagicMock

import pytest

from fimfarchive.mappers import StaticMapper, StoryPathMapper


class TestStaticMapper:
    """
    StaticMapper tests.
    """

    @pytest.fixture
    def value(self):
        """
        Returns a unique instance.
        """
        return object()

    def test_value(self, value):
        """
        Tests returns the supplied value.
        """
        mapper = StaticMapper(value)
        assert mapper() is value

    def test_default_value(self):
        """
        Tests `None` is returned by default.
        """
        mapper = StaticMapper()
        assert mapper() is None

    def test_args(self, value):
        """
        Tests callable ignores args.
        """
        mapper = StaticMapper(value)
        assert mapper(1, 2, 3) is value

    def test_kwargs(self, value):
        """
        Tests callable ignores kwargs.
        """
        mapper = StaticMapper(value)
        assert mapper(a=1, b=2) is value


class TestStoryPathMapper:
    """
    StoryPathMapper tests.
    """

    def test_joins_paths(self, story):
        """
        Tests returns directory joined with story key.
        """
        directory = os.path.join('some', 'directory')
        path = os.path.join(directory, str(story.key))

        mapper = StoryPathMapper(directory)

        assert mapper(story) == path

    def test_casts_values(self, tmpdir, story):
        """
        Tests casts all values to string when joining.
        """
        directory = MagicMock()
        directory.__str__.return_value = 'dir'

        story.key = MagicMock()
        story.key.__str__.return_value = 'key'

        mapper = StoryPathMapper(directory)

        assert mapper(story) == os.path.join('dir', 'key')
        assert directory.__str__.called_once_with()
        assert story.key.__str__.called_once_with()
