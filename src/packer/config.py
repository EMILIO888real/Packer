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
from packer.utils import load_config, normalize_settings_keys
from packer.utils import simple_merge_settings

class Settings(BaseModel):
    gofile_user_token: str
    gofile_folder_id: str
    github_repo_token: str
    program_name: str
    github_repo_url: str

    model: str = 'mistral'
    before_commands: Sequence[Sequence[str]] | None = None
    after_commands: Sequence[Sequence[str]] | None = None
    compile_command: Sequence[str] | None = None

    text_editor: str = 'code'

user_settings, default_settings, default_config = load_config(assets_dir, config_dir)
all_settings: dict[Any] | None = None

def load(project: str | Path) -> None:
    '''
    Load and merge configuration settings for a project.

    This function loads the user settings, default settings, and default configuration
    for a given project, then merges them together to create a complete settings object.

    :param project: The project path or name to load settings for
    :type project: str | Path
    '''

    global all_settings

    all_settings = Settings(**normalize_settings_keys(simple_merge_settings(user_settings[str(Path(project).absolute())], default_settings, default_config)))