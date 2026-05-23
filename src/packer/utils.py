from importlib.resources.abc import Traversable
from json import JSONDecodeError, load
from pathlib import Path


def load_config(assets_dir: Traversable, config_dir: str | Path) -> str | tuple[dict, dict, dict | None]:
    '''
    Load configuration settings from files.

    This function reads default settings and configuration files, then loads 
    user-specific settings to create a complete configuration tuple.

    :param assets_dir: Directory containing default configuration files
    :type assets_dir: Traversable
    :param config_dir: Path to the user configuration directory
    :type config_dir: str | Path
    :return: Tuple containing (user_settings, default_settings, default_config)
             where default_config may be None if not present. **Or a str for an error**.
    :rtype: tuple[dict, dict, dict | None] | str
    '''

    try:
        with open(f'{assets_dir}/default settings.json') as f:
            default_settings = load(f)

        if Path(f'{assets_dir}/default config.json').exists():
            with open(f'{assets_dir}/default config.json') as f:
                default_config = load(f)

        with open(f'{str(Path(config_dir).absolute())}/settings.json') as f:
            user_settings = load(f)
    except JSONDecodeError:
        return 'Couldn\'t parse settings\nPlease make sure your settings uses the JSON (JavaScript Object Notation) https://json.org syntax (ECMA-262 3rd edition)'
    except Exception as e:
        return f'Something went wrong.\nError: {e}'

    return (user_settings, default_settings, default_config if 'default_config' in locals() else None)