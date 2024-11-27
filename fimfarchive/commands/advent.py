# /usr/bin/env python3

from copy import deepcopy
from datetime import datetime
from io import BytesIO
from math import ceil
from pathlib import Path
from typing import Iterator
from xml.dom import minidom
from xml.dom.minidom import Document
from zipfile import ZipFile

from PIL import Image, ImageDraw, ImageFont
from requests import get

from fimfarchive.converters import Converter
from fimfarchive.fetchers import FimfarchiveFetcher
from fimfarchive.mappers import StorySlugMapper
from fimfarchive.stories import Story
from fimfarchive.writers import DirectoryWriter

from .base import Command

dt = datetime.fromisoformat


DATE_START = dt("2023-12-01T00:00:00+00:00")
DATE_STOP = dt("2024-01-01T00:00:00+00:00")
TARGET_AUTHOR = 46322

COVER_IMAGES = [
    "https://derpicdn.net/img/view/2015/12/1/1034522.png",
    "https://derpicdn.net/img/view/2015/12/2/1035253.png",
    "https://derpicdn.net/img/view/2015/12/3/1035985.png",
    "https://derpicdn.net/img/view/2015/12/4/1036703.png",
    "https://derpicdn.net/img/view/2015/12/5/1037293.png",
    "https://derpicdn.net/img/view/2015/12/6/1038118.png",
    "https://derpicdn.net/img/view/2015/12/7/1039018.png",
    "https://derpicdn.net/img/view/2015/12/8/1039677.png",
    "https://derpicdn.net/img/view/2015/12/9/1040332.png",
    "https://derpicdn.net/img/view/2015/12/10/1041053.png",
    "https://derpicdn.net/img/view/2015/12/11/1041870.png",
    "https://derpicdn.net/img/view/2015/12/12/1042606.png",
    "https://derpicdn.net/img/view/2015/12/13/1043527.png",
    "https://derpicdn.net/img/view/2015/12/14/1044284.png",
    "https://derpicdn.net/img/view/2015/12/15/1044966.png",
    "https://derpicdn.net/img/view/2015/12/16/1045571.png",
    "https://derpicdn.net/img/view/2015/12/17/1046350.png",
    "https://derpicdn.net/img/view/2015/12/18/1046935.png",
    "https://derpicdn.net/img/view/2015/12/19/1047728.png",
    "https://derpicdn.net/img/view/2015/12/20/1048773.png",
    "https://derpicdn.net/img/view/2015/12/21/1049626.png",
    "https://derpicdn.net/img/view/2015/12/22/1050322.png",
    "https://derpicdn.net/img/view/2015/12/23/1051004.png",
    "https://derpicdn.net/img/view/2015/12/24/1051596.png",
    "https://derpicdn.net/img/view/2015/12/25/1052173.png",
    None,
    "https://derpicdn.net/img/view/2017/12/22/1613311.png",
]


def day(story: Story) -> int:
    """
    Returns the day of publishing.
    """
    return dt(story.meta["date_published"]).day


class AdventConverter(Converter):
    """
    Base class for modifying story meta and data.
    """

    def handle_opf(self, story: Story, dom: Document):
        pass

    def handle_zip(self, story: Story, arc: ZipFile):
        pass

    def get_data(self, story: Story) -> bytes:
        buffer = BytesIO()
        target = ZipFile(buffer, "w")
        source = ZipFile(BytesIO(story.data), "r")

        with source, target:
            for info in source.infolist():
                data = source.read(info)

                if info.filename == "content.opf":
                    dom = minidom.parseString(data)
                    self.handle_opf(story, dom)
                    data = dom.toprettyxml().encode()

                target.writestr(info, data)

            self.handle_zip(story, target)

        return buffer.getvalue()

    def get_meta(self, story: Story) -> dict:
        return deepcopy(story.meta)

    def __call__(self, story: Story) -> Story:
        return story.merge(
            data=self.get_data(story),
            meta=self.get_meta(story),
        )


class CoverConverter(AdventConverter):
    """
    Adds advent cover by dm29.
    """

    file_name = "cover.png"

    def fetch(self, story: Story) -> bytes:
        if not (url := COVER_IMAGES[day(story) - 1]):
            raise ValueError("Missing cover")

        _, name = url.rsplit("/", 1)
        path = Path(f"covers/{name}")

        if not path.is_file():
            return get(url).content

        return path.read_bytes()

    def draw(self, story: Story) -> bytes:
        # Load cover art
        data = self.fetch(story)
        art = Image.open(BytesIO(data))

        # Create cover image
        height = ceil(art.width * 1.6)
        cover = Image.new("RGB", (art.width, height), "lightgray")
        cover.paste(art, (0, height - art.height))

        # Initialize draw tool
        draw = ImageDraw.Draw(cover)
        font = ImageFont.load_default(height // 12)

        # Draw story number
        ident = f"{story.key}"
        _, _, tw, th = draw.textbbox((0, 0), ident, font)
        ts = ((art.width - tw) / 2, (height - art.height - th) / 2 - th / 8)
        draw.text(ts, ident, "black", font)

        # Draw calendar date
        title = f"Advent {day(story):02}"
        _, _, tw, th = draw.textbbox((0, 0), title, font)
        ts = ((art.width - tw) / 2, (ts[1] + th + th / 4))
        draw.text(ts, title, "black", font)

        # Render image
        buffer = BytesIO()
        cover.save(buffer, "png")

        return buffer.getvalue()

    def handle_opf(self, story: Story, dom: Document):
        (manifest,) = dom.getElementsByTagName("manifest")

        cover = dom.createElement("item")
        cover.setAttribute("id", "cover")
        cover.setAttribute("href", self.file_name)
        cover.setAttribute("media-type", "image/png")

        manifest.insertBefore(cover, manifest.firstChild)

    def handle_zip(self, story: Story, arc: ZipFile):
        arc.writestr(self.file_name, self.draw(story))


class TitleConverter(AdventConverter):
    """
    Replaces title with advent date.
    """

    def handle_opf(self, story: Story, dom: Document):
        title = f"Advent {day(story):02} - {story.key}"
        (node,) = dom.getElementsByTagName("dc:title")
        (text,) = node.childNodes

        text.replaceWholeText(title)

    def get_meta(self, story: Story) -> dict:
        meta = super().get_meta(story)
        meta["title"] = f"Advent {day(story):02}"

        return meta


class AdventCommand(Command):
    """
    Creates advent calendar.
    """

    def filter(self, fetcher: FimfarchiveFetcher) -> Iterator[Story]:
        for story in fetcher:
            if story.meta["author"]["id"] != TARGET_AUTHOR:
                continue

            if not (published := story.meta["date_published"]):
                continue

            if DATE_START < dt(published) < DATE_STOP:
                yield story

    def __call__(self, *args: str) -> int:
        (archive,) = args

        slug = StorySlugMapper()
        fetcher = FimfarchiveFetcher(archive)
        writer = DirectoryWriter(data_path=slug)

        convert_cover = CoverConverter()
        convert_title = TitleConverter()

        for story in self.filter(fetcher):
            story = convert_cover(story)
            story = convert_title(story)
            writer.write(story)

        return 0
