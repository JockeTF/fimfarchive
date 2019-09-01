"""
Count command.
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


from typing import Set

from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.fetchers import DirectoryFetcher, FimfarchiveFetcher
from fimfarchive.utils import is_blacklisted, tqdm

from .base import Command


__all__ = (
    'CountCommand',
)


class CountCommand(Command):
    "Mwap!"

    def __call__(self, *args):
        fimfarchive = FimfarchiveFetcher(
            source='fimfarchive.zip'
        )

        directory = DirectoryFetcher(
            meta_path='worktree/update/meta',
            data_path='worktree/render/epub',
        )

        previous: Set[int] = set(fimfarchive.index.keys())
        upcoming: Set[int] = set()

        blocked: Set[int] = set()
        created: Set[int] = set()
        deleted: Set[int] = set()
        revived: Set[int] = set()
        updated: Set[int] = set()
        uniform: Set[int] = set()

        for new in tqdm(directory):
            key = new.key

            if key != new.meta['id']:
                raise ValueError("Derpy ID.")

            if is_blacklisted(new):
                blocked.add(key)
                continue

            upcoming.add(key)

            if key not in previous:
                created.add(key)
                continue

            try:
                new.data
            except InvalidStoryError:
                revived.add(key)
                continue

            old = fimfarchive.fetch(key)

            if key != old.meta['id']:
                raise ValueError("Derpy ID.")

            if old.data != new.data:
                updated.add(key)
                continue

            uniform.add(key)

        deleted = previous - upcoming

        info = [
            f"Previous: {len(previous)}",
            f"Upcoming: {len(upcoming)}",
            f"Created: {len(created)}",
            f"Revived: {len(revived)}",
            f"Updated: {len(updated)}",
            f"Deleted: {len(deleted)}",
            f"Blocked: {len(blocked)}",
            f"Uniform: {len(uniform)}",
        ]

        print('\n'.join(info))

        return 0
