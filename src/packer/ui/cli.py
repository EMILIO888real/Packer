'''Command-line interface for Packer.'''

__all__ = ['main']

from packer.ui.arguments import args # Run the argument parser before any of the heavy CLI imports.

from collections.abc import Callable
from json import dump, load
from os import mkdir
from pprint import pprint
from shutil import which
import sys
from subprocess import run
from pydantic import ValidationError
from pyzipper import WZ_AES, ZIP_DEFLATED, AESZipFile
from random import choice, randint
from datetime import datetime, timedelta
from itertools import cycle
from pyfiglet import FigletFont, figlet_format
from time import sleep
from typing import Literal
from pathlib import Path
from shutil import rmtree

from packer import actions
from packer.custom_modules.et import resolve_version, normalize_settings_keys, get_folder_size, format_size
from packer.custom_modules.etf import (print_colored_text, simple_prompt_retries, stripped_input, print_list,
                                       print_colored_text, clear_lines)
from packer.paths import (root_dir, assets_dir, config_dir, log_dir, log_path, error_report_path, data_dir,
                        cache_dir, projects_file_path, settings_file_path, metadata_path
                        )
from packer.config import (Project, projects_configurations, all_settings, find_user_project,
                        user_settings, all_settings_status,
                        packer_version
                        )
from packer.setup import main as setup, tui
from packer.change import main as change, tui as change_tui
from packer.ui.gui import Gui
from packer.utils import track_model_pull, TqdmProgressRenderer
from packer.initialization import (exception_handler, ollama_available, available_text_editors, default_text_editor,
                                   available_models, default_model)
from packer.constants import NICE_FONTS, COLOR_PALLETS


def _draw_frame(lines: list[str], colors: cycle):
    print_colored_text(lines[0], next(colors), end='\t')
    print('Packer version:', end=' ')
    print_colored_text(packer_version, [0, 0, 255])
    print_colored_text(lines[1], next(colors), end='\t')
    print('Developed by', end=' ')
    print_colored_text('EMILIO', [0, 0, 255])
    print_colored_text(lines[2], next(colors), end='\t')
    print('Project is under the', end=' ')
    print_colored_text('MIT License', [0, 0, 255])
    print_colored_text(f'{lines[3]}', next(colors), end='\t')
    print_colored_text('https://github.com/EMILIO888real/Packer', [255, 105, 180])
    for line in lines[4:]:
        print_colored_text(line, next(colors))

def _get_text_and_colors(font: str, all_colors: list[list[list[int]]] | list[list[int]]| str) -> tuple[list[str], cycle]:
    if type(all_colors) == str:
        colors = choice(COLOR_PALLETS) if all_colors == 'nice-random' else [[randint(0, 255) for _ in range(3)] for _ in range(0, randint(5, 10))]
    else:
        colors = all_colors

    if font in ('nice-random', 'random'):
        text = figlet_format('Packer', choice(NICE_FONTS) if font == 'nice-random' else choice(FigletFont.getFonts()))
    else:
        text = figlet_format('Packer', font)

    lines = text.splitlines()

    if len(colors) == len(lines):
        colors.pop()

    return (lines, cycle(colors))

def _version_animation(static: bool = False, font: str | Literal['nice-random', 'random'] = 'nice-random', all_color: Literal['nice-random', 'random'] | list[list[list[int, int, int]]] = 'nice-random'):
    try:
        if static:
            _draw_frame(*_get_text_and_colors(font, all_color))
        else:
            while True:
                lines, colors = _get_text_and_colors(font, all_color)
                lines_amount = len(lines)

                finish_time = datetime.now() + timedelta(seconds=2)
                while datetime.now() < finish_time:
                    _draw_frame(lines, colors)
                    sleep(0.1)
                    clear_lines(lines_amount)
    except KeyboardInterrupt:
        pass

def _clear_path(path: str | Path) -> None:
    path = Path(path)
    rmtree(path, ignore_errors=True)
    print(f'Cleared {path}')


def main():

    global default_model

    if args.gui:
        gui = Gui()
        gui.run()
    else:
        exception_handler.update() # Set the exception handler for anything except the GUI
        if type(all_settings_status) == list and all_settings_status != []:
            print_colored_text(f'Missing some mandatory settings: {all_settings_status}', [255, 0, 0])
            print_colored_text('Defaulted to default values for missing settings for this session', [255, 255, 0])

            print(f'Let\'s set up some basic settings [{len(all_settings_status)}]\n')
            settings = {}

            if 'text_editor' in all_settings_status:
                if available_text_editors:
                    print('Found text editors:')
                    for text_editor in available_text_editors:
                        print_colored_text(f'  {text_editor[0]} [{text_editor[1]}]')

                settings['text_editor'] = input(f'1. Text editor {f'[{default_text_editor}]' if default_text_editor else ''} ') or default_text_editor

            if 'wait_flag' in all_settings_status:
                for text_editor in available_text_editors:
                    if settings['text_editor'] == text_editor[1]:
                        settings['wait_flag'] = text_editor[2]
                        break
                else:
                    settings['wait_flag'] = input('2. Wait flag: ')

            if 'model' in all_settings_status:
                if ollama_available:
                    if available_models:
                        print('Found ollama AI models:')
                        print_list(available_models, [138, 43, 226], start='  - ')
                    else:
                        print_colored_text('No installed completion models found', [255, 255, 0])
                        if simple_prompt_retries('Install mistral [default] model'):
                            track_model_pull('mistral:latest', TqdmProgressRenderer())
                            default_model = 'mistral:latest'

                    settings['model'] = input(f'3. Model {f'[{default_model}]' if default_model else ''} ') or default_model
                else:
                    print_colored_text('Ollama ins\'t available on PATH', [255, 0, 0])
                    if simple_prompt_retries('Will u use AI features in Packer'):
                        print_colored_text('Then please install the ollama clint and start the program again', [134, 202, 146])
                        sys.exit()
                    else:
                        print_colored_text('Setting all AI prompts to None (disabling all AI features, excluding individual project configs) ...', [190, 144, 114])
                        settings['model'] = 'mistral'
                        settings['changes_summary_prompt'] = None
                        settings['high_level_summary_prompt'] = None
                        settings['suggestions_prompt'] = None

            user_settings.update(settings)

            with open(settings_file_path, 'w') as f:
                dump(user_settings, f, indent=4)

            if user_settings.get('automatic error reporting') != False:
                print_colored_text('Note that automatic error reporting is enabled by default', [255, 255, 0])
            print_colored_text('Settings saved at: ', [0, 255, 0], end='')
            print_colored_text(settings_file_path, [255, 105, 180])

        elif type(all_settings_status) == ValidationError:
            print_colored_text('There are problems with the user settings:', [255, 0, 0])
            for error in all_settings_status.errors():
                print_colored_text(f'{error['loc'][0]}:', end='\n  ')
        
                print(f'Problem type: ', end='')
                print_colored_text(error['type'], [255, 0, 0], end='\n  ')
        
                print('Message: ', end='')
                print_colored_text(error['msg'], [0, 255, 0])
            print(f'Settings: ', end='')
            print_colored_text(settings_file_path, [255, 105, 180])
            print_colored_text('Defaulted to default setting for this session', [255, 255, 0])

        elif type(all_settings_status) != list:
            print_colored_text('Unable to read your settings file.', [255, 0, 0])
            print_colored_text('This may be caused by invalid JSON, insufficient permissions, or file corruption.', [255, 255, 0])
            print_colored_text(f'Error: {all_settings_status}', [255, 0, 0])
            print(f'Settings: ', end='')
            print_colored_text(settings_file_path, [255, 105, 180])
            print_colored_text('Using the default settings for this session.', [255, 255, 0])


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

            with open(f'{project_path}/src/{project_path.name}/assets/version.json') as f:
                current_version = load(f)

            try:
                chosen_version = resolve_version(current_version, args.run_version if args.run_version else stripped_input('New version(x, y, z): '))
            except ValueError as e:
                print(f'Invalid version input: {e}')
                exit(1)

            actions.run(chosen_version, project_path, Project(**normalize_settings_keys(projects_configurations.get_w_tui()[str(project_path)])))

        
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
                    args.setup_authenticate), args.setup_open_project)}''')
        
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
                output = change_tui(args.change_changes, args.change_overall_description, not args.change_ai_suggestions, args.change_no_index)
                change(project, output[0], output[1], ai_summary=not args.change_ai_summary, no_index=output[2])
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
        _version_animation(static=args.static, font=args.version_font, all_color=args.version_color)

    if args.saves:
        if projects_configurations.get_w_tui():
            print_list(list(projects_configurations.get_w_tui().keys()))
        else:
            print('No projects saved!')
    
    if args.config:
        pprint(all_settings.model_dump())

    if args.projects:
        SENSITIVE_CONTENT = ('gofile user token', 'gofile folder id', 'github repo token', 'pypi api token')
        for project, project_settings in projects_configurations.get_w_tui().items():
            print(f'Project: {Path(project).name}')
            for setting_key, settings_value in project_settings.items():
                print(f'\t{setting_key}: {f'{(len(settings_value) - 4) * '*'}{settings_value[-4:]}' if setting_key in SENSITIVE_CONTENT else settings_value}')

    if len(sys.argv) > 1:
        sys.exit()