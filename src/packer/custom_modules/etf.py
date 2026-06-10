from typing import Any


def print_list(items: list[Any], start: Any = '* ', end: Any = '\n', index: bool = False, index_text: str = '%i. '):
    '''
    Print a list of items with optional formatting.

    This function prints each item in a list, optionally with a prefix, suffix, and/or index numbers.
    It is designed to be flexible for various display purposes.

    :param items: A list of items to be printed.
    :type items: list[Any]
    :param start: A string to be printed before each item. Defaults to '* '.
    :type start: Any
    :param end: A string to be printed after each item. Defaults to '\n'.
    :type end: Any
    :param index: If True, each item will be printed with an index number. Defaults to False.
    :type index: bool
    :param index_text: A string to be used as the index format. Defaults to '%i. '.
    :type index_text: str
    '''

    if index:
        def print_index(i):
            print(index_text.replace('%i', str(i)), end='')
    else:
        def print_index(i):
            pass

    for i, item in enumerate(items):
        print_index(i)
        print(f'{start}{item}', end=end)