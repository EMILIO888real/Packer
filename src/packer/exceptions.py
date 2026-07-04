import sys
from datetime import datetime
from pathlib import Path
from traceback import format_exception
from json import dump
from typing import Any
from requests import post, exceptions
from pyperclip import copy
from webbrowser import open_new_tab
from urllib import parse

from packer.custom_modules.etf import print_colored_text, prompt_user


class Global_exception_handler:
    def __init__(self, software_version: str, log_path: Path, error_report_path: Path,
                 formspree_endpoint_url: str = None, developer_email: str = None, github_repo_url: str = None):
        self.software_version = software_version
        self.log_path = log_path
        self.error_report_path = error_report_path
        self.formspree_endpoint_url = formspree_endpoint_url
        self.developer_email = developer_email
        self.github_repo_url = github_repo_url

    def handle_exception(self, exc_type, exc_value, exc_traceback):
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
                        'software version': self.software_version,
                        'platform': sys.platform,
                        'python version': sys.version,
                        'human notes': user_notes,
                        'traceback': ''.join(format_exception(exc_type, exc_value, exc_traceback)),
                        'log': self.log_path.read_text() if self.log_path.exists() else None
                        }
        
        with open(self.error_report_path, 'a' if self.error_report_path.exists() else 'w') as f:
            dump(error_report, f)
            f.write('\n') # For the next errors, so it's possible to compound them.

        print_colored_text(f'error report generated at: "{self.error_report_path.absolute()}"', [0, 255, 0])

        if self.formspree_endpoint_url:
            print('Automatically reporting the problem via formspree.io...')
            if not self.report_error(error_report):
                if self.github_repo_url and prompt_user('Open the default email client if no then GitHub new issue creation will be opened in the default browser'):
                    copy(error_report)
                    print('We copied the error report to your clipboard')
                    open_new_tab(f'https://github.com/{self.github_repo_url}/issues/new')
                elif self.developer_email:
                    print('Specify your email if needed and hit send')
                    self.prompt_user_to_email(error_report)
        sys.exit(1)

    def report_error(self, error_report: dict[str: Any]) -> bool:
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

        
        manual_report_prompt = f'Please report this manually yourself by sending an email to {self.developer_email} or opening a GitHub issue at https://github.com/{self.github_repo_url}/issues'

        headers = {
            'Accept': 'application/json'
        }
        
        payload = {
            'subject': 'Automated Crash Report',
        }
        payload.update(error_report)
        
        try:
            response = post(self.formspree_endpoint_url, json=payload, headers=headers)
            
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

    def prompt_user_to_email(self, error_report: dict[str: Any]):
        '''
        Prompts the user to manually send an email with the error report.

        :param error_report: A dictionary containing the error metadata to be included in the email.
        :type error_report: dict[str: Any]
        '''
        
        subject = 'Automated Error Report'
        body = parse.quote(f'Please do not edit this block.\n\nError report:\n{error_report}')
        mailto_url = f"mailto:{self.developer_email}?subject={subject}&body={body}"

        open_new_tab(mailto_url)
    
    def update(self):
        sys.excepthook = self.handle_exception