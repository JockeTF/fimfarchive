"""
Local timezone to UTC converter.
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


from copy import deepcopy
from typing import Any, Optional

import arrow

from fimfarchive.stories import Story
from fimfarchive.utils import JayWalker

from .base import Converter


class DateNormalizer(JayWalker):
    """
    Normalizes timezones of date values to UTC.
    """

    def handle(self, data, key, value) -> None:
        if str(key).startswith('date_'):
            data[key] = self.normalize(value)
        else:
            self.walk(value)

    def normalize(self, value: Any) -> Optional[str]:
        """
        Normalizes a single date value.
        """
        parsed = arrow.get(value or 0)

        if parsed.int_timestamp == 0:
            return None

        return parsed.to('utc').isoformat()


class LocalUtcConverter(Converter):
    """
    Converts date strings to UTC.
    """

    def __init__(self) -> None:
        self.normalizer = DateNormalizer()

    def __call__(self, story: Story) -> Story:
        meta = deepcopy(story.meta)
        self.normalizer.walk(meta)

        return story.merge(meta=meta)
