"""
Update task tests.
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


from unittest.mock import MagicMock, call, patch

import pytest

from fimfarchive.exceptions import InvalidStoryError, StorySourceError
from fimfarchive.fetchers import Fetcher
from fimfarchive.flavors import DataFormat, UpdateStatus
from fimfarchive.selectors import RefetchSelector, UpdateSelector
from fimfarchive.stories import Story
from fimfarchive.tasks.update import (
    UpdateTask, SUCCESS_DELAY, SKIPPED_DELAY, FAILURE_DELAY,
)


class DummyFetcher(Fetcher):
    """
    Fetcher with local instance storage.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.stories = dict()

    def add(self, key, date, flavors=()):
        """
        Adds a story to the fetcher.
        """
        story = Story(
            key=key,
            flavors=flavors,
            data=f'Story {key}',
            meta={
                'id': key,
                'date_modified': date,
                'chapters': [
                    {'id': key},
                ],
            },
        )

        self.stories[key] = story

        return story

    def fetch(self, key):
        """
        Returns a previously stored story.
        """
        try:
            return self.stories[key]
        except KeyError:
            raise InvalidStoryError()


class TestUpdateTask:
    """
    Tests update task.
    """

    @pytest.fixture
    def fimfiction(self):
        """
        Returns a `Fetcher` simulating Fimfiction.
        """
        return DummyFetcher()

    @pytest.fixture
    def fimfarchive(self):
        """
        Returns a `Fetcher` simulating Fimfarchive.
        """
        return DummyFetcher()

    @pytest.fixture
    def selector(self):
        """
        Returns an `UpdateSelector` instance.
        """
        return UpdateSelector()

    @pytest.fixture
    def task(self, fimfarchive, fimfiction, selector, tmpdir):
        """
        Returns an `UpdateTask` instance.
        """
        return UpdateTask(
            fimfiction=fimfiction,
            fimfarchive=fimfarchive,
            selector=selector,
            workdir=str(tmpdir),
            retries=2,
            skips=2,
        )

    def verify_run(self, task, delays):
        """
        Runs the task and verifies delays.
        """
        calls = [call(delay) for delay in delays]

        with patch('time.sleep') as m:
            task.run()
            m.assert_has_calls(calls)

    def verify_fetch(self, task, target, status):
        """
        Runs the task and verifies a regular fetch.
        """
        task.write = MagicMock(side_effect=lambda story: story)

        delays = (
            SKIPPED_DELAY,
            SUCCESS_DELAY,
            SKIPPED_DELAY,
            SKIPPED_DELAY,
        )

        self.verify_run(task, delays)
        task.write.assert_called_once_with(target)
        assert status in target.flavors
        assert task.state['key'] == 4

    def verify_empty(self, task, fetcher):
        """
        Runs the task and verifies an empty fetch.
        """
        task.skip_writer.write = MagicMock()

        target = fetcher.add(key=1, date=1)
        target.meta['chapters'].clear()

        delays = (
            SKIPPED_DELAY,
            SKIPPED_DELAY,
        )

        self.verify_run(task, delays)
        task.skip_writer.write.assert_called_once_with(target)

    def verify_failure(self, task, fetcher):
        """
        Runs the task and verifies a failed fetch.
        """
        task.write = MagicMock(side_effect=lambda story: story)
        fetcher.fetch = MagicMock(side_effect=StorySourceError)

        delays = (
            FAILURE_DELAY,
            FAILURE_DELAY,
        )

        self.verify_run(task, delays)
        task.write.assert_not_called()

    def test_created_story(self, task, fimfiction):
        """
        Tests updating for a created story.
        """
        target = fimfiction.add(key=1, date=1)

        self.verify_fetch(task, target, UpdateStatus.CREATED)

    def test_revived_story(self, task, fimfarchive, fimfiction):
        """
        Tests updating for a revived story.
        """
        target = fimfarchive.add(key=1, date=1)
        other = fimfiction.add(key=1, date=1)

        target.merge = MagicMock(return_value=target)
        self.verify_fetch(task, target, UpdateStatus.REVIVED)
        target.merge.assert_called_once_with(meta=other.meta)

    def test_updated_story(self, task, fimfarchive, fimfiction):
        """
        Tests updating for an updated story.
        """
        fimfarchive.add(key=1, date=0)
        target = fimfiction.add(key=1, date=1)

        self.verify_fetch(task, target, UpdateStatus.UPDATED)

    def test_deleted_story(self, task, fimfarchive):
        """
        Test updating for a deleted story.
        """
        target = fimfarchive.add(key=1, date=1)

        self.verify_fetch(task, target, UpdateStatus.DELETED)

    def test_cleared_story(self, task, fimfarchive, fimfiction):
        """
        Tests updating for a cleared story.
        """
        target = fimfarchive.add(key=1, date=0)
        other = fimfiction.add(key=1, date=1)
        other.meta['chapters'].clear()

        self.verify_fetch(task, target, UpdateStatus.DELETED)

    def test_empty_fimfiction_story(self, task, fimfiction):
        """
        Tests updating for an empty story from fimfiction.
        """
        self.verify_empty(task, fimfiction)

    def test_empty_fimfarchive_story(self, task, fimfarchive):
        """
        Tests updating for an empty story from fimfarchive.
        """
        self.verify_empty(task, fimfarchive)

    def test_fimfarchive_failure(self, task, fimfarchive):
        """
        Tests handling of a failure in Fimfarchive.
        """
        self.verify_failure(task, fimfarchive)

    def test_fimfiction_failure(self, task, fimfiction):
        """
        Tests handling of a failure in Fimfiction.
        """
        self.verify_failure(task, fimfiction)

    def test_write_epub(self, task, story):
        """
        Tests writing of a story in EPUB format.
        """
        story = story.merge(flavors=[DataFormat.EPUB])
        task.epub_writer.write = MagicMock()

        task.write(story)
        task.epub_writer.write.assert_called_once_with(story)

    def test_write_html(self, task, story):
        """
        Tests writing of a story in HTML format.
        """
        story = story.merge(flavors=[DataFormat.HTML])
        task.html_writer.write = MagicMock()

        task.write(story)
        task.html_writer.write.assert_called_once_with(story)

    def test_write_unsupported(self, task, story):
        """
        Tests `ValueError` is raised for unknown data formats.
        """
        story = story.merge(flavors=[DataFormat.FPUB])

        with pytest.raises(ValueError):
            task.write(story)


class TestRefetchingUpdateTask(TestUpdateTask):
    """
    Tests update task with a refetch selector.
    """

    @pytest.fixture
    def selector(self):
        """
        Returns a `RefetchSelector` instance.
        """
        return RefetchSelector()

    def test_revived_story(self, task, fimfarchive, fimfiction):
        """
        Tests updating for a revived story.
        """
        fimfarchive.add(key=1, date=1)
        target = fimfiction.add(key=1, date=1)

        self.verify_fetch(task, target, UpdateStatus.UPDATED)