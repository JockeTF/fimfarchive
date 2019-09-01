"""
Fetch task.
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


from typing import Iterable

from fimfarchive.converters import FpubEpubConverter, JsonFpubConverter
from fimfarchive.fetchers import Fetcher
from fimfarchive.writers import Writer
from fimfarchive.signals import Signal, SignalSender


__all__ = (
    'FetchTask',
)


class FetchTask(SignalSender):
    """
    Fetches a story and writes it to the current directory.
    """
    on_attempt = Signal('key')
    on_success = Signal('key', 'story')
    on_failure = Signal('key', 'error')

    def __init__(
            self,
            keys: Iterable[int],
            fetcher: Fetcher,
            writer: Writer,
            ) -> None:
        """
        Constructor.

        Args:
            keys: Stories to fetch.
            fetcher: Story source.
            writer: Story target.
        """
        super().__init__()
        self.fetcher = fetcher
        self.writer = writer
        self.to_fpub = JsonFpubConverter()
        self.to_epub = FpubEpubConverter()
        self.keys = sorted(set(keys))

    def run(self) -> None:
        """
        Runs the task.
        """
        for key in sorted(set(self.keys)):
            self.on_attempt(key)

            try:
                json = self.fetcher.fetch(key)
                fpub = self.to_fpub(json)
                epub = self.to_epub(fpub)
                self.writer.write(epub)
                self.on_success(key, epub)
            except Exception as e:
                self.on_failure(key, e)
