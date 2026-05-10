from getpass import getpass, getuser
from json import dump
from pathlib import Path
from shutil import rmtree
from typing import Any

from packer.setup import main as setup
from packer.paths import config_dir, assets_dir
from packer.custom_modules.et import capitalize, merge_settings, prompt_user, read_json, stripped_input, create_go_file_folder

def user_input(text: str, index: int = 3) -> str:
    '''
    strips user input and capitalizes input.

    :param text: The text to be displayed and the user will input.
    :type text: str
    :return: The user's response.
    :rtype: str
    '''
    return stripped_input(capitalize(text, index))

def main() -> tuple[str, dict[str: Any]]:
    '''
    Main function for the TUI. This script handles user input and performs various tasks based on the input. It includes options to create a new Go file or folder, setup configurations, manage assets, and interact with custom modules. The function also provides interactive prompts for user inputs and processes these inputs accordingly.

    :return: project directory and the settings associated with that project.
    :rtype: tuple
    '''

    if Path(f'{config_dir}/settings.json').exists():
        user_settings = read_json(f'{config_dir}/settings.json')

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


        project_directory = user_input('1. project directory (absolute path, leave empty for current directory): ')
        if project_directory == '':
            project_directory = str(Path().cwd().absolute())

        project_directory.rstrip('/')
        
        if Path(project_directory).exists():
            create_project = prompt_user('Remove the existing project profile and start fresh', default='n')
        else:
            create_project = True

        if create_project:
            if Path(project_directory).exists():
                rmtree(project_directory)

            create_github_repository = prompt_user('Create a new github repository')
            if create_github_repository:
                github_pat = user_input('Github personal access token (with Administration permissions): ')
                github_repo_url = None
            else:
                github_pat = None
                github_repo_url = user_input('Github repo url (username/repo): ')
            
            program_name = input('Program name: ')

            github_repo_url = setup(project_directory, input('Author name of the program: '), program_name, github_pat, github_repo_url)
            print('Starting setup...')


        gofile_user_token = user_input('2. gofile user token: ')

        gofile_folder_id_input = user_input('3. gofile folder id (leave empty to create a folder): ')
        if gofile_folder_id_input == '':
            gofile_folder_id = create_go_file_folder(stripped_input('name of the folder: '), gofile_user_token)['data']['id']
        else:
            gofile_folder_id = gofile_folder_id_input

        compile_command_input = user_input('4. nuitka compile command (leave empty to skip): ')

        if compile_command_input == '':
            compile_command_input = None
        else:
            compile_command_input = compile_command_input.split(' ')

        new_project_settings = {
            project_directory: {
                'gofile user token': gofile_user_token,
                'gofile folder id': gofile_folder_id,
                'github repo url': user_input('5. github repo url (username/repo): ') if 'github_repo_url' not in locals() else github_repo_url,
                'compile command': compile_command_input,
                'program name': user_input('6. program name: ') if 'program_name' not in locals() else program_name
                }
            }
        
        for i in range(len(required_settings)):
            setting = required_settings[i]
            new_project_settings[project_directory][setting] = user_input(f'{i + MANUAL_INPUT_SETTINGS + 1}. {setting}: ')

        if prompt_user('Would you like to edit optional settings', default='n'):
            optional_settings = ['model']
            for i in range(len(optional_settings)):
                setting = optional_settings[i]
                user_answer = user_input(f'{i}. {setting}: ')
                if user_answer != '':
                    new_project_settings[project_directory][setting] = user_answer


        if 'user_settings' not in locals():
            user_settings = {}
        user_settings.update(new_project_settings)
        with open(f'{config_dir}/settings.json', 'w') as f:
            dump(user_settings, f, indent=4)

        print(f'Settings saved at: {config_dir}/settings.json! You can change them later by editing the file or deleting it to go through the setup again.')

        if create_project:
            exit()

    user_settings = user_settings[project_directory]

    return (project_directory, merge_settings(user_settings, read_json(assets_dir.joinpath('default settings.json'))))