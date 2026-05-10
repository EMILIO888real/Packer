from importlib import resources
from platformdirs import user_config_dir

root_dir = resources.files('packer') 
assets_dir = root_dir.joinpath('assets')
config_dir = user_config_dir('packer', 'EMILIO', ensure_exists=True)