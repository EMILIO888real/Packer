'''Command-line argument parser and completion callbacks.'''

__all__ = ['args']

from pathlib import Path
from argparse import ArgumentParser
from argcomplete import autocomplete

# Completion CLI functions (.completer)

def get_nice_fonts(**kwargs) -> list[str]:
    from packer.initialization import nice_fonts

    return nice_fonts

def get_project_names(**kwargs):
    from packer.config import projects_configurations

    return [Path(project).name for project in projects_configurations.get_w_tui().keys()]

def get_new_version(**kwargs):
    return ['x', 'y', 'z']

def get_text_editors(**kwargs):
    return ['code', 'nvim', 'vim', 'nano', 'subl3', 'atom', 'emacs', 'idea', 'webstorm', 'notepad', 'pycharm']

def get_wait_flags(**kwargs):
    return ['--wait']

def get_license_types(**kwargs):
    from github import Github

    g = Github()
    return [github_license.key for github_license in g.get_licenses()]

def get_author_names(**kwargs):
    from getpass import getuser

    return [getuser()]

def get_setup_paths(**kwargs):
    from packer.paths import documents_dir

    return [f'{documents_dir}/']

parser = ArgumentParser('packer', description='Packer CLI tool')
subparsers = parser.add_subparsers(dest='command')

parser.add_argument('-p', '--paths', action='store_true', help='Output all storage paths')
parser.add_argument('-v', '--version', action='store_true', help='Display the software\'s version')
parser.add_argument('--static', action='store_true', help='Show a single static version banner instead of an animated loop')
parser.add_argument('--version-font', default='nice-random', help='Font name to use for the version banner, or use \'random\'/\'nice-random\'').completer = get_nice_fonts
parser.add_argument('--version-color', default='nice-random', help='Color palette to use for the version banner, or use \'random\'/\'nice-random\'')
parser.add_argument('-s', '--saves', action='store_true', help='Displays all saved projects')
parser.add_argument('-c', '--config', action='store_true', help='Displays the saved configuration or packer settings')
parser.add_argument('--projects', action='store_true', help='Displays the saved configurations of projects')
parser.add_argument('-g', '--gui', action='store_true', help='Launches the GUI interface')

clear_command_parser = subparsers.add_parser('clear', help='Clear data produced (cache, saves and so on)')
clear_command_parser.add_argument('-c', '--cache', action='store_true', help='Clear cache data')
clear_command_parser.add_argument('-s', '--save', action='store_true', help='Clear config/settings data')
clear_command_parser.add_argument('-l', '--log', action='store_true', help='Clear log directory')
clear_command_parser.add_argument('-u', '--user', action='store_true', help='Clear user directory')

run_command_parser = subparsers.add_parser('run', help='Runs packer release and update process on the specified project')
run_command_parser.add_argument('-p', '--project', help='Specify the project to release an update on').completer = get_project_names
run_command_parser.add_argument('-n', '--new-version', dest='run_version', help='Specify the new version to update to').completer = get_new_version

edit_command_parser = subparsers.add_parser('edit', help='Edits user related data, like configurations, projects and so on')
edit_command_parser.add_argument('-s', '--settings', action='store_true', help='Open to edit the settings.json in the user preferred text editor')
edit_command_parser.add_argument('-p', '--projects', dest='edit_project', action='store_true', help='Open to edit the projects.json in the user preferred text editor')
edit_command_parser.add_argument('-t', '--text_editor', help='Specify the text editor to use over the one saved in settings').completer = get_text_editors

edit_command_parser.add_argument('-w', '--wait_flag', help='Specify the wait flag for the text editor to use over the one saved in settings').completer = get_wait_flags

setup_command_parser = subparsers.add_parser('setup', help='Runs the packer new project setup function')



setup_command_parser.add_argument('-p', '--path', dest='setup_path', help='Project directory to use for setup').completer = get_setup_paths
setup_command_parser.add_argument('-a', '--author-name', dest='setup_author_name', help='Author name for the new project').completer = get_author_names
setup_command_parser.add_argument('-n', '--program-name', dest='setup_program_name', help='Program name for the new project')
setup_command_parser.add_argument('-t', '--pat', dest='setup_github_pat', help='GitHub personal access token')

setup_command_parser.add_argument('-u', '--github-url', dest='setup_github_repo_url', help='GitHub repository URL')
setup_command_parser.add_argument('-o', '--overwrite', action='store_true', dest='setup_overwrite', help='Overwrite existing project')
setup_command_parser.add_argument('-c', '--code', action='store_true', dest='setup_gofile_code', help='GoFile URL / code (eg. KtA9pExt)')

setup_command_parser.add_argument('-l', '--license', dest='setup_license', help='License for the new project').completer = get_license_types

setup_command_parser.add_argument('--authenticate', dest='setup_authenticate', action='store_true', help='Authenticate with GitHub using a PAT (Personal Access Token) for pushing')
setup_command_parser.add_argument('--open-project', dest='setup_open_project', action='store_true', help='Open the project after setup')

export_command_parser = subparsers.add_parser('export', help='Export all config saved by Packer in an archive')
export_command_parser.add_argument('-p', '--path', dest='export_path', help='Path to export archive to')
export_command_parser.add_argument('-s', '--safe', dest='export_safe', help='Password to the archive')

import_command_parser = subparsers.add_parser('import', help='Import Packer config from an archive')
import_command_parser.add_argument('-p', '--path', dest='import_path', required=True, help='Path to the archive to import')
import_command_parser.add_argument('-s', '--safe', dest='import_safe', help='Password to the archive')

change_command_parser = subparsers.add_parser('change', help='Commit a change of a packer like style project')

change_command_parser.add_argument('-p', '--project', dest='change_project', help='Specify the project').completer = get_project_names
change_command_parser.add_argument('-c', '--changes', dest='change_changes', help='Specify the changes')
change_command_parser.add_argument('-o', '--overall-description', dest='change_overall_description', help='Specify the overall description, only in use if there are more than 1 change')
change_command_parser.add_argument('-m', '--ai-summary', dest='change_ai_summary', action='store_true', help='Disable AI summary')
change_command_parser.add_argument('-s', '--ai-suggestions', dest='change_ai_suggestions', action='store_true', help='Disable AI suggestions')
change_command_parser.add_argument('-i', '--no-index', dest='change_no_index', action='store_true', help='Disable automatic full git indexation of the project, useful for large projects with many files')


autocomplete(parser)
args = parser.parse_args()