# Fimfarchive

Fimfarchive aims to release all stories on Fimfiction as a single ZIP-file. The
archive contains not only stories, but also metadata such as tags, ratings, and
descriptions. It is organized by author and could be used for backup, offline
reading, or data mining.

Releases can be found on Fimfarchive's [user profile] at [Fimfiction]. Note
that this is **not** an official Fimfiction project, so do not send questions
to Fimfiction staff. Instead, send a private message or post a comment to the
Fimfarchive user profile.

A new version will be released each season via BitTorrent, approximately once
every three months. When suitable, an xdelta3 patch will also be provided for
users who do not wish to redownload unchanged stories.

Note that the archive contains a large number of files. Unzipping it to your
file system may not be necessary if the archive is to be used together with
some application. If you are a developer, reading directly from the ZIP-file
may be preferable.

This repository contains code for updating and building the archive. While the
API is not guaranteed to be stable, it can also be used as a library for easy
access to stories and metadata within the archive. A [Fimfiction API] key is
however needed to stories directly from Fimfiction.

[Fimfiction]: https://www.fimfiction.net
[Fimfiction API]: https://www.fimfiction.net/developers/api/v2/docs
[user profile]: https://www.fimfiction.net/user/116950/Fimfarchive


# Installation

There are primarily two ways to install this tool. The first is installation as
a library for use within other projects, and the second is installation for
development of Fimfachive. Using a [virtual environment] is recommended for
both cases in order to avoid contaminating the rest of the Python installation.

## Installation as a Library

Make sure a virtual environment has been created and activated. When done,
simply install the library directly from the `master` branch on GitHub.

```bash
python3 -m pip install git+https://github.com/JockeTF/fimfarchive.git
```

Optionally also install `lz4` to lower the memory footprint of open archives.

```bash
python3 -m pip install lz4
```

That's it! Import a class to make sure things work as expected.

```python
from fimfarchive.fetchers import FimfarchiveFetcher
```

## Installation for Development

Start by creating a clone of the Fimfarchive repository.

```bash
git clone https://github.com/JockeTF/fimfarchive.git
```

Enter the cloned repository and create a virtual environment called `venv`
within it. Make sure to activate the virtual environment before proceeding to
install the development dependencies.

```bash
python3 -m pip install -r requirements.txt
```

Optionally also install `lz4` to lower the memory footprint of open archives.

```bash
python3 -m pip install lz4
```

All done! Run the test suite to make sure everything works as expected.

```bash
pytest
```

[virtual environment]: https://docs.python.org/3/tutorial/venv.html
