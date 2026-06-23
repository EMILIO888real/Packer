'''
Configuration module for the packer package.

This module manages all configuration settings for packer, including project-specific configurations
and user global settings. It provides a unified interface to access merged configurations from multiple
sources (user settings, defaults, and project-specific configs).

For detailed documentation on project and user settings, see:
- Project Configuration: https://github.com/EMILIO888real/Packer/blob/master/docs/PROJECT.md
- User Settings: https://github.com/EMILIO888real/Packer/blob/master/docs/SETTINGS.md

Example usage:
```
    from packer.config import all_settings, projects_configurations, Project
    from packer.utils import normalize_settings_keys
    
    all_settings.text_editor # Access a global setting
    packer_config = projects_configurations['packer'] # Access the dict containing the settings to that project, in this case the packer project.
    project = Project(**packer_config) # or you can also first call the normalize_settings_keys function to replace ' ' with '_', to create snake case words.

Attributes:
    all_settings: A Settings object containing all merged configuration for the selected project.
    user_settings: A dictionary containing user-defined configuration settings for all projects.
    default_settings: A dictionary containing default configuration settings for packer projects.
    default_config: A dictionary containing the default configuration structure.
    projects_configurations: Optional dictionary of project-specific configurations from projects.json.
    packer_version: The current version of the packer package.
'''

__all__ = 'user_settings, default_settings, default_config, all_settings, load, packer_version'

from collections.abc import Callable
from pathlib import Path
from shutil import which
from typing import Any, Sequence
from pydantic import BaseModel
from packer.custom_modules.et import format_version_text, normalize_settings_keys
from packer.paths import assets_dir, config_dir
import json

with open(f'{assets_dir}/version.json') as f:
    packer_version = format_version_text(json.load(f))


class Project(BaseModel):
    '''
    Project configuration model for packer.

    Defines all project-specific settings required for building, packaging, and releasing a project.
    This includes credentials for external services, build commands, and LLM prompts for generating
    release notes and metadata.

    For complete project configuration documentation, see:
    https://github.com/EMILIO888real/Packer/blob/master/docs/PROJECT.md

    Attributes:
        gofile_user_token (str): Authentication token for GoFile API.
        gofile_folder_id (str): Target folder ID on GoFile for uploads.
        github_repo_token (str): GitHub personal access token for repository operations.
        program_name (str): Name of the program/project.
        github_repo_url (str): URL of the GitHub repository.
        before_commands (tuple | None): Commands to execute before the build process.
        after_commands (tuple | None): Commands to execute after the build process.
        compile_command (Sequence[str] | None): Command sequence to compile/build the project.
        model (str): LLM model to use for generating descriptions (default: 'mistral').
        description_prompt (list[dict] | None): Prompt template for generating release descriptions.
        title_prompt (list[dict] | None): Prompt template for generating release titles.
        release_notes_template_path (str | Path): Path to the release notes template file.
        changelog_git_hash (bool): Whether to include git hash in changelog (default: True).
    '''

    gofile_user_token: str | None = None
    gofile_folder_id: str | None = None 
    github_repo_token: str
    program_name: str
    github_repo_url: str

    before_commands: tuple[tuple[str, ...] | Callable, ...] | None = None
    after_commands: tuple[tuple[str, ...], ...] | Callable | None = None
    compile_command: Sequence[str] | None = None
    model: str = 'mistral'
    description_prompt: list[dict[str, str]] | None = [
        {'role': 'system', 'content': 'You are a senior developer writing professional release notes. Summarize the following changelog into one short sentence. Focus strictly on the high-level impact (e.g., \'This release introduces a new TUI and streamlines Windows builds.\') rather than listing individual functions or fixes. Use professional, active language. Output ONLY the summary text, no markdown block syntax, no intros, and no explanations.'},
        {'role': 'user', 'content': f'Summarize the following changelog into exactly one concise sentence. Group related technical changes (e.g., UI, Build Automation, Refactoring). Do not use bullet points. Do not mention specific function names unless they are major features. Ensure the tone is professional.\n\nChangelog:\n%latest_changelog'}
    ]
    title_prompt: list[dict[str, str]] | None = [
        {'role': 'system', 'content': 'You are a cryptic oracle. Your answer must be exactly 2 or 3 words. No quotes, no punctuation, no preamble.'},
        {'role': 'user', 'content': f'Create a mystical, indirect puzzle title for this update. Do not include version numbers.\n\nChangelog:%latest_changelog\n'}
    ]
    release_notes_template_path: str | Path = Path(f'{assets_dir}/RELEASE.md')
    changelog_git_hash: bool = True


class Settings(BaseModel):
    '''
    Global settings model for packer.

    Defines user-level settings that apply across all packer projects. This includes editor preferences,
    output verbosity, LLM model selection, and prompt templates for generating change summaries and
    high-level release notes.

    For complete settings documentation, see:
    https://github.com/EMILIO888real/Packer/blob/master/docs/SETTINGS.md

    Attributes:
        text_editor (str): Name or path of the text editor to use (default: 'code' for VS Code).
        wait_flag (str | None): Flag to pass to the text editor (default: '--wait').
        verbose (bool): Enable verbose output logging (default: True).
        skip_git_status (bool): Skip git status checks before operations (default: False).
        model (str): LLM model to use for summaries (default: 'mistral').
        changes_summary_prompt (list[dict]): Prompt template for summarizing git diffs at a high level.
        high_level_summary_prompt (list[dict]): Prompt template for creating a single summary sentence
                                                  from a bullet-point list of changes.
    '''

    text_editor: str = 'code'
    wait_flag: str | None = '--wait'
    verbose: bool = True
    skip_git_status: bool = False
    changes_summary_prompt: list[dict[str, str]] = [
            {'role': 'system', 'content': (
                'You are a careful code-review assistant. '
                'Summarize the provided git diff at a high level only. '
                'Focus on the main intent and the most important behavioral or structural changes, '
                'not minor formatting, whitespace, or line-by-line details. '
                'Keep the explanation concise. '
                'Respond with an unordered single level list only using "-" bullets. '
                'Do not include an introduction, conclusion, or any extra commentary.'
        )},
            {'role': 'user', 'content': (
                'Summarize the changes in this git diff at a high level only. '
                'Ignore minor formatting or whitespace tweaks and focus on the main impact of the update. '
                'Return the result as an unordered list using "-" bullets only.\n\n'
                'Only consider modifications of these types: $changes.\n'
                'Map types using the project TUI: a=added, c=changed, f=fixed.\n\n'
                '$diff'
        )},
    ]
    high_level_summary_prompt: list[dict[str, str]] = [
        {'role': 'system', 'content': (
    'You are a concise reviewer. '
    'Take the bullet list below and write one short high-level summary sentence. '
    'Do not repeat every item. Focus on the overall change and its impact. '
    'Return only the summary sentence, with no bullets or extra commentary.'
)},
        {'role': 'user', 'content': '$bullet_summary'},
    ]
    model: str = 'mistral'

settings_path = f'{config_dir}/settings.json'

if not Path(settings_path).exists():
    with open(settings_path, 'w') as f:
        f.write('{}')

with open(settings_path) as f:
    user_settings = json.load(f)

all_settings: Settings = Settings(**normalize_settings_keys(user_settings))

# All setup for settings
all_settings.text_editor = which(all_settings.text_editor)


projects_configurations: dict[str, dict[str, Any]] | None
if Path(f'{config_dir}/projects.json').exists():
    with open(f'{config_dir}/projects.json') as f:
        projects_configurations = json.load(f)
else:
    projects_configurations = None