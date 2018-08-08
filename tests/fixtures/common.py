"""
Common pytest fixtures.
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


from unittest.mock import MagicMock

import pytest

from fimfarchive.fetchers import Fetcher
from fimfarchive.flavors import Flavor
from fimfarchive.stories import Story


@pytest.fixture
def fetcher():
    """
    Returns a parially mocked fetcher instance.
    """
    fetcher = Fetcher()

    fetcher.fetch_meta = MagicMock(method='fetch_meta')  # type: ignore
    fetcher.fetch_data = MagicMock(method='fetch_data')  # type: ignore

    return fetcher


@pytest.fixture
def flavor():
    """
    Returns a flavor with A and B members.
    """
    class MyFlavor(Flavor):
        A = ()
        B = ()

    return MyFlavor


@pytest.fixture
def story(flavor):
    """
    Returns a non-lazy dummy story.
    """
    story = Story(
        key=1,
        fetcher=None,
        meta={'id': 1},
        data=b'<html />',
        flavors={flavor.A},
    )

    return story
