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

from os import environ
from warnings import filterwarnings

filterwarnings(
    "ignore",
    message=r".*Your system is avx2 capable but pygame was not built with support for it.*",
    category=RuntimeWarning,
)

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1' # Turns off pygame hello message

from collections.abc import Callable
from pathlib import Path
from shutil import which
from typing import Any, Sequence
from pydantic import BaseModel
from getpass import getpass
from cryptography.fernet import InvalidToken
from plyer import notification

import json
import pygame

from packer.custom_modules.et import format_version_text, normalize_settings_keys, input_via_text_editor
from packer.paths import assets_dir, config_dir, log_path, error_report_path, projects_file_path
from packer.exceptions import Global_exception_handler
from packer.utils import is_file_encrypted, read_encrypted_file


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
        github_repo_url (str): URL of the GitHub repository.
        before_commands (tuple | None): Commands to execute before the build process.
        after_commands (tuple | None): Commands to execute after the build process.
        compile_command (Sequence[str] | None): Command sequence to compile/build the project.
        model (str): LLM model to use for generating descriptions (default: 'mistral').
        description_prompt (list[dict] | None): Prompt template for generating release descriptions.
        title_prompt (list[dict] | None): Prompt template for generating release titles.
        release_notes_template_path (str | Path): Path to the release notes template file.
        changelog_git_hash (bool): Whether to include git hash in changelog (default: True).
        description_prompt_kwargs (dict): Additional keyword arguments for the description prompt.
        title_prompt_kwargs (dict): Additional keyword arguments for the title prompt.
        check_todo (bool): Whether to check for TODO items in the project (default: True).
        todo_rel_path (str): Relative path to the TODO file in the project.
        list_start_identifier (str): Identifier marking the start of the TODO list section.
        list_end_identifier (str): Identifier marking the end of the TODO list section.
    '''

    gofile_user_token: str | None = None
    gofile_folder_id: str | None = None 
    github_repo_token: str
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
    description_prompt_kwargs: dict = {}
    title_prompt_kwargs: dict = {'options': {'temperature': 0.8, 'num_predict': 10}}
    check_todo: bool = True
    todo_rel_path: str = 'dev/TODO.md'
    list_start_identifier: str = 'before next release'
    list_end_identifier: str = '#'


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
        model (str): The LLM model to use for generating summaries and descriptions (default: 'mistral').
        getpass_echo_char (str | None): Character to echo when prompting for passwords (default: None, meaning no echo).
        copy_github_release_clipboard (bool): Whether to copy GitHub release notes to the clipboard (default: True).
        open_gitHub_release (bool): Whether to automatically open the GitHub release page after creating a release (default: True).
        automatic_error_reporting (bool): Whether to automatically report errors to the developers (default: True).
        desktop_notifications (bool): Whether to show desktop notifications for important events (default: True).
        notification_sound_path (str | Path): Path to the sound file for notifications (default: '1', which maps to a default sound).
        notification_volume (float): Volume level for notification sounds (default: 1.0, range 0.0 to 1.0).
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
    getpass_echo_char: str | None = None
    copy_github_release_clipboard: bool = True
    open_gitHub_release: bool = True
    automatic_error_reporting: bool = True
    desktop_notifications: bool = True
    notification_sound_path: str | Path = '1'
    notification_volume: float = 1.0
    smooth_output: bool = True
    smooth_output_speed: float = 0.005
    logs_size_threshold: int = 104_857_000 # 100 MiB
    cache_size_threshold: int = 1_073_741_824 # 1 GiB
    auto_clear_cache: bool = False
    auto_clear_logs: bool = True
    suggestions_prompt: list[dict[str, str]] = [
        {'role': 'system', 'content': (
            'You are writing a very short release-note style summary of a git diff. '
            'Focus only on meaningful user-facing or architectural changes that are actually present. '
            'Do not mention implementation details, parameter names, config keys, helper functions, file names, or line-by-line edits. '
            'Group the summary into the fewest useful sections: Added, Changed, and/or Fixed. '
            'Only include a section if there is at least one real bullet for it. '
            'Never write a section that says "No fixes", "No changes", or similar placeholders. '
            'If there is no genuine fix in the diff, omit the Fixed section entirely. '
            'Write 1-3 bullets per included section, each as a concise high-level statement. '
            'Keep the response short and avoid repetition.'
        )},
        {'role': 'user', 'content': '$diff'}]


settings_path = f'{config_dir}/settings.json'

if not Path(settings_path).exists():
    with open(settings_path, 'w') as f:
        f.write('{}')

with open(settings_path) as f:
    user_settings = json.load(f)

all_settings: Settings = Settings(**normalize_settings_keys(user_settings))


# All setup for settings
all_settings.text_editor = which(all_settings.text_editor)


def _getpass(prompt: str) -> str:
    '''
    Prompt the user for a password with echo_char option using whatever is specified in settings.

    :param prompt: The prompt to display to the user.
    :type prompt: str
    :return: The password entered by the user.
    :rtype: str
    '''
    return getpass(prompt, echo_char=all_settings.getpass_echo_char)

def _input_via_text_editor(text: str, file_path: str = None, text_editor: str = all_settings.text_editor, wait_flag: str = all_settings.wait_flag) -> str:
    '''
    Prompt the user for input using a text editor, as specified in the global settings.

    :param text: The initial text to display in the editor.
    :type text: str
    :param file_path: Optional path to a temporary file to use for the editor session.
    :type file_path: str | None
    :param text_editor: The text editor to use (default is the one specified in global settings).
    :type text_editor: str
    :param wait_flag: Optional flag to pass to the text editor to make it wait for the user to finish editing (default is the one specified in global settings).
    :type wait_flag: str | None
    :return: The text entered by the user in the editor.
    :rtype: str
    '''

    return input_via_text_editor(text, file_path, text_editor, wait_flag)

# All other miscellaneous setup

pygame.mixer.init()

notification_sound = pygame.mixer.Sound(f'{assets_dir}/audio/sounds/new notification {all_settings.notification_sound_path}.wav'
                                        if len(all_settings.notification_sound_path.strip()) == 1
                                        else all_settings.notification_sound_path)
notification_sound.set_volume(all_settings.notification_volume)


exception_handler = Global_exception_handler(packer_version, log_path, error_report_path,
                                             'https://formspree.io/f/xjgqgqbz' if all_settings.automatic_error_reporting else None, 'emilspro888@gmail.com', 'EMILIO888real/Packer')
exception_handler.update()

class _Projects_configurations_manager():
    def __init__(self):
        if projects_file_path.exists():
            if is_file_encrypted(projects_file_path):
                self.content = 'encrypted'
            else:
                with open(projects_file_path) as f:
                    self.content = json.load(f)
        else:
            self.content = {}

    def get(self) -> dict[str, dict[str, Any]] | str:
        return self.content
    
    def get_w_tui(self) -> dict[str, dict[str, Any]]:
        if self.content == 'encrypted':
            incorrect_password = True
            while incorrect_password:
                try:
                    self.decrypt(_getpass('Encryption password: '))
                    incorrect_password = False
                except InvalidToken:
                    print('Incorrect password!')
            return self.content
        else:
            return self.content

    def decrypt(self, password: str) -> None:
         self.content = json.loads(read_encrypted_file(projects_file_path, password.encode()))

projects_configurations = _Projects_configurations_manager()

def find_user_project(name: str) -> Path | None:
    '''

    This function looks for a projects full path from just the given name of the folder of the project.
    If no project is found, it returns None.

    :type name: str
    :return: The path to the project if found, otherwise None.
    :rtype: Path | None
    '''

    name.lower()
    for candidate_path in projects_configurations.get().keys():
        if Path(candidate_path).name.lower() == name:
            return Path(candidate_path)
    
    return None


def send_notification(title: str, message: str, timeout: int = 5):
    '''
    Send a desktop notification.

    :param title: the title of the notification
    :type title: str
    :param message: the message of the notification
    :type message: str
    :param timeout: the duration (in seconds) for which the notification should be displayed
    :type timeout: int
    '''

    notification.notify(
        title=title,
        message=message,
        app_name='Packer',
        app_icon=f'{assets_dir}/images/Packer icon.png',
        timeout=timeout
    )

    notification_sound.play()