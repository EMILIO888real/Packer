'''
This module contains the code for the packer, which is a script that creates an archive of the program, uploads it to Gofile, updates the git directory, and publishes a new release on Github. If any error is encountered it reverts all changes back to the previous version.
'''

from datetime import datetime
from shutil import get_terminal_size, rmtree, make_archive
from pathlib import Path
from os import remove, chdir
from json import dump
from subprocess import PIPE, STDOUT, CompletedProcess, Popen, run
from sys import executable, platform, exit
from time import sleep
from typing import Optional, Sequence
from github import Github, Auth, UnknownObjectException
from ollama import chat
from platformdirs import user_log_dir, user_data_dir, user_cache_dir
from requests import post
from git import GitCommandError, Repo
import tomlkit
from threading import Thread, Event

from packer.custom_modules.et import hide_cursor, print_bg_colored_text, print_colored_text, read_json, show_cursor, stripped_input, tree, delete_upload, simple_prompt, init_logger
from packer.paths import assets_dir
from packer.ui.tui import main as tui
from packer.config import Settings

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
    :param GOFILE_USER_TOKEN: The user token for Gofile, used to upload the archive.
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
                 before_commands: Sequence[Sequence][str] = None, after_commands: Sequence[Sequence][str] = None,
                 settings: Settings | None = Settings(gofile_user_token='None', gofile_folder_id='None', github_repo_token='None', program_name='None', github_repo_url='None')):
        self.version = version
        self.old_version = old_version
        self.GOFILE_USER_TOKEN = GOFILE_USER_TOKEN
        self.FOLDER_ID = FOLDER_ID
        self.GITHUB_REPO_TOKEN = GITHUB_REPO_TOKEN
        self.model = settings.model
        self.program_name = program_name
        self.github_repo_url = github_repo_url
        self.compile_command = compile_command
        self.before_commands = before_commands
        self.after_commands = after_commands

        self.terminal_width = get_terminal_size().columns
        self.logger = init_logger('packer', 'EMILIO')
        self.log_path = Path(f'{user_log_dir('packer', 'EMILIO', ensure_exists=True)}/{datetime.date(datetime.now())}.log')
        self.data_dir = user_data_dir('packer', 'EMILIO', ensure_exists=True)
        self.cache_dir = user_cache_dir('packer', 'EMILIO', ensure_exists=True)
        self.chosen_description_path = Path(f'{self.data_dir}/chosen description.txt')
        self.chosen_title_path = Path(f'{self.data_dir}/chosen version title.txt')

        self.print_and_log = self.print_and_log if settings.verbose else self.log

    def run(self):
        '''Runs the packer, which creates an archive of the program, uploads it to Gofile, updates the git directory, and publishes a new release on Github. If any error is encountered it reverts all changes back to the previous version.'''

        with open(self.log_path, 'w') as f:
            f.write('')
        self.print_and_log('Starting packer...')


        self.print_and_log('Updating version...')
        with open(f'{assets_dir}/version.json', 'w') as f:
            dump(self.version, f, indent=4)
        self.version = f'{self.version['major']}.{self.version['minor']}.{self.version['patch']}' # Not using a text variable to rewrite this one 

        old_version_text = f'{self.old_version['major']}.{self.old_version['minor']}.{self.old_version['patch']}' # Not possible above solution due to needing both
        self.print_and_log(f'Chosen version: {self.version}')


        self.print_and_log('Getting latest changelog...')
        with open('CHANGELOG.md') as f:
            full_changelog = f.read()
            latest_changelog = full_changelog[full_changelog.find(f'## [%new_version]') + 27:full_changelog.find(f'## [{old_version_text}]') - 7]

        self.print_and_log('Updating changelog with the new version...')
        full_changelog = full_changelog.replace('%new_version', self.version).replace('%date', str(datetime.date(datetime.now())), 1)
        with open('CHANGELOG.md', 'w') as f:
            f.write(full_changelog)


        self.print_and_log('Generating a version description...')

        generate_description = True
        if self.chosen_description_path.exists() and simple_prompt('Use the previously generated version description'):
            generate_description = False
            with open(self.chosen_description_path) as f:
                description = f.read()

        while generate_description:
            description = chat(self.model,
                               [
                                    {'role': 'system', 'content': 'You are a senior developer writing professional release notes. Summarize the following changelog into one short sentence. Focus strictly on the high-level impact (e.g., \'This release introduces a new TUI and streamlines Windows builds.\') rather than listing individual functions or fixes. Use professional, active language. Output ONLY the summary text, no markdown block syntax, no intros, and no explanations.'},
                                    {'role': 'user', 'content': f'Summarize the following changelog into exactly one concise sentence. Group related technical changes (e.g., UI, Build Automation, Refactoring). Do not use bullet points. Do not mention specific function names unless they are major features. Ensure the tone is professional.\n\nChangelog:\n{latest_changelog}'}
                                ])['message']['content'].strip()
            self.print_and_log(description)
            generate_description = not simple_prompt('Is the description all good', 'n')
        
        with open(self.chosen_description_path, 'w') as f:
            f.write(description)

        self.print_and_log('Generating a version title...')

        generate_title = True
        if self.chosen_title_path.exists() and simple_prompt('Use the previously generated version title'):
            generate_title = False
            with open(self.chosen_title_path) as f:
                version_title = f.read()

        while generate_title:
            version_title = chat(self.model,
                                 [
                                     {'role': 'system', 'content': 'You are a cryptic oracle. Your answer must be exactly 2 or 3 words. No quotes, no punctuation, no preamble.'},
                                     {'role': 'user', 'content': f'Create a mystical, indirect puzzle title for this update. Do not include version numbers.\n\nChangelog:\n{latest_changelog}'}
                                 ],
                                 options={'temperature': 0.8, 'num_predict': 10})['message']['content'].strip().replace('"', '').replace("'", "")
            self.print_and_log(version_title)
            generate_title = not simple_prompt('Is the Version title all good', 'n')
    
        with open(self.chosen_title_path, 'w') as f:
            f.write(version_title)


        self.print_and_log('Creating requirements.txt...')
        pip_path = Path('.venv/bin/pip') if platform != 'win32' else Path('.venv/Scripts/pip.exe')
        with open('requirements.txt', 'w') as f:
            run([pip_path, 'freeze', '--require-virtualenv', '-l'], stdout=f)


        self.print_and_log('Updating pyproject.toml...')
        with open('pyproject.toml', 'r', encoding='utf-8') as f:
            config = tomlkit.load(f)

        # (Note: In a pyproject.toml, 'version' is usually inside the [tool.poetry] or [project] table)
        if 'project' in config:
            config['project']['version'] = self.version
        elif 'tool' in config and 'poetry' in config['tool']:
            config['tool']['poetry']['version'] = self.version
        else:
            config['version'] = self.version # Fallback if it's just a top-level global key

        with open('pyproject.toml', 'w', encoding='utf-8') as f:
            tomlkit.dump(config, f)


        if Path(f'{self.cache_dir}/{self.program_name} {old_version_text}.zip').exists():
            self.print_and_log('Removing old archive...')
            remove(f'{self.cache_dir}/{self.program_name} {old_version_text}.zip')


        old_integrity = read_json(f'{assets_dir}/integrity.json')

        self.print_and_log('Generating the integrity file...')

        self.print_and_log('Getting exclusions from .gitignore...')
        with open('.gitignore') as f:
            exclusions = [entry for entry in f.read().splitlines() if '#' not in entry and entry != '']
        exclusions.append('.git')

        new_cwd = tree(Path().cwd(), exclusions)
        with open(f'{assets_dir}/integrity.json', 'w') as f:
            dump({'CWD': new_cwd}, f)


        self.print_and_log('Creating an archive of the current git repository...')
        self.git_repo = Repo()
        with open(f'{self.cache_dir}/{self.program_name} {self.version}.zip', 'wb') as fp:
            self.git_repo.archive(fp, format='zip')


        self.print_and_log(f'Added file: {set(new_cwd).difference(old_integrity['CWD'])}')
        self.print_and_log(f'Archive saved at: {self.cache_dir}/{self.program_name} {self.version}.zip')
        if simple_prompt('Is the arhive all good (no going back after this)'):

            if self.compile_command != None:
                self.print_and_log('Compiling the program using Nuitka...')
                waiting_for_compile_command = Event()
                compile_command_done = self._Popen(self.compile_command, waiting_for_compile_command)

                self.print_and_log('Creating archive of the compiled program...')
                make_archive(f'{self.cache_dir}/{self.program_name} [nuitka]', 'zip', f'{self.cache_dir}/main.dist')

            
            self.print_and_log('Bundling the program using PyInstaller...')
            waiting_for_pyinstaller_bundling = Event()
            pyinstaller_done = self._Popen([executable,
                        '-m',
                        'PyInstaller', 'main.spec',
                         '--distpath', f'{self.cache_dir}/dist',
                         '--workpath', f'{self.cache_dir}/build'], waiting_for_pyinstaller_bundling)

            self.print_and_log('Uploading archive to Gofile...')
            response = upload_gofile_file(Path(f'{self.cache_dir}/{self.program_name} {self.version}.zip'), self.GOFILE_USER_TOKEN, self.FOLDER_ID)

            download_url = response['data']['downloadPage']
            self.file_id = response['data']['id']

            if self.before_commands:
                self.print_and_log('Running before commit commands...')
                for cmd in self.before_commands:
                    self._run('sh', '-c', cmd)


            self.print_and_log('Staging changes...')
            self.log_action(f'Entries added: {self.git_repo.index.add(['pyproject.toml', 'requirements.txt', 'CHANGELOG.md',
                                                                       f'src/{self.program_name}/assets/version.json',
                                                                       f'src/{self.program_name}/assets/integrity.json'])}')


            self.print_and_log('Committing changes...')

            commit_subject = f'chore(release): version {self.version}'
            commit_body = f'{description}'
            commit_metadata = f'Gofile url: {download_url}\nPublished by packer v{self.version}!'

            commit_message = f'{commit_subject}\n\n{commit_body}\n\n{commit_metadata}'

            try:
                self.git_repo.index.commit(commit_message)
                self.committed = True 
            except GitCommandError as e:
                self.committed = False
                self.print_and_log(f'Something went wrong while committing: {e}', [255, 0, 0])


            sha = self.git_repo.head.commit.hexsha

            self.print_and_log('Pushing changes...')
            self.git_repo.remotes.origin.push()

            if self.after_commands:
                self.print_and_log('Running after commit commands...')
                for cmd in self.after_commands:
                    self._run('sh', '-c', cmd)

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

            self.print_and_log('Uploading the compiled programs to the github release...')

            self.print_and_log('Waiting for pyinstaller to finish...')
            waiting_for_pyinstaller_bundling.set()
            pyinstaller_done.wait()

            self.git_release.upload_asset(path=f'{self.cache_dir}/dist/{self.program_name}', content_type='application/octet-stream')

            if self.compile_command != None:
                self.print_and_log('Waiting for Nuitka to finish...')
                waiting_for_compile_command.set()
                compile_command_done.wait()
                self.git_release.upload_asset(path=f'{self.cache_dir}{self.program_name} [nuitka].zip', content_type='application/zip')


            self.print_and_log('Cleaning up cache...')
            rmtree(f'{self.cache_dir}/dist')

            if self.compile_command != None:
                rmtree(f'{self.cache_dir}/main.dist')
                remove(f'{self.cache_dir}{self.program_name} [nuitka].zip')

            self.print_and_log('Cleaning up temporary files...')
            remove(f'{self.data_dir}/chosen description.txt')
            remove(f'{self.data_dir}/chosen version title.txt')

            self.print_and_log('Writing social media post text to a file...')
            with open(f'{self.data_dir}/social media post.md', 'w') as f:
                f.write(social_media_post_text)

            if self.git_repo.active_branch.name == 'development':
                self.print_and_log('Switching to master branch...')
                self.git_repo.heads['master'].checkout()

                self.print_and_log('Merging development branch...')
                self.git_repo.git.merge('development', '-X', 'theirs')

                self.print_and_log('Deleting the old merged branch...')
                self.git_repo.git.branch('-D', 'development')

            if 'development' not in self.git_repo.heads:
                self.print_and_log('Creating a new branch and switching to it...')
                self.git_repo.create_head('development').checkout()

                self.print_and_log('Updating origin...')
                self.git_repo.remotes.origin.push()
            else:
                self.print_and_log('Switching to existing development branch...')
                self.git_repo.heads['development'].checkout()


            self.print_and_log('Adding changelog template for next version...')
            with open('CHANGELOG.md', 'w') as f:
                f.write(f'## [%new_version] - %date\n\n### Added\n- \n\n### Changed\n- \n\n### Fixed\n- \n\n---\n\n{full_changelog}')

            self.print_and_log('Committing next version preparation and updating origin...')
            added_items = self.git_repo.index.add(['CHANGELOG.md'])
            self.git_repo.index.commit(f'Prepared next version development branch by updating: {added_items}')
            self.git_repo.remotes.origin.push()

            self.print_and_log(f'New version released: {self.version} Hooray! \U0001F386')
            self.print_and_log(f'Social media post text has been saved to {self.data_dir}/social media post.md. You can use it to announce the new version on social media platforms!\nLog file has been saved to: {str(self.log_path.absolute())}')

            if simple_prompt('Do you want to revert', 'n'):
                self.revert_changes()
            
        else:
            self.print_and_log('Canceled going further!\nReverting back to previous version!')
            self.revert_changes()
    
    def revert_changes(self) -> None:
        '''Reverts the version to the previous one, deletes the uploaded copy and git release if they exist, and resets the git directory to the previous commit. Also restores the integrity file.'''

        if Path(f'{self.cache_dir}/{self.program_name} {self.version}.zip').exists():
            self.print_and_log('Removing archive...', [255, 255, 0])
            remove(f'{self.cache_dir}/{self.program_name} {self.version}.zip')

        if hasattr(self, 'file_id'):
            self.print_and_log('Deleting uploaded copy...', [255, 255, 0])
            delete_upload(self.file_id, self.GOFILE_USER_TOKEN)

        self.print_and_log('Reverting git changes...', [255, 255, 0])
        if hasattr(self, 'committed') and self.committed:
            self.git_repo.head.reset(commit='HEAD~1', working_tree=True)
            self.git_repo.git.clean('-fd')
            self.git_repo.remotes.origin.push(force=True) # In case we pushed it to github already!
        else:
            self.git_repo.head.reset(working_tree=True)
            self.git_repo.git.clean('-fd')

        if hasattr(self, 'git_release'):
            self.print_and_log('Deleting git release...', [255, 255, 0])
            self.git_release.delete_release()
            self.repo.get_git_ref(f"tags/{self.version}").delete()

    def print_and_log(self, text, color: Optional[Sequence[int]] = [255, 255, 255], level: int = 20):
            '''Prints the text and logs it to the packer log file.'''

            print_colored_text(text, color)
            self.log_action(text, level)

    def log(self, text, color: Optional[Sequence[int]] = [255, 255, 255], level: int = 20):
        self.log_action(text, level)

    def log_action(self, action: str, level: int = 20):
            '''Logs the action with the provided level
            
            :param action: The action to log.
            :type action: str
            :param level: Level of urgency 10-50 (DEBUG-CRITICAL)
            :type level: int
            '''

            self.logger.log(level, action)

    def _run(self, args: list[str]) -> CompletedProcess:
        '''
        Runs a subprocess command in the git directory and without stdout.
        
        :param args: The command and its arguments.
        :type args: list[str]
        :return: The result of the subprocess command.
        :rtype: CompletedProcess
        '''

        result = run(args, check=True, capture_output=True)
        self.log_action(f'Ran command: {" ".join(args)}\nstdout: {result.stdout.decode("utf-8")}\nstderr: {result.stderr.decode("utf-8")}')
        return result

    def _Popen(self, cmd: list[str], waiting: Event) -> Event:
        '''
        Runs a subprocess command in the git directory and prints the stdout in real time. Also logs the stdout to the packer log file.
        
        :param cmd: The command and its arguments.
        :type cmd: list[str]
        :param waiting: An event to signal when to start printing the output.
        :type waiting: Event
        :return: An event that is set when the subprocess is done.
        :rtype: Event
        '''

        done = Event()

        def thread_function(done: Event):
            process = Popen(cmd, stdout=PIPE, stderr=STDOUT, text=True)

            hide_cursor()
            for text in process.stdout:
                text = text.rstrip('\n')
                self.log_action(text)
                if waiting.is_set():
                    print_bg_colored_text(text, 255, 192, 203, self.terminal_width)
            show_cursor()

            process.wait()
            done.set()

        Thread(target=thread_function, args=[done], daemon=True).start()

        return done

def main():
    project_directory, all_settings = tui()

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
                        all_settings.gofile_user_token, all_settings.gofile_folder_id, all_settings.github_repo_token,
                        all_settings.program_name, all_settings.github_repo_url,
                        all_settings.compile_command, all_settings.after_commands, all_settings.after_commands,
                        all_settings)
        packer.run()
    except KeyboardInterrupt:
        packer.print_and_log('\nProcess interrupted by user!\nReverting back to previous version!', [255, 255, 0])
        packer.revert_changes()
    except Exception as e:
        packer.print_and_log(f'\nEncountered an error: {e}\nReverting back to previous version!', [255, 0, 0])
        packer.revert_changes()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        print_colored_text(f'Something went wrong externally, please report this.\nError: {e}', [255, 0, 0])
        exit()