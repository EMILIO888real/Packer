
from os import chdir, mkdir
from pathlib import Path
from shutil import rmtree
from subprocess import CalledProcessError, run
from typing import Sequence
from json import dump
from git import Repo
from github import Auth, Github
from multiprocessing import Process, Event
from sys import exit, platform

from packer.custom_modules.et import init_logger, print_colored_text, tree, read_json, format_version_text, prompt_user
from packer.paths import assets_dir

logger = init_logger('packer setup', 'EMILIO')

packer_version = format_version_text(read_json(f'{assets_dir}/version.json'))

def print_and_log(text: str, level: int = 20, color: Sequence[int] = [255, 255, 255], end: str = '\n') -> None:
    print_colored_text(text, color, end=end)
    logger.log(level, text)

def create_venv(created_venv) -> None:
    print_and_log('Creating a python virtual environment...')
    run(['python', '-m', 'venv', '.venv'])
    created_venv.set()

def main(project_directory: str | Path, author_name: str, program_name: str, github_pat: str = None, github_repo_url: str = None) -> str:
    '''Sets up a new project with the following structure:
    ```
    project_directory/
    ├── src/
    │   └── program_name/
    │       ├── __init__.py
    │       ├── main.py
    │       ├── paths.py
    │       └── assets/
    ├── docs/
    │   ├── todo.md
    │   ├── SETTINGS.md
    │   ├── CONFIGURATION.md
    │   ├── CUSTOMIZATION.md
    │   └── ROADMAP.md
    ├── tests/
    ├── dev/
    ├── .gitignore
    ├── LICENSE
    ├── README.md
    ├── CHANGELOG.md
    └── pyproject.toml
    ```
    The function also initializes a git repository, creates an initial commit, and optionally creates a remote repository on GitHub and pushes the initial commit to it.

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
    :return: The URL of the created GitHub repository.
    :rtype: str
    '''

    program_name = program_name.lower()
    root_dir = f'src/{program_name}'

    if Path(project_directory).exists():
        if prompt_user(f'The directory "{project_directory}" already exists. Do you want to delete it and create a new one'):
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
    
    print_and_log('Creating __init__.py file...')
    with open(f'{root_dir}/__init__.py', 'w') as f:
        f.write('')

    print_and_log('Creating paths.py file...')
    with open(f'{root_dir}/paths.py', 'w') as f:
        f.write(f'from importlib import resources\n\nroot_dir = resources.files(\'{program_name}\') \nassets_dir = root_dir.joinpath(\'assets\')\n')

    print_and_log('Creating main.py file...')
    with open(f'{root_dir}/main.py', 'w') as f:
        f.write(f'from {program_name}.paths import assets_dir\n\n\ndef main():\n    print("Hello, world!")\n\nif __name__ == "__main__":\n    main()\n')

    print_and_log('Creating version.json file...')
    with open(f'{root_dir}/assets/version.json', 'w') as f:
        f.write('{"major": 0, "minor": 0, "patch": 0}')

    print_and_log('Creating an integrity file...')
    with open(f'{root_dir}/assets/integrity.json', 'w') as f:
        dump({'CWD': tree(f'src/{program_name}')}, f)

    print_and_log('Starting outside src directory build process..')

    print_and_log('Creating a todo.md file...')
    with open('docs/todo.md', 'w') as f:
        f.write('# TODO\n\n- [ ] Write the README.md file\n- [ ] Write the CHANGELOG.md file\n- [ ] Write the ROADMAP.md file\nWrite the pyproject.toml file\n')

    print_and_log('Creating a SETTINGS.md file...')
    with open('docs/SETTINGS.md', 'w') as f:
        f.write(f'# SETTINGS\n\nThis file contains detailed information on user-configurable settings for {program_name}.\n\n## Setting 1\n\nDescription of setting 1.\n\n## Setting 2\n\nDescription of setting 2.\n\n## Setting 3\n\nDescription of setting 3.\n')

    print_and_log('Creating a CONFIGURATION.md file...')
    with open('docs/CONFIGURATION.md', 'w') as f:
        f.write(f'# CONFIGURATION\n\nThis file contains detailed information on game configuration parameters for {program_name}.\n\n## Parameter 1\n\nDescription of parameter 1.\n\n## Parameter 2\n\nDescription of parameter 2.\n\n## Parameter 3\n\nDescription of parameter 3.\n')

    print_and_log('Creating a CUSTOMIZATION.md file...')
    with open('docs/CUSTOMIZATION.md', 'w') as f:
        f.write(f'# CUSTOMIZATION\n\nThis file contains detailed information on how to add custom assets and important notes about settings for {program_name}.\n\n## Custom Asset 1\n\nDescription of custom asset 1.\n\n## Custom Asset 2\n\nDescription of custom asset 2.\n\n## Custom Asset 3\n\nDescription of custom asset 3.\n')

    print_and_log('Creating a pyproject.toml file...')
    with open('pyproject.toml', 'w') as f:
        f.write(f'[project]\nname = "{program_name}"\nversion = "0.0.0"\ndescription = ""\nreadme = "README.md"\nlicense = "MIT"\ndependencies = []\n\n[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n[tool.setuptools.packages.find]\nwhere = ["src"]  # This tells setuptools to look for packages inside \'src\'\n\n[project.scripts]\n{program_name} = "{program_name}.main:main"')

    print_and_log('Creating CHANGELOG.md...')
    with open('CHANGELOG.md', 'w') as f:
        f.write(f'## [%new_version] - %date\n\n### Added\n- \n\n### Changed\n- \n\n### Fixed\n- \n\n')

    print_and_log('Creating README.md...')
    with open('README.md', 'w') as f:
        f.write(f'# {program_name.capitalize()}\n\nA short description of the project.\n\n## Contents\n\n- [Installation](#Installation)\n- [Usage](#Usage)\n- [Configuration](#Configuration)\n\t- [Settings](#Settings)\n\t- [Config](#Config)\n\t- [Extra customization](#extra-customization)\n- [Extra notes](#extra-notes)\n- [Warning](#warning)\n- [Features](#features)\n- [Feedback and Suggestions](#feedback-and-suggestions)\n- [Honorable mentions](#honorable-mentions)\n- [Changelog](#changelog)\n- [In future updates](#in-future-updates)\n\n## Installation\n\nAvailable via Github or Gofile.\n\n1. Github\n\n- Download the latest release from the [releases page](%release_url)\n- Unzip the downloaded content if you installed the archive version\n- Run the executable file\n\n2. Gofile\n\n- Download the latest release from the [Gofile page](%gofile_url)\n- Unzip the downloaded content if you installed the archive version\n- Run the executable file\n\n## Usage\n\nInstructions on how to use the program.\n\n## Configuration\n\n### Settings\n\nSee [SETTINGS.md](docs/SETTINGS.md) for detailed information on user-configurable settings.\n\n### Config\n\nSee [CONFIGURATION.md](docs/CONFIGURATION.md) for detailed information on game configuration parameters.\n\n### Extra customization\n\nSee [CUSTOMIZATION.md](./docs/CUSTOMIZATION.md) for detailed information on how to add custom assets and important notes about settings.\n\n## Extra notes\n\nAny extra notes about the project.\n\n## Warning\n\nAny warnings about the project.\n\n## Features\n\nList of features in the project.\n\n## Feedback and Suggestions\n\nInstructions on how to provide feedback and suggestions for the project.\n\n## Honorable mentions\n\nAcknowledgment of any contributors or resources that were helpful in the development of the project.\n\n## Changelog\n\nSee the full history in [CHANGELOG.md](./CHANGELOG.md).\n\n## In future updates\nsee [ROADMAP.md](./docs/ROADMAP.md) for planned features and improvements.\n')

    print_and_log('Creating ROADMAP.md...')
    with open('docs/ROADMAP.md', 'w') as f:
        f.write('# Roadmap\n\n## Version 0.0.0\n\n- [ ] Initial release\n\n## Version 0.2.0\n\n- [ ] Add new features\n- [ ] Fix bugs\n\n## Version 1.0.0\n\n- [ ] Stable release with all planned features implemented and tested.\n')

    print_and_log('Creating an MIT license...')
    with open('LICENSE', 'w') as f:
        f.write(f'MIT License\n\nCopyright (c) 2025 {author_name}\n\nPermission is hereby granted, free of charge, to any person obtaining a copy\nof this software and associated documentation files (the "Software"), to deal\nin the Software without restriction, including without limitation the rights\nto use, copy, modify, merge, publish, distribute, sublicense, and/or sell\ncopies of the Software, and to permit persons to whom the Software is\nfurnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all\ncopies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\nIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\nFITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\nAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\nLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\nOUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\nSOFTWARE.\n')

    print_and_log('Creating .spec file...')
    with open(f'main.spec', 'w') as f:
        f.write(
f'''
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
''')
        
    print_and_log('Verify main.spec via running it...')

    verify_result = run([f'pyinstaller', 'main.spec'], capture_output=True)

    print_and_log(f'Ran command: pyinstaller main.spec\nstdout: {verify_result.stdout.decode()}\nstderr: {verify_result.stderr.decode()}')

    print_and_log('Removing build directory...')
    rmtree('build')

    repo = Repo.init(project_directory)

    print_and_log('Creating .gitignore file...')
    with open('.gitignore', 'w') as f:
        f.write(
            f'# Virtual environment directory\n'
            f'.venv/\n'
            f'# VSCode settings\n'
            f'.vscode/\n'
            f'# Python cache files\n'
            f'__pycache__/\n'
            f'# Distribution archives\n'
            f'dist/\n'
            f'# Build directories\n'
            f'build/\n'
            f'# Package metadata\n'
            f'{program_name}.egg-info/\n'
        )

    print_and_log('Waiting for .venv to finish creating...')
    created_venv.wait()

    print_and_log('Staging files for initial commit...')
    repo.git.add(all=True)
    print_and_log('Committing files...')
    repo.index.commit(f'Initial commit\nProject structure created by packer\'s setup.py v{packer_version}')

    if github_pat is not None:
        print_and_log('Creating remote repository on GitHub...')
        github_repo_url = Github(auth=Auth.Token(github_pat)).get_user().create_repo(
            program_name,
            description=f'Temporary description, this repo was created by packer\'s setup.py v{packer_version}',
            private=False
        ).clone_url

    if github_repo_url is not None:
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

    print_and_log(f'Please check the {project_directory}/dist directory to verify that the .spec file was correctly processed.\nWe will start it up for you automatically. It should just print out in the black box "Hello world!"')
    try:
        output = run([f'./dist/{program_name}{'.exe' if platform == 'win32' else ''}'], capture_output=True, text=True, check=True).stdout.rstrip('\n')
        print_and_log(f'Successfully ran the build. The output: {output}', end=' ')
        print_and_log(f'[{'valid' if output == 'Hello, world!' else 'invalid'}]', 30, [0, 255, 0] if output == 'Hello, world!' else [255, 0, 0])
    except CalledProcessError as e:
        print_and_log(f'Something went wrong in the built version: {e}', 30, [255, 0, 0])
    
    print_and_log(f'Project setup complete!\nYou can check out the log at {logger.handlers[0].baseFilename}')
    
    return github_repo_url.lstrip('https://github.com/') if github_repo_url is not None else None

if __name__ == '__main__':
    try:
        print(f'github repo url: {main(input('Project directory (absolute path, leave empty for current directory): '),
                      input('Author name of the program: '),
                      input('Program name: '),
                      input('Github repo token (leave empty to skip): '),
                      input('Github repo url (username/repo, leave empty to skip): '))}')
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        print_and_log(f'Something went wrong, please report this. | Error: {e}', color=[255, 0, 0])
        exit()