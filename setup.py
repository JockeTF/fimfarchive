#!/usr/bin/env python3
"""
Setuptools for Fimfarchive.
"""


#
# Fimfarchive, preserves stories from Fimfiction
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
from typing import Iterable, List, Tuple

from setuptools import setup

from fimfarchive import __author__, __license__, __version__


PACKAGE = 'fimfarchive'
GITHUB = 'https://github.com/JockeTF/fimfarchive'


def to_name(path: str) -> str:
    """
    Converts path to a package name.
    """
    return path.replace(os.path.sep, '.')


def iter_package_paths() -> Iterable[str]:
    """
    Yields all package paths to install.
    """
    for dirpath, dirnames, filenames in os.walk(PACKAGE):
        if '__init__.py' in filenames:
            yield dirpath


def iter_package_names() -> Iterable[str]:
    """
    Yields all package names to install.
    """
    for dirpath in iter_package_paths():
        yield to_name(dirpath)


def iter_package_data() -> Iterable[Tuple[str, List[str]]]:
    """
    Yields all package data to install.
    """
    for dirpath in iter_package_paths():
        filenames = [
            filename for filename in os.listdir(dirpath)
            if os.path.isfile(os.path.join(dirpath, filename))
            and not filename.endswith('.py')
        ]

        if filenames:
            yield to_name(dirpath), filenames


setup(
    name="fimfarchive",
    version=__version__,
    license=__license__,
    author=__author__,
    author_email='fimfarchive@gmail.com',
    url='http://www.fimfarchive.net/',
    download_url=f'{GITHUB}/archive/{__version__}.tar.gz',
    packages=list(iter_package_names()),
    package_data=dict(iter_package_data()),
    install_requires=(
        'arrow',
        'bbcode',
        'blinker',
        'importlib_resources',
        'jinja2',
        'jmespath',
        'jsonapi-client',
        'requests',
        'tqdm',
    ),
)
