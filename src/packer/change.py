from os import remove
from subprocess import run
from tempfile import NamedTemporaryFile

with NamedTemporaryFile('r', delete=False) as tf:
    temp_path = tf.name

run(['code', '--wait', temp_path])

with open(temp_path) as f:
    message = f.read()

remove(temp_path)
    
modification_type = input('Enter the modification type [a, c, f] ')

if not message.endswith('.'):
    message = f'{message}.'

with open('CHANGELOG.md', 'r') as f:
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

full_changelog = f'{full_changelog[0: end]}\n- {message}{full_changelog[end:]}'

with open('CHANGELOG.md', 'w') as f:
    f.write(full_changelog)


run(['git', 'add', '.'])
run(['git', 'commit', '-m', f'{modification_type} {message}'])
run(['git', 'push'])