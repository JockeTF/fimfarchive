"""
Update task.
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
import time
from copy import deepcopy
from typing import Optional

from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.fetchers import Fetcher
from fimfarchive.flavors import DataFormat, StorySource, UpdateStatus
from fimfarchive.mappers import StoryPathMapper
from fimfarchive.selectors import Selector, UpdateSelector
from fimfarchive.signals import Signal, SignalSender
from fimfarchive.stampers import Stamper, UpdateStamper
from fimfarchive.stories import Story
from fimfarchive.utils import PersistedDict
from fimfarchive.writers import DirectoryWriter


DEFAULT_WORKDIR = 'worktree/update'
DEFAULT_RETRIES = 10
DEFAULT_SKIPS = 500


#
# Lowering request delays could jeopordize the future of the archive.
#
# These timings are here so that the updater does not flood Fimfiction
# with requests. One spammy synchronous client would not take down the
# site. It might however make the site owners want to prevent archiving
# in the future. Consider downloading a Fimfarchive release instead.
#
# http://www.fimfarchive.net/
#

SUCCESS_DELAY = 5
SKIPPED_DELAY = 2
FAILURE_DELAY = 300


class UpdateTask(SignalSender):
    """
    Updates Fimfarchive.
    """
    on_attempt = Signal('key', 'skips', 'retries')
    on_success = Signal('key', 'story')
    on_skipped = Signal('key', 'story')
    on_failure = Signal('key', 'error')

    state_file = 'state.json'
    state_vars = {'key': 0}

    def __init__(
            self,
            fimfarchive: Fetcher,
            fimfiction: Fetcher,
            selector: Optional[Selector] = None,
            stamper: Optional[Stamper] = None,
            workdir: str = DEFAULT_WORKDIR,
            retries: int = DEFAULT_RETRIES,
            skips: int = DEFAULT_SKIPS,
            ) -> None:
        """
        Constructor.

        Args:
            fimfarchive: Fetcher for the old release.
            fimfiction: Fetcher for the new release.
            selector: Selector for which story to save.
            stamper: Stamper for adding story information.
            workdir: Path for storage of state and stories.
            retries: Number of retries before giving up.
            skips: Number of skips before giving up.
        """
        super().__init__()

        if selector is None:
            selector = UpdateSelector()

        if stamper is None:
            stamper = UpdateStamper()

        self.fimfarchive = fimfarchive
        self.fimfiction = fimfiction
        self.select = selector
        self.stamp = stamper
        self.workdir = workdir
        self.retries = retries
        self.skips = skips

        os.makedirs(self.workdir, exist_ok=True)
        state_path = os.path.join(self.workdir, self.state_file)
        self.state = PersistedDict(state_path, self.state_vars)

        meta_mapper = self.get_mapper('meta')
        skip_mapper = self.get_mapper('skip')
        epub_mapper = self.get_mapper('epub')
        html_mapper = self.get_mapper('html')
        json_mapper = self.get_mapper('json')

        self.meta_writer = DirectoryWriter(meta_mapper)
        self.skip_writer = DirectoryWriter(skip_mapper)
        self.epub_writer = DirectoryWriter(meta_mapper, epub_mapper)
        self.html_writer = DirectoryWriter(meta_mapper, html_mapper)
        self.json_writer = DirectoryWriter(meta_mapper, json_mapper)

    def get_mapper(self, subdir: str) -> StoryPathMapper:
        """
        Creates a mapper to the specified subdirectory.

        Args:
            subdir: Subdirectory for the mapper.
        """
        directory = os.path.join(self.workdir, subdir)
        return StoryPathMapper(directory)

    def fetch(self, fetcher: Fetcher, key: int) -> Optional[Story]:
        """
        Fetches a story unless invalid.

        Args:
            fetcher: Source for the story.
            key: Primary key of the story.

        Raises:
            StorySourceError: If the fetcher fails.
        """
        try:
            return fetcher.fetch(key)
        except InvalidStoryError:
            return None

    def write(self, story: Story) -> None:
        """
        Passes the story to the appropriate writer.

        Args:
            story: Object to write.

        Raises:
            ValueError: If story flavor is unsupported.
        """
        if StorySource.FIMFARCHIVE in story.flavors:
            self.meta_writer.write(story)
        elif DataFormat.HTML in story.flavors:
            self.html_writer.write(story)
        elif DataFormat.JSON in story.flavors:
            self.json_writer.write(story)
        elif DataFormat.EPUB in story.flavors:
            self.epub_writer.write(story)
        else:
            raise ValueError("Unsupported story flavor.")

    def copy_archive_meta(
            self,
            old: Optional[Story],
            new: Optional[Story],
            ) -> None:
        """
        Copies archive meta from old story to new.

        Args:
            old: The story to copy from.
            new: The story to copy to.

        Raises:
            ValueError: If new story already contains archive meta.
        """
        if old is None or new is None:
            return

        try:
            if 'archive' in new.meta:
                raise ValueError("New story contains archive meta.")

            new.meta['archive'] = deepcopy(old.meta['archive'])
        except (InvalidStoryError, KeyError):
            return

    def update(self, key: int) -> Optional[Story]:
        """
        Updates the specified story.

        args:
            key: Primary key of the story to update.

        Raises:
            StorySourceError: If any fetcher fails.
        """
        old = self.fetch(self.fimfarchive, key)
        new = self.fetch(self.fimfiction, key)

        self.copy_archive_meta(old, new)
        selected = self.select(old, new)

        if selected and UpdateStatus.REVIVED in selected.flavors:
            assert new is not None
            selected = selected.merge(meta=new.meta)

        if selected:
            self.stamp(selected)
            self.write(selected)
        elif new:
            self.skip_writer.write(new)
        elif old:
            self.skip_writer.write(old)

        return selected

    def run(self) -> None:
        """
        Runs the updater task.
        """
        retried = 0
        skipped = 0

        while skipped < self.skips and retried < self.retries:
            key = self.state['key']

            self.on_attempt(key, skipped, retried)

            try:
                story = self.update(key)
            except Exception as e:
                retried += 1
                self.on_failure(key, e)
                time.sleep(FAILURE_DELAY)
            else:
                retried = 0
                self.state['key'] += 1
                self.state.save()

                if story:
                    skipped = 0
                    self.on_success(key, story)
                    time.sleep(SUCCESS_DELAY)
                else:
                    skipped += 1
                    self.on_skipped(key, story)
                    time.sleep(SKIPPED_DELAY)
