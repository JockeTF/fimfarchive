"""
Directory fetcher.
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
import os
from typing import Any, Dict, Iterable

from fimfarchive.exceptions import InvalidStoryError, StorySourceError
from fimfarchive.flavors import Flavor

from .base import Fetcher


__all__ = (
    'DirectoryFetcher',
)


class DirectoryFetcher(Fetcher):
    """
    Fetches stories from file system.
    """
    prefetch_meta = True
    prefetch_data = False

    def __init__(
            self,
            meta_path: str,
            data_path: str,
            flavors: Iterable[Flavor],
            ) -> None:
        """
        Constructor.

        Args:
            meta: The directory for story meta.
            data: The directory for story data.
            flavors: The flavors to add to stories.
        """
        self.meta_path = meta_path
        self.data_path = data_path
        self.flavors = frozenset(flavors)

    def read_file(self, path: str) -> bytes:
        """
        Reads file data for the path.

        Args:
            path: The path to read from.

        Returns:
            The file contents as bytes.

        Raises:
            InvalidStoryError: If the file does not exist.
            StorySourceError: If the file could not be read.
        """
        try:
            with open(path, 'rb') as fobj:
                return fobj.read()
        except FileNotFoundError as e:
            raise InvalidStoryError("File does not exist.") from e
        except Exception as e:
            raise StorySourceError("Unable to read file.") from e

    def fetch_data(self, key: int) -> bytes:
        path = os.path.join(self.data_path, str(key))
        raw = self.read_file(path)

        return raw

    def fetch_meta(self, key: int) -> Dict[str, Any]:
        path = os.path.join(self.meta_path, str(key))
        raw = self.read_file(path)

        return json.loads(raw.decode())
