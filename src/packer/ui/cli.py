from argparse import ArgumentParser
from pathlib import Path
from shutil import rmtree
from sys import exit, argv

from packer.paths import root_dir, assets_dir, config_dir, log_dir, log_path, error_report_path, data_dir, cache_dir
from packer.config import packer_version


def _clear_path(path: str | Path) -> None:
    path = Path(path)
    rmtree(path, ignore_errors=True)
    print(f'Cleared {path}')


def main():
    parser = ArgumentParser('packer', description='Packer CLI tool')
    subparsers = parser.add_subparsers(dest='command')

    parser.add_argument('-p', '--paths', action='store_true', help='Output all storage paths')
    parser.add_argument('-v', '--version', action='store_true', help='Display the software\'s version')

    clear_command_parser = subparsers.add_parser('clear', help='Clear data produced (cache, saves and so on)')
    clear_command_parser.add_argument('-c', '--cache', action='store_true', help='Clear cache data')
    clear_command_parser.add_argument('-s', '--save', action='store_true', help='Clear config/settings data')
    clear_command_parser.add_argument('-l', '--log', action='store_true', help='Clear log directory')
    clear_command_parser.add_argument('-u', '--user', action='store_true', help='Clear user directory')

    args = parser.parse_args()

    if args.command == 'clear':
        targets = set()

        if args.cache:
            targets.add(cache_dir)
        if args.save:
            targets.add(config_dir)
        if args.log:
            targets.add(log_dir)
        if args.user:
            targets.add(data_dir)

        if not any((args.cache, args.save, args.log, args.user)):
            targets.update((cache_dir, config_dir, data_dir, log_dir))

        for target in targets:
            _clear_path(target)


    if args.paths:
        print(f'root_dir: {root_dir}')
        print(f'assets_dir: {assets_dir}')
        print(f'config_dir: {config_dir}')
        print(f'log_dir: {log_dir}')
        print(f'log_path: {log_path}')
        print(f'error_report_path: {error_report_path}')
        print(f'data_dir: {data_dir}')
        print(f'cache_dir: {cache_dir}')

    if args.version:
        print(f'Packer version {packer_version}')
    
    if len(argv) > 1:
        exit()