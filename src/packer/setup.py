
from datetime import datetime
from getpass import getuser
from importlib import import_module
from os import chdir, listdir, mkdir
from pathlib import Path
from shutil import copy, rmtree
from subprocess import PIPE, STDOUT, CalledProcessError, run, Popen
from textwrap import dedent
from typing import Sequence
from json import dump
from git import Repo
from github import Auth, Github, GithubException
from multiprocessing import Process, Event
from sys import exit, platform, builtin_module_names
from re import match
from keyword import iskeyword

from packer.utils import pip_install
from packer.custom_modules.et import init_logger, tree
from packer.custom_modules.etf import print_colored_text, simple_prompt, stripped_input
from packer.config import packer_version, _getpass
from packer.custom_modules.etf import print_list
from packer.paths import download_dir, documents_dir

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

def print_and_log(text: str, level: int = 20, color: Sequence[int] | None = None, end: str = '\n') -> None:
    if color:
        print_colored_text(text, color, end=end)
    else:
        print(text, end=end)
    logger.log(level, text)

def _create_venv(created_venv) -> None:
    print_and_log('Creating a python virtual environment...')
    run(['python', '-m', 'venv', '.venv'])
    created_venv.set()

def main(project_directory: str | Path, author_name: str, program_name: str, github_pat: str = None, github_repo_url: str = None,
         overwrite_existing: bool = False, gofile_code: str | None = None, license_type: str | None = 'MIT', github_auth: bool = False,
         use_pyinstaller: bool = True) -> str:
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
    :param gofile_code: The code for the GoFile folder where the project will be uploaded, defaults to None.
    :type gofile_code: str, optional
    :param license_type: The type of license to use for the project, defaults to 'MIT'.
    :type license_type: str, optional   
    :param github_auth: Whether to use GitHub authentication for pushing to the remote repository, defaults to False.
    :type github_auth: bool, optional
    :param use_pyinstaller: Whether to add PyInstaller related files and build process, defaults to True.
    :type use_pyinstaller: bool, optional
    :return: The URL of the created GitHub repository, if there is one
    :rtype: str | None
    '''

    root_dir = f'src/{program_name}'

    if Path(project_directory).exists():
        if overwrite_existing:
            print_and_log('Deleting existing directory...')
            rmtree(project_directory)
        else:
            print_and_log('Aborting setup...', 30)
            return github_repo_url.lstrip('https://github.com/')

    print_and_log('Creating project directory...')
    mkdir(project_directory)

    if Path().cwd() != Path(project_directory):
        print_and_log('Changing directory')
        chdir(project_directory)

    created_venv = Event()
    Process(target=_create_venv, args=[created_venv]).start()

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

    print_and_log('Creating utils.py...')
    with open(f'{root_dir}/utils.py', 'w') as f:
        f.write(dedent(f'''\
        '''))

    print_and_log('Creating core.py...')
    with open(f'{root_dir}/core.py', 'w') as f:
        f.write(dedent(f'''\
            def {program_name}():
                print('Hello, world!')
        '''))

    print_and_log('Creating config.py')
    with open(f'{root_dir}/config.py', 'w') as f:
        f.write(dedent(f'''
            from json import load

            from {program_name}.paths import assets_dir
                       
            with open(f'{{assets_dir}}/version.json') as f:
                {program_name}_version = '0.1.0' # You should replace this with a function to get the version from the json file or something, et has one if you want.
        '''))

    if not use_pyinstaller:
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

            - [ ] Update the README.md file, especially the Github and GoFile URL, if they aren't complete, replace None with the required info, for Github username/repo. And for GoFile folder URL
            - [ ] Update the CHANGELOG.md file, if not using packer's change.py
            - [ ] Update the ROADMAP.md file
            - [ ] Update the pyproject.toml file
            - [ ] Check and update the .gitignore if necessary
            - [ ] Checkout docs folder and remove or update the files that will be in use
            - [ ] Remove the paths.py file, if you won't need user tied paths to your software, *useful to remove for a library for example*
            - [ ] Update the main `__init__.py` module if you are going to have your python package importable
            - [ ] Remove the `UI` folder if you don't plan on building UI for your package, *useful to remove for a library for example*
            - [ ] Update the Github's repository settings or other fields, for example the temporary description created by Packer, recommended to use the same short description that you use in your pyproject.toml file
            - [ ] Update GoFile folder properties like the description or other things
                       
            ## Tips
            
            Some tips on how to maximize this project layout for your python packages.

            - Write you core or main logic of your project in core.py as individual python objects even if you aren't going to utilize them in multiple places or multiple times, since you can import them from in the tests folder and run unit tests or other test isolating individual pieces of you project.
            - You should try to leave main.py as small as possible, splitting your projects functionality into as many files as possible, if you got UI's create files and write them in the `UI` folder, other logic that doesn't quite fit with core.py then a new module just for it and if you got extra python objects that might come in handy in other projects as well, write them in utils.py and maybe in the future create a new project by moving utils as core.py in the new project, you can install your later projects as dependencies of these projects by adding an entry as such in the `pyproject.toml` file:
            
            ```toml
            dependencies = [
                "$program_name @ git+https://github.com/$username/$program_name.git"
            ]
            ```
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
            license = "{license_type}"
            dependencies = [
                "platformdirs"
            ]

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
            # {program_name}

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

            * **GitHub Releases:** [GitHub Releases](https://github.com/{github_repo_url if github_repo_url else None}/releases/)
            * **Third-party website (GoFile):** [Archive](https://gofile.io/d/{gofile_code if gofile_code else None})

            ### Binary Downloads

            When downloading, please choose the correct build for your operating system:

            | File Name | Platform | Description |
            | --- | --- | --- |
            | `{program_name}` | Linux/macOS | Executable for Unix-based systems. |
            | `{program_name}.exe` | Windows | Executable for Windows systems. |

            ### To install:

            * **GitHub:**
              Download the appropriate binary for your system from the [Releases page](https://github.com/{github_repo_url if github_repo_url else None}/releases/).
            * **Third-party website (GoFile):**
              Head to the website [Archive](https://gofile.io/d/{gofile_code if gofile_code else None}) and download the specific archive with the appropriate version.

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

    if license_type:
        g = Github()

        try:
            license_text = g.get_license(license_type).body.replace('[year]', str(datetime.now().year)).replace('[fullname]', author_name)
            print_and_log(f'Creating an {license_type} license...')
            with open('LICENSE', 'w') as f:
                f.write(license_text)
        except GithubException:
            print_and_log(f'Couldn\'t fetch {license_type} license from GitHub, please ensure the name is correct. | Error: {e}', 40)

    if not use_pyinstaller:
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
        
        process = Popen([f'pyinstaller', 'main.spec'], stdout=PIPE, stderr=STDOUT, text=True)

        for text in process.stdout:
            print_and_log(text.rstrip('\n'))

        print_and_log('Removing build directory...')
        rmtree('build')

        successfully_built = False
        print_and_log(f'We will start bundled version up for you automatically. It should just print out in the black box "Hello world!"')
        try:
            output = run([f'./dist/{program_name}{'.exe' if platform == 'win32' else ''}'], capture_output=True, text=True, check=True).stdout.rstrip('\n')
            print_and_log(f'Successfully ran the build. The output: {output}', end=' ')
            successfully_built = output == 'Hello, world!'
            print_and_log(f'[{'valid' if successfully_built else 'invalid'}]', 30, [0, 255, 0] if successfully_built else [255, 0, 0])
        except CalledProcessError as e:
            print_and_log(f'Something went wrong in the built version: {e}', 30, [255, 0, 0])

        if not successfully_built:
            if listdir('dist') != []:
                executable_name = f'{program_name}'
                if platform == 'win32':
                    executable_name += '.exe'

                copy(f'dist/{executable_name}', f'{download_dir}/{executable_name}')
                print_and_log('Copied the broken executable to your downloads directory for your inspection', 30)
            else:
                print_and_log('Failed to create the executable entirely, skipping copying', 40)

        print_and_log('Removing dist directory...')
        rmtree('dist')

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

    print_and_log('Installing platformdirs package into venv')
    pip_install(['platformdirs'])

    print_and_log('Installing your project in editable mode in .venv...')
    python_exe_path = ('.venv/Scripts/python.exe'
            if platform == 'win32'
            else '.venv/bin/python')
    run([python_exe_path, '-m', 'pip', 'install', '-e', '.'])

    print_and_log('Staging files for initial commit...')
    repo.git.add(all=True)
    print_and_log('Committing files...')
    repo.index.commit(f'Initial commit\nProject structure created by packer\'s setup.py v{packer_version}')

    master_branch = repo.active_branch

    print_and_log('Creating a new branch and switching to it...')
    repo.create_head('development').checkout()

    if github_pat:
        print_and_log('Creating remote repository on GitHub...')
        github_repo_url = Github(auth=Auth.Token(github_pat)).get_user().create_repo(
            program_name,
            description=f'Temporary description, this repo was created by packer\'s setup.py v{packer_version}',
            private=False
        ).clone_url

    if github_repo_url:
        if github_auth:
            print_and_log('Updating Github origin URL with PAT...')
            authenticated_url = (
            f"https://x-access-token:{github_pat}@github.com/"
            f"{github_repo_url.removeprefix('https://github.com/')}"
            )

        print_and_log('Creating remote repository...')
        if github_auth:
            repo.create_remote('origin', authenticated_url)
        else:
            repo.create_remote('origin', github_repo_url)

        try:
            print_and_log(f'Pushing {master_branch.name} branch to origin...')
            repo.git.push('-u', 'origin', master_branch.name)

            print_and_log('Pushing the development branch to origin...')
            repo.git.push('-u', 'origin', 'development')
        except Exception as e:
            print_and_log(f'Warning: Push failed with error: {e}', 30, [255, 165, 0])
            print_and_log(f'You can push manually with: git push -u origin {master_branch.name}', 20, [255, 165, 0])
    
    print_and_log(f'Project setup complete!\nYou can check out the log at {logger.handlers[0].baseFilename}')
    
    return github_repo_url.lstrip('https://github.com/') if github_repo_url else None

def tui(project_directory: str = None, author_name: str = None, program_name: str = None, github_pat: str = None, github_repo_url: str = None,
        overwrite: bool = None, gofile_code: str = None, license_type: str = None, github_auth: bool = None,
        use_pyinstaller: bool = None) -> list[str]:
    '''
    Interactive command-line user interface for collecting project setup information.

    This function prompts the user for various project details such as the program name,
    author name, and GitHub Personal Access Token (PAT). It ensures that required
    information is provided and returns the collected data as a list.

    :return: A list containing:
    - project_directory (str): The absolute path to the project directory.
    - author_name (str): The name of the author.
    - program_name (str): The name of the program.
    - github_pat (str or None): The GitHub PAT if provided, otherwise None.
    - github_repo_url (str or None): The GitHub repository URL if provided, otherwise None.
    - overwrite (bool): Whether to overwrite the existing project
    - gofile_code (str or None): The GoFile code if provided, otherwise None.
    - license_type (str or None): The type of license to use for the project, defaults to 'MIT'.
    - github_auth (bool): Whether to use GitHub authentication for pushing to the remote repository, defaults to False.
    - use_pyinstaller (bool): Whether to add PyInstaller related files and build process, defaults to True.
    :rtype: list[str]
    '''

    if not program_name:
        program_name = input('1. Program name: ')

        while (program_name[:1].isdigit()) or (program_name.count(' ') > 0) or (not match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', program_name)) or (iskeyword(program_name)) or (program_name in builtin_module_names or (check_module_conflict(program_name))):
            print('Name isn\'t acceptable since it doesn\'t follow restrictions:')
            print_list(['Can\'t start with a number', 'Can\'t contain any spaces', 'Can\'t contain any special characters (Alphanumeric characters and underscores only)', 'Can\'t be a Python keyword', 'Can\'t be a built-in module name', 'Can\'t be in conflict with other existing modules'], start='\t* ')
            program_name = input('Reenter the program name: ').capitalize()
        
        program_name = f'{program_name[0].upper()}{program_name[1:]}'


    default_project_dir = f'{documents_dir}/{program_name}'

    if not project_directory:
        project_directory = input(f'2. Project directory (absolute path, default to: {default_project_dir}): ')
        if project_directory == '':
            project_directory = default_project_dir

    if overwrite is None:
        overwrite = True
        if Path(project_directory).exists():
            if not simple_prompt('Directory already exists, overwrite it', 'n'):
                overwrite = False

    project_directory.rstrip('/')

    if not github_pat:
        github_pat = _getpass('3. Github personal access token (with Administration permissions (contents and workflows (all read and write) are extra optional permissions if you wanna authenticate using PAT)): ').strip() or None
    
    if not github_repo_url:
        github_repo_url = not github_pat and stripped_input('4. Github repo url (username/repo): ') or None

    default_name = getuser()

    if not author_name:
        author_name = input(f'5. Author name of the program [default to: {default_name}]: ')
        if author_name == '':
            author_name = default_name
    
    if not gofile_code:
        gofile_code = stripped_input('6. GoFile code [None]: ') or None
    
    if not license_type:
        license_type = stripped_input('7. License type: [MIT]: ') or None
    
    if not github_auth:
        github_auth = simple_prompt('8. Authenticate with GitHub using a PAT for pushing', 'n')
    
    if not use_pyinstaller:
        use_pyinstaller = simple_prompt('9. Add pyinstaller related files and build process')

    return [project_directory, author_name, program_name, github_pat, github_repo_url, overwrite, gofile_code, license_type, github_auth, use_pyinstaller]

if __name__ == '__main__':
    print('You will need to configure [idk] settings.')
    try:
        print(f'github repo url: {main(*tui())}')
    except KeyboardInterrupt:
        exit()