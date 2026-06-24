from datetime import datetime
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from traceback import format_exception
from json import dump
from shutil import make_archive, copy
from typing import Any
from requests import post, exceptions

from packer.custom_modules.etf import print_colored_text
from packer.config import packer_version
from packer.paths import log_path, error_report_path, log_dir


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
    
    print_colored_text(f'An error has occurred: Type: {exc_type} | Value: {exc_value}\nPlease report this to a developer via Email or Github!', [255, 0, 0])

    print('Generating an error report...')

    if Path(log_path).exists():
        with open(log_path) as f:
            content = f.read()
        timestamp_index = content.rfind('______Start of the log ') + 23
    
    

    error_report = {'packer version': packer_version,
                    'platform': sys.platform,
                    'python version': sys.version,
                    'human notes': input('Could you explain a bit more about the error? What, How or When did the error happen?\nInput: '),
                    'traceback': ''.join(format_exception(exc_type, exc_value, exc_traceback)),
                    'log timestamp': content[timestamp_index: timestamp_index + 26] if 'timestamp_index' in locals() else None}
    
    with open(error_report_path, 'a' if Path(error_report_path).exists() else 'w') as f:
        dump(error_report, f)
        f.write('\n') # For the next errors, so it's possible to compound them.

    print('Creating issue archive...')
    with TemporaryDirectory() as tmp_dir:
        copy(error_report_path, f'{tmp_dir}/{error_report_path.name}')
        if 'timestamp_index' in locals():
            copy(log_path, f'{tmp_dir}/{log_path.name}')
        make_archive(f'{log_dir}/issue {datetime.date(datetime.now())}', 'zip', tmp_dir)

    print(f'error report generated at: "{error_report_path.absolute()}"')
    print_colored_text(f'Created an issue archive with the error report and log associated with it: "{log_dir}/issue {datetime.date(datetime.now())}.zip".\nPlease submit this to a developer!', [0, 255, 0])

    if 'timestamp_index' in locals():
        with open(log_path) as f:
            log_content = f.read()

    print('Automatically reporting the problem via formspree.io...')
    report_error(error_report, log_content if 'timestamp_index' in locals() else None)
    sys.exit(1)


def report_error(error_report: dict[str: Any], log: str | None = None):
    '''
    Reports an error by sending to an email using formspree.io

    :param error_report: A dictionary containing error metadata such as version, platform, and traceback.
    :type error_report: dict[str: Any]
    :param log: The log content associated with the error.
    :type log: str | None
    '''

    endpoint_url = 'https://formspree.io/f/xjgqgqbz'
    manual_report_prompt = 'Please report this manually yourself by sending an email to emilspro888@gmail.com or opening a GitHub issue at https://github.com/EMILIO888real/Packer/issues'

    headers = {
        'Accept': 'application/json'
    }
    
    payload = {
        'subject': 'Automated Crash Report',
        'error report': error_report,
        'log': log
    }
    
    try:
        response = post(endpoint_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print_colored_text('Successfully automatically reported a problem to developers.', [0, 255, 0])
        else:
            print_colored_text(f'Failed to report a problem. Status: {response.status_code}', [255, 0, 0])
            print(manual_report_prompt)
            
    except exceptions.RequestException as e:
        print_colored_text(f'Could not connect to the reporting server: {e}', [255, 0, 0])
        print(manual_report_prompt)