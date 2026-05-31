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
from packer.config import Project, projects_configurations, Settings
from packer.utils import normalize_settings_keys

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

    if projects_configurations is not None:
        projects = {str(Path(project_directory).name): project_directory for project_directory in projects_configurations.keys()}
        project_names = list(projects.keys())
        print('Choose a project:')
        for i in range(len(project_names)):
            print(f'\t{i}. {project_names[i]}')

        new_project_index = i + 1
        print(f'\t{new_project_index}. new project')

        input_project = stripped_input('Project you wish to update: ')
        if int(input_project) == new_project_index if input_project.isdigit() else input_project == 'new project':
            project_directory = None
        else:
            project_directory = projects[project_names[int(input_project)]] if input_project.isdigit() else projects[input_project]
    else:
        project_directory = None


    if project_directory == None:

        print(f'Creating a new project profile!\nYou will need to set up some required settings[7] before we begin.')
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
        print('Setup complete. Continuing with configuration...')

        gofile_user_token = getpass('3. Gofile user token: ')

        gofile_folder_id_input = getpass('4. Gofile folder id (leave empty to create a folder): ')
        if gofile_folder_id_input == '':
            gofile_folder_id = create_go_file_folder(input('name of the folder: '), gofile_user_token)['data']['id']
        else:
            gofile_folder_id = gofile_folder_id_input

        print('Now go over to Github and create a PAT and enter it below.')
        new_project_settings = {
            project_directory: {
                'github repo token': getpass('5. Github repo token: '),
                'gofile user token': gofile_user_token,
                'gofile folder id': gofile_folder_id,
                'github repo url': input('6. Github repo url (username/repo): ') if 'github_repo_url' not in locals() else github_repo_url,
                'program name': input('7. Program name: ') if 'program_name' not in locals() else program_name
                }
            }

        if simple_prompt(f'Would you like to edit optional settings[1]', 'n'):
            compile_command_input = stripped_input('nuitka compile command [None]: ')
            if compile_command_input != '':
                new_project_settings[project_directory]['compile command'] = compile_command_input.split(' ')

        with open(f'{config_dir}/projects.json', 'w') as f:
            dump(new_project_settings, f, indent=4)

        print(f'Project configuration saved at: {config_dir}/projects.json! You can change them later by editing the file or deleting it to go through the setup again.')

    
    return (project_directory, Project(**normalize_settings_keys(new_project_settings[project_directory])) if projects_configurations is None else projects_configurations[project_directory])