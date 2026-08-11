# Packer

A Python automation tool that streamlines Python release workflows: creating archives, uploading them to GoFile, updating Git repositories, publishing GitHub releases with AI-generated notes, and building, uploading wheels to PyPI.

## Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Demos](#demos)
- [Configuration](#configuration)
	- [Settings](#settings)
	- [Config](#config)
- [Extra notes](#extra-notes)
- [Warning](#warning)
- [Features](#features)
- [Feedback and Suggestions](#feedback-and-suggestions)
- [Changelog](#changelog)
- [In future updates](#in-future-updates)

## Requirements

- python >=3.10 (unless you use one of the executables)
- git, For lots of things
- GitHub account, For creating a GitHub release
- GoFile account [optional] For uploading to your profile tied folder.
- ollama [optional] For AI generated version description, name and git diff summarization in the change module.
- PyPI account [optional] For uploading to PyPI

## Installation

Available via multiple methods — choose whichever fits your workflow:

- [From GitHub Releases](#from-github-releases)
- [From PyPI](#from-pypi)
- [From source (GitHub clone)](#from-source-github-clone)
- [From a source archive (GoFile)](#from-a-source-archive-gofile)

### From GitHub Releases

Prebuilt artifacts are published on the [Releases page](https://github.com/EMILIO888real/Packer/releases/):

- **PyInstaller executables:** standalone binaries — `packer` for Linux systems and `packer.exe` for Windows.
- **Wheel file:** a Python `.whl` built with the `build` package for easy installation on any platform.
- **Source archives:** `tar.gz` / `zip` source distributions for local builds.

Example install for a downloaded wheel:

```bash
pip install packer-x.y.z-py3-none-any.whl
```

### From PyPI

A release is also published to PyPI under the name `packer-release`:

```bash
pip install packer-release
```

### From source (GitHub clone)

Install from source in a virtual environment after cloning the repository:

```bash
git clone https://github.com/EMILIO888real/Packer.git
cd Packer
python -m venv .venv
source .venv/bin/activate
pip install .
```

> **Note**: There are 2 branches **master** (somewhat stable, default) and **development** (latest changes, updates every 1-3 days)

Or let `pip` clone and build directly from the GitHub repository (no manual clone required):

```bash
pip install git+https://github.com/EMILIO888real/Packer.git
```

### From a source archive (GoFile)

If you prefer to install from a downloaded source archive, download the archive from the [GoFile archive](https://gofile.io/d/bsT5ix) and install it with `pip`:

```bash
pip install /path/to/packer-x.y.z.tar.gz
```

After installing, continue following instructions in this README.

## Usage

After installing the project, you can run it from the command line using the command `packer`.

### Basic example

TUI
```bash
packer
```

GUI
```bash
packer -g
```

CLI
```
packer run -p packer -v m
```

Packer is also usable as a library: you can import parts of it into your own Python projects and call its functions or classes programmatically. Example:

```python
from packer import Packer # <- this works because the object is public. full path: packer.core.Packer
# or import specific helpers
from packer.actions import run # <- Isn't public, so full import path is needed.
from packer.config import Project

instance = Packer(**kwargs)

try:
	instance.run()
except KeyboardInterrupt:
	print('User canceled, reverting changes...')
	instance.revert_changes()

run(Project(**kwargs))
```

Explore more about how to use it as a library by checking out the top `__init__.py` for available public python objects and doctype for those objects on use case.

>**Note:** You can't import Packer if you installed one of the executables

### Interfaces

- **CLI:** Primary command-line interface; run `packer` with any command or flag.
- **GUI (pygame):** A graphical UI is available via a pygame-based frontend for interactive use; run `packer --gui`
- **TUI (Textual):** A terminal UI (TUI) built with Textual is included for rich, keyboard-driven workflows; just run `packer`

## Demos

- `TUI release Demo` - [Watch on youtube](https://youtu.be/dSdyEvqs394)
- `CLI setup demo` - [Watch on youtube](https://youtu.be/ZC9x80sogzA)
- `CLI change demo` - [Watch on youtube](https://youtu.be/TEoaclmCq2w)

## Configuration

### Settings

See [docs/SETTINGS.md](docs/SETTINGS.md#L1) for global Packer settings and [docs/PROJECT.md](docs/PROJECT.md#L1) for project-specific settings. For CLI options, see [docs/CLI.md](docs/CLI.md#L1).

### Config

Packer expects a project layout with `src/` code and an `assets/` folder containing at least `version.json` and `integrity.json`. A `CHANGELOG.md` at the project root is required for release-note generation.

## Extra notes

- Packer integrates with GoFile for archive hosting and GitHub for release publishing.
- Optional compilation via Nuitka is supported for producing compiled releases.

## Warning

- Possible problems might arise in that case, please back up your project before running for the first time and even if packer messed up, it won't destroy or corrupt your project so GL fixing it! Here is also a guide for manually reverting a release in case it fails catastrophically: [docs/MANUAL_REVERT.md](docs/MANUAL_REVERT.md#L1).
- Note that automatic error reporting is enabled by default. *You can disable it in the settings*

## Features

- Archive Creation: Packages your program with customizable exclusion rules. Uses `.gitignore`
- Cloud Upload: Uploads archives to GoFile with optional folder management.
- Git Integration: Handles repository updates and tagging.
- GitHub Releases: Publishes releases with AI-generated titles and descriptions.
- Optional Compilation: Supports Nuitka for compiled distributions.
- Error Handling: Automatic rollback to previous version if a step fails.
- AI-Powered: Uses Ollama (when available) to generate release notes.
- PyPI integration: builds python wheels and uploads them to PyPI.

## Feedback and Suggestions

Please open issues or pull requests on the project's GitHub repository, or email [emilspro888@gmail.com] to suggest improvements or report bugs.

## Changelog

See the full history in [CHANGELOG.md](./CHANGELOG.md#L1).

## In future updates

See planned features and roadmap in [docs/ROADMAP.md](docs/ROADMAP.md#L1).
