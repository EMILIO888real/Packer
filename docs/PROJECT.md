# All of the Project related settings structure and values

*project related settings* are those that are unique to each project created, there are also user settings that is uniform for all settings. Second are to control general behavior of Packer.

## File locations

Config files are stored in the user's platform-specific config directory using `user_config_dir('packer', 'EMILIO', ensure_exists=True)`. The two main config files are `settings.json` and `projects.json`.

| OS      | Path                                                           |
|---------|----------------------------------------------------------------|
| Linux   | `~/.config/packer/settings.json`                              |
|         | `~/.config/packer/projects.json`                              |
| macOS   | `~/Library/Application Support/packer/settings.json`          |
|         | `~/Library/Application Support/packer/projects.json`          |
| Windows | `C:\Users\<username>\AppData\Local\EMILIO\packer\settings.json` |
|         | `C:\Users\<username>\AppData\Local\EMILIO\packer\projects.json` |

## Settings

| Setting                     | Type                             | Value                                                                                                   | Description                                                                                                                                                       |
|-----------------------------|----------------------------------|---------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| gofile_user_token           | str                              |                                                                                                         | Token for accessing gofile API.                                                                                                                                   |
| gofile_folder_id            | str                              |                                                                                                         | ID of the folder in gofile where files are uploaded.                                                                                                              |
| github_repo_token           | str                              |                                                                                                         | Token for accessing GitHub repository.                                                                                                                            |
| changelog_git_hash         | bool                              |   True                                                                                                      | Whether to add git hashes to the changelog entries.                                                                                                                  |
| program_name                | str                              |                                                                                                         | Name of the program or project.                                                                                                                                   |
| github_repo_url             | str                              |                                                                                                         | URL of the GitHub repository.                                                                                                                                     |
| before_commands             | Sequence[Sequence[str]] \| None  | None                                                                                                    | Commands to run before committing process.                                                                                                                         |
| after_commands              | Sequence[Sequence[str]] \| None  | None                                                                                                    | Commands to run after the committing process.                                                                                                                          |
| compile_command             | Sequence[str] \| None            | None                                                                                                    | Command to compile the project.                                                                                                                                   |
| model                       | str                              | 'mistral'                                                                                               | LLM model to use for generating release notes and titles.                                                                                                         |
| description_prompt          | list[dict[str, str]]             | [ {'role': 'system', 'content': 'You are a senior developer writing professional release notes...'}, ... ] | Prompt used to generate a concise description of the changes.                                                                                                     |
| title_prompt                | list[dict[str, str]]             | [ {'role': 'system', 'content': 'You are a cryptic oracle...'}, ... ]                                   | Prompt used to generate a mystical, indirect puzzle title for the release.                                                                                        |
| release_notes_template_path | str \| Path                      | Path(f'{assets_dir}/RELEASE.md')                                                                        | Path to the template file used for generating release notes.                                                                                                      |

### Release notes template file structure

The release notes template contains the following sections:

**Header**
- `$program_name Update [$new_version]` - Title with program name and new version number

**Description**
- `$version_description` - AI-generated concise description of the changes in this release

**Installation**
- Provides two installation options:
  - **GitHub**: Clone repository link using the `$github_repo_url`
  - **GoFile**: Third-party archive download link using `$gofile_download_url`
- Includes clone command and instructions for both methods
- References README for post-installation setup

**Changes**
- `$latest_changelog` - The changelog entries for the current version
- Link to full changelog on GitHub master branch

**Tips**
- Explains differences between GitHub and GoFile distributions
- GitHub contains all versions but is larger; GoFile contains only the newest version
- Highlights advantages of GitHub installation (easy updates via git pull)

**Template Variables**
| Variable | Description |
|----------|-------------|
| `$program_name` | Name of the program/project |
| `$new_version` | The new release version number |
| `$version_description` | short high level version description |
| `$github_repo_url` | GitHub repository URL |
| `$gofile_download_url` | GoFile archive download URL |
| `$latest_changelog` | Changelog entries for the current version |

