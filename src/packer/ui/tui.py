from getpass import getpass, getuser
from json import dump
from pathlib import Path
from typing import Any
from platformdirs import user_documents_dir
from re import match
from keyword import iskeyword
from sys import builtin_module_names
from importlib import import_module

from packer.setup import main as setup
from packer.paths import config_dir
from packer.custom_modules.et import capitalize, stripped_input, create_go_file_folder, simple_prompt
from packer.config import load, user_settings, Settings

def user_input(text: str, index: int = 3) -> str:
    '''
    strips user input and capitalizes input.

    :param text: The text to be displayed and the user will input.
    :type text: str
    :return: The user's response.
    :rtype: str
    '''

    return stripped_input(capitalize(text, index))

def main() -> tuple[str, Settings]:
    '''
    Main function for the TUI. This script handles user input and performs various tasks based on the input. It includes options to create a new Go file or folder, setup configurations, manage assets, and interact with custom modules. The function also provides interactive prompts for user inputs and processes these inputs accordingly.

    :return: project directory and the settings associated with that project.
    :rtype: tuple
    '''

    if user_settings is not None:
        projects = list(user_settings.keys())
        print('Choose a project:')
        for i in range(len(projects)):
            print(capitalize(f'\t{i}. {Path(projects[i]).name}', 4))

        new_project_index = i + 1
        print(capitalize(f'\t{new_project_index}. new project', 4))

        input_project = stripped_input('Project you wish to update: ')
        if int(input_project) == new_project_index if input_project.isdigit() else input_project == 'new project':
            project_directory = None
        else:
            project_directory = projects[int(input_project)] if input_project.isdigit() else input_project
    else:
        project_directory = None


    if project_directory == None:

        required_settings = ['github repo token']
        MANUAL_INPUT_SETTINGS = 6

        print(f'Creating a new project profile!\nYou will need to set up some required settings[{len(required_settings) + MANUAL_INPUT_SETTINGS}] before we begin.')
        program_name = input('1. Program name: ')

        try:
            import_module(program_name)
            import_in_conflict = True
        except ImportError:
            import_in_conflict = False
            pass

        while (program_name[:1].isdigit()) or (program_name.count(' ') > 0) or (not match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', program_name)) or (iskeyword(program_name)) or (program_name in builtin_module_names or (import_in_conflict)):
            print('Name isn\'t acceptable since it doesn\'t follow restrictions:\n\t* Can\'t start with a number\n\t* Can\'t contain any spaces\n\t* Can\'t contain any special characters (Alphanumeric characters and underscores only)\n\t* Can\'t be a Python keyword\n\t* Can\'t be a built-in module name\n\t* Can\'t be in conflict with other existing modules')
            program_name = input('Reenter the program name: ')

        default_project_dir = f'{user_documents_dir()}/{program_name}'

        project_directory = user_input(f'2. project directory (absolute path, default to: {default_project_dir}): ')
        if project_directory == '':
            project_directory = default_project_dir

        project_directory.rstrip('/')

        if simple_prompt('Create a new github repository'):
            github_pat = getpass('Github personal access token (with Administration permissions): ')
            github_repo_url = None
        else:
            github_pat = None
            github_repo_url = stripped_input('Github repo url (username/repo): ')

        print('Starting setup...')
        github_repo_url = setup(project_directory, input('Author name of the program: '), program_name, github_pat, github_repo_url)
        print('Setup complete. Continuing with configuration.')

        gofile_user_token = getpass('3. gofile user token: ')

        gofile_folder_id_input = getpass('4. gofile folder id (leave empty to create a folder): ')
        if gofile_folder_id_input == '':
            gofile_folder_id = create_go_file_folder(stripped_input('name of the folder: '), gofile_user_token)['data']['id']
        else:
            gofile_folder_id = gofile_folder_id_input


        new_project_settings = {
            project_directory: {
                'gofile user token': gofile_user_token,
                'gofile folder id': gofile_folder_id,
                'github repo url': user_input('5. github repo url (username/repo): ') if 'github_repo_url' not in locals() else github_repo_url,
                'program name': user_input('6. program name: ') if 'program_name' not in locals() else program_name
                }
            }
        
        for i in range(len(required_settings)):
            setting = required_settings[i]
            new_project_settings[project_directory][setting] = user_input(f'{i + MANUAL_INPUT_SETTINGS + 1}. {setting}: ')

        if simple_prompt('Would you like to edit optional settings', 'n'):
            optional_settings = ['model']
            optional_settings_count = len(optional_settings)

            print(f'There are {optional_settings_count} optional settings.')

            for i in range(optional_settings_count):
                setting = optional_settings[i]
                user_answer = user_input(f'{i}. {setting}: ')
                if user_answer != '':
                    new_project_settings[project_directory][setting] = user_answer

            compile_command_input = stripped_input('nuitka compile command [None]: ')

            if compile_command_input != '':
                new_project_settings[project_directory]['compile command'] = compile_command_input.split(' ')

        with open(f'{config_dir}/settings.json', 'w') as f:
            dump(new_project_settings, f, indent=4)

        print(f'Settings saved at: {config_dir}/settings.json! You can change them later by editing the file or deleting it to go through the setup again.')

    return (project_directory, load(project_directory))