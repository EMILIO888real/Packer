'''
This module provides configuration settings for the packer package. When using the `load` function,
it is required to modify the source and read it from source, so you should use `import packer.config`
to import the module. However, if you are not using `load` and just need to access the configuration
settings, you can use `from packer.config import all_settings` to directly import the settings.

Example usage:
```
    # For load function (requires source modification)
    import packer.config as config

    config.load(project_dir)
    config.all_settings # Now this contains the new settings, after running the above line.

    # For direct settings access
    from packer.config import all_settings

Attributes:
    load: To create the Settings object, merge all settings.
    all_settings: A dictionary containing all configuration settings for the selected project.
    user_settings: A dictionary containing user-defined configuration settings for all projects.
    default_settings: A dictionary containing the default configuration settings for any packer style projects.
    default_config: A dictionary containing the default configuration config for any packer style projects.
'''

__all__ = 'user_settings, default_settings, default_config, all_settings, load, packer_version'

from collections.abc import Callable
from pathlib import Path
from typing import Any, Sequence
from pydantic import BaseModel
from packer.custom_modules.et import format_version_text
from packer.paths import assets_dir, config_dir
from packer.utils import load_config, normalize_settings_keys, simple_merge_settings
import json

with open(f'{assets_dir}/version.json') as f:
    packer_version = format_version_text(json.load(f))


class Project(BaseModel):
    gofile_user_token: str
    gofile_folder_id: str
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
    text_editor: str = 'code'
    wait_flag: str | None = '--wait'
    verbose: bool = True
    skip_git_status: bool = False


user_settings, default_settings, default_config = load_config(assets_dir, config_dir)
all_settings: Settings = Settings(**normalize_settings_keys(simple_merge_settings(user_settings, default_settings, default_config)))

projects_configurations: dict[str, dict[str, Any]]
if Path(f'{config_dir}/projects.json').exists():
    with open(f'{config_dir}/projects.json') as f:
        projects_configurations = json.load(f)
else:
    projects_configurations = None