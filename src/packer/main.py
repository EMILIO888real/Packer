'''
This module contains the code for the packer, which is a script that creates an archive of the program, uploads it to Gofile, updates the git directory, and publishes a new release on Github. If any error is encountered it reverts all changes back to the previous version.
'''

from argparse import ArgumentParser
from datetime import datetime
from multiprocessing import Queue
from re import MULTILINE, compile
from shutil import get_terminal_size, rmtree, make_archive
from pathlib import Path
from os import remove, chdir
from json import dump
from subprocess import PIPE, STDOUT, CompletedProcess, Popen, run
import sys
from time import sleep
from typing import Any, Optional
from collections.abc import Sequence
from github import Github, Auth, UnknownObjectException
from ollama import chat
from requests import post
from git import GitCommandError, Repo
import tomlkit
import threading
from string import Template

from packer.custom_modules.et import bool_answer, hide_cursor, print_bg_colored_text, print_colored_text, read_json, show_cursor, stripped_input, tree, delete_upload, simple_prompt, init_logger
from packer.ui.tui import main as tui
from packer.config import all_settings, Project, packer_version
from packer.paths import root_dir, assets_dir, config_dir, log_dir, log_path, error_report_path, data_dir, cache_dir
from packer.exceptions import global_exception_handler

def thread_excepthook(args):
    sys.excepthook(args.exc_type, args.exc_value, args.exc_traceback)

sys.excepthook = global_exception_handler # replace the default error handler with our own.
threading.excepthook = thread_excepthook # Also, so other threads access the same handler

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
                 GOFILE_USER_TOKEN: str, FOLDER_ID: str, GITHUB_REPO_TOKEN: str, program_name: str, github_repo_url: str,
                 input_queue: Queue = None, output_queue: Queue = None,
                 compile_command: Sequence[str] = Project.model_fields['compile_command'].default,
                 before_commands: tuple[tuple[str, ...], ...] = Project.model_fields['before_commands'].default, after_commands: tuple[tuple[str, ...], ...] = Project.model_fields['after_commands'].default,
                 model: str = Project.model_fields['model'].default, description_prompt: list[dict[str: str]] = Project.model_fields['description_prompt'].default, title_prompt: list[dict[str: str]] = Project.model_fields['title_prompt'].default,
                 release_notes_template_path: str = Project.model_fields['release_notes_template_path'].default, changelog_git_hash: bool = Project.model_fields['changelog_git_hash'].default
                ):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.version = version
        self.old_version = old_version
        self.GOFILE_USER_TOKEN = GOFILE_USER_TOKEN
        self.FOLDER_ID = FOLDER_ID
        self.GITHUB_REPO_TOKEN = GITHUB_REPO_TOKEN
        self.model = model
        self.program_name = program_name
        self.github_repo_url = github_repo_url
        self.compile_command = compile_command
        self.before_commands = before_commands
        self.after_commands = after_commands
        self.description_prompt = description_prompt
        self.title_prompt = title_prompt
        self.changelog_git_hash = changelog_git_hash

        self.terminal_width = get_terminal_size().columns
        self.logger = init_logger('packer', 'EMILIO')
        self.chosen_description_path = Path(f'{data_dir}/chosen description.txt')
        self.chosen_title_path = Path(f'{data_dir}/chosen version title.txt')
        self.git_repo = Repo()
        with open(release_notes_template_path) as f:
            self.release_text = f.read()

        self.assets_dir = f'./src/{program_name}/assets'
        self.ENTRY_RE = compile(
                r"^- (Added|Changed|Fixed):\s*(.+)$",
                MULTILINE
            )

        self.SINGLE_RE = compile(
            r"^(Added|Changed|Fixed):\s*(.+)$"
        )

        if input_queue:
            all_settings.verbose = False
        self.print_and_log = self._print_and_log if all_settings.verbose else self._log_and_output_queue
        self.prompt_user = self._queue_prompt if input_queue else self._terminal_prompt

    def run(self):
        '''Runs the packer, which creates an archive of the program, uploads it to Gofile, updates the git directory, and publishes a new release on Github. If any error is encountered it reverts all changes back to the previous version.'''

        self.print_and_log('Starting packer...')


        self.print_and_log('Updating version...')
        with open(f'{self.assets_dir}/version.json', 'w') as f:
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


        self.print_and_log('Getting the latest tag...')
        tags = sorted(self.git_repo.tags, key=lambda x: x.commit.committed_date, reverse=True)

        if tags and self.changelog_git_hash:
            latest_tag = tags[0]

            self.print_and_log('Fetching all commits from HEAD to latest tag...')
            new_versions_commits = list(self.git_repo.iter_commits(
                f"{latest_tag.commit.hexsha}..HEAD"
            ))

            self.print_and_log('Identifying changelog categories...')
            added_category = f'{full_changelog[full_changelog.find('### Added') + 10: full_changelog.find('### Changed') - 2]}'
            changed_category = f'{full_changelog[full_changelog.find('### Changed') + 12: full_changelog.find('### Fixed') - 2]}'
            fixed_category = f'{full_changelog[full_changelog.find('### Fixed') + 10: full_changelog.find('---') - 2]}'

            self.print_and_log('Parsing and updating changelog entries...')
            for commit in new_versions_commits:
                data_list = self._parse_commit(commit)

                for data in data_list:
                    match data['category']:
                        case 'Added':
                            commit_sha_location = added_category.find(data['text'])
                            added_category = f'{added_category[: commit_sha_location - 1]} [{data['hash']}] {added_category[commit_sha_location: ]}'
                        case 'Changed':
                            commit_sha_location = changed_category.find(data['text'])
                            changed_category = f'{changed_category[: commit_sha_location - 1]} [{data['hash']}] {changed_category[commit_sha_location: ]}'
                        case 'Fixed':
                            commit_sha_location = fixed_category.find(data['text'])
                            fixed_category = f'{fixed_category[: commit_sha_location - 1]} [{data['hash']}] {fixed_category[commit_sha_location: ]}'

            self.print_and_log('Constructing updated latest changelog...')
            latest_updated_changelog = (
                f'### Added\n{added_category.strip()}\n\n'
                f'### Changed\n{changed_category.strip()}\n\n'
                f'### Fixed\n{fixed_category.strip()}'
            )

            self.print_and_log('Stitching the entire changelog with latest...')
            new_full_changelog = f'{full_changelog[:full_changelog.find(f'{datetime.date(datetime.now())}') + len(f'{datetime.date(datetime.now())}') + 2]}{latest_updated_changelog}'
            full_changelog = f'{new_full_changelog}{full_changelog[full_changelog.find('---') - 2:]}'
        
        self.print_and_log('Writing out the updated changelog...')
        with open('CHANGELOG.md', 'w') as f:
            f.write(full_changelog)


        self.print_and_log('Generating a version description...')

        generate_description = True
        if self.chosen_description_path.exists() and self.prompt_user('Use the previously generated version description'):
            generate_description = False
            with open(self.chosen_description_path) as f:
                description = f.read()

        if self.description_prompt is not None:
            self.description_prompt[1 if self.description_prompt[1]['role'] == 'user' else 0]['content'] = self.description_prompt[1]['content'].replace('%latest_changelog', latest_changelog)
            while generate_description:
                description = chat(self.model, self.description_prompt)['message']['content'].strip()
                self.print_and_log(description)
                generate_description = not self.prompt_user('Is the description all good', 'n')
        else:
            description = 'Write your version description in this file. (press ctrl+a and then start writing your description. After you have written it, save it and close the editor)'
        
        with open(self.chosen_description_path, 'w') as f:
            f.write(description)
        self._run([all_settings.text_editor, '--wait', str(self.chosen_description_path)])
        with open(self.chosen_description_path) as f:
            description = f.read()


        self.print_and_log('Generating a version title...')

        generate_title = True
        if self.chosen_title_path.exists() and self.prompt_user('Use the previously generated version title'):
            generate_title = False
            with open(self.chosen_title_path) as f:
                version_title = f.read()

        if self.title_prompt is not None:
            self.title_prompt[1]['content'] = self.title_prompt[1 if self.title_prompt[1]['role'] == 'user' else 0]['content'].replace('%latest_changelog', latest_changelog)
            while generate_title:
                version_title = chat(self.model, self.title_prompt,
                                    options={'temperature': 0.8, 'num_predict': 10})['message']['content'].strip().replace('"', '').replace("'", "")
                self.print_and_log(version_title)
                generate_title = not self.prompt_user('Is the Version title all good', 'n')
        else:
            version_title = 'Write your version title in this file. (press ctrl+a and then start writing your title. After you have written it, save it and close the editor)'
    
        with open(self.chosen_title_path, 'w') as f:
            f.write(version_title)
        self._run([all_settings.text_editor, '--wait', str(self.chosen_title_path)])
        with open(self.chosen_title_path) as f:
            version_title = f.read()


        self.print_and_log('Creating requirements.txt...')
        pip_path = Path('.venv/bin/pip') if sys.platform != 'win32' else Path('.venv/Scripts/pip.exe')
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


        if Path(f'{cache_dir}/{self.program_name} {old_version_text}.zip').exists():
            self.print_and_log('Removing old archive...')
            remove(f'{cache_dir}/{self.program_name} {old_version_text}.zip')


        self.print_and_log('Getting exclusions from .gitignore...')
        with open('.gitignore') as f:
            exclusions = [entry for entry in f.read().splitlines() if '#' not in entry and entry != '']
        exclusions.append('.git')

        self.print_and_log('Generating the integrity file...')
        new_cwd = tree(Path().cwd(), exclusions)
        with open(f'{self.assets_dir}/integrity.json', 'w') as f:
            dump({'CWD': new_cwd}, f)


        self.print_and_log('Creating an archive of the current git repository...')
        with open(f'{cache_dir}/{self.program_name} {self.version}.zip', 'wb') as fp:
            self.git_repo.archive(fp, format='zip')


        if tags:
            latest_tag_commit = latest_tag.commit
            current_commit = self.git_repo.head.commit

            self.print_and_log(f'Comparing current HEAD ({current_commit.hexsha[:7]}) against latest tag: {latest_tag.name} ({latest_tag_commit.hexsha[:7]})')
            diffs = latest_tag_commit.diff(current_commit)

            for diff in diffs:
                if diff.new_file:
                    self.print_and_log(f'ADDED:    {diff.b_path}')
                elif diff.deleted_file:
                    self.print_and_log(f'REMOVED:  {diff.a_path}')
                else:
                    self.print_and_log(f'MODIFIED: {diff.a_path}')
        else:
            self.print_and_log('No git tags found. Skipping file changes to latest version...')


        self.print_and_log(f'Archive saved at: {cache_dir}/{self.program_name} {self.version}.zip')
        if self.prompt_user('Is the arhive all good (no going back after this)'):

            if self.compile_command != None:
                self.print_and_log('Compiling the program using Nuitka...')
                waiting_for_compile_command = threading.Event()
                compile_command_done = self._Popen(self.compile_command, waiting_for_compile_command)

                self.print_and_log('Creating archive of the compiled program...')
                make_archive(f'{cache_dir}/{self.program_name} [nuitka]', 'zip', f'{cache_dir}/main.dist')

            
            self.print_and_log('Bundling the program using PyInstaller...')
            waiting_for_pyinstaller_bundling = threading.Event()
            pyinstaller_done = self._Popen([sys.executable,
                        '-m',
                        'PyInstaller', 'main.spec',
                         '--distpath', f'{cache_dir}/dist',
                         '--workpath', f'{cache_dir}/build'], waiting_for_pyinstaller_bundling)

            self.print_and_log('Uploading archive to Gofile...')
            response = upload_gofile_file(Path(f'{cache_dir}/{self.program_name} {self.version}.zip'), self.GOFILE_USER_TOKEN, self.FOLDER_ID)

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
            commit_metadata = f'Gofile url: {download_url}\nPublished by packer v{packer_version}!'

            commit_message = f'{commit_subject}\n\n{commit_body}\n\n{commit_metadata}'

            try:
                self.git_repo.git.commit('-S', '-m', commit_message)
                self.committed = True
            except GitCommandError:
                try:
                    self.print_and_log('Fallback to unsigned commit...')
                    self.git_repo.git.commit('-m', commit_message)
                    self.committed = True
                except GitCommandError as e:
                    self.committed = False
                    self.print_and_log(f'Something went wrong while committing: {e}', [255, 0, 0])
                    self.revert_changes()


            sha = self.git_repo.head.commit.hexsha

            self.print_and_log('Pushing changes...')
            self.git_repo.remotes.origin.push()

            if self.after_commands:
                self.print_and_log('Running after commit commands...')
                for cmd in self.after_commands:
                    self._run('sh', '-c', cmd)

            self.print_and_log('Generating social media post text...')

            release_notes_template_data = {
                'program_name': self.program_name,
                'new_version': self.version,
                'version_description': description,
                'github_repo_url': self.github_repo_url,
                'gofile_download_url': download_url,
                'latest_changelog': latest_updated_changelog if 'latest_updated_changelog' in locals() else latest_changelog
            }

            self.release_text = Template(self.release_text).substitute(release_notes_template_data)

            # Publish a github release

            self.print_and_log('Authorizing on Github...')
            self.repo = Github(auth=Auth.Token(self.GITHUB_REPO_TOKEN)).get_repo(self.github_repo_url)

            # Keeps polling the repo, until we good.
            self.print_and_log('Waiting for Github to process the release...')
            while True:
                try:
                    self.repo.get_commit(sha)
                    break
                except UnknownObjectException:
                    self.print_and_log('Waiting...')
                    sleep(1)
            
            self.print_and_log('Publishing a new release on Github...')
            self.git_release = self.repo.create_git_release(tag=self.version, name=f'v{self.version} - {version_title}',
                                                            message=self.release_text, target_commitish=sha)
            
            self.print_and_log('Fetching the git tag...')
            self.git_repo.remotes.origin.fetch(tags=True)

            self.print_and_log('Uploading the compiled programs to the github release...')

            self.print_and_log('Waiting for pyinstaller to finish...')
            waiting_for_pyinstaller_bundling.set()
            pyinstaller_done.wait()

            self.git_release.upload_asset(path=f'{cache_dir}/dist/{self.program_name}', content_type='application/octet-stream')

            if self.compile_command != None:
                self.print_and_log('Waiting for Nuitka to finish...')
                waiting_for_compile_command.set()
                compile_command_done.wait()
                self.git_release.upload_asset(path=f'{cache_dir}{self.program_name} [nuitka].zip', content_type='application/zip')


            self.print_and_log('Cleaning up cache...')
            rmtree(f'{cache_dir}/dist')

            if self.compile_command != None:
                rmtree(f'{cache_dir}/main.dist')
                remove(f'{cache_dir}{self.program_name} [nuitka].zip')

            self.print_and_log('Cleaning up temporary files...')
            remove(f'{data_dir}/chosen description.txt')
            remove(f'{data_dir}/chosen version title.txt')

            self.print_and_log('Writing social media post text to a file...')
            with open(f'{data_dir}/social media post.md', 'w') as f:
                f.write(self.release_text)

            if self.git_repo.active_branch.name == 'development':
                self.print_and_log('Switching to master branch...')
                self.git_repo.heads['master'].checkout()

                self.print_and_log('Merging development branch...')
                self.git_repo.git.merge('development', '-X', 'theirs')

                self.print_and_log('Pushing master branch to origin...')
                self.git_repo.remotes.origin.push('master')

                self.print_and_log('Deleting the old merged branch...')
                self.git_repo.git.branch('-D', 'development')

            if 'development' not in self.git_repo.heads:
                self.print_and_log('Creating a new branch and switching to it...')
                self.git_repo.create_head('development').checkout()

                self.print_and_log('Pushing new development branch to origin...')
                self.git_repo.git.push('--set-upstream', 'origin', 'development')
            else:
                self.print_and_log('Switching to existing development branch...')
                self.git_repo.heads['development'].checkout()


            self.print_and_log('Adding changelog template for next version...')
            with open('CHANGELOG.md', 'w') as f:
                f.write(f'## [%new_version] - %date\n\n### Added\n\n### Changed\n\n### Fixed\n\n---\n\n{full_changelog}')

            self.print_and_log('Committing next version preparation and updating origin...')
            added_items = self.git_repo.index.add(['CHANGELOG.md'])
            self.git_repo.index.commit(f'Prepared next version development branch by updating: {added_items}')
            self.git_repo.remotes.origin.push()

            self.print_and_log(f'New version released: {self.version} Hooray! \U0001F386')
            self.print_and_log(f'Social media post text has been saved to {data_dir}/social media post.md. You can use it to announce the new version on social media platforms!')
            self.print_and_log(f'Log file has been saved to: {str(log_path.absolute())}')

            if self.prompt_user('Do you want to revert', 'n'):
                self.revert_changes()
            
        else:
            self.print_and_log('Canceled going further!')
            self.revert_changes()
    
    def revert_changes(self) -> None:
        '''Reverts the version to the previous one, deletes the uploaded copy and git release if they exist, and resets the git directory to the previous commit. Also restores the integrity file.'''
        self.print_and_log('Reverting back to previous version...', [255, 255, 0], 30)

        if Path(f'{cache_dir}/{self.program_name} {self.version}.zip').exists():
            self.print_and_log('Removing archive...', [255, 255, 0])
            remove(f'{cache_dir}/{self.program_name} {self.version}.zip')

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
            self.repo.get_git_ref(f'tags/{self.version}').delete()

    def _parse_commit(self, commit) -> list[dict[str: str]]:
        '''
        Parses a commit object into a dictionary containing commit information.

        :param commit: The commit object to parse.
        :return: A list of dictionaries containing the 'category', 'text', and 'hash' of a commit.
        :rtype: list[dict[str: str]]
        '''

        message = commit.message.strip()
        results = []

        # multi-entry format
        matches = self.ENTRY_RE.findall(message)

        if matches:
            for category, text in matches:
                results.append({
                    'category': category,
                    'text': text,
                    'hash': commit.hexsha[:7],
                })
            return results

        # single-entry format
        first_line = message.splitlines()[0]

        m = self.SINGLE_RE.match(first_line)

        if m:
            category, text = m.groups()

            results.append({
                'category': category,
                'text': text,
                'hash': commit.hexsha[:7],
            })
            return results
        
        return results

    def _print_and_log(self, text: str, color: Optional[Sequence[int]] = [255, 255, 255], level: int = 20):
            '''Prints the text and logs it to the packer log file.'''

            print_colored_text(text, color)
            self.log_action(text, level)
    
    def _send_queue_request(self, question: str, default: str | int = 'y') -> str | int:
        '''
        Sends a question to the input queue for processing.

        :param question: The question to be asked to the user.
        :type question: str
        :param default: The default value to use if no input is provided.
        :type default: str | int
        :return: The answer provided by the user or the default value.
        :rtype: str | int
        '''

        self.output.put({'question': question, 'default': default, 'expected output type': str | int})
        
    def _get_queue_input(self, question: str, default: str | int = 'y') -> Any:
        '''
        Gets input from the input queue.

        :param question: The question that was asked to the user.
        :type question: str
        :param default: The default value to use if no input is provided.
        :type default: str | int
        :return: The answer provided by the user or the default value.
        :rtype: Any
        '''

        answer = self.input.get()
        if not answer:
            answer = default
        answer = bool_answer(answer)
        self.log_action(f'Requested user input to "{question}" | Answer = "{answer}"')
        return answer
    
    def _queue_prompt(self, question: str, default: str | int = 'y') -> bool:
        '''
        Prompts the user with a question using the input queue.

        :param question: The question to be asked to the user.
        :type question: str
        :param default: The default value to use if no input is provided.
        :type default: str | int
        :return: The boolean value of the answer provided by the user or the default value.
        :rtype: bool
        '''

        self._send_queue_request(question, default)
        return self._get_queue_input(question, default)
    
    def _terminal_prompt(self, question: str, default: str | int = 'y') -> bool:
        '''
        Prompts the user with a question using the terminal.

        :param question: The question to be asked to the user.
        :type question: str
        :param default: The default value to use if no input is provided.
        :type default: str | int
        :return: The boolean value of the answer provided by the user or the default value.
        :rtype: bool
        '''

        answer = simple_prompt(question, default)
        self.log_action(f'Requested user input to "{question}" | Answer = "{answer}"')
        return answer

    def _just_log(self, text, color: Optional[Sequence[int]] = [255, 255, 255], level: int = 20):
        '''
        Logs text to the packer log file without printing it.

        :param text: The text to be logged.
        :param color: The color to use for printing (not used in logging).
        :type color: Optional[Sequence[int]]
        :param level: The logging level to use.
        :type level: int
        '''

        self.log_action(text, level)

    def _log_and_output_queue(self, text, color: Optional[Sequence[int]] = [255, 255, 255], level: int = 20):
        '''
        Logs text to the packer log file and outputs it to the queue.

        :param text: The text to be logged and output.
        :type text: str
        :param color: The color to use for printing.
        :type color: Optional[Sequence[int]]
        :param level: The logging level to use.
        :type level: int
        '''

        self.output_queue.put({'text': text, 'color': color, 'level': level})
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

    def _Popen(self, cmd: list[str], waiting: threading.Event) -> threading.Event:
        '''
        Runs a subprocess command in the git directory and prints the stdout in real time. Also logs the stdout to the packer log file.
        
        :param cmd: The command and its arguments.
        :type cmd: list[str]
        :param waiting: An event to signal when to start printing the output.
        :type waiting: Event
        :return: An event that is set when the subprocess is done.
        :rtype: Event
        '''

        done = threading.Event()

        def thread_function(done: threading.Event):
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

        threading.Thread(target=thread_function, args=[done], daemon=True).start()

        return done

def main():
    parser = ArgumentParser('packer', description='Packer CLI tool')
    
    parser.add_argument('-p', '--paths', action='store_true', help='Output all storage paths')
    parser.add_argument('-v', '--version', action='store_true', help='Display the software\'s version')

    args = parser.parse_args()

    if args.paths:
        print(f'root_dir: {root_dir}')
        print(f'assets_dir: {assets_dir}')
        print(f'config_dir: {config_dir}')
        print(f'log_dir: {log_dir}')
        print(f'log_path: {log_path}')
        print(f'error_report_path: {error_report_path}')
        print(f'data_dir: {data_dir}')
        print(f'cache_dir: {cache_dir}')
        sys.exit()
    
    if args.version:
        print(f'Packer version {packer_version}')
        sys.exit()
    
    project_directory, project_configuration = tui()

    if Path().cwd() != Path(project_directory):
        print('Changing working directory...')
        chdir(project_directory)
    
    if not all_settings.skip_git_status:
        if run(['git', 'status', '--porcelain'], capture_output=True).stdout.decode() != '':
            print('Your git directory is not clean! Please commit or stash your changes before running the packer. Exiting...')
            sys.exit()

    version = read_json(f'{project_directory}/src/{project_configuration.program_name}/assets/version.json')
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
            sys.exit()

    try:
        packer = Packer(version, old_version,
                        project_configuration.gofile_user_token, project_configuration.gofile_folder_id, project_configuration.github_repo_token,
                        project_configuration.program_name, project_configuration.github_repo_url,
                        None, None,
                        project_configuration.compile_command, project_configuration.before_commands, project_configuration.after_commands, 
                        project_configuration.model, project_configuration.description_prompt, project_configuration.title_prompt)

        def packer_exception_handler(exc_type, exc_value, exc_traceback):
            packer.revert_changes()
            global_exception_handler(exc_type, exc_value, exc_traceback)

        sys.excepthook = packer_exception_handler # replace the global exception handler with packer's to revert changes in case Packer was running.
        
        packer.run()
    except KeyboardInterrupt:
        packer.print_and_log('Process interrupted by user!', [255, 255, 0], level=30)
        packer.revert_changes()

if __name__ == '__main__':
    main()