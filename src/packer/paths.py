from importlib import resources

root_dir = resources.files('packer') 
assets_dir = root_dir.joinpath('assets')