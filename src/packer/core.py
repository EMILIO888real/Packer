from pathlib import Path
from datetime import datetime
from multiprocessing import Queue
from re import MULTILINE, compile, escape
from shutil import get_terminal_size, rmtree, make_archive
from os import chdir, listdir, makedirs, remove, path
from json import dump, load
from subprocess import PIPE, CompletedProcess, Popen, run
from time import sleep
from typing import Any, Literal, NoReturn, Optional
from collections.abc import Callable, Sequence
from github import Github, Auth, UnknownObjectException
from ollama import chat
from requests import HTTPError, post, exceptions
from git import GitCommandError, Repo
import tomlkit
import threading
from string import Template
import sys
from pyperclip import copy
from webbrowser import open_new_tab
from itertools import cycle
import queue
from tenacity import retry,stop_after_attempt, wait_exponential, retry_if_exception_type

from packer.custom_modules.et import format_size, format_version_text, get_folder_size, tree, delete_upload, init_logger
from packer.custom_modules.etf import bool_answer, clear_lines, lines_used, simple_prompt_retries, print_bg_colored_text, print_colored_text, print_with_delay
from packer.config import all_settings, Project, packer_version, send_notification, ollama_available, _input_via_text_editor
from packer.paths import log_path, data_dir, cache_dir, metadata_path, log_dir
from packer.utils import find_environments, process_deployed_environments, upload_package


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
    :param github_repo_token: The token for the Github repo, used to publish the release.
    :type github_repo_token: str
    :param github_repo_url: The url of the Github repo, used to publish the release and for the social media post. It should be in the format "username/repo".
    :type github_repo_url: str
    :param gofile_user_token: The user token for Gofile, used to upload the archive.
    :type gofile_user_token: str, optional
    :param gofile_folder_id: The folder id for Gofile, used to upload the archive.
    :type gofile_folder_id: str, optional
    :param pypi_api_token: The API token for PyPI, used to upload the built package.
    :type pypi_api_token: str, optional
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
    :param check_todo: Whether to check for TODOs in the specified file before proceeding with the build.
    :type check_todo: bool, optional
    :param todo_rel_path: The relative path to the file to check for TODOs.
    :type todo_rel_path: str, optional
    :param list_start_identifier: The identifier for the start of the TODO list in the specified file.
    :type list_start_identifier: str, optional
    :param list_end_identifier: The identifier for the end of the TODO list in the specified file.
    :type list_end_identifier: str, optional
    '''

    def __init__(self, version: dict, project_path: str | Path,
                 github_repo_token: str, github_repo_url: str, 
                 gofile_user_token: str | None = None, gofile_folder_id: str | None = None,
                 pypi_api_token: str | None = None,
                 input_queue: Queue = None, output_queue: Queue = None,
                 compile_command: Sequence[str] = Project.model_fields['compile_command'].default,
                 before_commands: tuple[tuple[str, ...] | Callable, ...] = Project.model_fields['before_commands'].default, after_commands: tuple[tuple[str, ...] | Callable, ...] = Project.model_fields['after_commands'].default,
                 model: str = Project.model_fields['model'].default, description_prompt: list[dict[str: str]] = Project.model_fields['description_prompt'].default, title_prompt: list[dict[str: str]] = Project.model_fields['title_prompt'].default,
                 description_prompt_kwargs: dict[Any, Any] = Project.model_fields['description_prompt_kwargs'].default, title_prompt_kwargs: dict[Any, Any] = Project.model_fields['title_prompt_kwargs'].default,
                 release_notes_template_path: str = Project.model_fields['release_notes_template_path'].default, changelog_git_hash: bool = Project.model_fields['changelog_git_hash'].default,
                 check_todo: bool = Project.model_fields['check_todo'].default, todo_rel_path: str = Project.model_fields['todo_rel_path'].default,
                 list_start_identifier: str = Project.model_fields['list_start_identifier'].default, list_end_identifier: str = Project.model_fields['list_end_identifier'].default,
                 environment_name: str = Project.model_fields['environment_name'].default, workflow_filename: str = Project.model_fields['workflow_filename'].default
                ):
        # parameter initialization
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.version = version
        self.GOFILE_USER_TOKEN = gofile_user_token
        self.FOLDER_ID = gofile_folder_id
        self.pypi_api_token = pypi_api_token
        self.GITHUB_REPO_TOKEN = github_repo_token
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
        self.print_message_parts = []
        self.environment_name = environment_name
        self.workflow_filename = workflow_filename

        # Actions needed to run once, (setup actions)
        self.logger = init_logger('packer', 'EMILIO')
        self.chosen_description_path = Path(f'{data_dir}/chosen description.md')
        self.chosen_title_path = Path(f'{data_dir}/chosen version title.md')
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
        self.prompt_edit_text = self.queue_prompt_edit_text if input_queue else _input_via_text_editor

        # Relies on some setup actions
        if Path().cwd() != Path(project_path):
            self.print_and_log('Changing working directory...')
            chdir(project_path)

        if not all_settings.skip_git_status:
            if run(['git', 'status', '--porcelain'], capture_output=True).stdout.decode() != '':
                self.print_and_log('Your git directory is not clean!', [255, 0, 0], 40, ' ')
                self.print_and_log('Please commit or stash your changes before running the packer.', [0, 255, 0], end=' ')
                self.print_and_log('Exiting...', [138, 43, 226])
                self._exit(1)

        self.git_repo = Repo()

        if (self.description_prompt or self.title_prompt) and not ollama_available:
            self.print_and_log('Couldn\'t find ollama on PATH', [255, 0, 0], 40, end=' ')
            self.print_and_log('please add it if installed otherwise install it: https://ollama.com/download.', [0, 255, 0], end=' '),
            self.print_and_log('Alternately you can also set both prompts to None.', [255, 255, 0], end=' ')
            self.print_and_log('Exiting...', [138, 43, 226])
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

        self.print_and_log('Starting packer...', [0, 255, 0])

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
        self.version = format_version_text(self.version) # Not using a text variable to rewrite this one 
        self.program_archive_path = Path(f'{self.cache_dir}/{self.program_name}-{self.version}.zip')

        old_version_text = f'{self.old_version['major']}.{self.old_version['minor']}.{self.old_version['patch']}' # Not possible above solution due to needing both
        self.print_and_log(f'Chosen version: {self.version}')


        self.print_and_log('Getting latest changelog...')
        with open('CHANGELOG.md') as f:
            full_changelog = f.read()

        latest_changelog = full_changelog[full_changelog.find(f'## [%new_version]') + 27:full_changelog.find(f'---')].strip()


        self.print_and_log('Getting the latest tag...')
        tags = sorted(self.git_repo.tags, key=lambda x: x.commit.committed_date, reverse=True)

        if tags and self.changelog_git_hash:
            latest_tag = tags[0]

            self.print_and_log('Fetching all commits from HEAD to latest tag...')
            new_versions_commits = list(self.git_repo.iter_commits(
                f"{latest_tag.commit.hexsha}..HEAD"
            ))

            self.print_and_log('Identifying changelog categories...')
            added_category = f'{full_changelog[full_changelog.find('### Added') + 9: full_changelog.find('### Changed')].strip()}'
            changed_category = f'{full_changelog[full_changelog.find('### Changed') + 11: full_changelog.find('### Fixed')].strip()}'
            fixed_category = f'{full_changelog[full_changelog.find('### Fixed') + 9: full_changelog.find('---')].strip()}'

            # helper to insert hash into the first matching list item "- <text>" using a regex
            def _insert_hash_into_category(category: str, text: str, short_hash: str) -> str:
                pattern = compile(rf'^[ \t]*-[ \t]+' + escape(text), MULTILINE)
                return pattern.subn(f'- [{short_hash}] {text}', category, count=1)[0]

            self.print_and_log('Parsing and updating changelog entries...')
            for commit in new_versions_commits:
                data_list = self._parse_commit(commit)

                for data in data_list:
                    match data['category']:
                        case 'Added':
                            added_category = _insert_hash_into_category(added_category, data['text'], data['hash'])
                        case 'Changed':
                            changed_category = _insert_hash_into_category(changed_category, data['text'], data['hash'])
                        case 'Fixed':
                            fixed_category = _insert_hash_into_category(fixed_category, data['text'], data['hash'])

            self.print_and_log('Updating the latest changelog...')
            latest_changelog = (
                f'### Added\n{added_category.strip()}\n\n'
                f'### Changed\n{changed_category.strip()}\n\n'
                f'### Fixed\n{fixed_category.strip()}'
            )

        self.print_and_log('Filtering out empty sections...')
        latest_changelog_start = full_changelog.find(f'## [%new_version]') + 27
        latest_changelog_end = full_changelog.find(f'---')
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
                self._wait_smooth_output()
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

        description = self.prompt_edit_text(description, str(self.chosen_description_path))


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
                self._wait_smooth_output()
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

        version_title = self.prompt_edit_text(version_title, str(self.chosen_title_path))


        self.print_and_log('Updating pyproject.toml...')
        with open('pyproject.toml', 'r', encoding='utf-8') as f:
            pyproject_config = tomlkit.load(f)

        # (Note: In a pyproject.toml, 'version' is usually inside the [tool.poetry] or [project] table)
        if 'project' in pyproject_config:
            pyproject_config['project']['version'] = self.version
        elif 'tool' in pyproject_config and 'poetry' in pyproject_config['tool']:
            pyproject_config['tool']['poetry']['version'] = self.version
        else:
            pyproject_config['version'] = self.version # Fallback if it's just a top-level global key

        self.pypi_program_name = pyproject_config['project']['name']

        with open('pyproject.toml', 'w', encoding='utf-8') as f:
            tomlkit.dump(pyproject_config, f)


        if Path(f'{self.cache_dir}/{self.program_name}-{old_version_text}.zip').exists():
            self.print_and_log('Removing old archive...', [0, 255, 0])
            remove(f'{self.cache_dir}/{self.program_name}-{old_version_text}.zip')


        self.print_and_log('Getting exclusions from .gitignore...')
        with open('.gitignore') as f:
            exclusions = [entry for entry in f.read().splitlines() if '#' not in entry and entry != '']
        exclusions.append('.git')

        self.print_and_log('Generating the integrity file...')
        new_cwd = tree(Path().cwd(), exclusions)
        with open(f'{self.assets_dir}/integrity.json', 'w') as f:
            dump({'CWD': new_cwd}, f)


        self.print_and_log('Creating an archive of the current git repository...')
        with open(self.program_archive_path, 'wb') as fp:
            self.git_repo.archive(fp, format='zip')


        if tags:
            latest_tag_commit = latest_tag.commit
            current_commit = self.git_repo.head.commit

            self.print_and_log(f'Comparing current HEAD', end=' ')
            self.print_and_log(f'({current_commit.hexsha[:7]})', [0, 0, 255], end=' ')
            self.print_and_log(f'against the latest tag', end=' ')
            self.print_and_log(latest_tag.name, [0, 0, 255], end=' ')
            self.print_and_log(f'({latest_tag_commit.hexsha[:7]})', [0, 0, 255])

            diffs = latest_tag_commit.diff(current_commit)

            for diff in diffs:
                if diff.new_file:
                    self.print_and_log(f'ADDED:    {diff.b_path}', [255, 255, 0])
                elif diff.deleted_file:
                    self.print_and_log(f'REMOVED:  {diff.a_path}', [255, 255, 0])
                else:
                    self.print_and_log(f'MODIFIED: {diff.a_path}')
        else:
            self.print_and_log('No git tags found. Skipping file changes to latest version...', [255, 255, 0], 30)


        with open(metadata_path) as f:
            metadata: dict = load(f)
        current_project_metadata = metadata.get(str(Path().absolute()), {})
        
        project_size = get_folder_size(Path(), exclusions)
        version_size = self.program_archive_path.stat().st_size

        if current_project_metadata:
            project_latest_size: int = current_project_metadata.get('project size')
            if project_latest_size:
                project_size_change = project_size - project_latest_size
                self.print_and_log('Project size change:', end=' +' if project_size_change > 0 else ' ')
                self.print_and_log(format_size(project_size_change), [162, 148, 187])
            last_versions_size: int = current_project_metadata.get('version size')
            if last_versions_size:
                versions_size_change = version_size - last_versions_size
                self.print_and_log(f'New versions size change:', end=' +' if versions_size_change > 0 else ' ')
                self.print_and_log(format_size(versions_size_change), [162, 148, 187])

        self.print_and_log(f'Full project size with exclusions:', end=' ')
        self.print_and_log(format_size(project_size), [162, 148, 187])
        self.print_and_log(f'New version\'s size:', end=' ')
        self.print_and_log(format_size(version_size), [162, 148, 187])


        self.print_and_log(f'Archive saved at:', end=' ')
        self.print_and_log(str(self.program_archive_path), [255, 105, 180])
        if self.prompt_user('Is the arhive all good (no going back after this)'):

            if self.compile_command:
                self.print_and_log('Compiling the program using Nuitka...')
                waiting_for_compile_command = threading.Event()
                compile_command_done = self._Popen(self.compile_command, waiting_for_compile_command)

            self.print_and_log(f'Building a python package ({2 if self.pypi_api_token else 1} files)')
            waiting_for_building = threading.Event()
            building_cmd = [sys.executable, '-m', 'build', '--outdir', f'{self.cache_dir}/dist']
            if not self.pypi_api_token:
                building_cmd.insert(3, '--wheel')
            building_done = self._Popen(building_cmd, waiting_for_building)
            
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
                            self.print_and_log(f'After', end=' ')
                            self.print_and_log(str(retry_gofile_count), [0, 0, 255], end=' ')
                            self.print_and_log('unsuccessful attempts the release has been paused', level=30)
                            self.print_and_log('You can attempt to resolve the problem right now, once done enter yes, if you wish to quit enter no', level=30)
                            if not self.prompt_user('Has the problem been resolved'):
                                self.revert_changes()

                        response = upload_gofile_file(self.program_archive_path, self.GOFILE_USER_TOKEN, self.FOLDER_ID)
                        if response.get('status') != 'ok' or not response.get('data'):
                            self.print_and_log(f'GoFile upload returned an invalid response: {response}', [255, 0, 0], 40)
                            self.revert_changes()
                        retry_gofile = False
                    except exceptions.SSLError:
                        self.print_and_log('Encountered an SSL (verification) error when uploading to GoFile', [255, 0, 0], 30)
                    except Exception as e:
                        self.print_and_log(f'Encountered a problem while uploading to GoFile | Error: {e}', [255, 0, 0], 30)

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

            self.committed = self.git_commit(f'{commit_subject}\n\n{commit_body}\n\n{commit_metadata}')


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
                'latest_changelog': latest_changelog,
                'pypi_program_name': self.pypi_program_name
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
                    self.print_and_log('Waiting for 1 second for Github to process the push...')
                    sleep(1)
            
            self.print_and_log('Publishing a new release on GitHub...')

            retry_release = True
            retry_release_count = 0
            while retry_release:
                try:
                    if retry_release_count > 3:
                        self.print_and_log(f'Failed to create a release on GitHub after', [255, 0, 0], 30, ' ')
                        self.print_and_log(str(retry_release_count), [0, 0, 255], 30, ' ')
                        self.print_and_log('unsuccessful attempts the release has been paused', level=30)
                        self.print_and_log('You can attempt to resolve the problem right now, once done enter yes, if you wish to quit enter no', level=30)
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

            self.print_and_log('Waiting for build to finish building python package...')
            self._wait_smooth_output()
            waiting_for_building.set()
            building_done.wait()
            
            self.print_and_log('Uploading python package built wheel file to GitHub release assets...')
            for item in listdir(f'{self.cache_dir}/dist'):
                if Path(item).suffix == '.whl':
                    break
            self._upload_github_asset(Path(f'{self.cache_dir}/dist/{item}'), 'application/octet')


            self.print_and_log('Uploading the built versions versions to the GitHub release...')

            if self.run_pyinstaller:
                self.print_and_log('Waiting for PyInstaller to finish...')
                self._wait_smooth_output()
                waiting_for_pyinstaller_bundling.set()
                pyinstaller_done.wait()

                self.print_and_log('Uploading bundled program to GitHub release assets...')
                self._upload_github_asset(Path(f'{self.cache_dir}/dist/{self.program_name}'), 'application/octet')

            if self.compile_command != None:
                self.print_and_log('Waiting for Nuitka to finish...')
                self._wait_smooth_output()
                waiting_for_compile_command.set()
                compile_command_done.wait()

                self.print_and_log('Creating archive of the compiled program...')
                make_archive(f'{self.cache_dir}/{self.program_name}-[nuitka]', 'zip', f'{self.cache_dir}/main.dist')

                self.print_and_log('Uploading compiled program to GitHub release assets...')
                self._upload_github_asset(Path(f'{self.program_name}-[nuitka].zip'), 'application/zip')


            if self.pypi_api_token:
                error_message = upload_package(f'{self.cache_dir}/dist', api_token=self.pypi_api_token)
                if error_message:
                    self.print_and_log(f'Failed to upload built files to PyPI. | Error: {error_message}', [255, 0, 0], 40)
                    self.revert_changes()
                else:
                    self.published_to_pypi = True


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

            if not self.pypi_api_token and self.environment_name and self.workflow_filename:
                publish_to_pypi = self.prompt_user('publish to PyPI')
                self.print_and_log('getting workflow and run id...')
                self.workflow = self.repo.get_workflow(self.workflow_filename)
                self.run_id = next(iter(self.workflow.get_runs())).id

                self.print_and_log('getting environment id and processing it...')
                self._process_environments('approved' if publish_to_pypi else 'rejected', 'Approved through Packer by user' if publish_to_pypi else 'Rejected through Packer by user')

                if publish_to_pypi:
                    self.published_to_pypi = True
                else:
                    self.revert_changes()


            self.print_and_log('New version released:', [0, 255, 0], end=' ')
            self.print_and_log(self.version, [149, 193, 148], end=' ')
            self.print_and_log('Hooray! \U0001F386', [0, 255, 0])
            if all_settings.desktop_notifications:
                send_notification('New version released!', f'Version {self.version} has been released successfully!')

            release_url = self.git_release.html_url
            if all_settings.open_gitHub_release:
                open_new_tab(release_url)
            if all_settings.copy_github_release_clipboard:
                copy(release_url)
                self.print_and_log('Copied GitHub release URL to clipboard', [0, 255, 0])
            else:
                self.print_and_log(f'Github release URL:', end=' ')
                self.print_and_log(release_url, [255, 105, 180])
            self.print_and_log(f'Social media post text has been saved to', end=' ')
            self.print_and_log(f'{data_dir}/social media post.md', [255, 105, 180], end=' ')
            self.print_and_log('You can use it to post on social media platforms')
            self.print_and_log(f'Log file has been saved to:', end=' ')
            self.print_and_log(str(log_path.absolute()), [255, 105, 180], end=' ')
            self.print_and_log('You can use it to check for any errors or warnings that occurred during the release process')

            if self.prompt_user('Do you want to revert', 'n'):
                self.revert_changes()


            self.print_and_log('Running post release clean up tasks...')
            
            self.print_and_log('Cleaning up cache...')
            rmtree(f'{self.cache_dir}/dist')
        
            if all_settings.auto_clear_cache and get_folder_size(Path(self.cache_dir)) > all_settings.cache_size_threshold:
                self.print_and_log(f'Deleting cache folder, over threshold', end=' [')
                self.print_and_log(format_size(all_settings.cache_size_threshold), [0, 0, 255], end='')
                self.print_and_log('] ...')
                rmtree(self.cache_dir)
        
            if all_settings.auto_clear_logs and get_folder_size(Path(log_dir)) > all_settings.logs_size_threshold:
                self.print_and_log(f'Deleting log files, over threshold', end=' [')
                self.print_and_log(format_size(all_settings.logs_size_threshold), [0, 0, 255], end='')
                self.print_and_log('] ...')
        
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
                    self.print_and_log(f'Removed {file}', [0, 255, 0])
        
            if self.compile_command != None:
                rmtree(f'{self.cache_dir}/main.dist')
                remove(f'{self.cache_dir}{self.program_name}-[nuitka].zip')
        
            self.print_and_log('Writing social media post text to a file...')
            with open(f'{data_dir}/social media post.md', 'w') as f:
                f.write(self.release_text)


            self.print_and_log('Adding changelog template for next version...')
            with open('CHANGELOG.md', 'w') as f:
                f.write(f'## [%new_version] - %date\n\n### Added\n\n### Changed\n\n### Fixed\n\n---\n\n{full_changelog}')
        
            self.print_and_log('Committing next version preparation and updating origin...')
            self.git_repo.index.add(['CHANGELOG.md'])
            self.prep_committed = self.git_commit('Prepared next version development branch')
            self.git_repo.remotes.origin.push()
        
            self.print_and_log('Cleaning up temporary files...')
            remove(self.chosen_description_path)
            remove(self.chosen_title_path)

            
            self.print_and_log('Updating metadata.json...')
            current_project_metadata['project size'] = project_size
            current_project_metadata['version size'] = version_size

            metadata[str(Path().absolute())] = current_project_metadata
            
            with open(metadata_path, 'w') as f:
                dump(metadata, f)

            for pattern in exclusions:
                if Path('build').match(pattern):
                    break
            else:
                self.print_and_log('Removing build directory created by python package building...')
                rmtree('build')
            
            self._wait_smooth_output()
        else:
            self.print_and_log('Canceled going further!')
            self.revert_changes()
    
    def revert_changes(self, exit: bool = True, wait: bool = True) -> None | NoReturn:
        '''Rollback the release process by removing the generated archive, deleting the uploaded Gofile copy and GitHub release when present, and resetting the Git repository to its previous state.'''

        if wait:
            self._wait_smooth_output()
        self.print_and_log('Reverting back to previous version...', [255, 255, 0], 30)

        if self.program_archive_path.exists():
            self.print_and_log('Removing archive...', [255, 255, 0])
            remove(self.program_archive_path)

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

        if hasattr(self, 'published_to_pypi') and self.published_to_pypi:
            self.print_and_log(f'I can\'t automatically yank the uploaded PyPI distribution.', [255, 255, 0], 30)
            self.print_and_log('Please head on over to:', end='')
            self.print_and_log(f'https://pypi.org/manage/project/{self.pypi_program_name}/releases/', [255, 105, 180], end=' ')
            self.print_and_log('and do it yourself through their web UI.')

            self.print_and_log('Updating pyproject.toml version...')
            with open('pyproject.toml', 'r', encoding='utf-8') as f:
                pyproject_config = tomlkit.load(f)

            if self.version.count('.') == 2:
                new_version = f'{self.version}.post1'
            else:
                for i, char in enumerate(self.version, self.version.find('-') + 1):
                    if char.isdigit():
                        new_version = f'{self.version[:i]}{int(self.version[i]) + 1}{self.version[i + 1:]}'
            if 'project' in pyproject_config:
                pyproject_config['project']['version'] = new_version
            elif 'tool' in pyproject_config and 'poetry' in pyproject_config['tool']:
                pyproject_config['tool']['poetry']['version'] = new_version
            else:
                pyproject_config['version'] = new_version
            
            with open('pyproject.toml', 'w', encoding='utf-8') as f:
                tomlkit.dump(pyproject_config, f)

            self.print_and_log(f'Committing the version bump to', end=' ')
            self.print_and_log(new_version, [0, 0, 255], end=' ')
            self.print_and_log('after failed release...')
            self.git_repo.index.add(['pyproject.toml'])
            self.git_commit('Bumped version after failed release')
        else:
            if hasattr(self, 'run_id'):
                self._process_environments('rejected', 'Rejected through Packer\'s revert changes method')

        if wait:
            self._wait_smooth_output()
        if exit:
            self._exit(1, wait)

    def git_commit(self, commit_message: str) -> bool:
        '''
        Commits the staged changes in the git repository with the provided commit message. It first attempts to create a signed commit, and if that fails, it falls back to an unsigned commit.

        :param commit_message: The message to use for the commit.
        :type commit_message: str
        :return: True if the commit was successful, False otherwise.
        :rtype: bool
        '''

        try:
            self.git_repo.git.commit('-S', '-m', commit_message)
            return True
        except GitCommandError:
            try:
                    self.print_and_log('Fallback to unsigned commit...', [255, 255, 0], 30)
                    self.git_repo.git.commit('-m', commit_message)
                    return True
            except GitCommandError as e:
                self.print_and_log(f'Something went wrong while committing: {e}', [255, 0, 0], 40)
                self.revert_changes()
                return False

    def queue_prompt_edit_text(self, edit_text: str, file_path: Path = None) -> str:
        '''
        Queues the provided text for editing and waits for the edited text to be returned.
        
        :param edit_text: The text to be edited.
        :type edit_text: str
        :param file_path: Not used in this method, only used for compatibility with the _input_via_text_editor function.
        :type file_path: Path, optional
        :return: The edited text returned from the queue.
        :rtype: str
        '''

        self.input_queue.put({'edit text': edit_text})
        return self.output_queue.get()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(HTTPError)
    )
    def _process_environments(self, state: Literal['approved', 'rejected'] = 'approved', comment: str = 'Approved through Packer'):
        process_deployed_environments(self.GITHUB_REPO_TOKEN, self.github_repo_url, self.run_id, find_environments(self.GITHUB_REPO_TOKEN, self.github_repo_url, self.run_id, self.environment_name), state, comment)
        
    def _exit(self, code: int = None, wait: bool = True):
        if wait:
            self._wait_smooth_output()
        sys.exit(code)

    def _wait_smooth_output(self):
        if hasattr(self, 'buffer_queue'):
            self.buffer_queue.join()
    
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

        self.print_and_log(f'Reverting HEAD', end=' ')
        self.print_and_log(f'{commit_count}', [0, 0, 255], end=' ')
        self.print_and_log(f'commit(s) back...')
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
                    all_settings.smooth_output_speed / (self.buffer_queue.qsize() + 1),
                    text['end']
                )
            except Exception as e:
                print_colored_text('A problem occurred in smooth print output background thread.', [255, 0, 0])
                print_colored_text(f'Most likely because of malformed text from the buffer. Error:', [0, 255, 0], end=' ')
                print_colored_text(str(e))
                self.log_action(f'A problem occurred in smooth print output background thread. | Error: {e}', 40)
                self.revert_changes(wait=False)
            finally:
                self.buffer_queue.task_done()

    def _print_and_log(self, text: str, color: Optional[Sequence[int]] | None = None, level: int = 20, end: str = '\n'):
        '''Prints the text and logs it to the packer log file.
        
        :param text: The text to print and log.
        :type text: str
        :param color: The color to use for printing, default is None (default terminal color).
        :type color: Optional[Sequence[int]] | None
        :param level: The logging level to use, default is 20 [INFO].
        :type level: int
        :param end: The string appended after the last value, default a newline.
        :type end: str
        '''

        if color:
            print_colored_text(text, color, end=end)
        else:
            print(text, end=end)
        self._process_partial_output(text + end, level)


    def _process_partial_output(self, text: str, level: int):
        '''
        Processes the provided text for partial output and logs it to the packer log file. If the text contains a newline character, it is logged immediately. Otherwise, it is stored in a buffer for later logging.

        :param text: The text to process for partial output.
        :type full_text: str
        :param level: The logging level to use
        :type level: int
        '''

        if '\n' in text:
            text = f'{''.join(self.print_message_parts)}{text}'
            self.print_message_parts.clear()
            self.log_action(text, level)
        else:
            self.print_message_parts.append(text)
        
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
        
    def _get_queue_input(self, question: str, default: str | int = 'y') -> bool | None:
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

        self._wait_smooth_output()
        answer = simple_prompt_retries(question, default)
        self.log_action(f'Requested user input to "{question}" | Answer = "{answer}"')
        return answer

    def _log_and_output_queue(self, text, color: Optional[Sequence[int]] | None = None, level: int = 20, end: str = '\n'):
        '''Puts the text in the output queue and logs it to the packer log file.
        
        :param text: The text to output to the queue and log.
        :type text: str
        :param color: The color to use for the text, default is None (default environment color).
        :type color: Optional[Sequence[int]] | None
        :param level: The logging level to use, default is 20 [INFO].
        :type level: int
        :param end: The string appended after the last value, default a newline.
        :type end: str
        '''

        self.output_queue.put({'text': text, 'color': color, 'end': end})
        self._process_partial_output(text + end, level)

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

        # setup
        def print_with_background(text):
            print_bg_colored_text(text, all_settings.stream_background_color, flush=True)
        output_text = print_with_background if all_settings.stream_background_color else print
        done = threading.Event()


        def thread_function(done: threading.Event):
            process = Popen(cmd, stdout=PIPE, stderr=PIPE, text=True)

            for text in process.stdout:
                text = text.rstrip('\n')
                self.log_action(text)
                if waiting.is_set():
                    output_text(text, force=True)
                    clear_lines(lines_used(text, get_terminal_size().columns), clear_formatting=True)

            return_code = process.wait()
            if return_code != 0:
                self.print_and_log(f'{cmd} failed with exit code: {return_code} | stderr: {process.stderr}', [255, 0, 0], 40)
                self.revert_changes()
            done.set()

        threading.Thread(target=thread_function, args=[done], daemon=True).start()

        return done