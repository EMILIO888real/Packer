'''Enhanced Tools (ET) Module.

A comprehensive utility module providing:
- Module importing and script management
- Color generation and formatting utilities
- File and directory operations (copying, hashing, tree structure)
- Terminal launching and process management
- Time formatting and duration handling
- Configuration loading and merging (JSON-based)
- Logging utilities with relative time formatting
- Version management and resolution
- GoFile API integration for file uploading/deletion
- Data validation and integrity checking

This module is designed to provide common utility functions for system operations,
file management, configuration handling, and API interactions.
'''

from decimal import Decimal
from hashlib import sha256
from importlib.resources.abc import Traversable
from importlib import import_module
import sys
from collections.abc import Collection
from os import execl, remove, replace, listdir, mkdir
from tempfile import NamedTemporaryFile
from typing import Any, Optional, Union
from pathlib import Path
from json import JSONDecodeError, load
from datetime import datetime, timedelta
from shutil import ignore_patterns, which, copy2, copytree
from subprocess import Popen, run
import logging
from dirhash import dirhash
from requests import get, post, delete, put
from platformdirs import user_log_dir
from random import randint
from itertools import islice, cycle

def import_modules(all_modules: dict) -> None:
    '''Import all functions from specified modules.

    Dynamically imports all specified functions from the provided modules dictionary.
    Returns a list of any modules that could not be found.

    :param all_modules: Dictionary with keys as module names and values as lists of functions to import.
    :type all_modules: dict
    :return: List of missing module names.
    :rtype: list
    '''
    missing_modules = []

    for module_name, functions in all_modules.items():
        try:
            module = import_module(module_name)
            for func in functions:
                globals()[func] = getattr(module, func)
        except ModuleNotFoundError:
            missing_modules.append(module_name)
        except AttributeError as e:
            print(f'Function not found: {e}')
    return missing_modules

def reboot_current_script() -> None:
    '''Reboot the current script.

    Restarts the current Python script with the same arguments.
    '''
    python = sys.executable
    execl(python, python, *sys.argv)

def color_generator(text_len: int = 78, save_to_disk: bool = True, color_scheme: str = 'random', style: int = 0, read_from_disk: bool = False) -> list[list[int]]:
    '''Generate a list of colors based on the specified color scheme.

    Generates RGB colors for text formatting using various color schemes.
    Supports random, neon, and neon cyberpunk schemes with different style options.

    :param text_len: The length of the text to generate colors for.
    :type text_len: int
    :param save_to_disk: If True, saves the generated colors to a file.
    :type save_to_disk: bool
    :param color_scheme: The color scheme to use ('random', 'neon_cyberpunk', 'neon').
    :type color_scheme: str
    :param style: The style variant of the color scheme to use (0, 1, etc.).
    :type style: int
    :param read_from_disk: If True, reads colors from a file instead of generating them.
    :type read_from_disk: bool
    :return: A list of RGB color triplets.
    :rtype: list[list[int]]
    '''

    # Add check for read from disk, type shi. File name, and so on

    if read_from_disk:
        with open('.colors.txt') as f:
            colors = {}
            exec(f.read(), {}, colors)
        return colors['colors']
    else:
        match color_scheme:
            case 'random':
                colors = [[randint(0, 255) for _ in range(3)] for _ in range(text_len)]
            case 'neon_cyberpunk':
                match style:
                    case 0:
                        preset_colors = [[112, 34, 144], [223, 0, 216], [18, 188, 197], [26, 64, 123], [17, 30, 54]]
                    case 1:
                        preset_colors = [[204, 17, 240], [99, 0, 255], [255, 0, 141], [209, 78, 234], [249, 99, 99]]
            case 'neon':
                preset_colors = [[78, 237, 233], [115, 237, 28], [255, 230, 0], [240, 0, 255], [0, 35, 255]]
        colors = list(islice(cycle(preset_colors), text_len))

        if not Path('.colors.txt').exists() and save_to_disk:
            with open('.colors.txt', 'w') as f:
                f.write('colors = ' + str(colors))
        return colors

def copy_with_exceptions(source: str | Path, destination: str | Path, exceptions: Optional[Collection[str]] = (), directory_exceptions: Optional[Collection[str]] = ()) -> None:
    '''Copy files and directories with exclusions.

    Copies files and directories from source to destination, excluding specified exceptions.

    :param source: The source path to copy from.
    :type source: str | Path
    :param destination: The destination path to copy to.
    :type destination: str | Path
    :param exceptions: File or directory names to exclude from copying.
    :type exceptions: Collection[str]
    :param directory_exceptions: Directory names to exclude from copying when encountered within source.
    :type directory_exceptions: Collection[str]
    '''

    if not Path(destination).exists():
        mkdir(destination)

    for item in listdir(source):
        if item in exceptions:
            continue
        item = Path(f'{source}/{item}')
        if Path(item).is_file():
            copy2(item, Path(destination))
        else:
            copytree(item, Path(f'{destination}/{item.name}'), ignore=ignore_patterns(*directory_exceptions))

def noop() -> None:
    '''Perform no operation.

    A no-operation function used as a placeholder or default value for callbacks
    and other function parameters where no action is desired.
    '''
    pass

def launch_in_new_terminal(script_path: str) -> bool:
    '''Launch a Python script in a new terminal window.

    Launches a Python script in a new terminal window with support for both Windows and Linux/WSL environments.
    Tries multiple terminal emulators in order of preference.

    :param script_path: The file path of the Python script to launch in a new terminal window.
    :type script_path: str
    :return: True if the terminal was successfully launched, False otherwise.
    :rtype: bool
    '''

    # -------------------------
    # WINDOWS OUT OF COMMISSION (doesn't work)
    # -------------------------
    if sys.platform == 'win32':
        print('Windows is temporary unsupported for automatic error report handler execution!')
        # Prefer Windows Terminal if available. OUT OF COMMISSION (doesn't work)
        wt = which('wt.exe')
        if wt:
            Popen([wt, "powershell", "-NoExit", "--%", sys.executable, script_path])
            return True

        # Fallback: PowerShell. OUT OF COMMISSION (doesn't work)
        powershell = which('powershell.exe')
        if powershell:
            Popen([powershell, '-NoExit', '-Command', f'"{sys.executable}" "{script_path}"'])
            return True

        # Fallback: CMD OUT OF COMMISSION (doesn't work)
        cmd = which('cmd.exe')
        if cmd:
            Popen([cmd, '/k', f'"{sys.executable}" "{script_path}"'])
            return True

        return False

    # -------------------------
    # LINUX / WSL
    # -------------------------
    terminals = [
        ('gnome-terminal', ['--']),
        ('konsole', ['-e']),
        ('xfce4-terminal', ['--command']),
        ('xterm', ['-e']),
        ('lxterminal', ['-e']),
        ('mate-terminal', ['-e']),
        ('tilix', ['-e']),
        ('alacritty', ['-e']),
        ('kitty', ['-e']),
        ('urxvt', ['-e']),
    ]

    for term, args in terminals:
        if which(term):
            Popen([term] + args + [sys.executable, script_path])
            return True

    return False

def format_time(seconds: float, time_format: str = '%M:%S.%m') -> str:
    '''Format a time duration into a human-readable string.

    Formats a time duration given in seconds into a human-readable string format.
    Supports format tokens: %H (hours), %M (minutes), %S (seconds), %m (milliseconds).

    :param seconds: The time duration in seconds to format.
    :type seconds: float
    :param time_format: Format string with tokens like %H, %M, %S, %m.
    :type time_format: str
    :return: A formatted string representing the time duration (e.g., "0:4:56.456").
    :rtype: str
    '''

    time_format = time_format.replace('%H', f'{int(seconds // 3600)}')
    time_format = time_format.replace('%M', f'{int((seconds % 3600) // 60)}')
    time_format = time_format.replace('%S', f'{int(seconds % 60)}')
    time_format = time_format.replace('%m', f'{int((seconds * 1000) % 1000):3d}')
    return time_format

def safe_replace(src: str | Path, dst: str | Path) -> None:
    '''Replace a file safely, retrying on permission errors.

    Replaces the file at dst with the file at src, handling PermissionError gracefully.
    Retries indefinitely until the operation succeeds.

    :param src: The source file to replace from.
    :type src: str | Path
    :param dst: The destination file to replace to.
    :type dst: str | Path
    '''
    while True:
        try:
            replace(src, dst)
            return
        except PermissionError:
            pass

def delete_upload(file_id: str, api_token: str) -> str:
    '''Delete an uploaded file from gofile.io.

    Deletes an uploaded file from gofile.io using the file ID and API token.

    :param file_id: The ID of the file to be deleted.
    :type file_id: str
    :param api_token: The API token for authentication.
    :type api_token: str
    :return: The API response as a dictionary, or error message if response is not JSON.
    :rtype: str
    '''

    response = delete(f'https://api.gofile.io/contents', headers={'Authorization': f'Bearer {api_token}'}, json={'contentsId': file_id})

    if response.headers.get('content-type','').startswith('application/json'):
        return response.json()
    else:
        return f'Unexpected response: {response.text}'

def tree(path: Union[str, Path], exclusions: Optional[Collection[str]] = ()) -> dict:
    '''Generate a nested dictionary representing directory structure.

    Generate a nested dictionary representing the directory structure with file hashes
    and a root directory hash.

    :param path: The root directory path to represent as a tree.
    :type path: str | Path
    :param exclusions: Glob patterns to exclude (e.g., '__pycache__', '*cache*', '*.pyc').
    :type exclusions: Collection[str]
    :return: Nested dictionary with directory structure, file hashes, and root hash.
    :rtype: dict
    '''

    root = Path(path)

    def iterate_dir(current_node: Path) -> dict:
        children = {'files': {}}
        for entry in sorted(current_node.iterdir(), key=lambda p: p.name):
            # Skip if entry matches any exclusion pattern
            if any(entry.match(exclusion) for exclusion in exclusions):
                continue
            
            if entry.is_file():
                file_hash = sha256()
                with open(str(entry), 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        file_hash.update(chunk)
                children['files'][entry.name] = file_hash.hexdigest()
            elif entry.is_dir():
                children[entry.name] = iterate_dir(entry)
        
        if not children['files']:
            children.pop('files')
            
        return children

    tree_result = iterate_dir(root)
    
    return {
        'root_hash': dirhash(root, 'sha256', ignore=exclusions),
        'tree': tree_result
    }

def check_dicts(integrity_dict: dict, user_dict: dict) -> set:
    '''Check dictionary integrity and find missing keys.

    Compares an integrity dictionary with a user dictionary to find missing or mismatched keys.
    Recursively checks nested dictionaries and set comparisons.

    :param integrity_dict: The reference integrity dictionary to check against.
    :type integrity_dict: dict
    :param user_dict: The user dictionary to validate.
    :type user_dict: dict
    :return: Set of missing keys or mismatched items.
    :rtype: set
    '''

    missing = set()

    for key in integrity_dict:

        integrity_item = integrity_dict[key]
        user_item = user_dict.get(key)
        if user_item == None:
            missing.add(key)
            continue

        if type(integrity_item) == list:
            integrity_item = set(integrity_item)
            user_item = set(user_item)
        else:
            check_dicts(integrity_item, user_item)

        if type(user_item) == set and type(integrity_item) == set:
            if not integrity_item.issubset(user_item) :
                missing.union(integrity_item - user_item)

    return missing

def load_clean_decimal(num: float | int | str) -> Decimal:
        '''
        loads a number as a Decimal object
        
        :param num: number to load
        :type num: float | int | str
        :return: Decimal object
        :rtype: Decimal
        '''

        return Decimal(str(num))


class RelativeTimeFormatter(logging.Formatter):
    '''A logging formatter with relative time since logger initialization.

    Formats log messages with the relative time (delta) since the logger was initialized,
    instead of absolute timestamps.

    :param fmt: The format string for the log messages. Default is '[%(levelname)s] %(asctime)s %(message)s'.
    :type fmt: str
    '''

    def formatTime(self, record, datefmt=None):
        '''Format the time of a log record using relative time.

        :param record: The log record.
        :param datefmt: Optional date format (unused).
        :return: Formatted relative time string.
        '''
        delta = timedelta(milliseconds=record.relativeCreated)
        s = str(delta)
        if '.' not in s:
            s += '.000000'  # Ensure micros are always shown
        return s.zfill(15)


def log_file_path(program: str, author: str) -> str:
    '''Get the file path for a log file in the user's log directory.

    Returns the file path for a log file in the user's log directory,
    named with the current date and .log extension.

    :param program: The name of the program for which the log file is being created.
    :type program: str
    :param author: The name of the author of the program.
    :type author: str
    :return: The file path for the log file.
    :rtype: str
    '''

    return f'{user_log_dir(program, author, ensure_exists=True)}/{datetime.date(datetime.now())}.log'

def init_logger(program: str, author: str, log_format: str = '[%(levelname)s] %(asctime)s %(message)s') -> logging.Logger:
    '''Initialize a logger with relative time formatting.

    Initializes a logger that writes to a file in the user's log directory,
    with each log message including relative time since logger initialization.

    :param program: The name of the program for which the logger is being initialized.
    :type program: str
    :param author: The name of the author of the program.
    :type author: str
    :param log_format: The format string for log messages.
    :type log_format: str
    :return: A logger instance that writes to the specified log file.
    :rtype: logging.Logger
    '''

    log_file_name = log_file_path(program, author)
    with open(log_file_name, 'a' if Path(log_file_name).exists() else 'w') as f:
        f.write(f'______Start of the log {datetime.now()}______\n')
    logger = logging.getLogger(log_file_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_file_name, 'a')
    handler.setFormatter(RelativeTimeFormatter(log_format))
    logger.addHandler(handler)
    logger.info('Initializing logger...')
    return logger

def format_version_text(version: dict) -> str:
    '''Format a version dictionary into a human-readable string.

    Formats a version dictionary into a human-readable string format.

    :param version: Dictionary with keys 'major', 'minor', and 'patch'.
    :type version: dict
    :return: Formatted string in the format "major.minor.patch".
    :rtype: str
    '''

    return f'{version["major"]}.{version["minor"]}.{version["patch"]}'

def create_gofile_folder(folder_name: str, GOFILE_USER_TOKEN: str) -> dict:
    '''Create a folder in the GoFile account root directory.

    Creates a folder in the root directory of the GoFile account and returns
    the response as a dictionary.

    :param folder_name: The name of the folder to be created.
    :type folder_name: str
    :param GOFILE_USER_TOKEN: The user token for the GoFile account.
    :type GOFILE_USER_TOKEN: str
    :return: The response from the GoFile API as a dictionary.
    :rtype: dict
    '''

    payload = {'token': GOFILE_USER_TOKEN}
    response = get('https://api.gofile.io/accounts/getid', params=payload)
    account_id = response.json()['data']['id']
    
    response = get(f'https://api.gofile.io/accounts/{account_id}', params=payload)
    
    create_payload = {
        'token': GOFILE_USER_TOKEN,
        'folderName': folder_name,
        'parentFolderId': response.json()['data']['rootFolder']
    }
    create_response = post('https://api.gofile.io/contents/createFolder', data=create_payload).json()
    
    if create_response.get('status') == 'ok':
        new_folder_id = create_response['data']['id']
        
        update_url = f'https://api.gofile.io/contents/{new_folder_id}/update'
        update_payload = {
            'token': GOFILE_USER_TOKEN,
            'attribute': 'public',
            'attributeValue': 'true' # Send as a string 'true' or 'false'
        }
        
        update_response = put(update_url, data=update_payload).json()
        
        # Inject the update confirmation into the final response payload for transparency
        create_response['data']['is_public_updated'] = update_response.get('status') == 'ok'
        
    return create_response

def load_config(assets_dir: Traversable, config_dir: str | Path) -> str | tuple[dict | None, dict, dict | None]:
    '''Load configuration settings from files.

    Reads default settings and configuration files, then loads user-specific settings
    to create a complete configuration tuple.

    :param assets_dir: Directory containing default configuration files.
    :type assets_dir: Traversable
    :param config_dir: Path to the user configuration directory.
    :type config_dir: str | Path
    :return: Tuple (user_settings, default_settings, default_config) or error string.
    :rtype: tuple[dict | None, dict, dict | None] | str
    '''

    try:
        with open(f'{assets_dir}/default settings.json') as f:
            default_settings = load(f)

        if Path(f'{assets_dir}/default config.json').exists():
            with open(f'{assets_dir}/default config.json') as f:
                default_config = load(f)
        if Path(f'{str(Path(config_dir).absolute())}/settings.json').exists():
            with open(f'{str(Path(config_dir).absolute())}/settings.json') as f:
                user_settings = load(f)
        else:
            with open(f'{str(Path(config_dir).absolute())}/settings.json', 'w') as f:
                f.write('{}')
                user_settings = {}

    except JSONDecodeError:
        return 'Couldn\'t parse settings\nPlease make sure your settings uses the JSON (JavaScript Object Notation) https://json.org syntax (ECMA-262 3rd edition)'
    except Exception as e:
        return f'Something went wrong.\nError: {e}'

    return (user_settings, default_settings, default_config if 'default_config' in locals() else None)

def normalize_settings_keys(all_settings: dict[str, Any]) -> dict[str, Any]:
    '''Normalize configuration settings keys by replacing spaces with underscores.

    Processes a dictionary of settings and converts any keys containing spaces
    into keys with underscores, making them valid Python identifiers.

    :param all_settings: Dictionary containing configuration settings with potentially spaces in keys.
    :type all_settings: dict[str, Any]
    :return: Dictionary with normalized keys (spaces replaced with underscores).
    :rtype: dict[str, Any]
    '''

    normalized_settings = {}

    for item in all_settings.items():
        normalized_settings[item[0].replace(' ', '_')] = item[1]
    
    return normalized_settings

def merge_settings(user_settings: dict, default_settings: dict) -> dict:
    '''Merge user settings with default settings.

    Merges user settings with default settings, filling in any missing values
    from the default settings.

    :param user_settings: The user settings to merge.
    :type user_settings: dict
    :param default_settings: The default settings to use for missing values.
    :type default_settings: dict
    :return: The merged settings as a dictionary.
    :rtype: dict
    '''

    settings = {}
    for setting in default_settings.items():
        current_setting = user_settings.get(setting[0])
        if current_setting == None:
            current_setting = default_settings[setting[0]]
        settings[setting[0]] = current_setting
    return settings

def simple_merge_settings(user_settings: dict[str, Any] | None, default_settings: dict[str, Any], default_config: dict[str, Any] | None = None) -> dict[str, Any]:
    '''Merge user settings with defaults and optional configuration.

    Combines user-provided settings with default settings. If a default configuration
    is provided, it is also merged into the result. User settings take precedence.

    :param user_settings: A dictionary of user-defined settings.
    :type user_settings: dict[str, Any]
    :param default_settings: A dictionary of default settings.
    :type default_settings: dict[str, Any]
    :param default_config: Optional dictionary of default configuration values.
    :type default_config: dict[str, Any] | None
    :return: A merged dictionary containing combined settings and configuration.
    :rtype: dict[str, Any]
    '''

    default_settings = normalize_settings_keys(default_settings)
    if default_config:
        default_settings.update(normalize_settings_keys(default_config))

    return merge_settings(normalize_settings_keys(user_settings), default_settings)

def resolve_version(current_version: dict[str, int], version_input: str) -> dict[str, int]:
    '''Resolve a version bump token or explicit version string.

    Resolves a version bump token (M/m/P) or explicit version string (e.g., '1.2.3')
    into a version dictionary.

    :param current_version: Current version as dict with keys 'major', 'minor', 'patch'.
    :type current_version: dict[str, int]
    :param version_input: Version bump token ('M'/'m'/'P') or explicit version string.
    :type version_input: str
    :return: Resolved version as dictionary with keys 'major', 'minor', 'patch'.
    :rtype: dict[str, int]
    '''

    version = current_version.copy()
    raw_value = version_input.strip()

    if raw_value.count('.') == 2:
        try:
            major, minor, patch = (int(part) for part in raw_value.split('.'))
        except ValueError as exc:
            raise ValueError('Use either M, m, p or a full version like 0.10.1.') from exc

        return {'major': major, 'minor': minor, 'patch': patch}

    match raw_value:
        case 'M':
            version['major'] = version['major'] + 1
            version['minor'] = 0
            version['patch'] = 0
        case 'm':
            version['minor'] = version['minor'] + 1
            version['patch'] = 0
        case 'P':
            version['patch'] = version['patch'] + 1
        case _:
            raise ValueError('Use either M, m, P or a full version like 0.10.1.')
        
    return version

def get_folder_size(folder_path: Path, exclusions: tuple[str] = ()) -> int:
    '''Calculate the total size of a folder and its subfolders in bytes.

    This function recursively calculates the total size of all files within
    a given folder and its subfolders. It is useful for determining the
    storage usage of directories in a file system. The function handles
    symbolic links.

    :param folder_path: The path to the folder for which to calculate the size.
    :type folder_path: Path
    :return: The total size of the folder in bytes. Returns 0 if the folder
             does not exist, is not a directory, or if there are permission
             errors during traversal.
    :rtype: int
    '''
    content = folder_path.rglob('*')

    result = 0
    for item in content:
        if item.is_file():
            allowed = True
            for pattern in exclusions:
                if item.match(pattern):
                    allowed = False
                    break
            if allowed:
                result += item.stat().st_size
    return result

def format_size(size_bytes: int, precision: int = 2) -> str:
    '''
    Format a size in bytes into a human-readable string with appropriate units.

    Converts a size given in bytes into a human-readable format using units such as
    B (bytes), KiB (kibibyte), MiB (mebibytes), GiB (gibibytes), and TiB (tebibyte).
    The result is rounded to two decimal places for clarity and readability.

    :param size_bytes: The size in bytes to be formatted.
    :type size_bytes: int
    :return: A formatted string representing the size with appropriate units (e.g., '1.23 MiB').
    :rtype: str
    '''

    if size_bytes is None:
        return 'N/A'
    for unit in ['B', 'KiB', 'MiB', 'GiB']:
        if size_bytes < 1024:
            return f'{size_bytes:.{precision}f} {unit}'
        size_bytes /= 1024
    return f'{size_bytes:.{precision}f} TiB'

def input_via_text_editor(text:str = '', text_editor: str = 'code', wait_flag: str = '--wait') -> str:
    '''
    Open a text editor for user input and return the edited text.

    :param text: Initial text to populate the editor with.
    :type text: str
    :param text_editor: The text editor to use for opening the file (default is 'code').
    :type text_editor: str
    :param wait_flag: The flag to pass to the editor to wait for it to close (default is '--wait').
    :type wait_flag: str
    :return: The text after editing in the text editor.
    :rtype: str
    '''

    with NamedTemporaryFile('r', delete=False) as tf:
        temp_path = tf.name
    with open(temp_path, 'w') as f:
        f.write(text)
    run([text_editor, wait_flag, temp_path])
    with open(temp_path, 'r') as f:
        text = f.read().strip()
    remove(temp_path)
    return text

if __name__ == '__main__':
    print('This module is not meant to be run directly')
    print('Import it in your program and use the functions from there')
    input('press enter to exit')