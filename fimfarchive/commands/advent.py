# /usr/bin/env python3

from copy import deepcopy
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Iterator, override
from xml.dom import minidom
from zipfile import ZipFile

from fimfarchive.converters import Converter
from fimfarchive.fetchers import FimfarchiveFetcher
from fimfarchive.stories import Story
from fimfarchive.mappers import StorySlugMapper
from fimfarchive.writers import DirectoryWriter

from .base import Command

dt = datetime.fromisoformat


DATE_START = dt("2023-12-01 00:00:00Z")
DATE_STOP = dt("2024-01-01 00:00:00Z")
TARGET_AUTHOR = 46322

COVER_PAGE = """
    <?xml version='1.0' encoding='utf-8'?>
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
            <meta name="calibre:cover" content="true"/>
            <title>Cover</title>
        </head>
        <body>
            <center>
                <h1>Title</h1>
                <img src="cover.png"/>
            </center>
        </body>
    </html>
""".lstrip()

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


class CoverPage:

    def __init__(self, story: Story) -> None:
        published = dt(story.meta["date_published"])
        self.day = published.day

    def get_cover(self) -> bytes:
        if not (url := COVER_IMAGES[self.day - 1]):
            raise ValueError("Missing cover")

        _, name = url.rsplit("/", 1)
        path = Path(f"covers/{name}")

        return path.read_bytes()

    def get_title(self) -> bytes:
        dom = minidom.parseString(COVER_PAGE)
        (title,) = dom.getElementsByTagName("h1")
        (text,) = title.childNodes

        text.replaceWholeText(f"Advent {self.day:02}")

        return dom.toprettyxml().encode()


class AdventConverter(Converter):
    """
    Replaces titles with advent dates.
    """

    def get_title(self, story: Story) -> str:
        published = dt(story.meta["date_published"])

        return f"Advent {published.day:02}"

    def get_opf(self, story: Story, data: bytes) -> bytes:
        dom = minidom.parseString(data)
        (package,) = dom.getElementsByTagName("package")
        (manifest,) = dom.getElementsByTagName("manifest")
        (spine,) = dom.getElementsByTagName("spine")
        (title,) = dom.getElementsByTagName("dc:title")

        (text,) = title.childNodes
        text.replaceWholeText(self.get_title(story))

        index = manifest.firstChild
        item = dom.createElement("item")
        item.setAttribute("id", "cover")
        item.setAttribute("href", "cover.png")
        item.setAttribute("media-type", "image/png")
        manifest.insertBefore(item, index)
        item = dom.createElement("item")
        item.setAttribute("id", "title")
        item.setAttribute("href", "title.xhtml")
        item.setAttribute("media-type", "application/xhtml+xml")
        manifest.insertBefore(item, index)

        index = spine.firstChild
        item = dom.createElement("itemref")
        item.setAttribute("idref", "title")
        spine.insertBefore(item, index)

        guide = dom.createElement("guide")
        reference = dom.createElement("reference")
        reference.setAttribute("type", "cover")
        reference.setAttribute("href", "title.xhtml")
        reference.setAttribute("title", "title")
        guide.appendChild(reference)
        package.appendChild(guide)

        return dom.toprettyxml().encode()

    def get_data(self, story: Story) -> bytes:
        buffer = BytesIO()
        target = ZipFile(buffer, "w")
        source = ZipFile(BytesIO(story.data), "r")

        with source, target:
            for info in source.infolist():
                data = source.read(info)

                if info.filename == "content.opf":
                    data = self.get_opf(story, data)

                target.writestr(info, data)

            cover = CoverPage(story)
            target.writestr("cover.png", cover.get_cover())
            target.writestr("title.xhtml", cover.get_title())

        return buffer.getvalue()

    def get_meta(self, story: Story) -> dict:
        meta = deepcopy(story.meta)
        meta["title"] = self.get_title(story)

        return meta

    @override
    def __call__(self, story: Story) -> Story:
        return story.merge(
            data=self.get_data(story),
            meta=self.get_meta(story),
        )


class AdventCommand(Command):
    """
    Creates an advent calendar.
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
        convert = AdventConverter()
        fetcher = FimfarchiveFetcher(archive)
        writer = DirectoryWriter(data_path=slug)

        for story in self.filter(fetcher):
            writer.write(convert(story))

        return 0
