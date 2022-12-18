"""
FPUB to EPUB converter for story data.
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


from functools import partial
from pathlib import Path
from shutil import rmtree
from subprocess import DEVNULL, STDOUT, run
from tempfile import mkdtemp
from typing import Union

from fimfarchive.flavors import DataFormat
from fimfarchive.stories import Story
from fimfarchive.utils import get_path

from .base import Converter


__all__ = (
    'FpubEpubConverter',
)


SOURCE = 'source.epub'
TARGET = 'target.epub'
TIMEOUT = 300

PROGRAM = 'ebook-convert'
ARGUMENTS = ('--no-default-epub-cover',)

proc = partial(run, stderr=STDOUT, timeout=TIMEOUT, check=True)


def ebook_convert(data: bytes, pipe: int = DEVNULL) -> bytes:
    """
    Calls the external ebook-convert program.
    """
    parent = Path(mkdtemp())
    source = parent / SOURCE
    target = parent / TARGET

    command = (PROGRAM, str(source), str(target), *ARGUMENTS)

    try:
        source.write_bytes(data)
        proc(command, stdout=pipe)
    except Exception:
        raise
    else:
        return target.read_bytes()
    finally:
        rmtree(parent)


class FpubEpubConverter(Converter):
    """
    Converts story data from FPUB to EPUB.
    """

    def __init__(self, logdir: Union[None, Path, str] = None) -> None:
        self.logdir = get_path(logdir)

        if self.logdir and not self.logdir.is_dir():
            raise ValueError("Logdir must be a directory.")

    def __call__(self, story: Story) -> Story:
        if DataFormat.FPUB not in story.flavors:
            raise ValueError(f"Missing flavor: {DataFormat.FPUB}")

        if self.logdir is not None:
            with open(self.logdir / str(story.key), 'a') as fobj:
                data = ebook_convert(story.data, fobj.fileno())
        else:
            data = ebook_convert(story.data)

        flavors = set(story.flavors)
        flavors.remove(DataFormat.FPUB)
        flavors.add(DataFormat.EPUB)

        return story.merge(data=data, flavors=flavors)
