from string import Template
from subprocess import run
from pathlib import Path
from git import Repo
from ollama import chat

from packer.config import _input_via_text_editor, all_settings

def main(git_directory: str | Path = '.', modification_types: list[str] = ['c'], overall_description: str = None,
         text_editor: str = all_settings.text_editor, wait_flag: str = all_settings.wait_flag,
         ai_summary: bool = True,
         check_todo: bool = True, todo_rel_path: str = '/dev/TODO.md', list_start_identifier: str = 'before committing', list_end_identifier: str = '#',
         bullet_summary_prompt = all_settings.changes_summary_prompt, high_level_summary_prompt = all_settings.high_level_summary_prompt,
         model: str = all_settings.model, verbose: bool = True):
    '''
    Opens a temporary file in the specified text editor for describing the project's modification

    This function creates a temporary file, opens it in the specified text editor,
    waits for the editor to close, and then removes the temporary file. Afterwards updates the changelog
    and commits it with the commit message as the project's entered modification as the user had.

    :param git_directory: The root directory of the project (default is '.')
    :type git_directory: str | Path
    :param modification_types: The types of modifications to record (a = added, c = changed, f = fixed) (default is ['c'])
    :type modification_types: list[str]
    :param overall_description: The overall description of the modifications, if there are multiple (default is None)
    :type overall_description: str
    :param ai_summary: Whether to generate an AI summary of the changes (default is True)
    :type ai_summary: bool
    :param check_todo: Whether to check for TODO items before committing (default is True)
    :type check_todo: bool
    :param todo_rel_path: The relative path to the TODO file (default is '/dev/TODO.md')
    :type todo_rel_path: str
    :param list_start_identifier: The identifier for the start of the TODO list (default is 'before committing')
    :type list_start_identifier: str
    :param list_end_identifier: The identifier for the end of the TODO list (default is '#')
    :type list_end_identifier: str
    :param verbose: Whether to print verbose output (default is True)
    :type verbose: bool
    :param bullet_summary_prompt: The prompt template for generating bullet point summaries (default is all_settings.changes_summary_prompt)
    :type bullet_summary_prompt: list[dict]
    :param high_level_summary_prompt: The prompt template for generating high-level summaries (default is all_settings.high_level_summary_prompt)
    :type high_level_summary_prompt: list[dict]
    :param model: The AI model to use for generating summaries (default is all_settings.model)
    :type model: str
    '''

    def input_via_text_editor(message: str) -> str:
        '''
        Opens a temporary file in the specified text editor for user input.

        :param message: The initial message to display in the text editor
        :type message: str
        :return: The user's input from the text editor
        :rtype: str
        '''
        return _input_via_text_editor(message, text_editor=text_editor, wait_flag=wait_flag)

    if check_todo:
        with open(f'{git_directory}{todo_rel_path}') as f:
            content = f.read().lower()

        list_start = content.find(list_start_identifier)
        list_end = content.find(list_end_identifier, list_start)

        before_committing_list = content[list_start + len(list_start_identifier):list_end].lstrip(':').strip()

        if before_committing_list:
            print(f'{list_start_identifier} task/s found, please delete them from the list once finished!\nList:\n{before_committing_list}')
            return


    repo = Repo(git_directory)
    diff_text = repo.git.diff(unified=3)

    if ai_summary:
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

        if ai_summary:
            bullet_summary_list = bullet_summary.splitlines()
            message = bullet_summary_list[i] if len(bullet_summary_list) > i else 'AI didn\'t generate anything...'
        else:
            message = ''

        message = input_via_text_editor(message)

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
        if message.lower().startswith(modification_type.lower()):
            message = message[len(modification_type):].lstrip()
        message = message.strip()

        message = f'{message[:1].capitalize()}{message[1:]}'
        if not message.endswith('.'):
            message = f'{message}.'

        messages.append([modification_type, message])

        full_changelog = f'{full_changelog[0: end]}\n- {message} {full_changelog[end:]}'
        with open(f'{git_directory}/CHANGELOG.md', 'w') as f:
            f.write(full_changelog)

    if len(messages) > 1:
        git_message = f'feat: {input_via_text_editor(high_level_summary if ai_summary else overall_description)}\n\n'
        for message in messages:
            git_message += f'- {message[0]}: {message[1]}\n'
    else:
        git_message = f'{messages[0][0]}: {messages[0][1]}'

    run(['git', 'add', '.'])
    run(['git', 'commit', '-m', git_message.strip()])
    run(['git', 'push'])

def tui(changes: list[str] | None = None, overall_description: str | None = None, ai_suggestions: bool = True):
    '''
    Launches a text-based user interface for creating project change logs and committing them.

    This function is intended to be used as an entry point for a TUI that guides the user
    through creating changelog entries and committing them to the repository.

    :param changes: A list of modification types (a = added, c = changed, f = fixed) (default is None)
    :type changes: list[str] | None
    :param overall_description: An overall description of the modifications, if there are multiple (default is None)
    :type overall_description: str | None
    :param ai_suggestions: Whether to generate AI suggestions for the changes (default is True)
    :type ai_suggestions: bool
    '''

    if ai_suggestions:
        print(f'AI suggestions:\n{generate_suggestions()}')

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

def generate_suggestions(git_directory: str | Path = '.', suggestions_prompt = all_settings.suggestions_prompt, model: str = all_settings.model, verbose: bool = True):
    '''
    Generates AI suggestions for the changes based on the current git diff.

    :param git_directory: The root directory of the project (default is '.')
    :type git_directory: str | Path
    :param suggestions_prompt: The prompt template for generating AI suggestions (default is all_settings.suggestions_prompt)
    :type suggestions_prompt: list[dict]
    :param model: The AI model to use for generating suggestions (default is all_settings.model)
    :type model: str
    '''
    repo = Repo(git_directory)
    diff_text = repo.git.diff(unified=3)
    
    suggestions_prompt[1]['content'] = Template(suggestions_prompt[1 if suggestions_prompt[1]['role'] == 'user' else 0]['content']).substitute({'diff': diff_text})

    if verbose:
        print('Generating AI suggestions...')
    return chat(
        model=model,
        messages=suggestions_prompt
    )['message']['content'].strip()

if __name__ == '__main__':
    output = tui()
    main(modification_types=output[0], overall_description=output[1])