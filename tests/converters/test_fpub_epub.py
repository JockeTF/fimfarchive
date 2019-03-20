"""
FPUB to EPUB converter tests.
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


from os import urandom, write
from pathlib import Path
from subprocess import DEVNULL
from unittest.mock import patch

import pytest

from fimfarchive.converters import fpub_epub, FpubEpubConverter
from fimfarchive.flavors import DataFormat


class TestFpubEpubConverter:
    """
    FpubEpubConverter tests.
    """

    @pytest.fixture
    def fpub(self):
        """
        Returns bytes simulating FPUB data.
        """
        return urandom(16)

    @pytest.fixture
    def epub(self):
        """
        Returns bytes simulating EPUB data.
        """
        return urandom(16)

    @pytest.fixture
    def log(self):
        """
        Returns bytes simulating log data.
        """
        return urandom(16)

    @pytest.fixture
    def calibre(self, fpub, epub, log):
        """
        Returns a function simulating Calibre.
        """
        def function(*args, **kwargs):
            source = Path(args[0][1])
            target = Path(args[0][2])
            stdout = kwargs['stdout']

            if 0 <= stdout:
                write(stdout, log)

            if fpub == source.read_bytes():
                target.write_bytes(epub)

        return function

    @pytest.fixture
    def proc(self, calibre):
        """
        Yeilds a mock for simulating process calls.
        """
        with patch.object(fpub_epub, 'proc') as mock:
            mock.side_effect = calibre
            yield mock

    @pytest.fixture
    def story(self, story, fpub):
        """
        Returns an FPUB story instance.
        """
        return story.merge(data=fpub, flavors=[DataFormat.FPUB])

    def verify_call(self, call, pipe):
        """
        Verifies process call arguments.
        """
        name, args, kwargs = call
        program, source, target, cover = args[0]
        stdout = kwargs['stdout']

        assert 1 == len(args)
        assert 1 == len(kwargs)

        assert 'ebook-convert' == program
        assert 'source.epub' == Path(source).name
        assert 'target.epub' == Path(target).name
        assert '--no-default-epub-cover' == cover

        assert pipe is (DEVNULL != stdout)

    def test_without_log(self, story, fpub, epub, proc):
        """
        Tests convertion without logging.
        """
        convert = FpubEpubConverter()
        output = convert(story)
        calls = proc.mock_calls

        assert 1 == len(calls)
        assert fpub == story.data
        assert epub == output.data

        self.verify_call(calls[0], False)

    def test_with_log(self, tmpdir, story, fpub, epub, log, proc):
        """
        Tests convertion with logging.
        """
        tmppath = Path(str(tmpdir))
        convert = FpubEpubConverter(tmppath)
        logfile = tmppath / str(story.key)
        output = convert(story)
        calls = proc.mock_calls

        assert 1 == len(calls)
        assert fpub == story.data
        assert epub == output.data
        assert log == logfile.read_bytes()

        self.verify_call(calls[0], True)
