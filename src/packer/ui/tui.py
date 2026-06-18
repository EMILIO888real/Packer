from getpass import getpass
from json import dumps, loads
from pathlib import Path
from typing import Callable
from subprocess import run

from packer.setup import main as setup, tui
from packer.paths import config_dir, projects_file_path
from packer.custom_modules.et import create_go_file_folder, normalize_settings_keys
from packer.custom_modules.etf import stripped_input, simple_prompt
from packer.config import Project, projects_configurations, all_settings

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

        user_setup_data = tui()
        project_directory = user_setup_data[0]
        program_name = user_setup_data[2]
        print('Starting setup...')
        github_repo_url = setup(*user_setup_data)
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


        if simple_prompt(f'Would you like to edit optional settings', 'n'):
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

            print(f'To customize description or title prompt, or any other settings edit the {config_dir}/projects.json file directly. And follow settings structure, check . \
                  You can check out the defaults for examples via Project class documentation.')
            
            if simple_prompt('Open projects.json', 'n'):
                run([all_settings.text_editor, '--wait', f'{config_dir}/projects.json'])
        

    if not projects_file_path.exists():
        projects_file_path.write_text(dumps(projects_configurations, indent=4))
    else:
        existing_projects_configurations = loads(projects_file_path.read_text())
        existing_projects_configurations.update(projects_configurations)
        projects_file_path.write_text(dumps(existing_projects_configurations, indent=4))

        print(f'Project configuration saved at: {config_dir}/projects.json! You can change them later by editing the file or deleting it to go through the setup again.')

    
    return (project_directory, Project(**normalize_settings_keys(projects_configurations[project_directory])))