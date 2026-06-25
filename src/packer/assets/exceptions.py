from datetime import datetime
from pathlib import Path
import sys
from traceback import format_exception
from json import dump
from typing import Any
from requests import post, exceptions
from pyperclip import copy
from webbrowser import open_new_tab
from urllib import parse

from packer.custom_modules.etf import print_colored_text, prompt_user
from packer.config import packer_version, all_settings
from packer.paths import log_path, error_report_path


def global_exception_handler(exc_type, exc_value, exc_traceback):

    global log_path

    '''
    Global exception handler for uncaught exceptions.

    :param exc_type: The type of the exception being handled
    :param exc_value: The exception value (the actual exception object)
    :param exc_traceback: The traceback object containing the stack trace
    ''' 

    if issubclass(exc_type, KeyboardInterrupt) or issubclass(exc_type, SystemExit): # Ignore any errors when quitting the program.
        return

    print_colored_text(f'An error has occurred: Type: {exc_type} | Value: {exc_value}', [255, 0, 0])

    try:
        user_notes = input('Could you explain a bit more about the error? What, How or When did the error happen?\nInput: ')
    except KeyboardInterrupt:
        user_notes = None

    print('Generating an error report...')

    error_report = {'timestamp': str(datetime.now()),
                    'packer version': packer_version,
                    'platform': sys.platform,
                    'python version': sys.version,
                    'human notes': user_notes,
                    'traceback': ''.join(format_exception(exc_type, exc_value, exc_traceback)),
                    'log': log_path.read_text() if log_path.exists() else None
                    }
    
    with open(error_report_path, 'a' if Path(error_report_path).exists() else 'w') as f:
        dump(error_report, f)
        f.write('\n') # For the next errors, so it's possible to compound them.

    print_colored_text(f'error report generated at: "{error_report_path.absolute()}"', [0, 255, 0])

    if all_settings.automatic_error_reporting:
        print('Automatically reporting the problem via formspree.io...')
        if not report_error(error_report):
            if prompt_user('Open the default email client if no then GitHub new issue creation will be opened in the default browser'):
                copy(error_report)
                print('We copied the error report to your clipboard')
                open_new_tab('https://github.com/EMILIO888real/Packer/issues/new')
            else:
                print('Specify your email if needed and hit send')
                prompt_user_to_email(error_report)
    sys.exit(1)


def report_error(error_report: dict[str: Any]) -> bool:
    '''
    Attempts to automatically report the error to a remote service.

    This function sends the error report to a predefined endpoint using a POST request.
    If the request fails, it returns False, indicating that the automatic reporting
    was unsuccessful.

    :param error_report: A dictionary containing all relevant information about the error,
                         such as timestamp, version, platform, notes, traceback, and log.
    :type error_report: dict[str, Any]
    :return: True if the error report was successfully sent, False otherwise.
    :rtype: bool
    '''

    endpoint_url = 'https://formspree.io/f/xjgqgqbz'
    manual_report_prompt = 'Please report this manually yourself by sending an email to emilspro888@gmail.com or opening a GitHub issue at https://github.com/EMILIO888real/Packer/issues'

    headers = {
        'Accept': 'application/json'
    }
    
    payload = {
        'subject': 'Automated Crash Report',
    }
    payload.update(error_report)
    
    try:
        response = post(endpoint_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print_colored_text('Successfully automatically reported a problem to developers.', [0, 255, 0])
            return True
        else:
            print_colored_text(f'Failed to report a problem. Status: {response.status_code}', [255, 0, 0])
            print(manual_report_prompt)
            return False
            
    except exceptions.RequestException as e:
        print_colored_text(f'Could not connect to the reporting server: {e}', [255, 0, 0])
        print(manual_report_prompt)
        return False

def prompt_user_to_email(error_report: dict[str: Any]):
    '''
    Prompts the user to manually send an email with the error report.

    :param error_report: A dictionary containing the error metadata to be included in the email.
    :type error_report: dict[str: Any]
    '''

    developer_email = "emilspro888@gmail.com"
    subject = 'Automated Error Report'

    body = parse.quote(f'Please do not edit this block.\n\nError report:\n{error_report}')

    mailto_url = f"mailto:{developer_email}?subject={subject}&body={body}"

    open_new_tab(mailto_url)