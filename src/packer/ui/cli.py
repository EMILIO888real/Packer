from argparse import ArgumentParser
from collections.abc import Callable
from json import dump, load
from os import mkdir
from pathlib import Path
from pprint import pprint
from shutil import rmtree, which
import sys
from subprocess import run
from textwrap import dedent
from pyzipper import WZ_AES, ZIP_DEFLATED, AESZipFile
from argcomplete import autocomplete
from getpass import getuser

from packer.custom_modules.et import resolve_version, normalize_settings_keys, get_folder_size, format_size
from packer.custom_modules.etf import print_colored_text, simple_prompt_retries, stripped_input
from packer.custom_modules.etf import print_list
from packer.paths import root_dir, assets_dir, config_dir, log_dir, log_path, error_report_path, data_dir, cache_dir, projects_file_path, settings_file_path, documents_dir, metadata_path
from packer.config import Project, packer_version, projects_configurations, all_settings, find_user_project, exception_handler, user_settings
from packer.core import Packer
from packer.setup import main as setup, tui
from packer.change import main as change, tui as change_tui

def _clear_path(path: str | Path) -> None:
    path = Path(path)
    rmtree(path, ignore_errors=True)
    print(f'Cleared {path}')

def get_project_names(**kwargs):
    return [Path(project).name for project in projects_configurations.get_w_tui().keys()]

def get_new_version(**kwargs):
    return ['M', 'm', 'p']

def get_text_editors(**kwargs):
    return ['code', 'nvim', 'vim', 'nano', 'subl3', 'atom', 'emacs', 'idea', 'webstorm', 'notepad', 'pycharm']

def get_wait_flags(**kwargs):
    return ['--wait']

def get_license_types(**kwargs):
    return ['MIT', 'Apache-2.0', 'GPL-3.0', 'BSD-3-Clause', 'Unlicense']

def get_author_names(**kwargs):
    return [getuser()]

def get_setup_paths(**kwargs):
    return [f'{documents_dir}/']

def main():
    parser = ArgumentParser('packer', description='Packer CLI tool')
    subparsers = parser.add_subparsers(dest='command')

    parser.add_argument('-p', '--paths', action='store_true', help='Output all storage paths')
    parser.add_argument('-v', '--version', action='store_true', help='Display the software\'s version')
    parser.add_argument('-s', '--saves', action='store_true', help='Displays all saved projects')
    parser.add_argument('-c', '--config', action='store_true', help='Displays the saved configuration or packer settings')
    parser.add_argument('--projects', action='store_true', help='Displays the saved configurations of projects')

    clear_command_parser = subparsers.add_parser('clear', help='Clear data produced (cache, saves and so on)')
    clear_command_parser.add_argument('-c', '--cache', action='store_true', help='Clear cache data')
    clear_command_parser.add_argument('-s', '--save', action='store_true', help='Clear config/settings data')
    clear_command_parser.add_argument('-l', '--log', action='store_true', help='Clear log directory')
    clear_command_parser.add_argument('-u', '--user', action='store_true', help='Clear user directory')

    run_command_parser = subparsers.add_parser('run', help='Runs packer release and update process on the specified project')
    run_command_parser.add_argument('-p', '--project', help='Specify the project to release an update on').completer = get_project_names
    run_command_parser.add_argument('-v', '--version', dest='run_version', help='Specify the new version to update to').completer = get_new_version

    edit_command_parser = subparsers.add_parser('edit', help='Edits user related data, like configurations, projects and so on')
    edit_command_parser.add_argument('-s', '--settings', action='store_true', help='Open to edit the settings.json in the user preferred text editor')
    edit_command_parser.add_argument('-p', '--projects', dest='edit_project', action='store_true', help='Open to edit the projects.json in the user preferred text editor')
    edit_command_parser.add_argument('-t', '--text_editor', help='Specify the text editor to use over the one saved in settings').completer = get_text_editors

    edit_command_parser.add_argument('-w', '--wait_flag', help='Specify the wait flag for the text editor to use over the one saved in settings').completer = get_wait_flags

    setup_command_parser = subparsers.add_parser('setup', help='Runs the packer new project setup function')



    setup_command_parser.add_argument('-p', '--path', dest='setup_path', help='Project directory to use for setup').completer = get_setup_paths
    setup_command_parser.add_argument('-a', '--author-name', dest='setup_author_name', help='Author name for the new project').completer = get_author_names
    setup_command_parser.add_argument('-n', '--program-name', dest='setup_program_name', help='Program name for the new project')
    setup_command_parser.add_argument('-t', '--pat', dest='setup_github_pat', help='GitHub personal access token')

    setup_command_parser.add_argument('-u', '--github-url', dest='setup_github_repo_url', help='GitHub repository URL')
    setup_command_parser.add_argument('-o', '--overwrite', action='store_true', dest='setup_overwrite', help='Overwrite existing project')
    setup_command_parser.add_argument('-c', '--code', action='store_true', dest='setup_gofile_code', help='GoFile URL / code (eg. OktQl5)')

    setup_command_parser.add_argument('-l', '--license', dest='setup_license', help='License for the new project').completer = get_license_types
    setup_command_parser.add_argument('--authenticate', dest='setup_authenticate', action='store_true', help='Authenticate with GitHub using a PAT (Personal Access Token) for pushing')

    export_command_parser = subparsers.add_parser('export', help='Export all config saved by Packer in an archive')
    export_command_parser.add_argument('-p', '--path', dest='export_path', help='Path to export archive to')
    export_command_parser.add_argument('-s', '--safe', dest='export_safe', help='Password to the archive')

    import_command_parser = subparsers.add_parser('import', help='Import Packer config from an archive')
    import_command_parser.add_argument('-p', '--path', dest='import_path', required=True, help='Path to the archive to import')
    import_command_parser.add_argument('-s', '--safe', dest='import_safe', help='Password to the archive')

    change_command_parser = subparsers.add_parser('change', help='Commit a change of a packer like style project')

    change_command_parser.add_argument('-p', '--project', dest='change_project', help='Specify the project').completer = get_project_names
    change_command_parser.add_argument('-c', '--changes', dest='change_changes', help='Specify the changes')
    change_command_parser.add_argument('-o', '--overall-description', dest='change_overall_description', help='Specify the overall description, only in use if there are more than 1 change')


    autocomplete(parser)
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
                if simple_prompt_retries('Are you sure you want to delete all Packer related data'):
                    targets.update((cache_dir, config_dir, data_dir, log_dir))

            for target in targets:
                _clear_path(target)


        case 'run':
            user_chosen_project = args.project if args.project else stripped_input('Enter the project to update: ')

            project_path = find_user_project(user_chosen_project)
            if not project_path:
                print(f'No such project found: {user_chosen_project}')
                sys.exit(1)

            project_config = Project(**normalize_settings_keys(projects_configurations.get_w_tui()[str(project_path)]))

            with open(f'{project_path}/src/{Path(project_path).name}/assets/version.json') as version_handle:
                current_version = load(version_handle)

            try:
                next_version = resolve_version(current_version, args.run_version if args.run_version else stripped_input('New version(M, m, P): '))
            except ValueError as exc:
                print(f'Invalid version input: {exc}')
                sys.exit(1)

            packer = Packer(
                next_version, current_version, project_path,
                project_config.github_repo_token,
                project_config.github_repo_url,
                project_config.gofile_user_token, project_config.gofile_folder_id, 
                None, None, project_config.compile_command,
                project_config.before_commands, project_config.after_commands,
                project_config.model, project_config.description_prompt, project_config.title_prompt,
                project_config.release_notes_template_path, project_config.changelog_git_hash,
            )
            def packer_exception_handler(exc_type, exc_value, exc_traceback):
                packer.revert_changes()
                exception_handler.handle_exception(exc_type, exc_value, exc_traceback)

            sys.excepthook = packer_exception_handler # replace the global exception handler with packer's to revert changes in case Packer was running.

            packer.run()

        
        case 'edit':
            text_editor = which(args.text_editor if args.text_editor else all_settings.text_editor)
            wait_flag = args.wait_flag if args.wait_flag else all_settings.wait_flag
            open_cmd = [f'{text_editor}', f'{wait_flag}']

            open_settings_cmd = [*open_cmd, f'{config_dir}/settings.json']
            open_projects_cmd = [*open_cmd, f'{config_dir}/projects.json']
            if args.settings:
                run(open_settings_cmd)
            if args.edit_project:
                run(open_projects_cmd)

            if not args.edit_project and not args.settings:
                run(open_settings_cmd)
                run(open_projects_cmd)
            
            
        case 'setup':
                print(f'''Github repository url: {setup(*tui(args.setup_path,
                    args.setup_author_name,
                    args.setup_program_name,
                    args.setup_github_pat,
                    args.setup_github_repo_url,
                    args.setup_overwrite,
                    args.setup_gofile_code,
                    args.setup_license, 
                    args.setup_authenticate))}''')
        
        case 'export':
            files = [
                f'projects.json',
                f'settings.json',
            ]

            archive_path = f'{args.export_path.rstrip('/') if args.export_path else '.'}/Packer config.zip'
            with AESZipFile(
                archive_path,
                'w',
                compression=ZIP_DEFLATED,
                encryption=WZ_AES if args.export_safe else None
            ) as zf:
                if args.export_safe:
                    zf.setpassword(args.export_safe.encode())
                for file in files:
                    zf.write(f'{config_dir}/{file}', arcname=file)
            print(f'Archive saved at: "{archive_path}"')
        
        case 'import':
            tmp_dir = f'{cache_dir}/tmp import'
            mkdir(tmp_dir)

            with AESZipFile(args.import_path) as zf:
                zf.setpassword(args.import_safe.encode() if args.import_safe else None)
                zf.extractall(tmp_dir)

            with open(f'{tmp_dir}/projects.json') as f:
                imported_projects = load(f)

            if projects_configurations.get_w_tui():
                print('Found existing saved projects, merging with imports...')

            projects_configurations.get_w_tui().update(imported_projects)

            with open(projects_file_path) as f:
                dump(projects_configurations.get_w_tui())
            
            # Settings file is always created, even if just an empty dict
            with open(f'{tmp_dir}/settings.json') as f:
                imported_settings = load(f)

            user_settings.update(imported_settings)
            with open(settings_file_path) as f:
                dump(user_settings)
            
            rmtree(tmp_dir)
        
        case 'change':
            user_chosen_project = args.change_project if args.change_project else Path().cwd().name
            project = find_user_project(user_chosen_project)
            if project:
                output = change_tui(args.change_changes, args.change_overall_description)
                change(project, modification_types=output[0], overall_description=output[1])
            else:
                print(f'I couldn\'t find your project: {user_chosen_project}')
                sys.exit(1)


    if args.paths:
        def create_entry(name: str, path: Path | str) -> tuple[str, int]:
            path = Path(path)
            return (f'{name}: ~/{path.relative_to(Path().home())}', (get_folder_size(path) if path.is_dir else path.stat().st_size) if path.exists() else None)
        
        def format_entry(entry: tuple[str, float]) -> str:
            return f'{entry[0]} ({format_size(entry[1])})'
        
        def print_colored_entry(entry: tuple, color: Callable):
            print(entry[0], end=' (')
            print_colored_text(format_size(entry[1]), color(entry), end='')
            print(')')
        
        print(format_entry(create_entry('root_dir', root_dir)))
        print(format_entry(create_entry('assets_dir', assets_dir)))
        print(format_entry(create_entry('config_dir', config_dir)))
        print_colored_entry(create_entry('log_dir', log_dir), lambda entry:[255, 0, 0] if all_settings.logs_size_threshold < entry[1] else [0, 255, 0])
        print(format_entry(create_entry('data_dir', data_dir)))
        print_colored_entry(create_entry('cache_dir', cache_dir), lambda entry:[255, 0, 0] if all_settings.cache_size_threshold < entry[1] else [0, 255, 0])
        print(format_entry(create_entry('log_path', log_path)))
        print(format_entry(create_entry('error_report_path', error_report_path)))
        print(format_entry(create_entry('metadata_path', metadata_path)))

    if args.version:
        print(dedent(f'''
                      ____            _                 Packer version {packer_version}
                     |  _ \\ __ _  ___| | _____ _ __     Developed by EMILIO
                     | |_) / _` |/ __| |/ / _ \\ '__|    Project is under the MIT license
                     |  __/ (_| | (__|   <  __/ |       https://github.com/EMILIO888real/Packer
                     |_|   \\__,_|\\___|_|\\_\\___|_|   
                     '''))

    if args.saves:
        if projects_configurations.get_w_tui():
            print_list(list(projects_configurations.get_w_tui().keys()))
        else:
            print('No projects saved!')
    
    if args.config:
        pprint(all_settings.model_dump())

    if args.projects:
        SENSITIVE_CONTENT = ('gofile user token', 'gofile folder id', 'github repo token')
        for project, project_settings in projects_configurations.get_w_tui().items():
            print(f'Project: {Path(project).name}')
            for setting_key, settings_value in project_settings.items():
                print(f'\t{setting_key}: {f'{(len(settings_value) - 4) * '*'}{settings_value[-4:]}' if setting_key in SENSITIVE_CONTENT else settings_value}')

    if len(sys.argv) > 1:
        sys.exit()