# Packer

A Python automation tool that streamlines Python release workflows: creating optimized archives, uploading releases to GoFile, updating Git repositories, and publishing GitHub releases with AI-generated notes.

## Contents

- [Installation](#installation)
- [Binary Downloads](#binary-downloads)
- [Usage](#usage)
- [Configuration](#configuration)
	- [Settings](#settings)
	- [Config](#config)
	- [Extra customization](#extra-customization)
- [Extra notes](#extra-notes)
- [Warning](#warning)
- [Features](#features)
- [Feedback and Suggestions](#feedback-and-suggestions)
- [Honorable mentions](#honorable-mentions)
- [Changelog](#changelog)
- [In future updates](#in-future-updates)

## Installation

Available via:

* **GitHub Releases:** [GitHub Releases](https://github.com/EMILIO888real/Packer/releases/)
* **Third-party website (GoFile):** [Archive](https://gofile.io/d/OktQl5)

You can also install from source in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

### Binary Downloads

When downloading, please choose the correct build for your operating system:

| File Name | Platform | Description |
| --- | --- | --- |
| `packer` | Linux/macOS | Executable for Unix-based systems. |
| `packer.exe` | Windows | Executable for Windows systems. |

### To install:

* **GitHub:** Download the appropriate binary or archive for your system from the [Releases page](https://github.com/EMILIO888real/Packer/releases/).
* **Third-party website (GoFile):** Head to the website [Archive](https://gofile.io/d/OktQl5) and download the specific archive for the desired version.

After installing, continue following instructions in this README.

## Usage

After installing the project, you can run it from the command line using the package entry points.

### Basic example

```bash
python -m packer.main
```

If the package is installed in your environment, you can also run:

```bash
packer
```

For interactive CLI usage see [src/packer/ui/cli.py](src/packer/ui/cli.py#L1).

## Configuration

### Settings

See [docs/PROJECT.md](docs/PROJECT.md#L1) and [docs/CLI.md](docs/CLI.md#L1) for detailed information on user-configurable settings and CLI options.

### Config

Packer expects a project layout with `src/` code and an `assets/` folder containing at least `version.json` and `integrity.json`. A `CHANGELOG.md` at the project root is required for release-note generation.

### Extra customization

See [docs/PROJECT.md](docs/PROJECT.md#L1) for notes about adding custom assets and creating profiles.

## Extra notes

- Packer integrates with GoFile for archive hosting and GitHub for release publishing.
- Optional compilation via Nuitka is supported for producing compiled releases.

## Warning

Possible problems might arise in that case, please back up your project before running for the first time and even if packer messed up, it won't destroy or corrupt your project so GL fixing it!

## Features

- Archive Creation: Packages your program with customizable exclusion rules.
- Cloud Upload: Uploads archives to GoFile with optional folder management.
- Git Integration: Handles repository updates and tagging.
- GitHub Releases: Publishes releases with AI-generated titles and descriptions.
- Optional Compilation: Supports Nuitka for compiled distributions.
- Error Handling: Automatic rollback to previous version if a step fails.
- AI-Powered: Uses Ollama (when available) to generate release notes.

## Feedback and Suggestions

Please open issues or pull requests on the project's GitHub repository, or email suggested improvements and bugs.

## Honorable mentions

- Ollama — used for AI-generated release notes (optional).
- GoFile — used as archive hosting provider.

## Changelog

See the full history in [CHANGELOG.md](./CHANGELOG.md#L1).

## In future updates

See planned features and roadmap in [docs/ROADMAP.md](docs/ROADMAP.md#L1).
