from getpass import getpass, getuser
from json import dump
from pathlib import Path
from typing import Any, Callable
from platformdirs import user_documents_dir
from re import match
from keyword import iskeyword
from sys import builtin_module_names
from importlib import import_module

from packer.setup import main as setup
from packer.paths import config_dir
from packer.custom_modules.et import stripped_input, create_go_file_folder, simple_prompt
from packer.config import Project, projects_configurations
from packer.utils import normalize_settings_keys

def print_list(items: list[Any], start: Any = '* ', end: Any = '\n', index: bool = False, index_text: str = '%i. '):
    '''
    Print a list of items with optional formatting.

    This function prints each item in a list, optionally with a prefix, suffix, and/or index numbers.
    It is designed to be flexible for various display purposes.

    :param items: A list of items to be printed.
    :type items: list[Any]
    :param start: A string to be printed before each item. Defaults to '* '.
    :type start: Any
    :param end: A string to be printed after each item. Defaults to '\n'.
    :type end: Any
    :param index: If True, each item will be printed with an index number. Defaults to False.
    :type index: bool
    :param index_text: A string to be used as the index format. Defaults to '%i. '.
    :type index_text: str
    '''

    if index:
        def print_index(i):
            print(index_text.replace('%i', str(i)), end='')
    else:
        def print_index(i):
            pass

    for i, item in enumerate(items):
        print_index(i)
        print(f'{start}{item}', end=end)

def check_module_conflict(program_name: str) -> bool:
    '''
    Check if a module name conflicts with Python built-in modules or keywords.

    :param program_name: The name of the program/module to check
    :type program_name: str
    :return: True if there is a conflict, False otherwise
    :rtype: bool
    '''

    try:
        import_module(program_name)
        return True
    except ImportError:
        return False


def main() -> tuple[str, Project]:
    '''
    Main function for the TUI. This script handles user input and performs various tasks based on the input. It includes options to create a new Go file or folder, setup configurations, manage assets, and interact with custom modules. The function also provides interactive prompts for user inputs and processes these inputs accordingly.

    :return: project directory and the settings associated with that project.
    :rtype: tuple
    '''

    global projects_configurations

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

        while (program_name[:1].isdigit()) or (program_name.count(' ') > 0) or (not match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', program_name)) or (iskeyword(program_name)) or (program_name in builtin_module_names or (check_module_conflict(program_name))):
            print('Name isn\'t acceptable since it doesn\'t follow restrictions:')
            print_list(['Can\'t start with a number', 'Can\'t contain any spaces', 'Can\'t contain any special characters (Alphanumeric characters and underscores only)', 'Can\'t be a Python keyword', 'Can\'t be a built-in module name', 'Can\'t be in conflict with other existing modules'], start='\t* ')
            program_name = input('Reenter the program name: ')


        default_project_dir = f'{user_documents_dir()}/{program_name}'

        project_directory = input(f'2. Project directory (absolute path, default to: {default_project_dir}): ')
        if project_directory == '':
            project_directory = default_project_dir

        project_directory.rstrip('/')


        if simple_prompt('Create a new github repository'):
            github_pat = getpass('Github personal access token (with Administration permissions): ')
            github_repo_url = None
        else:
            github_pat = None
            github_repo_url = stripped_input('Github repo url (username/repo): ')


        default_name = getuser()

        author_name = input(f'Author name of the program [default to: {default_name}]: ')
        if author_name == '':
            author_name = default_name


        print('Starting setup...')
        github_repo_url = setup(project_directory, author_name, program_name, github_pat, github_repo_url)
        print('Setup complete. Continuing with configuration...')


        gofile_user_token = getpass('3. Gofile user token: ')

        gofile_folder_id_input = getpass('4. Gofile folder id (leave empty to create a folder): ')
        if not gofile_folder_id_input:
            gofile_folder_id = create_go_file_folder(input('name of the folder: '), gofile_user_token)['data']['id']
        else:
            gofile_folder_id = gofile_folder_id_input


        print('Now go over to Github and create a PAT and enter it below.')
        projects_configurations = {
            project_directory: {
                'github repo token': getpass('5. Github repo token: '),
                'gofile user token': gofile_user_token,
                'gofile folder id': gofile_folder_id,
                'github repo url': github_repo_url,
                'program name': program_name
                }
            }


        if simple_prompt(f'Would you like to edit optional settings[1]', 'n'):
            def prompt_optional_setting(setting: str, text: str = None, key: Callable = lambda x:x) -> None:
                if text is None:
                    text = setting
                setting = stripped_input(f'{text} [{Project.model_fields[setting.replace(' ', '_')].default}]: ')
                if setting:
                    projects_configurations[project_directory][setting] = key(setting)

            def split_str(x: str) -> list[str]:
                return x.split(' ')
            
            prompt_optional_setting('compile command', 'Nuitka compile command', split_str)
            prompt_optional_setting('before commands', 'Before committing commands', split_str)
            prompt_optional_setting('after commands', 'After committing commands', split_str)
            prompt_optional_setting('model', 'Enter the name of the ollama model you wish to use')

            print(f'To customize description or title prompt edit the {config_dir}/projects.json file directly. And follow this structure: list[dict[str, str]]. \
                  You can check out the defaults for examples via Project class documentation.')


        with open(f'{config_dir}/projects.json', 'w') as f:
            dump(projects_configurations, f, indent=4)

        print(f'Project configuration saved at: {config_dir}/projects.json! You can change them later by editing the file or deleting it to go through the setup again.')

    
    return (project_directory, Project(**normalize_settings_keys(projects_configurations[project_directory])))