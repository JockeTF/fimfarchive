#!/usr/bin/env python3
"""
Web resource printer.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2023  Joakim Soderlund
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


from io import BytesIO
from json import dumps
from multiprocessing import Pool
from sys import argv
from typing import Dict, Iterator, List, Tuple
from urllib.parse import urlparse, parse_qs
from zipfile import ZipFile

from bs4 import BeautifulSoup

from fimfarchive.fetchers import FimfarchiveFetcher
from fimfarchive.stories import Story
from fimfarchive.utils import tqdm


def parse(data: bytes) -> Iterator[str]:
    dom = BeautifulSoup(data, features='html.parser')

    for tag in dom.find_all('img'):
        if 'src' in tag.attrs:
            yield tag.attrs['src']

    for tag in dom.find_all('a'):
        if 'href' in tag.attrs:
            yield tag.attrs['href']


def clean(urls: Iterator[str]) -> Iterator[str]:
    for url in urls:
        url = url.split('[/')[0]
        url = url.split('">')[0]
        url = url.replace('\n', '')
        url = url.replace('\r', '')

        if not url.strip():
            continue

        try:
            parts = urlparse(url)
            query = parse_qs(parts.query)
            lhost = parts.netloc.lower()
        except Exception as e:
            yield f'error://{e!r}'
            continue

        if 'imgur' in lhost:
            yield url
        elif 'camo' in lhost and 'url' in query:
            yield from query['url']
        elif 'google' in lhost and 'q' in query:
            yield from query['q']
        elif 'google' in lhost and 'imgurl' in query:
            yield from query['imgurl']
        elif 'bing' in lhost and 'mediaurl' in query:
            yield from query['mediaurl']
        else:
            yield url


def entries(source: ZipFile) -> Iterator[Tuple[str, List[str]]]:
    for info in source.infolist():
        data = source.read(info)
        name = info.filename

        if name.endswith('.htm') or name.endswith('.html'):
            try:
                yield name, list(clean(parse(data)))
            except Exception as e:
                yield name, [f'error://{e!r}']


def mapping(data: bytes) -> List[Tuple[str, List[str]]]:
    with ZipFile(BytesIO(data)) as source:
        return list(entries(source))


def extract(fetcher: FimfarchiveFetcher) -> Iterator[bytes]:
    for story in fetcher:
        yield story.data


if __name__ == '__main__':
    fetcher = FimfarchiveFetcher(argv[1])
    progbar = tqdm(total=len(fetcher))

    with Pool(4) as pool:
        loader = extract(fetcher)
        mapper = pool.imap_unordered(mapping, loader)

        for results in mapper:
            progbar.update(1)

            for name, urls in results:
                print("\n".join(urls))
