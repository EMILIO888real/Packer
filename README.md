# Packer

A Python automation tool that streamlines python software release workflows. Packer creates optimized archives, uploads releases to Gofile for distribution, updates Git repositories, and publishes releases on GitHub. Built-in error handling automatically reverts changes if any step fails, ensuring safe and reliable deployments.

## Warning

This is a very early release, and while it has been tested on multiple projects, there may still be edge cases that could cause issues. Always make sure to have a backup of your project before using Packer, especially if it's your first time. We recommend testing it on a non-critical project first to get familiar with its functionality. A new project directory initialization and creation will be added in the next release, so for now you must have an existing project with the required structure to use Packer.

## Features

- **Archive Creation**: Automatically packages your program with customizable exclusion rules
- **Cloud Upload**: Uploads archives to Gofile with automatic folder management
- **Git Integration**: Handles repository updates and version control
- **GitHub Releases**: Publishes releases directly to GitHub with AI-generated descriptions
- **Optional Compilation**: Supports Nuitka compilation for distributing compiled versions
- **Error Handling**: Automatic rollback to previous version if any step fails
- **AI-Powered**: Uses Ollama to generate intelligent release titles and descriptions

## Requirements

- Python 3.8+
- GitHub account with API token
- GoFile account with API token
- Git installed locally
- Ollama (for AI-generated release notes)
- Nuitka (optional, for compilation)

Your project must be a Git repository with the src layout (src/ for source code, assets/ for program assets, which must include a version.json and integrity.json), also at project root level a CHANGELOG.md file is required for release notes generation.

## Getting Started

Set up a python virtual environment and install the required dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install .
```

Just run it in your project directory:

```bash
packer
```

Follow the prompts to create a profile / configuration for your project, and Packer will handle the rest!