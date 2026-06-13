from importlib.resources.abc import Traversable
from json import JSONDecodeError, load
from pathlib import Path
from typing import Any

from packer.custom_modules.et import merge_settings


def load_config(assets_dir: Traversable, config_dir: str | Path) -> str | tuple[dict | None, dict, dict | None]:
    '''
    Load configuration settings from files.

    This function reads default settings and configuration files, then loads 
    user-specific settings to create a complete configuration tuple.

    :param assets_dir: Directory containing default configuration files
    :type assets_dir: Traversable
    :param config_dir: Path to the user configuration directory
    :type config_dir: str | Path
    :return: Tuple containing (user_settings, default_settings, default_config)
             where default_config or user_settings may be {} if not present. **Or a str for an error**.
    :rtype: tuple[dict, dict, dict | None] | str
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

def simple_merge_settings(user_settings: dict[str, Any] | None, default_settings: dict[str, Any], default_config: dict[str, Any] | None = None) -> dict[str, Any]:
    '''
    Merge user settings with default settings and optional default configuration.

    This function combines user-provided settings with default settings. If a
    default configuration is provided, it is also merged into the result. The
    merging process ensures that user settings take precedence over defaults.

    :param user_settings: A dictionary of user-defined settings
    :type user_settings: dict[str, Any]
    :param default_settings: A dictionary of default settings
    :type default_settings: dict[str, Any]
    :param default_config: An optional dictionary of default configuration values
    :type default_config: dict[str, Any] | None
    :return: A merged dictionary containing the combined settings and configuration
    :rtype: dict[str, Any]
    '''

    default_settings = normalize_settings_keys(default_settings)
    if default_config:
        default_settings.update(normalize_settings_keys(default_config))

    return merge_settings(normalize_settings_keys(user_settings), default_settings)

def normalize_settings_keys(all_settings: dict[str: Any]) -> dict[str: Any]:
    '''
    Normalize configuration settings keys by replacing spaces with underscores.
    
    This function processes a dictionary of settings and converts any keys that 
    contain spaces into keys with underscores, making them valid Python identifiers.
    
    :param all_settings: Dictionary containing configuration settings with potentially 
                         spaces in keys
    :type all_settings: dict[str, Any]
    :return: Dictionary with normalized keys (spaces replaced with underscores)
    :rtype: dict[str, Any]
    '''

    normalized_settings = {}

    for item in all_settings.items():
        normalized_settings[item[0].replace(' ', '_')] = item[1]
    
    return normalized_settings

def resolve_version(current_version: dict[str, int], version_input: str) -> dict[str, int]:
    '''
    Resolve a version bump token or explicit version string into a version dict.

    :param current_version: The current version as a dictionary with keys 'major', 'minor', and 'patch'
    :type current_version: dict[str, int]
    :param version_input: A version bump token ('major', 'minor', 'patch') or explicit version string (e.g., '1.2.3')
    :type version_input: str
    :return: The resolved version as a dictionary with keys 'major', 'minor', and 'patch'
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

    match version_input:
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
            raise ValueError('Use either M, m, p or a full version like 0.10.1.')
        
    return version