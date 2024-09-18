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
development of Fimfarchive. Using a [virtual environment] is recommended for
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

Enter the cloned repository and install the development dependencies.

```bash
uv sync
```

Optionally also install `lz4` to lower the memory footprint of open archives.

```bash
uv sync --extra lz4
```

All done! Run the test suite to make sure everything works as expected.

```bash
uv run pytest
```

[virtual environment]: https://docs.python.org/3/tutorial/venv.html


# Running

Fimfarchive has a command line interface which is invoked as a Python module.
It can't do much except prepare new Fimfarchive releases. For archive browsing
you will need to use third-party tools, or make your own.

```
$ uv run python -m fimfarchive
Usage: COMMAND [PARAMETERS]

Fimfarchive, ensuring that history is preseved.

Commands:
  build   Builds a new Fimfarchive release.
  update  Updates stories for Fimfarchive.
```

The command line interface features multiple subcommands, each with its own
brief help text. The subcommand is specified as the second program argument.

```
$ uv run python -m fimfarchive update --help
usage: [-h] [--alpha] --archive PATH [--refetch]

Updates stories for Fimfarchive.

optional arguments:
  -h, --help      show this help message and exit
  --alpha         fetch from Fimfiction APIv1
  --archive PATH  previous version of the archive
  --refetch       refetch all available stories
```

Some commands (such as `update`) require a Fimfiction API key. The program
reads this key from the environment variable `FIMFICTION_ACCESS_TOKEN`. Any
data downloaded from Fimfiction is stored in the current working directory,
typically in the `worktree` subdirectory. The same thing goes for rendered
stories, built archives, or anything else related to the release process.


# Process

The process for building a new Fimfarchive release consists of a few simple
steps. Before starting, make sure you have the previous version of Fimfarchive
nearby, as well as a Fimfiction APIv2 key. Also, remove any previous `worktree`
directory from the current working directory. Some of the commands mentioned
below are currently only available in feature branches.

- **Update**: Invoke the `update` subcommand to refresh all stories. This takes
  about one month since _all_ story metadata has to be traversed. Story data
  isn't downloaded unless changes have been made since the last release. Use
  the `--refetch` flag if all data should be updated regardless of if there
  have been any changes. Write down the `Started` and `Done` dates for later.

- **Render**: Use the `render` subcommand to generate EPUB-files for all
  stories with updated content. The subcommand requires `ebook-convert` from
  Calibre to be installed and accessible from the command line. Fimfarchive
  will usually keep the CPU maxed out for a few hours during this step.

- **Count**: The `count` subcommand compares the upcoming release with the
  previous one. The output mainly consists of statistics for the changelog.

- **Document**: Update the documentation in `docs/readme.tex` for the upcoming
  release. Change the document title, add a row to the changelog table, and a
  new changelog subsection. Render the document _a few times_ with `lualatex`
  and place the results in `worktree/extras` as `readme.pdf`.

- **About**: Create an `about.json` file in `worktree/extras`. The file has
  three keys named `version`, `start`, and `end`. Each key has a simple date
  string like `20201201` as its value. Preferably use the file included with
  the previous release as a template to keep things consistent.

- **Build**: Create a `build` directory in `worktree`, and then run the `build`
  subcommand. Expect this to take up to 15 minutes depending on the machine.
  The resulting archive will be written to the `build` directory.

- **Verify**: Go through the archive to check that everything looks good. One
  tip is to test the CRC checksums of both the outer ZIP-archive and internal
  EPUB-files. Sample some old and new stories to check that they look right.
  Successfully opening the archive with [Fimfareader] can help prove that the
  metadata has all of the required fields with the correct data types.

- **Patch**: Create an [xdelta3] patch if applicable. It's important to allow
  `xdelta3` to use a lot of memory since it otherwise has trouble seeing the
  similarities between the archives. For example, `xdelta3 -B 2147483648 -e -s
  <old> <new> <patch>` uses the maximum allowed value of 2 GiB.

- **Torrent**: Create a torrent file if applicable. Using a private tracker
  with a whitelist is preferable since public ones could be flaky or have poor
  response times. However, it's usually a good idea to include a few public
  trackers as well to improve availability. Set the chunk size so that the
  torrent is split into somewhere between 1000 and 2000 pieces. Values outside
  that range could cause performance issues or prevent the torrent from being
  easily distributed via magnet links.

- **Release**: Upload, announce, and distribute the release!

[Calibre]: https://calibre-ebook.com
[Fimfareader]: https://github.com/JockeTF/fimfareader
[xdelta3]: http://xdelta.org
