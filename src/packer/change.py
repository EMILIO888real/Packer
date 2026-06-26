from os import remove
from shutil import which
from string import Template
from subprocess import run
from tempfile import NamedTemporaryFile
from pathlib import Path
from git import Repo
from ollama import chat

from packer.config import all_settings

def main(git_directory: str | Path = '.', text_editor: str = all_settings.text_editor, wait_flag: str = all_settings.wait_flag, modification_types: list[str] = ['c'],
         overall_description: str = None, ai_summary: bool = True, verbose: bool = True,
         bullet_summary_prompt = all_settings.changes_summary_prompt, high_level_summary_prompt = all_settings.high_level_summary_prompt, model: str = all_settings.model):
    '''
    Opens a temporary file in the specified text editor for describing the project's modification

    This function creates a temporary file, opens it in the specified text editor,
    waits for the editor to close, and then removes the temporary file. Afterwards updates the changelog
    and commits it with the commit message as the project's entered modification as the user had.

    :param git_directory: The root directory of the project (default is '.')
    :type git_directory: str | Path
    :param text_editor: The text editor to use for opening the file (default is 'code')
    :type text_editor: str
    :param wait_flag: The flag to pass to the editor to wait for it to close (default is '--wait')
    :type wait_flag: str
    :param modification_types: The types of modifications to record (a = added, c = changed, f = fixed) (default is ['c'])
    :type modification_types: list[str]
    :param overall_description: The overall description of the modifications, if there are multiple (default is None)
    :type overall_description: str
    :param ai_summary: Whether to generate an AI summary of the changes (default is True)
    :type ai_summary: bool
    :param verbose: Whether to print verbose output (default is True)
    :type verbose: bool
    :param bullet_summary_prompt: The prompt template for generating bullet point summaries (default is all_settings.changes_summary_prompt)
    :type bullet_summary_prompt: list[dict]
    :param high_level_summary_prompt: The prompt template for generating high-level summaries (default is all_settings.high_level_summary_prompt)
    :type high_level_summary_prompt: list[dict]
    :param model: The AI model to use for generating summaries (default is all_settings.model)
    :type model: str
    '''

    text_editor = which(text_editor)

    if ai_summary:
        repo = Repo(git_directory)

        diff_text = repo.git.diff(unified=3)

        # Update prompts with runtime data
        summary_data = {
                'diff': diff_text,
                'changes': ','.join(modification_types)
            }

        bullet_summary_prompt[1]['content'] = Template(bullet_summary_prompt[1 if bullet_summary_prompt[1]['role'] == 'user' else 0]['content']).substitute(summary_data)
        if verbose:
            print('Generating bullet summary...')
        bullet_summary = chat(
        model=model,
        messages=bullet_summary_prompt
        )['message']['content'].strip()


        high_level_summary_data = {
            'bullet_summary': bullet_summary
        }

        high_level_summary_prompt[1]['content'] = Template(high_level_summary_prompt[1 if high_level_summary_prompt[1]['role'] == 'user' else 0]['content']).substitute(high_level_summary_data)
        if verbose:
            print('Generating high level summary...')
        high_level_summary = chat(
        model=model,
        messages=high_level_summary_prompt
        )['message']['content'].strip()



    with open(f'{git_directory}/CHANGELOG.md', 'r') as f:
        full_changelog = f.read()

    messages = []

    for i, modification_type in enumerate(modification_types):
        with NamedTemporaryFile('r', delete=False) as tf:
            temp_path = tf.name
        
        if ai_summary:
            bullet_summary_list = bullet_summary.splitlines()
            with open(temp_path, 'w') as f:
                f.write(bullet_summary_list[i] if len(bullet_summary_list) > i else 'AI didn\'t generate anything...')

        run([text_editor, wait_flag, temp_path])

        with open(temp_path) as f:
            message = f.read().strip()
        remove(temp_path)

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

        message = message.lstrip('-')
        message = message.lstrip()
        message = message.lstrip(modification_type)
        message = message.strip()

        message = f'{message[:1].capitalize()}{message[1:]}'
        if not message.endswith('.'):
            message = f'{message}.'

        messages.append([modification_type, message])

        full_changelog = f'{full_changelog[0: end]}\n- {message} {full_changelog[end:]}'
        with open(f'{git_directory}/CHANGELOG.md', 'w') as f:
            f.write(full_changelog)

    if len(messages) > 1:
        with NamedTemporaryFile('r', delete=False) as tf:
            temp_path = tf.name
        if ai_summary:
            with open(temp_path, 'w') as f:
                f.write(high_level_summary)
        else:
            with open(temp_path, 'w') as f:
                f.write(overall_description)
        run([text_editor, wait_flag, temp_path])
        with open(temp_path, 'r') as f:
            high_level_summary = f.read().strip()
        remove(temp_path)

        git_message = f'feat: {high_level_summary if ai_summary else overall_description}\n\n'
        for message in messages:
            git_message += f'- {message[0]}: {message[1]}\n'
    else:
        git_message = f'{messages[0][0]}: {messages[0][1]}'

    run(['git', 'add', '.'])
    run(['git', 'commit', '-m', git_message.strip()])
    run(['git', 'push'])

def tui(changes: list[str] | None = None, overall_description: str | None = None):
    '''
    Launches a text-based user interface for creating project change logs and committing them.

    This function is intended to be used as an entry point for a TUI that guides the user
    through creating changelog entries and committing them to the repository.
    '''

    if not changes:
        amount = int(input('Enter the amount of changes: '))
        if amount > 1:
            print('Enter each change idvidually, both in terminal and text editor.')

        changes = []
        for _ in range(amount):
            changes.append(input('Enter the modification type [a, c, f] ').strip().lower())

    if not overall_description:
        if len(changes) > 1:
            overall_description = input('High level description for all changes together [None]: ').strip()
        else:
            overall_description = None

    return (changes, overall_description)

if __name__ == '__main__':
    output = tui()
    main(modification_types=output[0], overall_description=output[1])