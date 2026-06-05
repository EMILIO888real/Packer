from datetime import datetime
from os import mkdir
import sys
from traceback import format_exception
from json import dump
from shutil import make_archive, copy, rmtree
from packer.custom_modules.et import print_colored_text
from packer.config import packer_version
from packer.paths import log_path, error_report_path, log_dir


def global_exception_handler(exc_type, exc_value, exc_traceback):
    '''
    Global exception handler for uncaught exceptions.

    :param exc_type: The type of the exception being handled
    :param exc_value: The exception value (the actual exception object)
    :param exc_traceback: The traceback object containing the stack trace
    ''' 

    if issubclass(exc_type, KeyboardInterrupt) or issubclass(exc_type, SystemExit): # Ignore any errors when quitting the program.
        return
    
    print_colored_text(f'An error has occurred: Type: {exc_type} | Value: {exc_value}\nPlease report this to a developer via Discord or Github!', [255, 0, 0])

    print('Generating an error report...')
    error_report = {'packer version': packer_version,
                    'platform': sys.platform,
                    'python version': sys.version,
                    'human notes': input('Could you explain a bit more about the error? What, How or When did the error happen?\nInput: '),
                    'traceback': ''.join(format_exception(exc_type, exc_value, exc_traceback)),
                    'associated log file': log_path}


    with open(error_report_path, 'a') as f:
        dump(error_report, f)
        f.write('\n') # For the next errors, so it's possible to compound them.

    print('Creating issue archive...')
    tmp_dir = f'{log_dir}/temp dir'
    mkdir(tmp_dir)
    copy(error_report_path, f'{tmp_dir}/{error_report_path.name}')
    copy(log_path, f'{tmp_dir}/{log_path.name}')
    make_archive(f'{log_dir}/issue {datetime.now()}', 'zip', tmp_dir)
    rmtree(tmp_dir)

    print(f'error report generated at: "{error_report_path.absolute()}"')
    print_colored_text(f'Created an issue archive with the error report and log associated with it: "{log_dir}/issue {datetime.now()}.zip".\nPlease submit this to a developer!', [0, 255, 0])
    sys.exit(1)