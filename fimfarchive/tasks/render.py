"""
Render task.
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


from multiprocessing import Pool
from os import cpu_count
from pathlib import Path
from typing import List, Optional, Tuple

from fimfarchive.converters import JsonFpubConverter, FpubEpubConverter
from fimfarchive.fetchers import DirectoryFetcher
from fimfarchive.flavors import DataFormat, MetaFormat
from fimfarchive.mappers import MetaFormatMapper
from fimfarchive.signals import Signal, SignalSender
from fimfarchive.stories import Story
from fimfarchive.writers import DirectoryWriter


__all__ = (
    'RenderTask',
)


WORKERS = 4
WORKTREE = 'worktree'


class PathSpec:
    def __init__(self, worktree: str) -> None:
        self.worktree = Path(worktree)
        self.source = self.worktree / 'update'
        self.target = self.worktree / 'render'
        self.meta = self.source / 'meta'
        self.json = self.source / 'json'
        self.epub = self.target / 'epub'
        self.logs = self.target / 'logs'

    def verify_dir(self, path: Path) -> None:
        if not path.is_dir():
            raise ValueError(f"Missing dir: {path}")

    def create_dir(self, path: Path) -> None:
        path.mkdir(mode=0o755, parents=True, exist_ok=True)

    def prepare(self) -> None:
        self.verify_dir(self.meta)
        self.verify_dir(self.json)
        self.create_dir(self.epub)
        self.create_dir(self.logs)


class Executor:
    initialized: bool = False

    def __init__(self, worktree: str) -> None:
        self.worktree = worktree

    def initialize(self) -> None:
        path = PathSpec(self.worktree)

        self.fetcher = DirectoryFetcher(
            meta_path=path.meta,
            data_path=path.json,
            flavors=[DataFormat.JSON],
        )

        self.writer = DirectoryWriter(
            data_path=str(path.epub),
            make_dirs=False,
        )

        self.to_fpub = JsonFpubConverter()
        self.to_epub = FpubEpubConverter(str(path.logs))
        self.get_meta_format = MetaFormatMapper()
        self.initialized = True

    def fetch(self, key: int) -> Story:
        story = self.fetcher.fetch(key)

        if MetaFormat.BETA in story.flavors:
            raise ValueError("Flavor should not be static: {MetaFormat.BETA}")

        if self.get_meta_format(story) != MetaFormat.BETA:
            raise ValueError("Flavor could not be detected: {MetaFormat.BETA}")

        story.flavors.add(MetaFormat.BETA)

        return story

    def apply(self, key: int) -> None:
        json = self.fetch(key)
        fpub = self.to_fpub(json)
        epub = self.to_epub(fpub)
        self.writer.write(epub)

    def __call__(self, key: int) -> Tuple[int, Optional[str]]:
        if not self.initialized:
            self.initialize()

        try:
            self.apply(key)
        except Exception as e:
            return key, f"{type(e).__name__}: {e}"
        else:
            return key, None


class RenderTask(SignalSender):
    on_enter = Signal('keys', 'workers', 'spec')
    on_exit = Signal('converted', 'remaining')
    on_success = Signal('key')
    on_failure = Signal('key', 'error')

    def __init__(self, worktree: str = WORKTREE) -> None:
        """
        Constructor.
        """
        super().__init__()
        self.worktree = worktree

    def subtasks(self, spec: PathSpec) -> List[int]:
        sources = {int(path.name) for path in spec.json.iterdir()}
        targets = {int(path.name) for path in spec.epub.iterdir()}

        return sorted(sources - targets)

    def run(self) -> None:
        spec = PathSpec(self.worktree)

        spec.prepare()
        keys = self.subtasks(spec)
        func = Executor(self.worktree)

        cpus = cpu_count() or 0
        workers = cpus // 2 or WORKERS
        converted: List[int] = list()
        remaining: List[int] = list()

        self.on_enter(keys, workers, spec)

        with Pool(workers) as pool:
            mapper = pool.imap_unordered(func, keys)

            for key, error in mapper:
                if error is None:
                    converted.append(key)
                    self.on_success(key)
                else:
                    remaining.append(key)
                    self.on_failure(key, error)

        self.on_exit(converted, remaining)
