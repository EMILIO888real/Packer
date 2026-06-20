from datetime import datetime
from importlib import resources
from pathlib import Path
from platformdirs import user_cache_dir, user_config_dir, user_data_dir, user_log_dir

root_dir = resources.files('packer') 
assets_dir = root_dir.joinpath('assets')
config_dir = user_config_dir('packer', 'EMILIO', ensure_exists=True)
projects_file_path = Path(f'{config_dir}/projects.json')
settings_file_path = Path(f'{config_dir}/settings.json')
log_dir = user_log_dir('packer', 'EMILIO', ensure_exists=True)
log_path = Path(f'{log_dir}/{datetime.date(datetime.now())}.log')

error_report_path = Path(f'{log_dir}/error report {datetime.date(datetime.now())}.json')


data_dir = user_data_dir('packer', 'EMILIO', ensure_exists=True)
cache_dir = user_cache_dir('packer', 'EMILIO', ensure_exists=True)