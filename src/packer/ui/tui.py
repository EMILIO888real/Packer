from json import dump, dumps, loads, load
from pathlib import Path
from typing import Callable
from subprocess import run
from inspect import signature
from sys import exit

from packer import actions
from packer.setup import main as setup, tui
from packer.paths import config_dir, projects_file_path
from packer.custom_modules.et import create_gofile_folder, normalize_settings_keys, resolve_version
from packer.custom_modules.etf import stripped_input, simple_prompt_retries
from packer.config import Project, _getpass, projects_configurations, all_settings
from packer.utils import write_encrypted_file

def main() -> tuple[str, Project]:
    '''
    Main function for the TUI. This script handles user input and performs various tasks based on the input. It includes options to create a new Go file or folder, setup configurations, manage assets, and interact with custom modules. The function also provides interactive prompts for user inputs and processes these inputs accordingly.

    :return: project directory and the settings associated with that project, as well the user chosen version.
    :rtype: tuple
    '''

    if projects_configurations.get_w_tui():
        projects = {str(Path(project_directory).name): project_directory for project_directory in projects_configurations.get_w_tui().keys()}
        project_names = list(projects.keys())
        print('Choose a project:')
        for i in range(len(project_names)):
            print(f'\t{i}. {project_names[i]}')

        new_project_index = i + 1
        print(f'\t{new_project_index}. new project')

        input_project = stripped_input('Project you wish to update: ')
        try:
            if int(input_project) == new_project_index if input_project.isdigit() else input_project == 'new project':
                project_directory = None
            else:
                project_directory = projects[project_names[int(input_project)]] if input_project.isdigit() else projects[input_project]
        except (KeyError, IndexError):
            print(f'Couldn\'t find/evaluate the project: {input_project}')
            exit(1)
    else:
        project_directory = None


    if project_directory == None:
        print(f'Creating a new project profile!\nYou will need to set up some required settings before we begin.')

        print(f'Starting with creating a new project, up to {len(signature(tui).parameters)} options.')
        user_setup_data = tui()
        project_directory = user_setup_data[0]

        gofile_user_token = _getpass('1. Gofile user token: ') or None

        if gofile_user_token:
            gofile_folder_id = _getpass('2. Gofile folder id (leave empty to create a folder): ') or None
            if not gofile_folder_id:
                folder_name = input('name of the folder: (leave empty to skip): ') or None
                if folder_name:
                    response = create_gofile_folder(folder_name, gofile_user_token)
                    user_setup_data[6] = response['data']['code']
                    gofile_folder_id = response['data']['id']
            gofile_data = {'gofile user token': gofile_user_token, 'gofile folder id': gofile_folder_id}

        print('Starting setup...')
        github_repo_url = setup(*user_setup_data)
        print('Setup complete. Continuing with configuration...')


        print('Now go over to Github and create a PAT and enter it below.')
        new_projects_configurations = {
            project_directory: {
                'github repo token': _getpass('5. Github repo token: '),
                **gofile_data,
                'github repo url': github_repo_url
                }
            }

        print('lastly at pypi.org get an API token')
        new_projects_configurations[project_directory]['pypi api token'] = _getpass('6. pypi API token [None] ') or None


        if simple_prompt_retries(f'Would you like to edit optional settings', 'n'):
            def prompt_optional_setting(setting: str, text: str = None, key: Callable = lambda x:x) -> None:
                if text is None:
                    text = setting
                setting = stripped_input(f'{text} [{Project.model_fields[setting.replace(' ', '_')].default}]: ')
                if setting:
                    new_projects_configurations[project_directory][setting] = key(setting)

            def split_str(x: str) -> list[str]:
                return x.split(' ')
            
            prompt_optional_setting('compile command', 'Nuitka compile command', split_str)
            prompt_optional_setting('before commands', 'Before committing commands', split_str)
            prompt_optional_setting('after commands', 'After committing commands', split_str)
            prompt_optional_setting('model', 'Enter the name of the ollama model you wish to use')

            print(f'To customize description or title prompt, or any other settings edit the {config_dir}/projects.json file directly. And follow settings structure, check . \
                  You can check out the defaults for examples via Project class documentation.')
            
            if simple_prompt_retries('Open projects.json', 'n'):
                run([all_settings.text_editor, '--wait', f'{config_dir}/projects.json'])

        if projects_file_path.exists():
            final_projects_configurations = loads(projects_file_path.read_text())
            final_projects_configurations.update(new_projects_configurations)
        else:
            final_projects_configurations = new_projects_configurations

        if simple_prompt_retries('Encrypt projects.json (sensitive data, like tokens)', 'n'):
            write_encrypted_file(dumps(new_projects_configurations, indent=4).encode(), projects_file_path, _getpass('Create a password: ').encode())
        else:
            with open(projects_file_path) as f:
                dump(final_projects_configurations, f, indent=4)

        print(f'Project configuration saved at: {config_dir}/projects.json! You can change them later by editing the file or deleting it to go through the setup again.')
        exit()


    with open(f'{project_directory}/src/{Path(project_directory).name}/assets/version.json') as f:
        current_version = load(f)

    try:
        next_version = resolve_version(current_version, stripped_input('New version(x, y, z): '))
    except ValueError as exc:
        print(f'Invalid version input: {exc}')
        exit(1)

    actions.run(next_version, project_directory, Project(**normalize_settings_keys(projects_configurations.get_w_tui()[project_directory])))