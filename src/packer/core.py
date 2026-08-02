from pathlib import Path
from datetime import datetime
from multiprocessing import Queue
from re import MULTILINE, compile
from shutil import get_terminal_size, rmtree, make_archive, which
from os import chdir, listdir, makedirs, remove, path
from json import dump, load
from subprocess import PIPE, STDOUT, CompletedProcess, Popen, run
from time import sleep
from typing import Any, NoReturn, Optional
from collections.abc import Callable, Sequence
from github import Github, Auth, UnknownObjectException
from ollama import chat
from requests import post, exceptions
from git import GitCommandError, Repo
import tomlkit
import threading
from string import Template
import sys
from pyperclip import copy
from webbrowser import open_new_tab
from itertools import cycle
import queue

from packer.custom_modules.et import format_size, get_folder_size, tree, delete_upload, init_logger, input_via_text_editor
from packer.custom_modules.etf import bool_answer, clear_lines, lines_used, simple_prompt_retries, print_bg_colored_text, print_colored_text, print_with_delay
from packer.config import all_settings, Project, packer_version, send_notification
from packer.paths import log_path, data_dir, cache_dir, metadata_path, log_dir


def _filter_empty_changelog_sections(changelog: str) -> str:
    '''Return a changelog with empty "###" sections removed.'''

    lines = changelog.splitlines()
    filtered_lines: list[str] = []
    current_header: str | None = None
    current_section_lines: list[str] = []
    pending_blank_lines: list[str] = []

    def flush_current_section() -> None:
        nonlocal current_header, current_section_lines

        if current_header is None:
            return

        section_lines = list(current_section_lines)
        while section_lines and not section_lines[0].strip():
            section_lines.pop(0)
        while section_lines and not section_lines[-1].strip():
            section_lines.pop()

        section_content = '\n'.join(section_lines).strip()
        if section_content:
            if filtered_lines and filtered_lines[-1].strip():
                filtered_lines.append('')
            filtered_lines.extend([current_header, *section_lines])

        current_header = None
        current_section_lines = []

    for line in lines:
        if line.startswith('### '):
            flush_current_section()
            pending_blank_lines.clear()
            current_header = line
        elif current_header is not None:
            current_section_lines.append(line)
        else:
            if line.strip():
                if pending_blank_lines:
                    if filtered_lines and filtered_lines[-1].strip():
                        filtered_lines.append('')
                    pending_blank_lines.clear()
                filtered_lines.append(line)
            elif filtered_lines and filtered_lines[-1].strip():
                pending_blank_lines.append(line)

    flush_current_section()
    return '\n'.join(filtered_lines).strip()


def thread_excepthook(args):
    sys.excepthook(args.exc_type, args.exc_value, args.exc_traceback)

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

    with open(file_path, 'rb') as f:
        files = {
            'file': f
        }

        data = {
            'token': token,
            'folderId': folder_id
        }

        response = post('https://upload.gofile.io/uploadfile', files=files, data=data, timeout=60)
        response.raise_for_status()

        return response.json()

class Packer():
    '''
    The Packer class is responsible for creating an archive of the program, uploading it to Gofile, updating the git directory, and publishing a new release on Github. If any error is encountered it reverts all changes back to the previous version.
    
    :param version: The new version of the program.
    :type version: dict
    :param project_path: The path to the project directory.
    :type project_path: str | Path
    :param GOFILE_USER_TOKEN: The user token for Gofile, used to upload the archive.
    :type GOFILE_USER_TOKEN: str, optional
    :param FOLDER_ID: The folder id for Gofile, used to upload the archive.
    :type FOLDER_ID: str, optional
    :param GITHUB_REPO_TOKEN: The token for the Github repo, used to publish the release.
    :type GITHUB_REPO_TOKEN: str
    :param github_repo_url: The url of the Github repo, used to publish the release and for the social media post. It should be in the format "username/repo".
    :type github_repo_url: str
    :param input_queue: A queue for input operations, used for inter-thread communication.
    :type input_queue: Queue, optional
    :param output_queue: A queue for output operations, used for inter-thread communication.
    :type output_queue: Queue, optional
    :param compile_command: The command to compile the program using Nuitka, used to compile the program and upload the compiled version to the Github release.
    :type compile_command: Sequence[str], optional
    :param before_commands: A tuple of commands to run before the build process.
    :type before_commands: tuple[tuple[str, ...] | Callable, ...], optional
    :param after_commands: A tuple of commands to run after the build process.
    :type after_commands: tuple[tuple[str, ...] | Callable, ...], optional
    :param model: The language model to use for generating the version description and title, defaults to 'mistral'.
    :type model: str, optional
    :param description_prompt: The prompt to use for generating the release description.
    :type description_prompt: list[dict[str: str]], optional
    :param title_prompt: The prompt to use for generating the release title.
    :type title_prompt: list[dict[str: str]], optional
    :param release_notes_template_path: The path to the release notes template file.
    :type release_notes_template_path: str, optional
    :param changelog_git_hash: Whether to include the git hash in the changelog.
    :type changelog_git_hash: bool, optional
    '''

    def __init__(self, version: dict, project_path: str | Path,
                 GITHUB_REPO_TOKEN: str, github_repo_url: str, 
                 GOFILE_USER_TOKEN: str | None = None, FOLDER_ID: str | None = None,
                 input_queue: Queue = None, output_queue: Queue = None,
                 compile_command: Sequence[str] = Project.model_fields['compile_command'].default,
                 before_commands: tuple[tuple[str, ...] | Callable, ...] = Project.model_fields['before_commands'].default, after_commands: tuple[tuple[str, ...] | Callable, ...] = Project.model_fields['after_commands'].default,
                 model: str = Project.model_fields['model'].default, description_prompt: list[dict[str: str]] = Project.model_fields['description_prompt'].default, title_prompt: list[dict[str: str]] = Project.model_fields['title_prompt'].default,
                 description_prompt_kwargs: dict[Any, Any] = Project.model_fields['description_prompt_kwargs'].default, title_prompt_kwargs: dict[Any, Any] = Project.model_fields['title_prompt_kwargs'].default,
                 release_notes_template_path: str = Project.model_fields['release_notes_template_path'].default, changelog_git_hash: bool = Project.model_fields['changelog_git_hash'].default,
                 check_todo: bool = Project.model_fields['check_todo'].default, todo_rel_path: str = Project.model_fields['todo_rel_path'].default,
                 list_start_identifier: str = Project.model_fields['list_start_identifier'].default, list_end_identifier: str = Project.model_fields['list_end_identifier'].default
                ):
        # parameter initialization
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.version = version
        self.GOFILE_USER_TOKEN = GOFILE_USER_TOKEN
        self.FOLDER_ID = FOLDER_ID
        self.GITHUB_REPO_TOKEN = GITHUB_REPO_TOKEN
        self.model = model
        self.program_name = Path(project_path).name
        self.github_repo_url = github_repo_url
        self.compile_command = compile_command
        self.before_commands = before_commands
        self.after_commands = after_commands
        self.description_prompt = description_prompt
        self.title_prompt = title_prompt
        self.changelog_git_hash = changelog_git_hash
        self.title_prompt_kwargs = title_prompt_kwargs
        self.description_prompt_kwargs = description_prompt_kwargs

        # Actions needed to run once, (setup actions)
        self.logger = init_logger('packer', 'EMILIO')
        self.chosen_description_path = Path(f'{data_dir}/chosen description.md')
        self.chosen_title_path = Path(f'{data_dir}/chosen version title.md')
        self.git_repo = Repo()
        with open(release_notes_template_path) as f:
            self.release_text = f.read()
        self.assets_dir = f'./src/{self.program_name}/assets'
        self.ENTRY_RE = compile(
                r'^- (Added|Changed|Fixed):\s*(.+)$',
                MULTILINE
            )
        self.SINGLE_RE = compile(
            r'^(Added|Changed|Fixed):\s*(.+)$'
        )
        self.run_pyinstaller = any(Path().glob('*.spec'))
        self.cache_dir = f'{cache_dir}/{self.program_name}'
        makedirs(self.cache_dir, exist_ok=True)
        with open(f'{project_path}/src/{self.program_name}/assets/version.json') as f:
            self.old_version = load(f)


        # Settings related actions
        if input_queue:
            all_settings.verbose = False
        if all_settings.smooth_output:
            self.buffer_queue = queue.Queue()
            self.finished_output = threading.Event()
            threading.Thread(target=self._process_print, daemon=True).start()

        self.print_and_log = self._print_and_log if all_settings.verbose else self._log_and_output_queue
        self.prompt_user = self._queue_prompt if input_queue else self._terminal_prompt
        self.stream_output_chunk = self._stream_queue_chunk if input_queue else self._stream_print_chunk

        # Relies on some setup actions
        if Path().cwd() != Path(project_path):
            self.print_and_log('Changing working directory...')
            chdir(project_path)
        
        if not all_settings.skip_git_status:
            if run(['git', 'status', '--porcelain'], capture_output=True).stdout.decode() != '':
                self.print_and_log('Your git directory is not clean! Please commit or stash your changes before running the packer. Exiting...', [255, 0, 0], 40)
                self._exit(1)

        if self.description_prompt or self.title_prompt and not which('ollama'):
            self.print_and_log('Couldn\'t find ollama on PATH, please add it if installed otherwise install it: https://ollama.com/download. Alternately you can also set both prompts to None. Exiting...', [255, 0, 0], 40)
            self._exit(1)
        
        if check_todo:
            with open(f'{todo_rel_path}') as f:
                content = f.read().lower()

            list_start = content.find(list_start_identifier)
            list_end = content.find(list_end_identifier, list_start)

            todo_list = content[list_start + len(list_start_identifier):list_end].lstrip(':').strip()

            if todo_list:
                self.print_and_log(f'{list_start_identifier} task/s found, please delete them from the list once finished!\n{list_start_identifier} List:\n{todo_list}\nExiting...', [255, 0, 0], 40)
                self._exit(1)

    def run(self):
        '''Runs the packer, which creates an archive of the program, uploads it to Gofile, updates the git directory, and publishes a new release on Github. If any error is encountered it reverts all changes back to the previous version.'''

        self.print_and_log('Starting packer...')

        self.print_and_log('Updating Github origin URL with PAT...')

        authenticated_url = f'https://{self.GITHUB_REPO_TOKEN}@github.com/{self.github_repo_url}.git'
        if 'origin' in self.git_repo.remotes:
            origin = self.git_repo.remotes.origin
            origin.set_url(authenticated_url)
        else:
            origin = self.git_repo.create_remote('origin', authenticated_url)

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

            self.print_and_log('Updating the latest changelog...')
            latest_changelog = (
                f'### Added\n{added_category.strip()}\n\n'
                f'### Changed\n{changed_category.strip()}\n\n'
                f'### Fixed\n{fixed_category.strip()}'
            )

        self.print_and_log('Filtering out empty sections...')
        latest_changelog_start = full_changelog.find(f'## [%new_version]') + 27
        latest_changelog_end = full_changelog.find(f'## [{old_version_text}]') - 7
        latest_changelog = _filter_empty_changelog_sections(latest_changelog)

        self.print_and_log('Stitching full changelog with the updated latest changelog')
        full_changelog = f'{full_changelog[:latest_changelog_start]}{latest_changelog}{full_changelog[latest_changelog_end:]}'

        self.print_and_log('Updating changelog with the new version...')
        full_changelog = full_changelog.replace('%new_version', self.version).replace('%date', str(datetime.date(datetime.now())), 1)

        self.print_and_log('Writing out the updated changelog...')
        with open('CHANGELOG.md', 'w') as f:
            f.write(full_changelog)


        self.print_and_log('Generating a version description...')

        generate_description = True
        if self.chosen_description_path.exists() and self.prompt_user('Use the previously generated version description'):
            generate_description = False
            with open(self.chosen_description_path) as f:
                description = f.read()

        GENERATING_COLOR = [144, 213, 255]
        if self.description_prompt is not None:
            self.description_prompt[1 if self.description_prompt[1]['role'] == 'user' else 0]['content'] = self.description_prompt[1]['content'].replace('%latest_changelog', latest_changelog)
            while generate_description:
                description = []
                stream = chat(self.model, self.description_prompt, stream=True, **self.description_prompt_kwargs)

                first_chunk = next(stream).message.content.lstrip()
                description.append(first_chunk)
                self.buffer_queue.join()
                self.stream_output_chunk(first_chunk, 'version description output', GENERATING_COLOR) # First chunk to get rid of the empty whitespaces

                for chunk in stream:
                    chunk = chunk.message.content
                    self.stream_output_chunk(chunk, 'version description output', GENERATING_COLOR)
                    description.append(chunk)
                self._finish_stream()
                description = ''.join(description)
                self.log_action(description)
                generate_description = not self.prompt_user('Is the description all good', 'n')
        else:
            description = 'Write your version description in this file. (select all text [usually ctrl+a] and then start writing your description. After you have written it, save it and close the editor)'

        description = input_via_text_editor(description, str(self.chosen_description_path))


        self.print_and_log('Generating a version title...')

        generate_title = True
        if self.chosen_title_path.exists() and self.prompt_user('Use the previously generated version title'):
            generate_title = False
            with open(self.chosen_title_path) as f:
                version_title = f.read()

        if self.title_prompt is not None:
            self.title_prompt[1]['content'] = self.title_prompt[1 if self.title_prompt[1]['role'] == 'user' else 0]['content'].replace('%latest_changelog', latest_changelog)
            while generate_title:
                version_title = []
                stream = chat(self.model, self.title_prompt, stream=True, **self.title_prompt_kwargs)

                first_chunk = first_chunk = next(stream).message.content.lstrip()
                version_title.append(first_chunk)
                self.buffer_queue.join()
                self.stream_output_chunk(first_chunk, 'version title output', GENERATING_COLOR) # First chunk to get rid of the empty whitespaces
                for chunk in stream:
                    chunk = chunk.message.content
                    self.stream_output_chunk(chunk, 'version title output', GENERATING_COLOR)
                    version_title.append(chunk)
                self._finish_stream()
                version_title = ''.join(version_title)
                self.log_action(version_title)
                generate_title = not self.prompt_user('Is the Version title all good', 'n')
        else:
            version_title = 'Write your version title in this file. (select all text [usually ctrl+a] and then start writing your title. After you have written it, save it and close the editor)'

        version_title = input_via_text_editor(version_title, str(self.chosen_title_path))


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


        self.print_and_log('Getting exclusions from .gitignore...')
        with open('.gitignore') as f:
            exclusions = [entry for entry in f.read().splitlines() if '#' not in entry and entry != '']
        exclusions.append('.git')

        self.print_and_log('Generating the integrity file...')
        new_cwd = tree(Path().cwd(), exclusions)
        with open(f'{self.assets_dir}/integrity.json', 'w') as f:
            dump({'CWD': new_cwd}, f)


        self.print_and_log('Creating an archive of the current git repository...')
        with open(f'{self.cache_dir}/{self.program_name} {self.version}.zip', 'wb') as fp:
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


        with open(metadata_path) as f:
            metadata: dict = load(f)
        current_project_metadata = metadata.get(str(Path().absolute()), {})
        
        project_size = get_folder_size(Path(), exclusions)
        version_size = Path(f'{self.cache_dir}/{self.program_name} {self.version}.zip').stat().st_size

        if current_project_metadata:
            project_latest_size: int = current_project_metadata.get('project size')
            if project_latest_size:
                self.print_and_log(f'Project size change: {format_size(project_latest_size - project_size)}')
            last_versions_size: int = current_project_metadata.get('version size')
            if last_versions_size:
                self.print_and_log(f'New versions size change: {format_size(last_versions_size - version_size)}')

        self.print_and_log(f'Full project size with exclusions: {format_size(project_size)}')
        self.print_and_log(f'New version\'s size: {format_size(version_size)}')


        self.print_and_log(f'Archive saved at: {self.cache_dir}/{self.program_name} {self.version}.zip')
        if self.prompt_user('Is the arhive all good (no going back after this)'):

            if self.compile_command != None:
                self.print_and_log('Compiling the program using Nuitka...')
                waiting_for_compile_command = threading.Event()
                compile_command_done = self._Popen(self.compile_command, waiting_for_compile_command)

                self.print_and_log('Creating archive of the compiled program...')
                make_archive(f'{self.cache_dir}/{self.program_name} [nuitka]', 'zip', f'{self.cache_dir}/main.dist')

            
            if self.run_pyinstaller:
                self.print_and_log('Bundling the program using PyInstaller...')
                waiting_for_pyinstaller_bundling = threading.Event()
                pyinstaller_done = self._Popen([sys.executable,
                            '-m',
                            'PyInstaller', 'main.spec',
                            '--distpath', f'{self.cache_dir}/dist',
                            '--workpath', f'{self.cache_dir}/build'], waiting_for_pyinstaller_bundling)
            
            if self.GOFILE_USER_TOKEN and self.FOLDER_ID:
                self.print_and_log('Uploading archive to Gofile...')
                retry_gofile = True
                retry_gofile_count = -1
                while retry_gofile:
                    try:
                        retry_gofile_count += 1
                        if retry_gofile_count > 2:
                            self.print_and_log(f'After {retry_gofile_count} unsuccessful attempts the release has been paused', 30)
                            self.print_and_log('You can attempt to resolve the problem right now, once done enter yes, if you wish to quit enter no', 30)
                            if not self.prompt_user('Has the problem been resolved'):
                                self.revert_changes()

                        response = upload_gofile_file(Path(f'{self.cache_dir}/{self.program_name} {self.version}.zip'), self.GOFILE_USER_TOKEN, self.FOLDER_ID)
                        if response.get('status') != 'ok' or not response.get('data'):
                            self.print_and_log(f'GoFile upload returned an invalid response: {response}', 40)
                            self.revert_changes()
                        retry_gofile = False
                    except exceptions.SSLError:
                        self.print_and_log('Encountered an SSL (verification) error when uploading to GoFile', 30)
                    except Exception as e:
                        self.print_and_log(f'Encountered a problem while uploading to GoFile | Error: {e}', 30)

                    if retry_gofile:
                        self.print_and_log('retrying in 3 seconds...', 30)
                        sleep(3)


                download_url = response['data']['downloadPage']
                self.file_id = response['data']['id']

            if self.before_commands:
                self.print_and_log('Running pre commit hooks...')
                for cmd in self.before_commands:
                    if callable(cmd):
                        cmd()
                    else:
                        self._run('sh', '-c', cmd)


            self.print_and_log('Staging changes...')
            self.log_action(f'Entries added: {self.git_repo.index.add(['pyproject.toml', 'CHANGELOG.md',
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
                        self.print_and_log('Fallback to unsigned commit...', 30)
                        self.git_repo.git.commit('-m', commit_message)
                        self.committed = True
                except GitCommandError as e:
                    self.committed = False
                    self.print_and_log(f'Something went wrong while committing: {e}', [255, 0, 0], 40)
                    self.revert_changes()


            sha = self.git_repo.head.commit.hexsha

            self.print_and_log('Pushing changes...')
            self.git_repo.remotes.origin.push()

            if self.after_commands:
                self.print_and_log('Running post commit hooks...')
                for cmd in self.after_commands:
                    if callable(cmd):
                        cmd()
                    else:
                        self._run('sh', '-c', cmd)

            self.print_and_log('Generating release notes...')

            release_notes_template_data = {
                'program_name': self.program_name,
                'new_version': self.version,
                'version_description': description,
                'github_repo_url': self.github_repo_url,
                'gofile_download_url': download_url,
                'latest_changelog': latest_changelog
            }

            self.release_text = Template(self.release_text).substitute(release_notes_template_data)

            # Publish a github release

            self.print_and_log('Authorizing on Github...')
            self.repo = Github(auth=Auth.Token(self.GITHUB_REPO_TOKEN)).get_repo(self.github_repo_url)

            # Keeps polling the repo, until we good.
            self.print_and_log('Waiting for Github to process the push...')
            while True:
                try:
                    self.repo.get_commit(sha)
                    break
                except UnknownObjectException:
                    self.print_and_log('Waiting...')
                    sleep(1)
            
            self.print_and_log('Publishing a new release on GitHub...')

            retry_release = True
            retry_release_count = 0
            while retry_release:
                try:
                    if retry_release_count > 3:
                        self.print_and_log(f'Failed to create a release on GitHub after {retry_release_count} attempts', 30)
                        self.print_and_log('You can attempt to resolve the problem right now, once done enter yes, if you wish to quit enter no', 30)
                        if not self.prompt_user('Has the problem been resolved'):
                            self.revert_changes()
                    self.git_release = self.repo.create_git_release(tag=self.version, name=f'v{self.version} - {version_title}',
                                                                    message=self.release_text, target_commitish=sha)
                    retry_release = False
                except Exception as e:
                    self.print_and_log(f'Failed to create a release on GitHub | Error: {e}', [255, 0, 0], 30)
                    self.print_and_log('Retrying in 3 seconds...', [0, 0, 255], 30)
                    sleep(3)
                    retry_release_count += 1
            
            self.print_and_log('Fetching the git tag...')
            self.git_repo.remotes.origin.fetch(tags=True)

            self.print_and_log('Uploading the compiled programs to the GitHub release...')

            if self.run_pyinstaller:
                self.print_and_log('Waiting for PyInstaller to finish...')
                waiting_for_pyinstaller_bundling.set()
                pyinstaller_done.wait()

                self._upload_github_asset(Path(f'{self.cache_dir}/dist/{self.program_name}'), 'application/octet')

            if self.compile_command != None:
                self.print_and_log('Waiting for Nuitka to finish...')
                waiting_for_compile_command.set()
                compile_command_done.wait()

                self._upload_github_asset(Path(f'{self.program_name} [nuitka].zip'), 'application/zip')


            self.print_and_log('Cleaning up cache...')
            if self.run_pyinstaller:
                rmtree(f'{self.cache_dir}/dist')
            
            if all_settings.auto_clear_cache and get_folder_size(Path(self.cache_dir)) > all_settings.cache_size_threshold:
                self.print_and_log(f'Deleting cache folder, over threshold [{format_size(all_settings.cache_size_threshold)}]...')
                rmtree(self.cache_dir)
            
            if all_settings.auto_clear_logs and get_folder_size(Path(log_dir)) > all_settings.logs_size_threshold:
                self.print_and_log(f'Cleaning logs folder, over threshold: [{format_size(all_settings.logs_size_threshold)}]...')

                def _get_timestamp(file: str) -> datetime:
                    if 'error report' in file:
                        file = file.rstrip('.json').lstrip('error report ')
                    else:
                        file = file.rstrip('.log')
                    
                    return datetime.strptime(file, '%Y-%m-%d')

                files = sorted(listdir(log_dir), key=_get_timestamp)

                while get_folder_size(Path(log_dir)) > all_settings.logs_size_threshold:
                    file = files.pop(0)
                    remove(f'{log_dir}/{file}')
                    self.print_and_log(f'Removed {file}')

            if self.compile_command != None:
                rmtree(f'{self.cache_dir}/main.dist')
                remove(f'{self.cache_dir}{self.program_name} [nuitka].zip')

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
            self.git_repo.index.add(['CHANGELOG.md'])
            next_versions_commit_message = 'Prepared next version development branch'
            try:
                self.git_repo.git.commit('-S', '-m', next_versions_commit_message)
                self.prep_committed = True
            except GitCommandError:
                try:
                    self.print_and_log('Fallback to unsigned commit...', 30)
                    self.git_repo.git.commit('-m', next_versions_commit_message)
                    self.prep_committed = True
                except GitCommandError as e:
                    self.print_and_log(f'Something went wrong while committing: {e}', [255, 0, 0], 40)
            self.git_repo.remotes.origin.push()

            self.print_and_log('Cleaning up temporary files...')
            remove(self.chosen_description_path)
            remove(self.chosen_title_path)


            self.print_and_log(f'New version released: {self.version} Hooray! \U0001F386')
            if all_settings.desktop_notifications:
                send_notification('New version released!', f'Version {self.version} has been released successfully!')

            release_url = self.git_release.html_url
            if all_settings.open_gitHub_release:
                open_new_tab(release_url)
            if all_settings.copy_github_release_clipboard:
                copy(release_url)
                self.print_and_log('Copied GitHub release URL to clipboard')
            else:
                self.print_and_log(f'Github release: {release_url}')
            self.print_and_log(f'Social media post text has been saved to {data_dir}/social media post.md. You can use it to announce the new version on social media platforms!')
            self.print_and_log(f'Log file has been saved to: {str(log_path.absolute())}')

            if self.prompt_user('Do you want to revert', 'n'):
                self.revert_changes()
            
            self.print_and_log('Updating metadata.json...')
            current_project_metadata['project size'] = project_size
            current_project_metadata['version size'] = version_size


            metadata[str(Path().absolute())] = current_project_metadata
            
            with open(metadata_path, 'w') as f:
                dump(metadata, f)
            
            self.buffer_queue.join()

            
        else:
            self.print_and_log('Canceled going further!')
            self.revert_changes()
    
    def revert_changes(self, exit: bool = True) -> None | NoReturn:
        '''Rollback the release process by removing the generated archive, deleting the uploaded Gofile copy and GitHub release when present, and resetting the Git repository to its previous state.'''

        self.buffer_queue.join()
        self.print_and_log('Reverting back to previous version...', [255, 255, 0], 30)

        if Path(f'{self.cache_dir}/{self.program_name} {self.version}.zip').exists():
            self.print_and_log('Removing archive...', [255, 255, 0])
            remove(f'{self.cache_dir}/{self.program_name} {self.version}.zip')

        if hasattr(self, 'file_id'):
            self.print_and_log('Deleting uploaded copy...', [255, 255, 0])
            delete_upload(self.file_id, self.GOFILE_USER_TOKEN)

        self.print_and_log('Reverting git changes...', [255, 255, 0])

        self.print_and_log('Counting commits...')
        commit_count = 0
        if hasattr(self, 'committed') and self.committed:
            commit_count += 1
        if hasattr(self, 'prep_committed') and self.prep_committed:
            commit_count += 1

        if commit_count > 0:
            self.print_and_log('Cleaning up git environment...')
            self._revert_git_head(commit_count)
            if commit_count == 2:
                self.print_and_log('Switching to master branch...')
                self.git_repo.heads['master'].checkout()
                self._revert_git_head(commit_count)
                self.print_and_log('Switching back to development branch...')
                self.git_repo.heads['development'].checkout()
        else:
            self.git_repo.head.reset(working_tree=True)

        if hasattr(self, 'git_release'):
            self.print_and_log('Deleting git release...', [255, 255, 0])
            self.git_release.delete_release()

            # Delete from GitHub first while the local ref is fully intact
            self.print_and_log('Updating origin (deleting remote tag)...')
            self.git_repo.remotes.origin.push(refspec=f':refs/tags/{self.version}')

            self.print_and_log('Deleting local git tag...')
            self.git_repo.delete_tag(self.version)
        if exit:
            self._exit(1)
        
    def _exit(self, code: int = None):
        self.buffer_queue.join()
        sys.exit(code)
    
    def _upload_github_asset(self, file_path: Path, content_type: str):
        with open(file_path, 'rb') as f:
            self.git_release.upload_asset_from_memory(f,
                                                        path.getsize(file_path),
                                                        file_path.name,
                                                        f'{content_type}-stream')
    
    def _stream_queue_chunk(self, chunk: str, type: str, color: list[int] | None = None):
        self.output_queue.put({'type': type, 'chunk': chunk, 'color': color})


    def _stream_print_chunk(self, chunk: str, type: str, color: list[int] | None = None):
        if color:
            print_colored_text(chunk, color, flush=True, end='')
        else:
            print(chunk, end='', flush=True)
    
    def _finish_stream(self):
        if self.output_queue:
            self.output_queue.put('Stream finished!')
        else:
            print()
        

    def _revert_git_head(self, commit_count: int):
        '''
        Reverts the git repository head by the specified number of commits.

        :param commit_count: The number of commits to revert.
        :type commit_count: int
        '''

        self.print_and_log(f'Reverting HEAD {commit_count} commits back...')
        self.git_repo.head.reset(commit=f'HEAD~{commit_count}', working_tree=True)
        self.git_repo.remotes.origin.push(force=True) # In case we pushed it to github already!

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
    
    def _process_print(self):
        while True:
            text = self.buffer_queue.get()
            try:
                print_with_delay(
                    text["text"],
                    cycle([text["color"]]),
                    all_settings.smooth_output_speed / (self.buffer_queue.qsize() + 1)
                )
            finally:
                self.buffer_queue.task_done()

    def _print_and_log(self, text: str, color: Optional[Sequence[int]] | None = None, level: int = 20):
        '''Prints the text and logs it to the packer log file.'''

        if all_settings.smooth_output:
            self.buffer_queue.put({'text': text, 'color': color})
        else:
            if color:
                print_colored_text(text, color)
            else:
                print(text)
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

        self.buffer_queue.join()
        answer = simple_prompt_retries(question, default)
        self.log_action(f'Requested user input to "{question}" | Answer = "{answer}"')
        return answer

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

        self.buffer_queue.join()


        # setup
        def print_with_background(text):
            print_bg_colored_text(text, all_settings.stream_background_color)
        output_text = print_with_background if all_settings.stream_background_color else print
        done = threading.Event()


        def thread_function(done: threading.Event):
            process = Popen(cmd, stdout=PIPE, stderr=STDOUT, text=True)

            for text in process.stdout:
                text = text.rstrip('\n')
                self.log_action(text)
                if waiting.is_set():
                    output_text(text)
                    clear_lines(lines_used(text, get_terminal_size().columns), clear_formatting=True)

            process.wait()
            done.set()

        threading.Thread(target=thread_function, args=[done], daemon=True).start()

        return done