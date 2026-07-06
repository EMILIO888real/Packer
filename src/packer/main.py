# PYTHON_ARGCOMPLETE_OK
'''
This module contains the code for the packer, which is a script that creates an archive of the program, uploads it to Gofile, updates the git directory, and publishes a new release on Github. If any error is encountered it reverts all changes back to the previous version.
'''

from pathlib import Path
import sys
from json import load

from packer.custom_modules.et import resolve_version
from packer.ui.tui import main as tui
from packer.ui.cli import main as cli
from packer.core import Packer
from packer.custom_modules.etf import stripped_input
from packer.config import all_settings, exception_handler, send_notification

def main():

    cli()
    project_directory, project_configuration = tui()

    with open(f'{project_directory}/src/{Path(project_directory).name}/assets/version.json') as f:
        version = load(f)
    try:
        new_version = resolve_version(version, stripped_input('New version(M, m, P): '))
    except ValueError as e:
        print(f'Invalid version input: {e}')

    try:
        packer = Packer(new_version, version, project_directory,
                        project_configuration.github_repo_token,
                        project_configuration.github_repo_url,
                        project_configuration.gofile_user_token, project_configuration.gofile_folder_id,
                        None, None,
                        project_configuration.compile_command, project_configuration.before_commands, project_configuration.after_commands, 
                        project_configuration.model, project_configuration.description_prompt, project_configuration.title_prompt)

        def packer_exception_handler(exc_type, exc_value, exc_traceback):
            packer.revert_changes(False)
            if all_settings.desktop_notifications:
                send_notification('Packer encountered an error and reverted all changes.', 'error')
            exception_handler.handle_exception(exc_type, exc_value, exc_traceback)

        sys.excepthook = packer_exception_handler # replace the global exception handler with packer's to revert changes in case Packer was running.
        
        packer.run()
    except KeyboardInterrupt:
        packer.print_and_log('Process interrupted by user!', [255, 255, 0], level=30)
        packer.revert_changes()

if __name__ == '__main__':
    main()