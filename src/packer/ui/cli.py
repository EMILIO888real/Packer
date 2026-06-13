from argparse import ArgumentParser
from json import load
from pathlib import Path
from shutil import rmtree
import sys

from packer.assets.exceptions import global_exception_handler
from packer.custom_modules.etf import print_list
from packer.paths import root_dir, assets_dir, config_dir, log_dir, log_path, error_report_path, data_dir, cache_dir
from packer.config import Project, packer_version, projects_configurations
from packer.core import Packer
from packer.utils import normalize_settings_keys


def _clear_path(path: str | Path) -> None:
    path = Path(path)
    rmtree(path, ignore_errors=True)
    print(f'Cleared {path}')


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

    normalized = raw_value.lower()

    if raw_value == 'M' or normalized == 'major':
        version['major'] += 1
        version['minor'] = 0
        version['patch'] = 0
        return version

    if raw_value == 'm' or normalized == 'minor':
        version['minor'] += 1
        version['patch'] = 0
        return version

    if raw_value == 'p' or normalized == 'patch':
        version['patch'] += 1
        return version

    raise ValueError('Use either M, m, p or a full version like 0.10.1.')


def main():
    parser = ArgumentParser('packer', description='Packer CLI tool')
    subparsers = parser.add_subparsers(dest='command')

    parser.add_argument('-p', '--paths', action='store_true', help='Output all storage paths')
    parser.add_argument('-v', '--version', action='store_true', help='Display the software\'s version')
    parser.add_argument('-s', '--saves', action='store_true', help='Displays all saved projects')

    clear_command_parser = subparsers.add_parser('clear', help='Clear data produced (cache, saves and so on)')
    clear_command_parser.add_argument('-c', '--cache', action='store_true', help='Clear cache data')
    clear_command_parser.add_argument('-s', '--save', action='store_true', help='Clear config/settings data')
    clear_command_parser.add_argument('-l', '--log', action='store_true', help='Clear log directory')
    clear_command_parser.add_argument('-u', '--user', action='store_true', help='Clear user directory')

    run_command_parser = subparsers.add_parser('run', help='Runs packer release and update process on the specified project')
    run_command_parser.add_argument('-p', '--project', required=True, help='Specify the project to release an update on')
    run_command_parser.add_argument('-n', '--new_version', required=True, help='Specify the new version to update to')


    args = parser.parse_args()


    match args.command:
        case 'clear':
            targets = set()

            if args.cache:
                targets.add(cache_dir)
            if args.save:
                targets.add(config_dir)
            if args.log:
                targets.add(log_dir)
            if args.user:
                targets.add(data_dir)

            if not any((args.cache, args.save, args.log, args.user)):
                targets.update((cache_dir, config_dir, data_dir, log_dir))

            for target in targets:
                _clear_path(target)
        
        case 'run':
            project_config = None
            project_path = None

            for candidate_path in projects_configurations.keys():
                if Path(candidate_path).name == args.project:
                    project_path = Path(candidate_path)
                    project_config = Project(**normalize_settings_keys(projects_configurations[candidate_path]))
                    break

            if not project_path:
                print(f'No such project found: {args.project}')
                sys.exit(1)

            with open(f'{project_path}/src/{project_config.program_name}/assets/version.json') as version_handle:
                current_version = load(version_handle)

            try:
                next_version = resolve_version(current_version, args.new_version)
            except ValueError as exc:
                print(f'Invalid version input: {exc}')
                sys.exit(1)

            packer = Packer(
                next_version, current_version, project_path,
                project_config.gofile_user_token, project_config.gofile_folder_id, project_config.github_repo_token,
                project_config.program_name, project_config.github_repo_url, None, None, project_config.compile_command,
                project_config.before_commands, project_config.after_commands,
                project_config.model, project_config.description_prompt, project_config.title_prompt,
                project_config.release_notes_template_path, project_config.changelog_git_hash,
            )
            def packer_exception_handler(exc_type, exc_value, exc_traceback):
                packer.revert_changes()
                global_exception_handler(exc_type, exc_value, exc_traceback)

            sys.excepthook = packer_exception_handler # replace the global exception handler with packer's to revert changes in case Packer was running.

            packer.run()
            


    if args.paths:
        print(f'root_dir: {root_dir}')
        print(f'assets_dir: {assets_dir}')
        print(f'config_dir: {config_dir}')
        print(f'log_dir: {log_dir}')
        print(f'log_path: {log_path}')
        print(f'error_report_path: {error_report_path}')
        print(f'data_dir: {data_dir}')
        print(f'cache_dir: {cache_dir}')

    if args.version:
        print(f'Packer version {packer_version}')

    if args.saves:
        if projects_configurations:
            print_list(list(projects_configurations.keys()))
        else:
            print('No projects saved!')
    
    if len(sys.argv) > 1:
        sys.exit()