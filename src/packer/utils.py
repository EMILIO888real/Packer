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
    :return: None
    :rtype: None
    '''
    cmd = [python_exe_path or 'python', '-m', 'pip', 'install'] + packages
    run(cmd, check=True)
    if not python_exe_path:
        if platform == 'win32':
            python_exe = Path('.venv/Scripts/python.exe')
        else:
            python_exe = Path('.venv/bin/python')
    run([str(python_exe), '-m', 'pip', 'install', *packages], check=True)