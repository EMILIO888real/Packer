# Project Settings

This document describes the project-specific Packer settings stored in the user configuration directory.

Unlike the global settings in `settings.json`, these settings are unique to each Packer-managed project and are stored in `projects.json`.

## File locations

Project settings are stored in the platform-specific Packer config directory.

| OS      | Path                                                            |
| ------- | --------------------------------------------------------------- |
| Linux   | `~/.config/packer/projects.json`                                |
| macOS   | `~/Library/Application Support/packer/projects.json`            |
| Windows | `C:\Users\<username>\AppData\Local\EMILIO\packer\projects.json` |

## Settings

The following options are stored for each project in `projects.json`.

| Setting                       | Type                              | Default             | Description                                                                                                         |
| ----------------------------- | --------------------------------- | ------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `gofile_user_token`           | `str`                             | `None`              | GoFile API token used to upload release archives.                                                                   |
| `gofile_folder_id`            | `str`                             | `None`              | ID of the GoFile folder where release archives are uploaded.                                                        |
| `github_repo_token`           | `str`                             | —                   | GitHub personal access token used for repository operations.                                                        |
| `github_repo_url`             | `str`                             | —                   | GitHub repository URL in the form `username/repository`.                                                            |
| `pypi_api_token`              | `str`                             | `None`              | API token used for publishing releases to PyPI.                                                                     |
| `before_commands`             | `Sequence[Sequence[str]] or None` | `None`              | Commands executed before the release process begins. Each command is represented as a sequence of arguments.        |
| `after_commands`              | `Sequence[Sequence[str]] or None` | `None`              | Commands executed after the release process completes. Each command is represented as a sequence of arguments.      |
| `compile_command`             | `Sequence[str] or None`           | `None`              | Command used to build or compile the project before packaging.                                                      |
| `model`                       | `str`                             | `mistral`           | AI model used when generating release titles and descriptions for this project. Overrides the global model setting. |
| `description_prompt`          | `list[dict[str, str]]`            | prompt template     | Prompt template used to generate the release description.                                                           |
| `title_prompt`                | `list[dict[str, str]]`            | prompt template     | Prompt template used to generate the release title.                                                                 |
| `release_notes_template_path` | `str or Path`                     | `assets/RELEASE.md` | Path to the release notes template used when generating GitHub releases.                                            |
| `changelog_git_hash`          | `bool`                            | `true`              | Whether to include git hash in changelog (default: True).                                                           |
| `description_prompt_kwargs`   | `dict`                            | `{}`                | Additional keyword arguments for the description prompt.                                                            |
| `title_prompt_kwargs`         | `dict`                            |           `{'options': {'temperature': 0.8, 'num_predict': 10}}`        |               Additional keyword arguments for the title prompt.|
| `check_todo`                  | `bool`                            | `true`              | Whether to check for TODO items in the project.                                                                     |
| `todo_rel_path`               | `str`                             | `dev/TODO.md`       | Relative path to the TODO file in the project.                                                                      |
| `list_start_identifier`       | `str`                             | `before next release`| Identifier marking the start of the TODO list section.                                                             |
| `list_end_identifier`         | `str`                             | `#`                 | Identifier marking the end of the TODO list section.                                                                |

## Release notes template

`release_notes_template_path` points to the Markdown template used when generating GitHub releases.

Supported template variables:

| Variable | Description |
| --- | --- |
| `$program_name` | Project name. |
| `$new_version` | Newly created release version. |
| `$version_description` | AI-generated high-level summary of the release. |
| `$github_repo_url` | GitHub repository URL. |
| `$gofile_download_url` | GoFile archive download URL. |
| `$latest_changelog` | Changelog entries for the current release. |
| `$pypi_program_name` | Project name on PyPI. |

See the default release template (used by Packer):
[`src/packer/assets/RELEASE.md`](../src/packer/assets/RELEASE.md)