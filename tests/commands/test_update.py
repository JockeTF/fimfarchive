"""
Update command tests.
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


from textwrap import dedent
from typing import Any, Dict, Set

from fimfarchive.flavors import Flavor, MetaPurity, UpdateStatus
from fimfarchive.commands.update import StoryFormatter


class TestStoryFormatter():
    """
    StoryFormatter tests.
    """

    def assert_formatted_equals(self, expected, story):
        """
        Asserts that the formatted story matches the expected text.
        """
        formatted = str(StoryFormatter(story))
        dedented = dedent(expected).strip()

        assert dedented == formatted

    def test_empty_meta(self, story):
        """
        Tests story formatting with empty meta.
        """
        flavors: Set[Flavor] = set()
        meta: Dict[str, Any] = dict()

        expected = """
            Title: None
            Author: None
            Status: None
            Words: None
            Likes: None
            Dislikes: None
            Approval: None
            Chapters: None
            Action: None
        """

        story = story.merge(meta=meta, flavors=flavors)
        self.assert_formatted_equals(expected, story)

    def test_old_meta(self, story):
        """
        Tests story formatting with old-style meta.
        """
        flavors: Set[Flavor] = {
            UpdateStatus.CREATED,
        }

        meta: Dict[str, Any] = {
            'title': 'A',
            'author': {
                'name': 'B'
            },
            'status': 'C',
            'words': 4,
            'likes': 3,
            'dislikes': 2,
            'chapters': [
                1
            ],
        }

        expected = """
            Title: A
            Author: B
            Status: C
            Words: 4
            Likes: 3
            Dislikes: 2
            Approval: 60%
            Chapters: 1
            Action: Created
        """

        story = story.merge(meta=meta, flavors=flavors)
        self.assert_formatted_equals(expected, story)

    def test_new_meta(self, story):
        """
        Tests story formatting with new-style meta.
        """
        flavors: Set[Flavor] = {
            UpdateStatus.CREATED,
        }

        meta: Dict[str, Any] = {
            'title': 'A',
            'author': {
                'name': 'B'
            },
            'status': 'visible',
            'completion_status': 'C',
            'num_words': 4,
            'num_likes': 3,
            'num_dislikes': 2,
            'chapters': [
                1
            ],
        }

        expected = """
            Title: A
            Author: B
            Status: C
            Words: 4
            Likes: 3
            Dislikes: 2
            Approval: 60%
            Chapters: 1
            Action: Created
        """

        story = story.merge(meta=meta, flavors=flavors)
        self.assert_formatted_equals(expected, story)

    def test_edge_meta(self, story):
        """
        Tests story formatting with some edge cases.
        """
        flavors: Set[Flavor] = {
            MetaPurity.DIRTY,
        }

        meta: Dict[str, Any] = {
            'title': None,
            'author': {},
            'status': {},
            'words': 0,
            'likes': 0,
            'dislikes': 0,
            'chapters': (),
        }

        expected = """
            Title: None
            Author: None
            Status: {}
            Words: 0
            Likes: 0
            Dislikes: 0
            Approval: 0%
            Chapters: 0
            Action: None
        """

        story = story.merge(meta=meta, flavors=flavors)
        self.assert_formatted_equals(expected, story)
