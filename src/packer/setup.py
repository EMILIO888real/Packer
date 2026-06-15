
from getpass import getpass, getuser
from importlib import import_module
from os import chdir, mkdir
from pathlib import Path
from shutil import rmtree
from subprocess import CalledProcessError, run
from textwrap import dedent
from typing import Sequence
from json import dump
from git import Repo
from github import Auth, Github
from multiprocessing import Process, Event
from sys import exit, platform, builtin_module_names
from re import match
from keyword import iskeyword
from platformdirs import user_documents_dir

from packer.custom_modules.et import init_logger, print_colored_text, simple_prompt, stripped_input, tree, read_json, format_version_text
from packer.config import packer_version
from packer.custom_modules.etf import print_list

logger = init_logger('packer setup', 'EMILIO')

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

def print_and_log(text: str, level: int = 20, color: Sequence[int] = [255, 255, 255], end: str = '\n') -> None:
    print_colored_text(text, color, end=end)
    logger.log(level, text)

def create_venv(created_venv) -> None:
    print_and_log('Creating a python virtual environment...')
    run(['python', '-m', 'venv', '.venv'])
    created_venv.set()

def main(project_directory: str | Path, author_name: str, program_name: str, github_pat: str = None, github_repo_url: str = None, overwrite_existing: bool = False) -> str:
    '''Set up a new project scaffold and initialize its local Git history.

    The generated layout currently looks like this:

    ```text
    project_directory/
    ├── src/
    │   └── program_name/
    │       ├── __init__.py
    │       ├── core.py
    │       ├── main.py
    │       ├── config.py
    │       ├── paths.py
    │       ├── assets/
    │       │   ├── exceptions.py
    │       │   ├── integrity.json
    │       │   └── version.json
    │       └── ui/
    ├── docs/
    │   ├── SETTINGS.md
    │   ├── CONFIGURATION.md
    │   ├── CUSTOMIZATION.md
    │   └── ROADMAP.md
    ├── tests/
    ├── dev/
    │   └── TODO.md
    ├── .github/
    │   └── workflows/
    │       └── build.yaml
    ├── .gitignore
    ├── CHANGELOG.md
    ├── LICENSE
    ├── README.md
    ├── main.spec
    └── pyproject.toml
    ```

    The function also initializes a Git repository, creates an initial commit,
    and optionally creates and pushes a remote repository on GitHub.

    :param project_directory: The absolute path to the project directory. If it already exists, the user will be prompted to delete it and create a new one.
    :type project_directory: str | Path
    :param author_name: The name of the author of the program, used in the LICENSE file and the pyproject.toml file.
    :type author_name: str
    :param program_name: The name of the program, used for the project directory, the source code directory, and the pyproject.toml file.
    :type program_name: str
    :param github_pat: The GitHub Personal Access Token (PAT) used to create a remote repository on GitHub. If not provided, the remote repository will not be created.
    :type github_pat: str, optional
    :param github_repo_url: The URL of the GitHub repository in the format "username/repo". If not provided, the repository will be created with the same name as the program. This parameter is only used if github_pat is provided.
    :type github_repo_url: str, optional
    :param overwrite_existing: Overwrite the existing folder if it exists, defaults to False.
    :type overwrite_existing: bool, optional
    :return: The URL of the created GitHub repository.
    :rtype: str
    '''

    program_name = program_name.lower()
    root_dir = f'src/{program_name}'

    if Path(project_directory).exists():
        if overwrite_existing:
            print_and_log('Deleting existing directory...')
            rmtree(project_directory)
        else:
            print_and_log('Aborting setup...')
            return

    print_and_log('Creating project directory...')
    mkdir(project_directory)

    if Path().cwd() != Path(project_directory):
        print_and_log('Changing directory')
        chdir(project_directory)

    created_venv = Event()
    Process(target=create_venv, args=[created_venv]).start()

    print_and_log('Creating source code directory...')
    mkdir(f'src')
    mkdir(f'src/{program_name}')
    mkdir(f'{root_dir}/assets')
    mkdir('docs')
    mkdir('tests')
    mkdir('dev')
    mkdir('.github')
    mkdir('.github/workflows')
    mkdir(f'{root_dir}/ui')

    print_and_log('Creating core.py...')
    with open(f'{root_dir}/core.py', 'w') as f:
        f.write(dedent(f'''\
            def {program_name}():
                print('Hello, world!')
        '''))

    print_and_log('Creating exceptions.py...')
    with open(f'{root_dir}/assets/exceptions.py', 'w') as f:
        f.write(dedent(f'''\
            from datetime import datetime
            from os import mkdir
            from pathlib import Path
            import sys
            from traceback import format_exception
            from json import dump
            from shutil import make_archive, copy, rmtree
            from {program_name}.config import {program_name}_version
            from {program_name}.paths import log_path, error_report_path, log_dir


            def global_exception_handler(exc_type, exc_value, exc_traceback):

                global log_path

                """
                Global exception handler for uncaught exceptions.

                :param exc_type: The type of the exception being handled
                :param exc_value: The exception value (the actual exception object)
                :param exc_traceback: The traceback object containing the stack trace
                """

                if issubclass(exc_type, KeyboardInterrupt) or issubclass(exc_type, SystemExit): # Ignore any errors when quitting the program.
                    return
                
                print(f'An error has occurred: Type: {{exc_type}} | Value: {{exc_value}}\\nPlease report this to a developer via Discord or Github!')

                print('Generating an error report...')

                if not log_path.exists():
                    log_path = None

                error_report = {{'program version': {program_name}_version,
                                'platform': sys.platform,
                                'python version': sys.version,
                                'human notes': input('Could you explain a bit more about the error? What, How or When did the error happen?\\nInput: '),
                                'traceback': ''.join(format_exception(exc_type, exc_value, exc_traceback)),
                                'associated log file': str(log_path)}}


                with open(error_report_path, 'a') as f:
                    dump(error_report, f)
                    f.write('\\n') # For the next errors, so it's possible to compound them.

                print('Creating issue archive...')
                tmp_dir = f'{{log_dir}}/temp dir'
                if not Path(tmp_dir).exists():
                    mkdir(tmp_dir)
                copy(error_report_path, f'{{tmp_dir}}/{{error_report_path.name}}')
                if log_path is not None:
                    copy(log_path, f'{{tmp_dir}}/{{log_path.name}}')
                make_archive(f'{{log_dir}}/issue {{datetime.date(datetime.now())}}', 'zip', tmp_dir)
                rmtree(tmp_dir)

                print(f'error report generated at: "{{error_report_path.absolute()}}"')
                print(f'Created an issue archive with the error report and log associated with it: "{{log_dir}}/issue {{datetime.date(datetime.now())}}.zip".\\nPlease submit this to a developer!')
                sys.exit(1)
        '''))
    
    print_and_log('Creating config.py')
    with open(f'{root_dir}/config.py', 'w') as f:
        f.write(dedent(f'''
            import json

            from {program_name}.paths import assets_dir
                       
            with open(f'{{assets_dir}}/version.json') as f:
                {program_name}_version = format_version_text(json.load(f))
        '''))

    print_and_log('Creating build.yaml file...')
    with open(f'.github/workflows/build.yaml', 'w') as f:
        f.write(dedent(f'''\
            name: Build Windows EXE for Release

            on:
              release:
                types: [created]

            permissions:
              contents: write

            jobs:
              build:
                runs-on: windows-latest
                # Opt-in to Node.js 24 as recommended by GitHub
                env:
                  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true
                steps:
                  - uses: actions/checkout@v4

                  - name: Set up Python
                    uses: actions/setup-python@v5
                    with:
                      python-version: "3.12"

                  - name: Install dependencies
                    run: pip install .

                  - name: Install PyInstaller
                    run: pip install pyinstaller

                  - name: Build executable
                    run: python -m PyInstaller main.spec

                  - name: Upload to GitHub Release
                    uses: softprops/action-gh-release@v2
                    with:
                      files: dist/{program_name}.exe
        '''))
    
    print_and_log('Creating __init__.py file...')
    with open(f'{root_dir}/__init__.py', 'w') as f:
        f.write(dedent('''\
            # import here object that users will import.

            __all__ = [] # populate this list with str names of all the objects.
        '''))

    print_and_log('Creating paths.py file...')
    with open(f'{root_dir}/paths.py', 'w') as f:
        f.write(dedent(f'''\
            from datetime import datetime
            from importlib import resources
            from pathlib import Path
            from platformdirs import user_cache_dir, user_config_dir, user_data_dir, user_log_dir

            root_dir = resources.files('{program_name}')
            assets_dir = root_dir.joinpath('assets')
            config_dir = user_config_dir('{program_name}', '{author_name}', ensure_exists=True)
            log_dir = user_log_dir('{program_name}', '{author_name}', ensure_exists=True)
            log_path = Path(f'{{log_dir}}/{{datetime.date(datetime.now())}}.log')

            error_report_path = Path(f'{{log_dir}}/error report {{datetime.date(datetime.now())}}.json')
            if not Path(error_report_path).exists():
                with open(error_report_path, 'w') as f:
                    f.write('')

            data_dir = user_data_dir('{program_name}', '{author_name}', ensure_exists=True)
            cache_dir = user_cache_dir('{program_name}', '{author_name}', ensure_exists=True)
            '''))

    print_and_log('Creating main.py file...')
    with open(f'{root_dir}/main.py', 'w') as f:
        f.write(dedent(f'''\
            from {program_name}.paths import assets_dir
            from {program_name}.core import {program_name}


            def main():
                {program_name}()


            if __name__ == '__main__':
                main()
        '''))

    print_and_log('Creating version.json file...')
    with open(f'{root_dir}/assets/version.json', 'w') as f:
        f.write('{"major": 0, "minor": 0, "patch": 0}')

    print_and_log('Creating an integrity file...')
    with open(f'{root_dir}/assets/integrity.json', 'w') as f:
        dump({'CWD': tree(f'src/{program_name}')}, f)

    print_and_log('Starting outside src directory build process..')

    print_and_log('Creating a TODO.md file...')
    with open('dev/TODO.md', 'w') as f:
        f.write(dedent('''\
            # TODO

            - [ ] Write the README.md file
            - [ ] Write the CHANGELOG.md file
            - [ ] Write the ROADMAP.md file
            - [ ] Write the pyproject.toml file
            - [ ] Check and update the .gitignore if necessary
            - [ ] Remove the dist directory with the test executable
        '''))

    print_and_log('Creating a SETTINGS.md file...')
    with open('docs/SETTINGS.md', 'w') as f:
        f.write(dedent(f'''\
            # SETTINGS

            This file contains detailed information on user-configurable settings for {program_name}.

            ## Setting 1

            Description of setting 1.

            ## Setting 2

            Description of setting 2.

            ## Setting 3

            Description of setting 3.
        '''))

    print_and_log('Creating a CONFIGURATION.md file...')
    with open('docs/CONFIGURATION.md', 'w') as f:
        f.write(dedent(f'''\
            # CONFIGURATION

            This file contains detailed information on game configuration parameters for {program_name}.

            ## Parameter 1

            Description of parameter 1.

            ## Parameter 2

            Description of parameter 2.

            ## Parameter 3

            Description of parameter 3.
        '''))

    print_and_log('Creating a CUSTOMIZATION.md file...')
    with open('docs/CUSTOMIZATION.md', 'w') as f:
        f.write(dedent(f'''\
            # CUSTOMIZATION

            This file contains detailed information on how to add custom assets and important notes about settings for {program_name}.

            ## Custom Asset 1

            Description of custom asset 1.

            ## Custom Asset 2

            Description of custom asset 2.

            ## Custom Asset 3

            Description of custom asset 3.
        '''))

    print_and_log('Creating a pyproject.toml file...')
    with open('pyproject.toml', 'w') as f:
        f.write(dedent(f'''\
            [build-system]
            requires = ["setuptools>=61.0"]
            build-backend = "setuptools.build_meta"

            [project]
            name = "{program_name}"
            version = "0.0.0"
            description = "A short description about your program: {program_name}."
            readme = "README.md"
            license = "MIT"
            dependencies = []

            [tool.setuptools]
            include-package-data = true
            package-dir = {{"" = "src"}}

            [tool.setuptools.packages.find]
            where = ["src"]

            [tool.setuptools.package-data]
            {program_name} = ["assets/*"]

            [project.scripts]
            {program_name} = "{program_name}.main:main"
        '''))

    print_and_log('Creating CHANGELOG.md...')
    with open('CHANGELOG.md', 'w') as f:
        f.write(dedent('''\
            ## [%new_version] - %date

            ### Added

            ### Changed

            ### Fixed

        '''))

    print_and_log('Creating README.md...')
    with open('README.md', 'w') as f:
        f.write(dedent(f'''\
            # {program_name.capitalize()}

            A short description of the project.

            ## Contents

            - [Installation](#installation)
            - [Binary Downloads](#binary-downloads)
            - [Usage](#usage)
            - [Configuration](#configuration)
              - [Settings](#settings)
              - [Config](#config)
              - [Extra customization](#extra-customization)
            - [Extra notes](#extra-notes)
            - [Warning](#warning)
            - [Features](#features)
            - [Feedback and Suggestions](#feedback-and-suggestions)
            - [Honorable mentions](#honorable-mentions)
            - [Changelog](#changelog)
            - [In future updates](#in-future-updates)

            ## Installation

            Available via:

            * **GitHub Releases:** [GitHub Releases](%release_url)
            * **Third-party website (GoFile):** [Archive](%gofile_url)

            ### Binary Downloads

            When downloading, please choose the correct build for your operating system:

            | File Name | Platform | Description |
            | --- | --- | --- |
            | `{program_name}` | Linux/macOS | Executable for Unix-based systems. |
            | `{program_name}.exe` | Windows | Executable for Windows systems. |

            ### To install:

            * **GitHub:**
              Download the appropriate binary for your system from the [Releases page](%release_url).
            * **Third-party website (GoFile):**
              Head to the website [Archive](%gofile_url) and download the specific archive with the appropriate version.

            After installing, continue following instructions in this README.

            ## Usage

            After installing the project, you can run it from the command line with the entry point defined in your pyproject.toml file.

            ### Basic example

            ```bash
            python -m {program_name}.main
            ```

            If you installed the package in your environment, you can also run:

            ```bash
            {program_name}
            ```

            ## Configuration

            ### Settings

            See [SETTINGS.md](docs/SETTINGS.md) for detailed information on user-configurable settings.

            ### Config

            See [CONFIGURATION.md](docs/CONFIGURATION.md) for detailed information on game configuration parameters.

            ### Extra customization

            See [CUSTOMIZATION.md](./docs/CUSTOMIZATION.md) for detailed information on how to add custom assets and important notes about settings.

            ## Extra notes

            Any extra notes about the project.

            ## Warning

            Any warnings about the project.

            ## Features

            List of features in the project.

            ## Feedback and Suggestions

            Instructions on how to provide feedback and suggestions for the project.

            ## Honorable mentions

            Acknowledgment of any contributors or resources that were helpful in the development of the project.

            ## Changelog

            See the full history in [CHANGELOG.md](./CHANGELOG.md).

            ## In future updates

            See [ROADMAP.md](./docs/ROADMAP.md) for planned features and improvements.
        '''))

    print_and_log('Creating ROADMAP.md...')
    with open('docs/ROADMAP.md', 'w') as f:
        f.write(dedent('''\
            # Roadmap

            ## Version 0.0.0

            - [ ] Initial release

            ## Version 0.2.0

            - [ ] Add new features
            - [ ] Fix bugs

            ## Version 1.0.0

            - [ ] Stable release with all planned features implemented and tested.
        '''))

    print_and_log('Creating an MIT license...')
    with open('LICENSE', 'w') as f:
        f.write(f'MIT License\n\nCopyright (c) 2025 {author_name}\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n')

    print_and_log('Creating .spec file...')
    with open(f'main.spec', 'w') as f:
        f.write(dedent(f'''\
            # -*- mode: python ; coding: utf-8 -*-

            a = Analysis(
                ['src/{program_name}/main.py'],
                pathex=['src'],
                binaries=[],
                datas=[
                    ('src/{program_name}/assets', '{program_name}/assets'),
                ],
                hookspath=[],
                hooksconfig={{}},
                runtime_hooks=[],
                excludes=[],
                noarchive=False,
            )

            pyz = PYZ(a.pure)

            exe = EXE(
                pyz,
                a.scripts,
                a.binaries,
                a.datas,
                [],
                name='{program_name}',
                debug=False,
                bootloader_ignore_signals=False,
                strip=False,
                upx=True,
                console=True,
                onefile=True
            )
        '''))
        
    print_and_log('Verify main.spec via running it...')

    verify_result = run([f'pyinstaller', 'main.spec'], capture_output=True)

    print_and_log(f'Ran command: pyinstaller main.spec\nstdout: {verify_result.stdout.decode()}\nstderr: {verify_result.stderr.decode()}')


    print_and_log('Removing build directory...')
    rmtree('build')

    print_and_log(f'We will start bundled version up for you automatically. It should just print out in the black box "Hello world!"')
    try:
        output = run([f'./dist/{program_name}{'.exe' if platform == 'win32' else ''}'], capture_output=True, text=True, check=True).stdout.rstrip('\n')
        print_and_log(f'Successfully ran the build. The output: {output}', end=' ')
        print_and_log(f'[{'valid' if output == 'Hello, world!' else 'invalid'}]', 30, [0, 255, 0] if output == 'Hello, world!' else [255, 0, 0])
    except CalledProcessError as e:
        print_and_log(f'Something went wrong in the built version: {e}', 30, [255, 0, 0])

    print_and_log('Removing dist directory...')
    #rmtree('dist')

    repo = Repo.init(project_directory)

    print_and_log('Creating .gitignore file...')
    with open('.gitignore', 'w') as f:
        f.write(dedent(f'''\
            # Virtual Environments and settings
            .venv
            .vscode

            # Developer related stuff
            tests
            dev
            **/__pycache__/
            *.py[cod]

            # Distribution / Packaging
            *.egg-info/
        '''))

    print_and_log('Waiting for .venv to finish creating...')
    created_venv.wait()

    print_and_log('Staging files for initial commit...')
    repo.git.add(all=True)
    print_and_log('Committing files...')
    repo.index.commit(f'Initial commit\nProject structure created by packer\'s setup.py v{packer_version}')

    if github_pat:
        print_and_log('Creating remote repository on GitHub...')
        github_repo_url = Github(auth=Auth.Token(github_pat)).get_user().create_repo(
            program_name,
            description=f'Temporary description, this repo was created by packer\'s setup.py v{packer_version}',
            private=False
        ).clone_url

    if github_repo_url:
        print_and_log('Creating remote repository...')
        origin = repo.create_remote('origin', github_repo_url)

        # This ensures 'git push' or 'git pull' knows where to go by default
        print_and_log('Registering the master branch with the remote repository...')
        with repo.config_writer() as writer:
            writer.set_value('branch "master"', 'remote', 'origin')
            writer.set_value('branch "master"', 'merge', 'refs/heads/master')

        print_and_log('Pushing initial commit to remote repository...')
        try:
            origin.push()
        except Exception as e:
            print_and_log(f'Warning: Push failed with error: {e}', 30, [255, 165, 0])
            print_and_log('You can push manually with: git push -u origin master', 20, [255, 165, 0])
    
    print_and_log(f'Project setup complete!\nYou can check out the log at {logger.handlers[0].baseFilename}')
    
    return github_repo_url.lstrip('https://github.com/') if github_repo_url is not None else None

def tui() -> tuple[str]:
    '''
    Interactive command-line user interface for collecting project setup information.

    This function prompts the user for various project details such as the program name,
    author name, and GitHub Personal Access Token (PAT). It ensures that required
    information is provided and returns the collected data as a tuple.

    :return: A tuple containing:
        - program_name (str): The name of the program.
        - author_name (str): The name of the author.
        - github_pat (str or None): The GitHub PAT if provided, otherwise None.
    :rtype: tuple[str]
    '''

    program_name = input('1. Program name: ')

    while (program_name[:1].isdigit()) or (program_name.count(' ') > 0) or (not match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', program_name)) or (iskeyword(program_name)) or (program_name in builtin_module_names or (check_module_conflict(program_name))):
        print('Name isn\'t acceptable since it doesn\'t follow restrictions:')
        print_list(['Can\'t start with a number', 'Can\'t contain any spaces', 'Can\'t contain any special characters (Alphanumeric characters and underscores only)', 'Can\'t be a Python keyword', 'Can\'t be a built-in module name', 'Can\'t be in conflict with other existing modules'], start='\t* ')
        program_name = input('Reenter the program name: ')


    default_project_dir = f'{user_documents_dir()}/{program_name}'

    project_directory = input(f'2. Project directory (absolute path, default to: {default_project_dir}): ')
    if project_directory == '':
        project_directory = default_project_dir

    if Path(project_directory).exists():
        if not simple_prompt('Directory already exists, overwrite it', 'n'):
            print('Aborting setup')
            return

    project_directory.rstrip('/')

    github_pat = getpass('3. Github personal access token (with Administration permissions): ').strip() or None
    github_repo_url = not github_pat and stripped_input('4. Github repo url (username/repo): ') or None

    default_name = getuser()

    author_name = input(f'5. Author name of the program [default to: {default_name}]: ')
    if author_name == '':
        author_name = default_name

    return (project_directory, author_name, program_name, github_pat, github_repo_url)

if __name__ == '__main__':
    print('You will need to configure [4-5] settings.')
    try:
        print(f'github repo url: {main(*tui(), overwrite_existing=True)}')
    except KeyboardInterrupt:
        exit()