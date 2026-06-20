from datetime import datetime
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from traceback import format_exception
from json import dump, loads
from shutil import make_archive, copy
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
    
    print_colored_text(f'An error has occurred: Type: {exc_type} | Value: {exc_value}\nPlease report this to a developer via Discord or Github!', [255, 0, 0])

    print('Generating an error report...')

    error_report = {'packer version': packer_version,
                    'platform': sys.platform,
                    'python version': sys.version,
                    'human notes': input('Could you explain a bit more about the error? What, How or When did the error happen?\nInput: '),
                    'traceback': ''.join(format_exception(exc_type, exc_value, exc_traceback)),
                    'associated log file': None if not log_path.exists() else str(log_path)}
    
    with open(error_report_path, 'a' if Path(error_report_path).exists() else 'w') as f:
        dump(error_report, f)
        f.write('\n') # For the next errors, so it's possible to compound them.
    
    with open(error_report_path, 'r') as f:
        error_reports = f.readlines()
        for i in range(len(error_reports)):
            error_reports[i] = loads(error_reports[i])

    print('Creating issue archive...')
    with TemporaryDirectory() as tmp_dir:
        copy(error_report_path, f'{tmp_dir}/{error_report_path.name}')
        for error_report in error_reports:
            log_path = error_report['associated log file']
            if log_path:
                copy(log_path, f'{tmp_dir}/{log_path.name}')
        make_archive(f'{log_dir}/issue {datetime.date(datetime.now())}', 'zip', tmp_dir)

    print(f'error report generated at: "{error_report_path.absolute()}"')
    print_colored_text(f'Created an issue archive with the error report and log associated with it: "{log_dir}/issue {datetime.date(datetime.now())}.zip".\nPlease submit this to a developer!', [0, 255, 0])
    sys.exit(1)