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

__all__ = 'user_settings, default_settings, default_config, all_settings, load'

from pathlib import Path
from typing import Any, Sequence
from pydantic import BaseModel
from packer.paths import assets_dir, config_dir
from packer.utils import load_config, normalize_settings_keys, simple_merge_settings
import json

class Project(BaseModel):
    gofile_user_token: str
    gofile_folder_id: str
    github_repo_token: str
    program_name: str
    github_repo_url: str

    before_commands: Sequence[Sequence[str]] | None = None
    after_commands: Sequence[Sequence[str]] | None = None
    compile_command: Sequence[str] | None = None

class Settings(BaseModel):
    model: str = 'mistral'
    text_editor: str = 'code'
    verbose: bool = True,
    skip_git_status: bool = False

user_settings, default_settings, default_config = load_config(assets_dir, config_dir)
all_settings: dict[str: Any] = Settings(**normalize_settings_keys(simple_merge_settings(user_settings, default_settings, default_config)))

projects_configurations: dict[str: dict[str: Any]]
if Path(f'{config_dir}/projects.json').exists():
    with open(f'{config_dir}/projects.json') as f:
        projects_configurations = json.load(f)
else:
    projects_configurations = None
