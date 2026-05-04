'''
This module contains the code for the packer, which is a script that creates an archive of the program, uploads it to Gofile, updates the git directory, and publishes a new release on Github. If any error is encountered it reverts all changes back to the previous version.
'''

from datetime import datetime
from shutil import get_terminal_size, rmtree, make_archive, copy2, unpack_archive
from pathlib import Path
from os import remove, listdir, chdir
from json import dump
from subprocess import PIPE, STDOUT, CompletedProcess, Popen, run
from sys import platform, exit
from time import sleep
from typing import Optional, Sequence
from github import Github, Auth, UnknownObjectException
from ollama import chat
from platformdirs import user_config_dir, user_log_dir, user_data_dir, user_cache_dir
from requests import get, post
from git import Repo

from packer.custom_modules.et import copy_with_exceptions, hide_cursor, merge_settings, print_bg_colored_text, print_colored_text, read_json, show_cursor, tree, delete_upload, log_action as _log_action, create_log_message, prompt_user
from packer.paths import assets_dir
from packer.setup import main as setup

def create_go_file_folder(folder_name: str, GOFILE_USER_TOKEN: str) -> dict:
    '''Creates a folder in the root directory of the GoFile account and returns the response as a dictionary.
    
    :param folder_name: The name of the folder to be created.
    :type folder_name: str
    :param GOFILE_USER_TOKEN: The user token for the GoFile account.
    :type GOFILE_USER_TOKEN: str
    :return: The response from the GoFile API as a dictionary.
    :rtype: dict
    '''

    payload = {'token': GOFILE_USER_TOKEN}

    response = get('https://api.gofile.io/accounts/getid', params=payload)
    account_id = response.json()['data']['id']
    response = get(f'https://api.gofile.io/accounts/{account_id}', params=payload)

    payload = {
        'token': GOFILE_USER_TOKEN,
        'folderName': folder_name,
        'parentFolderId': response.json()['data']['rootFolder']
    }

    response = post('https://api.gofile.io/contents/createFolder', data=payload)

    return response.json()

def upload_gofile_file(file_path: Path, token: str, folder_id: str) -> dict:
    '''Uploads a file to a specified folder in the GoFile account and returns the response as a dictionary.
    
    :param file_path: The path to the file to be uploaded.
    :type file_path: Path
    :param token: The user token for the GoFile account.
    :type token: str
    :param folder_id: The ID of the folder where the file will be uploaded.
    :type folder_id: str
    :return: The response from the GoFile API as a dictionary.
    :rtype: dict
    '''

    files = {
        'file': (file_path.name, open(file_path, 'rb'))
    }

    data = {
        'token': token,
        'folderId': folder_id
    }

    response = post('https://upload.gofile.io/uploadfile', files=files, data=data)

    return response.json()

class Packer():
    '''
    The Packer class is responsible for creating an archive of the program, uploading it to Gofile, updating the git directory, and publishing a new release on Github. If any error is encountered it reverts all changes back to the previous version.
    
    :param version: The new version of the program.
    :type version: dict
    :param old_version: The previous version of the program.
    :type old_version: dict
    :param GOFILE_USER_TOKEN: The user token for Gofile, used to upload the
    archive.
    :type GOFILE_USER_TOKEN: str
    :param FOLDER_ID: The folder id for Gofile, used to upload the archive
    :type FOLDER_ID: str
    :param GITHUB_REPO_TOKEN: The token for the Github repo, used to publish the release.
    :type GITHUB_REPO_TOKEN: str
    :param program_name: The name of the program, used for naming the archive and the release.
    :type program_name: str
    :param github_repo_url: The url of the Github repo, used to publish the release and for the social media post. It should be in the format "username/repo".
    :type github_repo_url: str
    :param compile_command: The command to compile the program using Nuitka, used to compile the program and upload the compiled version to the Github release.
    :type compile_command: Sequence[str], optional
    :param model: The language model to use for generating the version description and title, defaults to 'mistral'.
    :type model: str, optional
    '''

    def __init__(self, version: dict, old_version: dict,
                 GOFILE_USER_TOKEN: str, FOLDER_ID: str, GITHUB_REPO_TOKEN: str,
                 program_name: str, github_repo_url: str, compile_command: Sequence[str] = None,
                 model: str = 'mistral'):
        self.version = version
        self.old_version = old_version
        self.GOFILE_USER_TOKEN = GOFILE_USER_TOKEN
        self.FOLDER_ID = FOLDER_ID
        self.GITHUB_REPO_TOKEN = GITHUB_REPO_TOKEN
        self.model = model
        self.program_name = program_name
        self.github_repo_url = github_repo_url
        self.compile_command = compile_command

        self.terminal_width = get_terminal_size().columns
        self.last_log_time = datetime.now() # init the logger
        self.log_path = Path(f'{user_log_dir('packer', 'EMILIO', ensure_exists=True)}/{datetime.date(datetime.now())}.log')
        self.data_dir = user_data_dir('packer', 'EMILIO', ensure_exists=True)
        self.cache_dir = user_cache_dir('packer', 'EMILIO', ensure_exists=True)
        self.chosen_description_path = Path(f'{self.data_dir}/chosen description.txt')
        self.chosen_title_path = Path(f'{self.data_dir}/chosen version title.txt')

    def run(self):
        '''Runs the packer, which creates an archive of the program, uploads it to Gofile, updates the git directory, and publishes a new release on Github. If any error is encountered it reverts all changes back to the previous version.'''

        with open(self.log_path, 'w') as f:
            f.write('')
        self.print_and_log('Starting packer...')

        self.print_and_log('Creating requirements.txt...')
        pip_path = Path('.venv/bin/pip') if platform != 'win32' else Path('.venv/Scripts/pip.exe')
        with open('requirements.txt', 'w') as f:
            run([pip_path, 'freeze', '--require-virtualenv', '-l'], stdout=f)


        self.print_and_log('Updating version...')
        with open(f'{assets_dir}/version.json', 'w') as f:
            dump(self.version, f, indent=4)
        self.version = f'{self.version['major']}.{self.version['minor']}.{self.version['patch']}' # Not using a text variable to rewrite this one 
        old_version_text = f'{old_version['major']}.{old_version['minor']}.{old_version['patch']}' # Not possible above solution due to needing both
        self.print_and_log(f'Chosen version: {self.version}')


        self.print_and_log('Getting latest changelog...')
        with open('CHANGELOG.md') as f:
            full_changelog = f.read()
            latest_changelog = full_changelog[full_changelog.find(f'## [%new_version]') + 27:full_changelog.find(f'## [{old_version_text}]') - 7]

        self.print_and_log('Updating changelog with the new version...')
        self.old_changelog = full_changelog[:]
        full_changelog = full_changelog.replace('%new_version', self.version).replace('%date', str(datetime.date(datetime.now())), 1)
        with open('CHANGELOG.md', 'w') as f:
            f.write(full_changelog)


        self.print_and_log('Generating a version description...')

        generate_description = True
        if self.chosen_description_path.exists() and prompt_user('Use the previously generated version description'):
            generate_description = False
            with open(self.chosen_description_path) as f:
                description = f.read()

        while generate_description:
            description_prompt = [
                {'role': 'system', 'content': 'You are a technical writer. Output ONLY the raw markdown paragraph. No intros, no explanations.'},
                {'role': 'user', 'content': f'Summarize this changelog into exactly one markdown paragraph. Do not use lists. Use only the provided info.\n\nChangelog:\n{latest_changelog}'}
            ]
            description = chat(model=self.model, messages=description_prompt, options={'temperature': 0.2})['message']['content'].strip().replace('\n', ' ')
            self.print_and_log(description)
            generate_description = not prompt_user('Is the description all good', default='n')
        
        with open(self.chosen_description_path, 'w') as f:
            f.write(description)

        self.print_and_log('Generating a version title...')

        generate_title = True
        if self.chosen_title_path.exists() and prompt_user('Use the previously generated version title'):
            generate_title = False
            with open(self.chosen_title_path) as f:
                version_title = f.read()

        while generate_title:
            title_prompt = [
                {'role': 'system', 'content': 'You are a cryptic oracle. Your answer must be exactly 2 or 3 words. No quotes, no punctuation, no preamble.'},
                {'role': 'user', 'content': f'Create a mystical, indirect puzzle title for this update. Do not include version numbers.\n\nChangelog:\n{latest_changelog}'}
            ]
            version_title = chat(model=self.model, messages=title_prompt, options={'temperature': 0.8, 'num_predict': 10})['message']['content'].strip().replace('"', '').replace("'", "")
            self.print_and_log(version_title)
            generate_title = not prompt_user('Is the Version title all good', default='n')
    
        with open(self.chosen_title_path, 'w') as f:
            f.write(version_title)


        if Path(f'{self.cache_dir}/{self.program_name} {old_version_text}.zip').exists():
            self.print_and_log('Removing old archive...')
            remove(f'{self.cache_dir}/{self.program_name} {old_version_text}.zip')


        self.old_integrity = read_json(f'{assets_dir}/integrity.json')

        self.print_and_log('Generating the integrity file...')
        new_cwd = tree(f'{self.cache_dir}/{self.program_name} {self.version}.zip')
        with open(f'{assets_dir}/integrity.json', 'w') as f:
            dump({'CWD': new_cwd}, f)


        self.print_and_log('Creating an archive of the current git repository...')
        self.git_repo = Repo()
        with open(f'{self.cache_dir}/{self.program_name} {self.version}.zip', 'wb') as fp:
            self.git_repo.archive(fp, format='zip')


        self.print_and_log(f'Added file: {set(new_cwd).difference(self.old_integrity['CWD'])}')
        self.print_and_log(f'Archive saved at: {self.cache_dir}/{self.program_name} {self.version}.zip')
        if prompt_user('Is the arhive all good'):

            self.print_and_log('Uploading archive to Gofile...')
            response = upload_gofile_file(Path(f'{self.cache_dir}/{self.program_name} {self.version}.zip'), self.GOFILE_USER_TOKEN, self.FOLDER_ID)

            download_url = response['data']['downloadPage']
            self.file_id = response['data']['id']


            self.print_and_log('Staging changes...')
            self._run(['git', 'add', '.'])

            self.print_and_log('Committing changes...')
            self.committed = True if self._run(['git', 'commit', '-m', f'Auto generated commit message!\nVersion: {self.version}\nGofile url: {download_url}\nDescription: {description}\nLatest changelog:\n{latest_changelog}\nThis commit was generated by packer.py. Commit contains the new version of the program, which was uploaded to Gofile and is ready to be published as a new release on Github!']).returncode == 0 else False

            sha = run(['git', 'rev-parse', 'HEAD'], cwd=self.git_directory, capture_output=True).stdout.decode().strip()

            self.print_and_log('Pushing changes...')
            self._run(['git', 'push'])

            self.print_and_log('Generating social media post text...')
            social_media_post_text = f'# {self.program_name} Update [{self.version}]\n\n{description}\n\n## Installation\n\nAvailable via:\n\n- **GitHub**: [GitHub Repo](https://github.com/{self.github_repo_url})\n- **Third-party website (GoFile) as an archive**: [Archive]({download_url}) and click the download button.\n\n### To install:\n\n- **GitHub:**\n\tClone the repo using:\n\n\t```bash\n\tgit clone https://github.com/{self.github_repo_url}\n\t```\n\n- **Third-party website (GoFile):**\n\tSimply head to the website [Archive]({download_url}) and click the download button.\n\nAfter installing, continue following instructions via the README.\n\n## Changes in v{self.version}\n\n{latest_changelog}\n\n[Full changelog](https://github.com/{self.github_repo_url}/blob/master/CHANGELOG.md)\n\n## Tips\n\nThe difference between the two is that GitHub contains all versions (newest and older ones), which increases file size. The archive contains only the newest version. A nice upside to installing from GitHub is that you can easily update the program or, in the future, automatically update the software by simply pulling from the repo, since the GitHub URL doesn\'t change.'

            # Publish a github release

            self.print_and_log('Publishing a new release on Github...')
            self.repo = Github(auth=Auth.Token(self.GITHUB_REPO_TOKEN)).get_repo(self.github_repo_url)

            # Keeps polling the repo, until we good.
            while True:
                try:
                    self.repo.get_commit(sha)
                    break
                except UnknownObjectException:
                    print('Waiting...')
                    sleep(1)
            
            self.git_release = self.repo.create_git_release(tag=self.version, name=f'v{self.version} - {version_title}', message=social_media_post_text)


            if self.compile_command != None:
                self.print_and_log('Compiling the program using Nuitka...')
                self._Popen(self.compile_command)

                self.print_and_log('Creating archive of the compiled program...')
                make_archive(f'{self.cache_dir}/{self.program_name} [nuitka]', 'zip', f'{self.cache_dir}/main.dist')

            
            pyinstaller_path = Path('.venv/bin/pyinstaller') if platform != 'win32' else Path('.venv/Scripts/pyinstaller.exe')
            self.print_and_log('Bundling the program using PyInstaller...')
            self._Popen([pyinstaller_path, f'{Path().cwd().absolute()}/main.spec'])


            self.print_and_log('Uploading the compiled programs to the github release...')
            self.git_release.upload_asset(path=f'{self.cache_dir}/dist/{self.program_name}', content_type='application/octet-stream')

            if self.compile_command != None:
                self.git_release.upload_asset(path=f'{self.cache_dir}{self.program_name} [nuitka].zip', content_type='application/zip')


            self.print_and_log('Cleaning up cache...')
            rmtree(f'{self.cache_dir}/dist')

            if self.compile_command != None:
                rmtree(f'{self.cache_dir}/main.dist')
                remove(f'{self.cache_dir}{self.program_name} [nuitka].zip')

            self.print_and_log('Cleaning up temporary files...')
            remove(f'{self.data_dir}/chosen description.txt')
            remove(f'{self.data_dir}/chosen version title.txt')

            self.print_and_log('Adding changelog template for next version...')

            with open('CHANGELOG.md', 'w') as f:
                f.write(f'## [%new_version] - %date\n\n### Added\n- \n\n### Changed\n- \n\n### Fixed\n- \n\n---\n\n{full_changelog}')

            self.print_and_log('Writing social media post text to a file...')
            
            with open(f'{self.data_dir}/social media post.md', 'w') as f:
                f.write(social_media_post_text)

            self.print_and_log(f'New version released: {self.version} Hooray! \U0001F386')
            self.print_and_log(f'Social media post text has been saved to {self.data_dir}/social media post.md. You can use it to announce the new version on social media platforms!\nLog file has been saved to: {str(self.log_path.absolute())}')

            if prompt_user('Do you want to revert', default='n'):
                self.revert_changes()
            
        else:
            self.print_and_log('Canceled going further!\nReverting back to previous version!')
            self.revert_changes()
    
    def revert_changes(self) -> None:
        '''Reverts the version to the previous one, deletes the uploaded copy and git release if they exist, and resets the git directory to the previous commit. Also restores the integrity file.'''

        self.print_and_log('Changing version...')
        with open(f'{assets_dir}/version.json', 'w') as f:
            dump(old_version, f)
        
        if hasattr(self, 'old_changelog'):
            self.print_and_log('Restoring changelog...')
            with open('CHANGELOG.md', 'w') as f:
                f.write(self.old_changelog)

        if hasattr(self, 'old_integrity'):
            self.print_and_log('Restoring integrity file...')
            with open(f'{assets_dir}/integrity.json', 'w') as f:
                dump(self.old_integrity, f)

        if Path(f'{self.cache_dir}/archive').exists():
            self.print_and_log('Removing temporary directory...')
            rmtree(f'{self.cache_dir}/archive')

        if Path(f'{self.cache_dir}/{self.program_name} {self.version}.zip').exists():
            self.print_and_log('Removing archive...')
            remove(f'{self.cache_dir}/{self.program_name} {self.version}.zip')

        if hasattr(self, 'file_id'):
            self.print_and_log('Deleting uploaded copy...')
            delete_upload(self.file_id, self.GOFILE_USER_TOKEN)

        self.print_and_log('Reverting git changes...')
        if hasattr(self, 'committed') and self.committed:
            self._run(['git', 'reset', '--hard', 'HEAD~1'])
            self._run(['git', 'clean', '-fd'])
            self._run(['git', 'push', '--force']) # In case we pushed it to github already!
        else:
            self._run(['git', 'reset', '--hard', 'HEAD'])
            self._run(['git', 'clean', '-fd'])

        if hasattr(self, 'git_release'):
            self.print_and_log('Deleting git release...')
            self.git_release.delete_release()
            self.repo.get_git_ref(f"tags/{self.version}").delete()

    def print_and_log(self, text, color: Optional[Sequence[int]] = [255, 255, 255]):
            '''Prints the text and logs it to the packer log file.'''

            print_colored_text(text, color)
            self.log_action(text, 'PACKER')

    def log_action(self, action: str, type: str):
            '''Logs the action to the packer log file with a timestamp and type.'''

            _log_action(create_log_message(action, type, last_log_time=self.last_log_time), self.log_path)
            self.last_log_time = datetime.now()

    def _run(self, args: list[str]) -> CompletedProcess:
        '''
        Runs a subprocess command in the git directory and without stdout.
        
        :param args: The command and its arguments.
        :type args: list[str]
        :return: The result of the subprocess command.
        :rtype: CompletedProcess
        '''

        result = run(args, check=True, capture_output=True)
        self.log_action(f'Ran command: {" ".join(args)}\nstdout: {result.stdout.decode("utf-8")}\nstderr: {result.stderr.decode("utf-8")}', 'SUBPROCESS')
        return result

    def _Popen(self, cmd: list[str]) -> None:
        '''
        Runs a subprocess command in the git directory and prints the stdout in real time. Also logs the stdout to the packer log file.
        
        :param cmd: The command and its arguments.
        :type cmd: list[str]
        '''

        process = Popen(cmd, stdout=PIPE, stderr=STDOUT, text=True, cwd=self.cache_dir)

        hide_cursor()
        for text in process.stdout:
            text = text.rstrip('\n')
            self.log_action(text, 'SUBPROCESS')
            print_bg_colored_text(text, 255, 192, 203, self.terminal_width)
        show_cursor()

        process.wait()

def stripped_input(prompt: object) -> str:
    '''
    Gets input from the user and strips it of leading and trailing whitespaces.
    
    :param prompt: The prompt to show to the user.
    :type prompt: object
    :return: The stripped input from the user.
    :rtype: str
    '''

    return input(prompt).strip()

def capitalize(text: str, index: int = 3) -> str:
    return f'{text[:index]}{text[index:].capitalize()}'

def user_input(text: str) -> str:
    return stripped_input(capitalize(text))

if __name__ == '__main__':
    config_dir = user_config_dir('packer', 'EMILIO', ensure_exists=True)

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

            github_repo_url = setup(project_directory, input('Author name of the program: '), program_name, github_pat, github_repo_url,'.')
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

    all_settings = merge_settings(user_settings, read_json(assets_dir.joinpath('default settings.json')))

    if Path().cwd() != Path(project_directory):
        print('Changing working directory...')
        chdir(project_directory)

    if run(['git', 'status', '--porcelain'], capture_output=True).stdout.decode() != '':
        print('Your git directory is not clean! Please commit or stash your changes before running the packer. Exiting...')
        exit()

    version = read_json(f'{assets_dir}/version.json')
    old_version = version.copy()
    input_version = stripped_input('New version(M, m, P): ')
    match input_version:
        case 'M':
            version['major'] = version['major'] + 1
            version['minor'] = 0
            version['patch'] = 0
        case 'm':
            version['minor'] = version['minor'] + 1
            version['patch'] = 0
        case 'P':
            version['patch'] = version['patch'] + 1
        case _:
            print('Unknown version! exiting...', [255, 0, 0])
            exit()
    try:
        packer = Packer(version, old_version,
                        all_settings['gofile user token'], all_settings['gofile folder id'], all_settings['github repo token'],
                        all_settings['program name'], all_settings['github repo url'], all_settings['compile command'], all_settings['model'])
        packer.run()
    except KeyboardInterrupt:
        packer.print_and_log('\nProcess interrupted by user!\nReverting back to previous version!', [255, 255, 0])
        packer.revert_changes()
    except Exception as e:
        packer.print_and_log(f'\nEncountered an error: {e}\nReverting back to previous version!', [255, 0, 0])
        packer.revert_changes()