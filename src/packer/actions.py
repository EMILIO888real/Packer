from pathlib import Path
from queue import Queue

from packer.config import Project, all_settings, send_notification, exception_handler
import sys

from packer.core import Packer


def run(new_version: dict, project_directory: Path, project_configuration: Project, input_queue: Queue | None = None, output_queue: Queue | None = None):

    try:
        packer = Packer(new_version, project_directory, **project_configuration.model_dump(), input_queue=input_queue, output_queue=output_queue)

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