from datetime import datetime
from os import remove
from subprocess import run
from tempfile import NamedTemporaryFile
from pathlib import Path

from packer.config import all_settings

def main(git_directory: str | Path = '.', text_editor: str = 'code', modification_types: list[str] = ['a'], overall_description: str = None):
    '''
    Opens a temporary file in the specified text editor for describing the project's modification

    This function creates a temporary file, opens it in the specified text editor,
    waits for the editor to close, and then removes the temporary file. Afterwards updates the changelog
    and commits it with the commit message as the project's entered modification as the user had.

    :param git_directory: The root directory of the project (default is '.')
    :type git_directory: str | Path
    :param text_editor: The text editor to use for opening the file (default is 'code')
    :type text_editor: str
    :param modification_types: The types of modifications to record (a = added, c = changed, f = fixed) (default is ['a'])
    :type modification_types: list[str]
    :param overall_description: The overall description of the modifications, if there are multiple (default is None)
    :type overall_description: str
    '''
    

    with open(f'{git_directory}/CHANGELOG.md', 'r') as f:
        full_changelog = f.read()

    messages = []

    for modification_type in modification_types:
        with NamedTemporaryFile('r', delete=False) as tf:
            temp_path = tf.name
        run([text_editor, '--wait', temp_path])

        with open(temp_path) as f:
            message = f.read().strip()
            message = f'{message[:1].capitalize()}{message[1:]}'
        remove(temp_path)

        if not message.endswith('.'):
            message = f'{message}.'

        match modification_type:
            case 'a':
                modification_type = 'Added'
                end = full_changelog.find('### Changed') - 2
            case 'c':
                end = full_changelog.find('### Fixed') - 2
                modification_type = 'Changed'
            case 'f':
                end = full_changelog.find('---') - 2
                modification_type = 'Fixed'
        
        messages.append((modification_type, message))

        with open(f'{git_directory}/CHANGELOG.md', 'w') as f:
            f.write(f'{full_changelog[0: end]}\n- {message} [{datetime.now().strftime("Day %d %H:%M")}]{full_changelog[end:]}')

    if len(messages) > 1:
        git_message = f'feat: {overall_description}\n\n'
        for message in messages:
            git_message += f'- {message[0]}: {message[1]}\n'
    else:
        git_message = f'{messages[0][0]}: {messages[0][1]}'

    run(['git', 'add', '.'])
    run(['git', 'commit', '-m', git_message])
    run(['git', 'push'])

def tui():
    '''
    Launches a text-based user interface for creating project change logs and committing them.

    This function is intended to be used as an entry point for a TUI that guides the user
    through creating a changelog entry and committing it to the repository.
    '''

    amount = int(input('Enter the amount of changes: '))
    if amount > 1:
        print('Enter each change idvidually, both in terminal and text editor.')

    changes = []
    for _ in range(amount):
        changes.append(input('Enter the modification type [a, c, f] '))
    if len(changes) > 1:
        overall_description = input('High level description for all changes together: ')
    else:
        overall_description = None
    main(text_editor=all_settings.text_editor, modification_types=changes, overall_description=overall_description)

if __name__ == '__main__':
    tui()