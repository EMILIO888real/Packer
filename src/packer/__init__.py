'''Public package-level exports for Packer.'''

__all__ = [
    'load_config', 'Packer', 'setup', 'commit_change', 
    'simple_merge_settings', 'normalize_settings_keys', 
    'Global_exception_handler', 'tree'
]

def __getattr__(name: str):
    match name:
        case 'Packer':
            from packer.core import Packer
            return Packer
        case 'setup':
            from packer.setup import main as setup
            return setup
        case 'commit_change':
            from packer.change import main as commit_change
            return commit_change
        case 'load_config':
            from packer.custom_modules.et import load_config
            return load_config
        case 'normalize_settings_keys':
            from packer.custom_modules.et import normalize_settings_keys
            return normalize_settings_keys
        case 'tree':
            from packer.custom_modules.et import tree
            return tree
        case 'simple_merge_settings':
            from packer.custom_modules.et import simple_merge_settings
            return simple_merge_settings
        case 'Global_exception_handler':
            from packer.exceptions import Global_exception_handler
            return Global_exception_handler
        case _:
            raise AttributeError(f'module \'{__name__}\' has no attribute \'{name}\'')