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
from pdb import post_mortem
from queue import Queue

from packer.custom_modules.etf import print_colored_text, simple_prompt, bool_answer


class Global_exception_handler:
    '''
    A class to handle uncaught exceptions globally in a Python application.
    
    :param software_version: software version of the application, used for error reporting
    :type software_version: str
    :param log_path: path to the log file, used for error reporting
    :type log_path: Path
    :param error_report_path: path to the error report file, used for error reporting
    :type error_report_path: Path
    :param formspree_endpoint_url: endpoint URL for formspree.io, used for automatic error reporting
    :type formspree_endpoint_url: str
    :param developer_email: email address of the developer, used for manual error reporting
    :type developer_email: str
    :param github_repo_url: URL of the GitHub repository, used for manual error reporting
    :type github_repo_url: str
    :param input_queue: a queue for receiving user input, defaults to None
    :type input_queue: Queue | None
    :param output_queue: a queue for sending output messages, defaults to None
    :type output_queue: Queue | None

    methods:
    - handle_exception: handles uncaught exceptions, generates an error report, and optionally reports it, the raw function is set to sys.excepthook
    - update: updates the exception handler to use Packer's exception handler
    - report_error: attempts to automatically report the error to a remote service. Already called in handle_exception
    - prompt_user_to_email: prompts the user to manually send an email with the error report. Already called in handle_exception
    '''

    def __init__(self, software_version: str, log_path: Path, error_report_path: Path,
                 formspree_endpoint_url: str = None, developer_email: str = None, github_repo_url: str = None,
                 input_queue: Queue | None = None, output_queue: Queue | None = None):

        self.software_version = software_version
        self.log_path = log_path
        self.error_report_path = error_report_path
        self.formspree_endpoint_url = formspree_endpoint_url
        self.developer_email = developer_email
        self.github_repo_url = github_repo_url
        self.input_queue = input_queue
        self.output_queue = output_queue

        self._set_dynamic_functions()

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        '''
        Global exception handler for uncaught exceptions.

        :param exc_type: The type of the exception being handled
        :param exc_value: The exception value (the actual exception object)
        :param exc_traceback: The traceback object containing the stack trace
        ''' 

        if issubclass(exc_type, KeyboardInterrupt) or issubclass(exc_type, SystemExit): # Ignore any errors when quitting the program.
            return

        self.output_to_user(f'An error has occurred: Type: {exc_type} | Value: {exc_value}', [255, 0, 0])

        try:
            user_notes = self.user_input('Could you explain a bit more about the error? What, How or When did the error happen?\nInput: ')
        except KeyboardInterrupt:
            user_notes = None

        self.output_to_user('Generating an error report...')

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

        self.output_to_user(f'error report generated at: "{self.error_report_path.absolute()}"', [0, 255, 0])

        if self.formspree_endpoint_url:
            self.output_to_user('Automatically reporting the problem via formspree.io...')
            if not self.report_error(error_report):
                if self.github_repo_url and self.prompt_user('Open the default email client if no then GitHub new issue creation will be opened in the default browser'):
                    copy(error_report)
                    self.output_to_user('We copied the error report to your clipboard')
                    open_new_tab(f'https://github.com/{self.github_repo_url}/issues/new')
                elif self.developer_email:
                    self.output_to_user('Specify your email if needed and hit send')
                    self.prompt_user_to_email(error_report)
        
        try:
            if self.prompt_user('Enter interactive debugger', default='n'):
                self.output_to_user('Entering post-mortem session...')
                post_mortem(exc_traceback)
        except KeyboardInterrupt:
            pass

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

        
        MANUAL_ERROR_PROMPT = f'Please report this manually yourself by sending an email to {self.developer_email} or opening a GitHub issue at https://github.com/{self.github_repo_url}/issues'

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
                self.output_to_user('Successfully automatically reported a problem to developers.', [0, 255, 0])
                return True
            else:
                self.output_to_user(f'Failed to report a problem. Status: {response.status_code}', [255, 0, 0])
                self.output_to_user(MANUAL_ERROR_PROMPT)
                return False
                
        except exceptions.RequestException as e:
            self.output_to_user(f'Could not connect to the reporting server: {e}', [255, 0, 0])
            self.output_to_user(MANUAL_ERROR_PROMPT)
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
    
    def update(self, input_queue: Queue | None = None, output_queue: Queue | None = None):
        '''
        Updates the python exception handler through the sys.excepthook to use Packer's exception handler.

        :param input_queue: A queue for receiving user input, defaults to None
        :type input_queue: Queue | None, optional
        :param output_queue: A queue for sending output messages, defaults to None
        :type output_queue: Queue | None, optional
        '''

        self.input_queue = input_queue
        self.output_queue = output_queue
        self._set_dynamic_functions()
        sys.excepthook = self.handle_exception
    

    def _print_queue(self, text: str = '', color: list[int] = [138, 43, 226], end: str = '\n'):
        '''
        Puts a message into the output queue to be printed by the main thread.

        :param text: The message to be printed, defaults to ''
        :type text: str, optional
        :param color: The RGB color for the message, defaults to [138, 43, 226]
        :type color: list[int], optional
        :param end: The string appended after the message, defaults to '\n'
        :type end: str, optional
        '''

        self.output_queue.put({'text': text + end, 'color': color})
    
    def _prompt_queue(self, question: str, default: str | int = 'y') -> bool | None:
        '''
        Puts a prompt into the output queue and waits for a response from the input queue.
        
        :param question: The question to be asked to the user
        :type question: str
        :param default: The default answer if the user provides no input, defaults to 'y'
        :type default: str | int
        :return: The user's response converted to a boolean, or None if no response was given
        :rtype: bool | None
        '''

        self.output_queue.put({'question': question, 'default': default})
        answer = self.input_queue.get()
        return bool_answer(answer if answer else default)

    def _queue_input(self, prompt: str = '') -> str:
        '''
        Puts a prompt into the output queue and waits for a response from the input queue.
        
        :param prompt: The prompt to be displayed to the user, defaults to 
        :str, optional
        :return: The user's input as a string
        :rtype: str
        '''

        self.output_queue.put({'prompt': prompt})
        return self.input_queue.get()

    def _set_dynamic_functions(self):
        '''
        Sets all user related dynamic functions to either use the queue or the default functions based on the presence of input and output queues.
        '''

        self.output_to_user = self._print_queue if self.output_queue else print_colored_text
        self.prompt_user = self._prompt_queue if self.input_queue else simple_prompt
        self.user_input = self._queue_input if self.input_queue else input