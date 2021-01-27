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

This repository contains the code for updating and building the archive. While
the API is not guaranteed to be stable, it can also be used as a library for
easy access to stories and metadata within the archive.

[Fimfiction]: https://www.fimfiction.net
[user profile]: https://www.fimfiction.net/user/116950/Fimfarchive


# Installation

This repository contains only things that are useful to developers. While it
does include a command line tool as well, it cannot do anything productive on
its own without access to the [Fimfiction API].

There are primarily two ways to install this tool. The first is installation
for use as a library, and the other is installation for developing Fimfachive.
Using a [virtual environment] is recommended for both approaches to avoid
contaminating the rest of the Python installation.

[Fimfiction API]: https://www.fimfiction.net/developers/api/v2/docs
[virtual environment]: https://docs.python.org/3/tutorial/venv.html


## Library Installation

First, make sure the [virtual environment] has been created an activated. Then,
simply install the library directly from the `master` branch on GitHub.

```bash
python3 -m pip install git+https://github.com/JockeTF/fimfarchive.git
```

Optionally install `lz4` to lower the memory footprint of open archives.

```bash
python3 -m pip install lz4
```

TODO: Demonstrate usage.


## Development Installation

TODO: Populate section.
