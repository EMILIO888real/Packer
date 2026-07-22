from pathlib import Path

from packer.config import Project, all_settings, send_notification, exception_handler
import sys

from packer.core import Packer


def run(new_version: dict, project_directory: Path, project_configuration: Project):

    try:
        packer = Packer(new_version, project_directory,
                        project_configuration.github_repo_token,
                        project_configuration.github_repo_url,
                        project_configuration.gofile_user_token, project_configuration.gofile_folder_id,
                        None, None,
                        project_configuration.compile_command, project_configuration.before_commands, project_configuration.after_commands, 
                        project_configuration.model, project_configuration.description_prompt, project_configuration.title_prompt,
                        project_configuration.description_prompt_kwargs, project_configuration.title_prompt_kwargs,
                        project_configuration.release_notes_template_path, project_configuration.changelog_git_hash,
                        project_configuration.check_todo, project_configuration.todo_rel_path, project_configuration.list_start_identifier, project_configuration.list_end_identifier)

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