from pathlib import Path
from subprocess import run
from sys import platform


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