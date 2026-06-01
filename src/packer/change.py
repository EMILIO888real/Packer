from os import remove
from subprocess import run
from tempfile import NamedTemporaryFile
from packer.config import all_settings

def main(root_dir: str = '.', text_editor: str = 'code', modification_type: str = 'a'):
    '''
    Opens a temporary file in the specified text editor for describing the project's modification

    This function creates a temporary file, opens it in the specified text editor,
    waits for the editor to close, and then removes the temporary file. Afterwards updates the changelog
    and and commits it with the commit message as the project's entered modification as the user had.

    :param root_dir: The root directory to use for the temporary file (default is '.')
    :type root_dir: str
    :param text_editor: The text editor to use for opening the file (default is 'code')
    :type text_editor: str
    :param modification_type: The type of modification to record (a = added, c = changed, f = fixed) (default is 'a')
    :type modification_type: str
    '''

    with NamedTemporaryFile('r', delete=False) as tf:
        temp_path = tf.name
    run([text_editor, '--wait', temp_path])

    with open(temp_path) as f:
        message = f.read().strip()
        message = f'{message[:1].capitalize()}{message[1:]}'
    remove(temp_path)

    if not message.endswith('.'):
        message = f'{message}.'


    with open(f'{root_dir}/CHANGELOG.md', 'r') as f:
        full_changelog = f.read()

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


    with open(f'{root_dir}/CHANGELOG.md', 'w') as f:
        f.write(f'{full_changelog[0: end]}\n- {message}{full_changelog[end:]}')


    run(['git', 'add', '.'])
    run(['git', 'commit', '-m', f'{modification_type}: {message}'])
    run(['git', 'push'])

if __name__ == '__main__':
    main(text_editor=all_settings.text_editor, modification_type=input('Enter the modification type [a, c, f] '))