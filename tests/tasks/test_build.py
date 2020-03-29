"""
Build task tests.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2020  Joakim Soderlund
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


from pathlib import Path
from unittest.mock import call, patch, MagicMock

import arrow
import pytest

from fimfarchive.tasks import build, BuildTask
from fimfarchive.utils import AUTHOR_BLACKLIST

from .conftest import DummyConverer, DummyFetcher


BLACKLISTED = sorted(AUTHOR_BLACKLIST)[0]


class TestBuildTask:
    """
    Tests build task.
    """

    @pytest.fixture
    def previous(self):
        """
        Returns a `Fetcher` simulating Fimfarchive.
        """
        fetcher = DummyFetcher()

        fetcher.add(key=1, date=1)
        fetcher.add(key=2, date=2)
        fetcher.add(key=3, date=3)

        fetcher.add(key=BLACKLISTED, date=BLACKLISTED)

        return fetcher

    @pytest.fixture
    def upcoming(self):
        """
        Returns a `Fetcher` simulating a directory.
        """
        fetcher = DummyFetcher()

        fetcher.add(key=1, date=1, data=None)
        fetcher.add(key=2, date=2, data=None)
        fetcher.add(key=3, date=4)
        fetcher.add(key=4, date=5)

        fetcher.add(key=BLACKLISTED, date=BLACKLISTED + 1)

        return fetcher

    @pytest.fixture
    def result(self):
        """
        Returns a `Fetcher` simulating the expected result.
        """
        fetcher = DummyFetcher()

        fetcher.add(key=1, date=1)
        fetcher.add(key=2, date=2)
        fetcher.add(key=3, date=4)
        fetcher.add(key=4, date=5)

        for story in fetcher:
            story.meta['conversions'] += 1

        return fetcher

    @pytest.fixture
    def output(self, tmp_path):
        """
        Returns the output path.
        """
        output = tmp_path / 'output'
        output.mkdir()

        return Path(output)

    @pytest.fixture
    def extras_data(self):
        """
        Returns the extra archive data.
        """
        return [
            ('alpaca.txt', b"Alpacas are floofy!"),
            ('pegasus.bin', b"\xF1u\xffy ponies!"),
        ]

    @pytest.fixture
    def extras_path(self, tmp_path, extras_data):
        """
        Returns the extras path.
        """
        extras = tmp_path / 'extras'
        extras.mkdir()

        for name, data in extras_data:
            path = extras / name
            path.write_bytes(data)

        return Path(extras)

    @pytest.fixture
    def task(self, output, upcoming, previous, extras_path):
        """
        Returns a `BuildTask` instance.
        """
        task = BuildTask(
            output=output,
            upcoming=upcoming,
            previous=previous,
            extras=extras_path,
        )

        with patch.object(task, 'convert', DummyConverer()):
            yield task

    def test_path(self, task, output):
        """
        Tests archive output path.
        """
        date = arrow.utcnow().strftime("%Y%m%d")
        name = f'fimfarchive-{date}.zip'
        path = output / name

        assert path.resolve() == task.output.resolve()

    def test_extras(self, task, extras_data):
        """
        Tests extra archive data.
        """
        assert extras_data == sorted(task.extras)

    def test_generate(self, task, result):
        """
        Tests content generator.
        """
        for actual, expected in zip(task.generate(), result):
            assert expected.meta == actual.meta
            assert expected.data == actual.data

    def test_run(self, task):
        """
        Tests writer calls.
        """
        writer = MagicMock()

        manager = patch.object(build, 'FimfarchiveWriter', writer)
        content = patch.object(task, 'generate', return_value=[1, 2, 4])

        with manager, content:
            task.run()

        assert writer.mock_calls == [
            call(task.output, task.extras),
            call().__enter__(),
            call().__enter__().write(1),
            call().__enter__().write(2),
            call().__enter__().write(4),
            call().__exit__(None, None, None),
        ]
