# PYTHON_ARGCOMPLETE_OK
'''
This module contains the code for the packer, which is a script that creates an archive of the program, uploads it to Gofile, updates the git directory, and publishes a new release on Github. If any error is encountered it reverts all changes back to the previous version.
'''

from packer.ui.tui import main as tui
from packer.ui.cli import main as cli

def main():
    cli()
    tui()

if __name__ == '__main__':
    main()