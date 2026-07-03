from pathlib import Path
from subprocess import run
from sys import platform
from plyer import notification

from packer.paths import assets_dir
from packer.config import notification_sound


def pip_install(packages: list[str], python_exe_path: str | Path | None = None):
    '''
    Install Python packages using pip.

    This function installs a list of Python packages using pip. It can optionally
    use a specific Python executable path for the installation.

    :param packages: A list of package names to install
    :type packages: list[str]
    :param python_exe_path: Path to the Python executable to use for installation.
        If None, the CWD .venv executable is used
    :type python_exe_path: str | Path | None
    '''
    
    if not python_exe_path:
        python_exe_path = ('.venv/Scripts/python.exe'
            if platform == 'win32'
            else '.venv/bin/python')
    run([python_exe_path, '-m', 'pip', 'install', *packages], check=True)


def send_notification(title: str, message: str, timeout: int = 5):
    '''
    Send a desktop notification.

    :param title: the title of the notification
    :type title: str
    :param message: the message of the notification
    :type message: str
    :param timeout: the duration (in seconds) for which the notification should be displayed
    :type timeout: int
    '''

    notification.notify(
        title=title,
        message=message,
        app_name='Packer',
        app_icon=f'{assets_dir}/images/Packer icon.png',
        timeout=timeout
    )

    notification_sound.play()