from os import listdir, remove
from pathlib import Path
from shutil import unpack_archive
from tempfile import TemporaryDirectory
from json import loads
from platformdirs import user_downloads_path

from packer.custom_modules.etf import print_list, prompt_user
from packer.paths import log_dir

download_path = user_downloads_path()

def parse_issue(path: str | Path) -> dict[str: list[dict], str: dict[str: str]]:
    path = Path(path)

    with TemporaryDirectory() as tmpdir:
        unpack_archive(path, tmpdir, 'zip')
        files = listdir(tmpdir)

        logs = {}
        for file in files:
            with open(f'{tmpdir}/{file}') as f:
                if Path(file).suffix == '.json':
                    error_reports = f.readlines()
                    for i in range(len(error_reports)):
                        error_reports[i] = loads(error_reports[i])
                else:
                    logs[file] = f.read()
    results = {'error reports': error_reports}

    if logs != {}:
        results['logs'] = logs

    return results

def print_formatted(issue: dict):
    for error_report in issue['error reports']:
        print('-' * 150)
        for item in error_report.items():
            if item[0] != 'traceback':
                print(f'{item[0]}: {item[1]}')
        print(error_report['traceback'])
        log_file = error_report['associated log file']
        if log_file:
            print(issue['logs'][Path(log_file).name])
        

def tui():

    user_error = prompt_user('Parse a user issue')

    if user_error:
        issues = [Path(f'{download_path}/{issue}') for issue in listdir(download_path) if Path(issue).suffix == '.zip' and Path(issue).name.startswith('issue')]
        print_list(issues, index=True)
    else:
        issues = [Path(f'{log_dir}/{issue}') for issue in listdir(log_dir) if Path(issue).suffix == '.zip']
        print_list(issues, index=True, start='')
    
    if issues != []:
        index = int(input('Enter the index you wish to choose: '))
        print_formatted(parse_issue(issues[index]))
        if prompt_user('Delete the issue'):
            remove(issues[index])
    else:
        print('No error packages found')

if __name__ == '__main__':
    tui()