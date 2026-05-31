''' et -> tools
My module with some functions and classes for simplifying coding!😁

Requires:
    colorama: for compatibility with shell using ANSI escape codes
    keyboard: for detecting key strokes e.g. to cancel countdowns
    msvcrt: for flushing the input buffer
    pygame: for playing music
These aren't required for all functions but are used in some of them
You can install them using pip or other package managers
rest of the modules are builtin's

Functions:
    hide_cursor: hides the cursor
    show_cursor: shows the cursor
    clear_terminal(ANSI and from os system): clears the terminal
    clear_lines: clears specified amount of lines
    auto_start_message(ADVANCED and SIMPLE): warns user of continuing code while waiting for key input to cancel
    loading_terminal_animation: 3 dots loading animation
    character_loading_animation: character loading animation
    import_modules: imports functions from other modules
    flush_input: flushes the input buffer
    cinematic_dialogue: prints out a cinematic dialogue with a delay between each character
    info: prints out the docstring of the function
    reboot_current_script: reboots the current script
    change_color: changes the color of the terminal text using RGB values
    reset_formatting: resets the formatting of the terminal text
    dissolve_text: dissolves the text in the terminal using random characters
    style_terminal: a decorator to style the terminal for a function
    user_input: flushes the input buffer and returns the user input
    ask_user_repeatedly: asks the user a question and waits for a valid answer
    print_colored_text: prints out colored text
    options_selector: a simple options selector that allows the user to select an option using the up and down arrow keys
    set_raw_mode: sets the terminal to raw mode (unbuffered input), as well turns off echo

Classes:
    Loading_animations: A class for loading animation, more for terminal
    Methods:
        character_loading_animation: Simple terminal character loading animation | / - \\
        loading_terminal_animation: Simple terminal 3 dots loading animation . .. ...
        run: Runs a standardized function to start(previously known initializing) the animation
        stop: Stops the animation. This is a standardized function to stop the animation
        restart: Restarts the animation
    Attributes:
        animation_type: The type of animation to use, can be 'character' or 'dots
        text: The text to display with the animation
        allow_multiple: If True, allows multiple instances of the animation to run at the same time
    media_player: A class for playing music
    Methods:
        list_music: Lists all the music files in the specified path
        print_music: Prints out all the music files in the specified path

for more info use info(func) function on specific methods
'''

# import all outside modules neded here, so we don't try to import them each function call

from decimal import Decimal
from hashlib import sha256
from math import ceil
import sys
from collections.abc import Collection
from os import execl, path, replace, listdir, mkdir
from threading import Event # This is used for 2 functions in this module (loading_terminal_animation, character_loading_animation)
from typing import Any, Callable, Optional, Union
from pathlib import Path
from json import dump, load
from datetime import datetime
from shutil import ignore_patterns, which, copy2, copytree
from subprocess import Popen
import logging
from dirhash import dirhash
from requests import get, post

def hide_cursor() -> None:
    '''Hides the cursor
    uses ANSI escape codes'''
    print('\033[?25l', end='')

def show_cursor() -> None:
    '''Shows the cursor
    uses ANSI escape codes'''
    print('\033[?25h', end='')

def clear_terminal() -> None:
    '''Clears the terminal
    uses ANSI escape codes'''
    print('\033[2J\033[H', end='')

def clear_terminal_s() -> None:
    '''Clears the terminal
    using system from os module
    '''
    from os import system, name
    system('cls' if name == 'nt' else 'clear')

def clear_lines(lines_to_clear:int = 1, force_clear:bool = True, clear_formatting: bool = False) -> None:
    '''Clears specified lines of text from the terminal
    using ANSI escape codes
    
    :param lines_to_clear: specify the count of lines to clear
    :type lines_to_clear: int
    :param force_clear: specify whether to truly clear specified lines or just move the cursor back
    :type force_clear: bool
    '''
    if clear_formatting:
        reset_formatting()

    text_clearer = '\033[F'
    if force_clear:
        text_clearer += '\033[2K'
    for _ in range(lines_to_clear):
        print(text_clearer, end='')

def auto_start_message_s(message:str = 'Moving on to the next part of program in', wait_time:float = 10, abort:bool = True, abort_key_stroke:str = 'ctrl + x') -> bool:
    '''Warns the user with a message and countdown before executing next part of code SIMPLE VERSION
    This version uses time.sleep to calculate the time difference
    Returns False if countdown was interrupted otherwise True
    
    :param message: message to display to user
    :type message: str
    :param wait_time: time to wait before moving on to next part of code
    :type wait_time: float
    :param abort: if True waits for a key stroke to cancel the countdown
    :type abort: bool
    :param abort_key_stroke: key stroke to cancel the countdown
    :type abort_key_stroke: str
    :return: False if countdown was interrupted otherwise True
    :rtype: bool
    '''
    from time import sleep
    from threading import Event

    cancel_detected = Event()

    if abort:
        from threading import Thread
        from keyboard import wait

        def detect_abort():
            wait(abort_key_stroke)
            cancel_detected.set()

        interrupt_thread = Thread(target = detect_abort, daemon=True)
        interrupt_thread.start()

    while wait_time > 0 and cancel_detected.is_set() == False:
        clear_lines(1)
        print(message, round(wait_time, 1), 'seconds.')
        sleep(0.1)
        wait_time -= 0.1

    clear_lines(1)
    return False if cancel_detected.is_set() else True

def auto_start_message(message:str = 'Moving on to the next part of program in', wait_time:float = 10, abort:bool = True, abort_key_stroke:str = 'ctrl + x') -> bool:
    '''Warns the user with a message and countdown before executing next part of code ADVANCED VERSION
    This version uses datetime and timedelta to calculate the time difference
    returns False if countdown was interrupted otherwise True
    Parameters:
        message: message to display to user
        wait_time: time to wait before moving on to next part of code
        abort: if True waits for a key stroke to cancel the countdown
        abort_key_stroke: key stroke to cancel the countdown
    '''
    from time import sleep
    from threading import Event
    from datetime import datetime, timedelta

    cancel_detected = Event()

    if abort:
        from threading import Thread
        from keyboard import wait

        def detect_abort():
            wait(abort_key_stroke)
            cancel_detected.set()

        interrupt_thread = Thread(target = detect_abort, daemon=True)
        interrupt_thread.start()
    
    end_time = datetime.now() + timedelta(seconds = wait_time)

    while datetime.now() < end_time and not cancel_detected.is_set():
        remaining_time = (end_time - datetime.now()).total_seconds()
        clear_lines(1)
        print(message, round(remaining_time, 1), 'seconds.')
        sleep(0.1)

    clear_lines(1)
    return False if cancel_detected.is_set() else True

class Loading_animations():
    '''A class for loading animation, more for terminal.
    Contains all of the animation's functions themselves and as well an option to let a function set it up and stop it.
    You can also change the type of animation to be used and the text as well via the attributes(data).
    These are data attributes or just variables.
    Attributes:
        animation_type: The type of animation to use, can be 'character' or 'dots'
        text: The text to display with the animation
        allow_multiple: If True, allows multiple instances of the animation to run at the same time
    Methods:
        character_loading_animation: Simple terminal character loading animation | / - \\
        loading_terminal_animation: Simple terminal 3 dots loading animation . .. ...
        run: Runs a standardized function to start(previously known initializing) the animation
        stop: Stops the animation. This is a standardized function to stop the animation
        restart: Restarts the animation
    Usage/Example how to use:
    ```
    animation = Loading_animations()
    animation.run(text='Cooking ', type='character')  # or 'dots'
    # Do some work here
    animation.stop()  # Stops the animation and shows the cursor again
    ```
    '''
    # To do list:
    # 1. Make a check so you can't launch or run another instance of the animation at the same time while another one is already running.

    def __init__(self):
        self.animation_type: str = 'character'
        self.text: str = 'loading '
        self.allow_multiple: bool = False
        self.already_running: bool = False
    
    class RunError(Exception):
        pass

    def character_loading_animation(self, stop_condition: Event, wait_for_animation: Event, speed: float = 0.1, to_hide_cursor: bool = True, text: str = '') -> None:
        '''Simple terminal character loading animation | / - \\
        Use with the flag.wait() method in main thread to func correctly
        Warning: if you hide the cursor, you will have to call the show_cursor() function yourself after the animation is finished
        example:
            ```
            stop_condition = Event()
            wait_for_animation = Event()
            #Task running...
            #Task finished running!
            stop_condition.set()
            wait_for_animation.wait()
            Program continuation!
            ```
        Parameters:
            stop_condition: Condition to keep printing out the animation (reversed)
            wait_for_animation: an internal flag to determine when sub thread has finished.
            speed: time to wait before going to next phase of animation
            hide_cursor: If true hides the cursor after finishing shows it again, Uses the self.hide_show_cursor method
        '''
        from time import sleep
        from threading import Thread
        all_phases = ['|', '/', '-', '\\']
        def thread_func():
            while not stop_condition.is_set():
                for i in all_phases:
                    print(text + i, end='\r')
                    sleep(speed)
            print()
            clear_lines(1)
            wait_for_animation.set()
        if to_hide_cursor:
            hide_cursor()
        thread = Thread(target=thread_func, daemon=True)
        thread.start()

    def loading_terminal_animation(self, stop_condition: Event, wait_for_animation: Event, speed:float = 0.4, to_hide_cursor:bool = True, text: str = '') -> None:
        '''Simple terminal 3 dots loading animation . .. ...
        Use with the flag.wait() method in main thread to func correctly
        example:
            ```
            stop_condition = Event()
            wait_for_animation = Event()
            #Task running...
            #Task finished running!
            stop_condition.set()
            wait_for_animation.wait()
            Program continuation!
            ```
        Parameters:
            while_condition: Condition to keep printing out the animation (reversed)
            wait_for_animation: an internal flag to determine when sub thread has finished.
            speed: time to wait before going to next phase of animation
            hide_cursor: If true hides the cursor after finishing shows it again, Uses the self.hide_show_cursor method
        '''
        from threading import Thread
        from time import sleep
        def thread_func():
            loading_list = ['.', '..', '...']
            loading_list_loop = 0
            if to_hide_cursor:
                hide_cursor()
            while not stop_condition.is_set():
                print(f'{text + loading_list[loading_list_loop]:<{3 + len(text)}}', end='\r')  # Ensure the printed string is 3 characters long, padded with spaces
                loading_list_loop += 1
                if loading_list_loop == len(loading_list):
                    loading_list_loop = 0
                sleep(speed)
            print()
            clear_lines(1)
            wait_for_animation.set()

        if to_hide_cursor:
            show_cursor()

        thread = Thread(target = thread_func, daemon=True)
        thread.start()
    
    def run(self, text: str = '', type: str = '') -> None:
        '''Runs a standardized function to start(previously known initializing) the animation
        Parameters:
            text: The text to display with the animation
            type: the type of animation to initiate. There are 2 options character and dots
        '''
        if not self.already_running or self.allow_multiple:
            self.already_running = True
            self.stop_condition = Event()
            self.wait_for_animation = Event()
            if type == '':
                type = self.animation_type
            match type:
                case 'character':
                    self.character_loading_animation(self.stop_condition, self.wait_for_animation, text=self.text if text == '' else text)
                case 'dots':
                    self.loading_terminal_animation(self.stop_condition, self.wait_for_animation, text=self.text if text == '' else text)
        else:
            raise self.RunError('The animation is already running! If you still want to launch it you can change the attribute: allow_multiple.')

    def stop(self, to_hide_cursor: bool = True) -> None:
        '''Stops the animation. This is a standardized function to stop the animation
        Parameters:
            to_hide_cursor: If True, hides the cursor after finishing shows it again
        '''
        if self.already_running or self.allow_multiple:
            self.already_running = False
            self.stop_condition.set()
            self.wait_for_animation.wait()
            if to_hide_cursor:
                show_cursor()
        else:
            raise self.RunError('The animation isn\'t running! If you still want to stop it you can change the attribute: allow_multiple.')
    
    def restart(self, text: str = '') -> None:
        '''Restarts the animation
        This is a standardized function to restart the animation
        Parameters:
            text: The text to display with the animation, if not specified uses the self.text attribute
        '''
        self.stop()
        if text != '':
            self.text = text
        self.run()

def import_modules(all_modules: dict) -> None:
    '''Imports all functions from all modules in the all_modules dictionary
    FROM (KEYWORD) VERSION

    Parameters:
        all_modules: dictionary with keys as module names and values as lists of functions to import
    '''
    from importlib import import_module
    missing_modules = []

    for module_name, functions in all_modules.items():
        try:
            module = import_module(module_name)
            for func in functions:
                globals()[func] = getattr(module, func)
        except ModuleNotFoundError:
            missing_modules.append(module_name)
        except AttributeError as e:
            print(f'Function not found: {e}')
    return missing_modules

def flush_input(win_only: bool = False) -> None:
    '''Flushes the input buffer
    Parameters:
        win_only: If True, only works on Windows'''
    from sys import platform
    match platform:
        case 'win32':
            from msvcrt import kbhit, getch
        case 'linux':
                if not win_only:
                    from sys import stdin
                    from select import select

                    def kbhit():
                        return bool(select([stdin], [], [], 0)[0])

                    def getch():
                        return stdin.read(1)
    while kbhit():
        getch()

def cinematic_dialogue(dialogs: dict, dialogs_type: str, dialogs_index: int, wait: bool = True, delay: float = 0.03, randomize_color: bool = True, do_reset_formatting: bool = True, hidden_cursor: bool = False,
                       wait_time: float = 1.0, clear_text_on_finish: bool = True) -> None:
    '''Prints out a cinematic dialogue with a delay between each character
    Parameters:
        dialogs: dictionary with keys as dialogue types and values as lists of dialogues
        dialogs_type: type of dialogue to print
        dialogs_index: index of dialogue to print
        wait: if True waits for the specified time before moving on to the next part of code
        delay: delay between each character
        randomize_color: if True randomizes the color of the text
        do_reset_formatting: if True resets the formatting of the text after printing
        hidden_cursor: if True hides the cursor during the animation
        wait_time: time to wait before moving on to the next part of code
        clear_text_on_finish: if True clears the text after printing
    '''

    if randomize_color:
        from random import randint
    from time import sleep
    if hidden_cursor:
        hide_cursor()

    for i in dialogs[dialogs_type][dialogs_index]:
        if randomize_color:
            change_color([randint(0, 255), randint(0, 255), randint(0, 255)])
        print(i, end = '', flush = True)
        sleep(delay)
    if wait:
        sleep(wait_time)
    if do_reset_formatting:
        reset_formatting()
    if clear_text_on_finish:
        print()
        clear_lines(1)
    if hidden_cursor:
        show_cursor()

def info(func):
    '''Prints out the docstring of the function'''
    print(func.__doc__)

class media_player():
    '''A class for playing music
    Methods:
        list_music: Lists all the music files in the specified path
        print_music: Prints out all the music files in the specified path
    '''
    def __init__(self):
        from pygame import mixer
        clear_terminal()
        mixer.init()
        self.mixer = mixer

    def list_music(self, path: str = 'Music') -> list:
        '''Lists all the music files in the specified path'''
        from os import listdir
        return listdir(path)

    def print_music(self, path: str = 'Music', exclude_file_extension: bool = True, max_character_length: int = 130) -> None:
        '''Prints out all the music files in the specified path'''
        if exclude_file_extension:
            index = 0
            for i in self.list_music(path):
                i = i.split('.')[0]
                print(f'nr.{index} {i[:max_character_length]}', end='')
                if len(i) > max_character_length:
                    print('...')
                else:
                    print()
                index += 1

def reboot_current_script() -> None:
    '''Reboots the current script'''
    python = sys.executable
    execl(python, python, *sys.argv)

def change_color(color: list = [138, 43, 226]) -> None:
    '''Changes the color of the terminal text using RGB values
    example is blue violet color
    Parameters:
        color: A list of three integers [R, G, B] representing the RGB color
    '''
    print(f'\033[38;2;{color[0]};{color[1]};{color[2]}m', end='')

def reset_formatting() -> None:
    '''Resets the formatting of the terminal text'''
    print('\033[0m', end='')

def dissolve_text(text: str = 'Average sentence is about this long, not really longer!', delay: float = 0.04,
                  randomize_color: bool = False, single_character_color: bool = False,
                  cinematic_display: bool = False, cinematic_delay: float = 0.001, dynamic_cinematic_display: bool = False,
                  multi_character_replace: bool = False, max_characters_to_replace: int = 3, stop_too_many_reroll: bool = False, chance_to_repeat: int = 2,
                  limit_time: bool = False, max_time: float = 5.0, cinematic_time_text:bool = False, time_text_delay: float = 1.0,
                  multiple_lines: bool = False, do_reset_formatting: bool = True, do_hide_cursor: bool = True) -> None:

    '''Dissolves the text in the terminal using random characters
    Parameters:
        text: The text to dissolve
        delay: The delay between each character in seconds
        randomize_color: If True, randomizes the color of the text
        single_character_color: If True, randomizes the color of each character in the text. Only active if cinematic_display is.
        cinematic_display: If True, displays the text in a cinematic way
        cinematic_delay: The delay between each character in cinematic display
        dynamic_cinematic_display: If True, displays the text in a cinematic way rewriting the text every time
        multi_character_replace: If True, replaces multiple characters at the same time
        max_characters_to_replace: The maximum number of characters to replace at the same time
        stop_too_many_reroll: If True, won't allow the same specific character to be rerolled multiple times in a row
        chance_to_repeat: The chance to repeat the same character multiple times in a row. The higher the number, the lower the chance. 2 = 33.3% chance, 3 = 25% chance, etc.
        limit_time: If True, limits the time for the animation to finish
        max_time: The maximum time for the animation to finish in seconds
        cinematic_time_text: If True, displays the text in a cinematic way after the time limit expires
        time_text_delay: The delay between each character in cinematic display with a time limit. This parameter is proportional to the delay parameter
        multiple_lines: If True, clears the screen more often to not make the text duplicate itself
        do_reset_formatting: Resets the formatting after the animation, good for colors.
        do_hide_cursor: If True, hides the cursor during the animation
    This function is a bit goofy and not very efficient, just a fun little project.
    Could be improved in the future, but for now it works well enough.
    '''

    # To do list:
    #   1. Fix the multiple lines , it doesn't clear the entire screen, and when it does it doesn't work as intended. New lines characters disappear?

    # These modules are necessary for the function to work

    from random import randint
    from time import sleep
    from string import punctuation, digits, ascii_letters

    # These modules are optional and only used if some arguments are set to True

    if limit_time:
        from datetime import datetime, timedelta
    
    # Generates a list of all characters to use for dissolving the text

    all_characters = list(punctuation.replace('"', '').replace("'", "").replace('\'', '') + digits + ascii_letters)
    all_characters_len = len(all_characters)

    # Generates a random string of characters to use for dissolving the text, skipping spaces

    dissolved_text = ''
    text_len = len(text)

    i = 0
    while len(dissolved_text) < text_len:
        if not text[i].isspace():
            dissolved_text += all_characters[randint(0, all_characters_len - 1)]
            while dissolved_text[i] == text[i]:
                dissolved_text = dissolved_text[:i] + all_characters[randint(0, all_characters_len - 1)] + dissolved_text[i + 1:]
        else:
            dissolved_text += ' '
        i += 1
    
    # execute some extra code for optional arguments

    if do_hide_cursor:
        hide_cursor()

    if limit_time:
        end_time = datetime.now() + timedelta(seconds=max_time)

    if multi_character_replace:
        i_end = len(text)
    else:
        i_end = i + 1

    repeated_characters = [0 for _ in range(text_len)] # Have to generate this list regardless if the parameter is set to False, the if condition checks it
    
    # Main animation loop

    while dissolved_text != text:
        i = randint(0, len(dissolved_text) - 1) # Randomly selects a character to dissolve
        if multi_character_replace:
            i_end = i + randint(1, max_characters_to_replace)
            if i_end > len(text) - 1:
                i_end = i + 1
        else:
            i_end = i + 1
        if limit_time: # Checks if the time limit has been reached
            if end_time < datetime.now():
                if cinematic_time_text:
                    for i in range(len(text)):
                        print(text[i], end='', flush=True)
                        sleep(delay * time_text_delay)
                break
        if (dissolved_text[i:i_end].count(' ') == 0) and (dissolved_text[i:i_end] != text[i:i_end]): # Checks if the character is not a space and is not the same as the original text
            dissolved_text = dissolved_text[:i] + text[i:i_end] + dissolved_text[i_end:] # Replaces the character with the original text
            if randint(0, chance_to_repeat) == 0 and repeated_characters[i] < 2: # 33.3% chance to replace the character with a random character
                replace_characters = ''
                for _ in range(i_end - i): # Generates a random string of characters to use for dissolving the text
                    replace_characters += all_characters[randint(0, all_characters_len - 1)]
                dissolved_text = dissolved_text[:i] + replace_characters + dissolved_text[i_end:]
                if stop_too_many_reroll:
                    repeated_characters[i] += 1
            if randomize_color: # randomize the color of the text
                change_color([randint(0, 255), randint(0, 255), randint(0, 255)])
            if cinematic_display: # cinematic display of the text
                cinematic_dialogue({'text': [dissolved_text]}, 'text', 0, False, cinematic_delay, single_character_color, do_reset_formatting=False, clear_text_on_finish=dynamic_cinematic_display)
                if not dynamic_cinematic_display:
                    print(end='\r')
            if multiple_lines:
                clear_terminal()
            if not cinematic_display: # prints the text in a normal way
                print(dissolved_text, end='\r')
            sleep(delay)

    # Last text clean up after the animation

    if randomize_color or single_character_color and do_reset_formatting:
        reset_formatting()
    if do_hide_cursor:
        show_cursor()
    if multiple_lines:
        clear_terminal()
    print('\r' + text)

def style_terminal(raw_mode: bool = True, terminal_settings: list = None) -> None:
    '''A decorator to style the terminal for a function
    Parameters:
        raw_mode: If True, expects unbuffered input for the function, you can use the set_raw_mode() function to set it up
        terminal_settings: If not None, sets the terminal to the specified settings otherwise changes to enable echo and input buffering
    Note: This decorator only works on Linux systems'''
    def decorator(func):
        def wrapper(*args, **kwargs):
            from sys import platform
            match platform:
                case 'linux':
                    from sys import stdin
                    from termios import tcsetattr, tcgetattr, ECHO, ICANON, TCSAFLUSH
                    if raw_mode:
                        fd = stdin.fileno()
                        if terminal_settings is None:
                            current_terminal = tcgetattr(fd)
                            current_terminal[3] |= current_terminal[3] | ECHO | ICANON
                            tcsetattr(fd, TCSAFLUSH, current_terminal)
                        else:
                            tcsetattr(fd, TCSAFLUSH, terminal_settings)
            results =  func(*args, **kwargs)
            set_raw_mode()
            return results
        return wrapper
    return decorator

@style_terminal()
def user_input(values: object = '', lower_it: bool = True) -> str:
    '''Flushes the input buffer and returns the user input
    This is a more polished version of the input function for more typical use cases
    Parameters:
        values: The values to display to the user
        lower_it: If True, converts the input to lowercase
    '''

    flush_input()
    if lower_it:
        user_input_data = input(values).lower().strip()
    else:
        user_input_data = input(values).strip()
    return user_input_data

def ask_user_repeatedly(question: str, default: str = 'y', valid_answers: list = ['y', 'n'], delay: float = 1.0, lower_it: bool = True, do_hide_cursor: bool = True) -> str:
    '''Asks the user a question and waits for a valid answer
    Parameters:
        question: The question to ask the user
        default: The default answer to the question
        valid_answers: The valid answers to the question.
        delay: The delay between each question, when the answer is invalid
        lower_it: If True, converts the input to lowercase
        do_hide_cursor: If True, hides the cursor, when the answer is invalid
    Returns:
        the user answer
    '''
    from time import sleep
    user_answer = None
    
    while user_answer not in valid_answers:
        user_answer = user_input(question, lower_it)
        if user_answer == '':
            user_answer = default
        if user_answer in valid_answers:
            return user_answer
        else:
            if do_hide_cursor:
                hide_cursor()
            print('Invalid input!')
            if do_hide_cursor:
                show_cursor()
            sleep(delay)
            clear_lines(2)

def print_colored_text(text: str = '', color: list[int] = [138, 43, 226], reset: bool = True, flush: bool = False, end: str = '\n') -> None:
    '''Prints out colored text
    Parameters:
        text: the text to print out
        color: the color the text is going to be printed out in
        reset: If true resets the terminal font after printing out the text'''
    change_color(color)
    print(text, flush=flush, end=end)
    if reset:
        reset_formatting()

def options_selector(options: list[str] = ['1. options', '2. option'], color: list[int] = [138, 43, 226], speed: float = 0.005, selected: int = 0) -> int:
    '''A simple options selector that allows the user to select an option using the up and down arrow keys
    It returns the index of the selected option.
    Inspired and based on the GitHub CLI.
    Parameters:
        options: A list of options to choose from
        color: A list of RGB values to set the color of the selected option
        speed: The speed of retrashrate, how fast the options are switched
        selected: The index of the selected option, defaults to 0. Use this to set the default selected option
    '''
    from keyboard import is_pressed
    from time import sleep

    hide_cursor()
    options_len = len(options)
    last_value = options_len - 1
    selecting_options = True
    selected_option_changed = False
    previous_selected = None
    
    while selecting_options:
        for option in range(options_len):
            if option == selected:
                print_colored_text(options[option], color)
            else:
                if not selected_option_changed and selected != previous_selected:
                    print(options[option])
                else:
                    print('\033[1B')
        previous_selected = selected
        print(f'\033[{options_len + 1}A\033[0G')
        nether_key_pressed = True
        while nether_key_pressed:
            if is_pressed('up') and selected != 0:
                selected -= 1
                nether_key_pressed = False
                while is_pressed('up'):
                    sleep(speed)
            elif is_pressed('down') and selected != last_value:
                selected += 1
                nether_key_pressed = False
                while is_pressed('down'):
                    sleep(speed)
            elif is_pressed('Enter'):
                selecting_options = False
                print(f'\033[{options_len - selected + 1}B')
                clear_lines(4)
                return selected
            pass

def set_raw_mode() -> list:
    '''Sets the terminal to raw mode (unbuffered input), as well turns off echo
    Returns:
        the previous terminal settings as a list, not mandatory to use
    Note: This function only works on Linux systems'''
    
    from termios import ICANON, ECHO, TCSAFLUSH, tcsetattr, tcgetattr
    from atexit import register
    from sys import stdin

    fd = stdin.fileno()
    default_terminal = tcgetattr(fd)
    raw_terminal = tcgetattr(fd)
    raw_terminal[3] = raw_terminal[3] & ~ICANON & ~ECHO

    register(lambda : tcsetattr(fd, TCSAFLUSH, default_terminal)) # execute's once at the end of the program to reset the terminal to previous settings.
    tcsetattr(fd, TCSAFLUSH, raw_terminal) # sets the terminal to unbuffered or changes it's settings.

    return default_terminal

def graph_drawer(points: list[list[int]], size: int = 10, background: str = '~', multiplier: int = 1):
    '''
    Draws a simple graph in the terminal using ASCII characters
    Parameters:
        points: A list of tuples representing the points to plot on the graph
        size: The size of the graph (size x size)
        background: The character to use for the background of the graph
        multiplier: The multiplier to use for the x-axis
    '''

    # Could make another option for drawing the graph, instead of printing each character one after the next, rather instead it might be more efficient to build a string and just print it once.

    for pair in points:
        for cord in pair:
            if cord < 0:
                print('Negative feed!') # Temp
                exit()

    points = sorted(points, key=lambda points:points[1]) # Sorts the graph by the y cords.

    sorted_x = False
    while not sorted_x:
        sorted_x = True
        for i in range(1, len(points)):
            if points[i][1] == points[i - 1][1]:
                if points[i - 1][0] > points[i][0]:
                    temp = points[i][0]
                    points[i][0] = points[i - 1][0]
                    points[i - 1][0] = temp
                    sorted_x = False

    for pair in points:
        print(pair)

    points_last_i = len(points) - 1
    i = 0
    comparison_i = 1
    went_down = False # Temp
    for y in range(size):
        for x in range(size * multiplier):
            if points[i][0] == x and points[i][1] == y:
                if (points[comparison_i][0] == x) and (points[comparison_i][1] == y + 1 or points[comparison_i][1] == y - 1):
                    print('|', end='')
                elif (points[comparison_i][0] == x + 1 or points[comparison_i][0] == x - 1) and (points[comparison_i][1] == y):
                    print('-', end='')
                elif points[comparison_i][0] - points[i][0] == points[comparison_i][1] - points[i][1]:
                    print('\\', end='')
                    went_down = True # Temp
                else:
                    print('/', end='')
                i += 1 if i != points_last_i else 0
                comparison_i = i - 1
            else:
                print(background, end='')
        print()
    else:
        if went_down:
            exit()

def generate_points(size: int = 10, fps: int = 10, multiplier: int = 4, vertical: bool = True, back_ground: str = '~', smooth_turns: bool = True):
    
    from time import sleep
    from random import randint

    # To do list:
    # 1. Make the smooth_turns parameter. It should smooth out turning the graph rapidly, by adding a straight section, before and after every turn.
    # For example: -\
    #               |
    #               /

    hide_cursor()
    speed = 1 / fps # Called fps, because this function is a display function, while the main function or logic is draw_graph()
    points = []
    try:
        while True:
            if vertical:
                randomized_cord = randint(0, size * multiplier - 1)
            else:
                randomized_cord = randint(0, size - 1)
            points.clear()
            for linear_cord in range(size):
                points.append([linear_cord, randomized_cord])
                randomized_cord += randint(-1, 1)
                while randomized_cord < 0 or randomized_cord > size:
                    randomized_cord += randint(-1, 1)
            graph_drawer(points, size, back_ground, multiplier)
            sleep(speed)
            clear_terminal_s()
    except KeyboardInterrupt:
        show_cursor()

def scrollable_text_display(text: str = 'You can even win a reward! Awesome right? To sign up just call +371 26 634 954', condition: Event | Callable[[], bool] = lambda: True,
                            size: int = 30, speed: float = 0.05,
                            continues: bool = False, start_up: bool = True, wait_for_exit: Optional[Event] = None, spaces: int = 0, hidden_cursor: bool = True,
                            once_startup: bool = False,
                            display_colors: bool = False, color: Optional[list[int] | list[list[int]] | str ] = 'random', single_char_color: bool = True, static_colors: bool = False,
                            moving_static_colors: bool = False, remember_colors: bool = False) -> None:
    '''Displays a scrollable text in the terminal
    Parameters:
        text: The text to display
        condition: The condition to stop the scrolling, can be an Event or a callable that returns a boolean
        size: The size of the display window
        speed: The speed of the scrolling
        continues: If True, the text will continue scrolling from the beginning after reaching the end
        start_up: If True, the text will be displayed character by character at the start
        wait_for_exit: If not None, an Event that will be set when the scrolling stops
        spaces: The number of spaces to add at the end of the text
        hidden_cursor: If True, hides the cursor during the scrolling
    '''

    # Also would like to optimize and write this function in a more clean way! <!>
    # Fix a bug where the colors are incorrectly used for the next cycle with continues and remember colors.

    from time import sleep
    from threading import Thread

    if display_colors and color == 'random':
        from random import randint

    text += ' ' * spaces
    text_len = len(text)

    if continues:
        end = '\r'
    else:
        end = '\n'

    if hidden_cursor:
        hide_cursor()

    # Color handling, generating, using provided, fixing it and so on

    if type(color) != str:
        if type(color[0]) == list:
            all_colors = color[:]
            color = 'random'
            remember_colors = True
    elif color == 'random':
        all_colors = [[randint(0, 255) for _ in range(3)] for _ in range(text_len)]

    if len(all_colors) <= text_len:
        for i in range(size + spaces if continues else 0):
            all_colors.append(all_colors[i])
    colors = all_colors[:size]

    def main():

        nonlocal start_up, colors

        # The start up parameter

        condition_type = type(condition)
        while not condition.is_set() if condition_type == Event else condition():
            if start_up:
                if moving_static_colors and not remember_colors:
                    colors = [[randint(0, 255) for _ in range(3)] for _ in range(size)]
                if display_colors and not static_colors:
                    change_color([randint(0, 255) for _ in range(3)] if color == 'random' else color)

                for char in range(len(text[0:size])):
                    if single_char_color and display_colors:
                        print_colored_text(text[char], colors[char] if moving_static_colors else ([randint(0, 255) for _ in range(3)] if color == 'random' else color), flush=True, end='')
                    else:
                        print(text[char], flush=True, end='')
                    sleep(speed)
                print(end='\r')

                if once_startup:
                    start_up = False

            # Main animation generation loop

            if static_colors and not moving_static_colors:
                colors = [[randint(0, 255) for _ in range(3)] for _ in range(text_len)]

            for i in range(text_len):
                processed_text = f'{text[i: size + i - (size + i - text_len if size + i >= text_len else 0)]}{(text[0:size + i - text_len] if size + i >= text_len else '') if continues else ''}'
                if display_colors:
                    if single_char_color:
                        for char in range(len(processed_text)):
                            print_colored_text(processed_text[char], colors[char] if static_colors else ([randint(0, 255) for _ in range(3)] if color == 'random' else color), flush=True, end='')
                        print(end=end)
                    else:
                        print_colored_text(processed_text, [randint(0, 255) for _ in range(3)] if color == 'random' else color, flush=True, end=end)
                else:
                    print(processed_text, flush=True, end=end)
                if not continues:
                    clear_lines()
                if moving_static_colors:
                    colors.pop(0)
                    if remember_colors:
                        if i == text_len - 1:
                            colors = all_colors[:size]
                        else:
                            colors.append(all_colors[size + i])
                    else:
                        colors.append([randint(0, 255) for _ in range(3)])
                sleep(speed)

        if wait_for_exit is not None:
            wait_for_exit.set()
            if hidden_cursor:
                show_cursor()

    message_thread = Thread(target=main, daemon=True)
    message_thread.start()

def color_generator(text_len: int = 78, save_to_disk: bool = True, color_scheme: str = 'random', style: int = 0, read_from_disk: bool = False):
    '''Generates a list of colors based on the specified color scheme
    Parameters:
        text_len: The length of the text to generate colors for
        save_to_disk: If True, saves the generated colors to a file
        color_scheme: The color scheme to use for generating colors (neon_cyberpunk: 2, neon: 1)
        style: The style of the color scheme to use (0, 1, ...)
        read_from_disk: If True, reads the colors from a file instead of generating them
    '''

    # Add check for read from disk, type shi. File name, and so on

    from pathlib import Path
    from random import randint
    from itertools import islice, cycle

    if read_from_disk:
        with open('.colors.txt') as f:
            colors = {}
            exec(f.read(), {}, colors)
        return colors['colors']
    else:
        match color_scheme:
            case 'random':
                colors = [[randint(0, 255) for _ in range(3)] for _ in range(text_len)]
            case 'neon_cyberpunk':
                match style:
                    case 0:
                        preset_colors = [[112, 34, 144], [223, 0, 216], [18, 188, 197], [26, 64, 123], [17, 30, 54]]
                    case 1:
                        preset_colors = [[204, 17, 240], [99, 0, 255], [255, 0, 141], [209, 78, 234], [249, 99, 99]]
            case 'neon':
                preset_colors = [[78, 237, 233], [115, 237, 28], [255, 230, 0], [240, 0, 255], [0, 35, 255]]
        colors = list(islice(cycle(preset_colors), text_len))

        if not Path('.colors.txt').exists() and save_to_disk:
            with open('.colors.txt', 'w') as f:
                f.write('colors = ' + str(colors))
        return colors

def fade_animation(background_color: list[int] = None):
    # Try to make an animation to fade in and or out text. The text could start at the same color as the background and gradually change to the desired color.
    # Could also do it the other way around.
    pass

def read_json(file_name: str | Path, default_values: Optional[dict] = {}, indent: int = 4, create: bool = True) -> dict:
    '''
    Reads a JSON file and returns the data as a dictionary. If the file does not exist, it creates it with the default values.
    
    :param file_name: The name of the JSON file to read
    :type file_name: str | Path
    :param default_values: The default values to use if the file does not exist
    :type default_values: dict
    :param indent: The number of spaces to use for indentation in the JSON file
    :type indent: int
    :param create: If True, creates the file with default values if it does not exist
    :type create: bool
    :return: The data from the JSON file as a dictionary
    :rtype: dict
    '''

    if create and not Path(file_name).exists():
        with open(file_name, 'w') as f:
            dump(default_values, f, indent=indent)
    with open(file_name, 'r') as f:
        return load(f)

def merge_settings(user_settings: dict, default_settings: dict) -> dict:
    '''
    Merges user settings with default settings, filling in any missing values from the default settings.
    
    :param user_settings: The user settings to merge
    :type user_settings: dict
    :param default_settings: The default settings to use for missing values
    :type default_settings: dict
    :return: The merged settings as a dictionary
    :rtype: dict
    '''

    settings = {}
    for setting in default_settings.items():
        current_setting = user_settings.get(setting[0])
        if current_setting == None:
            current_setting = default_settings[setting[0]]
        settings[setting[0]] = current_setting
    return settings

def copy_with_exceptions(source: str | Path, destination: str | Path, exceptions: Optional[Collection[str]] = (), directory_exceptions: Optional[Collection[str]] = ()) -> None:
    '''
    Copies files and directories from source to destination, excluding specified exceptions.
    
    :param source: The source path to copy from
    :type source: str | Path
    :param destination: The destination path to copy to
    :type destination: str | Path
    :param exceptions: A sequence of file or directory names to exclude from copying
    :type exceptions: Sequence[str]
    :param directory_exceptions: A sequence of directory names to exclude from copying when encountered within the source directory
    :type directory_exceptions: Sequence[str]
    '''

    if not Path(destination).exists():
        mkdir(destination)

    for item in listdir(source):
        if item in exceptions:
            continue
        item = Path(f'{source}/{item}')
        if Path(item).is_file():
            copy2(item, Path(destination))
        else:
            copytree(item, Path(f'{destination}/{item.name}'), ignore=ignore_patterns(*directory_exceptions))

def log_action(text: str, file_name: str | Path, end: str = '\n') -> None:
    '''
    Logs an action by appending the specified text to a log file.
    
    :param text: The text to log
    :type text: str
    :param file_name: The name of the log file to append to
    :type file_name: str | Path
    :param end: The string to append at the end of the log entry (default is a newline character)
    :type end: str
    '''

    with open(file_name, 'a') as f:
        f.write(f'{text}{end}')

def format_text(text: str, index: int, var: Any) -> str:
    '''
    formats text by inserting a variable at a specific index
    
    :param text: text to format
    :type text: str
    :param index: index to insert the variable at
    :type index: int
    :param var: variable to insert
    :type var: Any
    :return: formatted text
    :rtype: str
    '''
    return f'{text[:index]}{var}{text[index:]}'

def create_log_message(action: str, action_type: str, text: str = '[%A] %t %a', time_format_code: str = '%Y-%m-%d %H:%M:%S.%f', relative_time: bool = True, last_log_time: datetime = None) -> None:
    '''
    Creates a log message by replacing placeholders in the text with the specified values.
    
    :param action: The description of the action being logged
    :type action: str
    :param action_type: The type of action being logged (e.g., 'INFO', 'ERROR', 'WARNING')
    :type action_type: str
    :param text: The log message template containing placeholders for action type (%A), time (%t), and action description (%a)
    :type text: str
    :param time_format_code: The format code to use for formatting the time placeholder (%t) if relative_time is False (default is '%Y-%m-%d %H:%M:%S.%f')
    :type time_format_code: str
    :param relative_time: If True, replaces the time placeholder (%t) with the relative time since the last log entry; if False, formats the current time using the specified time_format_code (default is True)
    :type relative_time: bool
    :param last_log_time: The datetime of the last log entry, used for calculating relative time if relative_time is True
    :type last_log_time: datetime
    '''

    text = text.replace('%A', action_type)
    text = text.replace('%t', str(datetime.now() - last_log_time if relative_time else datetime.strftime(datetime.now(), time_format_code)))
    text = text.replace('%a', action)
    return text

def noop() -> None:
    '''A no-operation function that does nothing, used as a placeholder or default value for callbacks and other function parameters where no action is desired.'''
    pass

def launch_in_new_terminal(script_path: str) -> bool:
    '''
    Launches a Python script in a new terminal window, with support for both Windows and Linux/WSL environments.
    
    :param script_path: The file path of the Python script to launch in a new terminal window
    :type script_path: str
    :return: True if the terminal was successfully launched, False otherwise
    '''

    # -------------------------
    # WINDOWS OUT OF COMMISSION (doesn't work)
    # -------------------------
    if sys.platform == 'win32':
        print('Windows is temporary unsupported for automatic error report handler execution!')
        # Prefer Windows Terminal if available. OUT OF COMMISSION (doesn't work)
        wt = which('wt.exe')
        if wt:
            Popen([wt, "powershell", "-NoExit", "--%", sys.executable, script_path])
            return True

        # Fallback: PowerShell. OUT OF COMMISSION (doesn't work)
        powershell = which('powershell.exe')
        if powershell:
            Popen([powershell, '-NoExit', '-Command', f'"{sys.executable}" "{script_path}"'])
            return True

        # Fallback: CMD OUT OF COMMISSION (doesn't work)
        cmd = which('cmd.exe')
        if cmd:
            Popen([cmd, '/k', f'"{sys.executable}" "{script_path}"'])
            return True

        return False

    # -------------------------
    # LINUX / WSL
    # -------------------------
    terminals = [
        ('gnome-terminal', ['--']),
        ('konsole', ['-e']),
        ('xfce4-terminal', ['--command']),
        ('xterm', ['-e']),
        ('lxterminal', ['-e']),
        ('mate-terminal', ['-e']),
        ('tilix', ['-e']),
        ('alacritty', ['-e']),
        ('kitty', ['-e']),
        ('urxvt', ['-e']),
    ]

    for term, args in terminals:
        if which(term):
            Popen([term] + args + [sys.executable, script_path])
            return True

    return False

def format_time(seconds: float, time_format: str = '%M:%S.%m') -> str:
    '''Formats a time duration given in seconds into a human-readable string format (e.g., "0:4:56.456").
    
    :param seconds: The time duration in seconds to format
    :type seconds: float
    :return: A formatted string representing the time duration in hours, minutes, and seconds
    :rtype: str
    '''

    time_format = time_format.replace('%H', f'{int(seconds // 3600)}')
    time_format = time_format.replace('%M', f'{int((seconds % 3600) // 60)}')
    time_format = time_format.replace('%S', f'{int(seconds % 60)}')
    time_format = time_format.replace('%m', f'{int((seconds * 1000) % 1000):3d}')
    return time_format

def safe_replace(src: str | Path, dst: str | Path) -> None:
    '''
    Replaces the file at dst with the file at src in case of PermissionError. This is used to ensure that anything locking the file doesn't immediately kill the program.
    
    :param src: the source file to replace from
    :type src: str | Path
    :param dst: the destination file to replace to
    :type dst: str | Path
    '''
    while True:
        try:
            replace(src, dst)
            return
        except PermissionError:
            pass

def delete_upload(file_id: str, api_token: str) -> str:
    '''Deletes an uploaded file from gofile.io using the file ID and API token.
    
    :param file_id: The ID of the file to be deleted.
    :type file_id: str
    :param api_token: The API token for authentication.
    :type api_token: str
    :return: A message indicating the result of the delete operation, or an error message if the response is not JSON.
    :rtype: str
    '''

    from requests import delete

    response = delete(f'https://api.gofile.io/contents', headers={'Authorization': f'Bearer {api_token}'}, json={'contentsId': file_id})

    if response.headers.get('content-type','').startswith('application/json'):
        return response.json()
    else:
        return f'Unexpected response: {response.text}'

def tree(path: Union[str, Path], exclusions: Optional[Collection[str]] = ()) -> dict:
    '''
    Generate a nested dictionary representing the directory structure of the given path, including file hashes and a root directory hash.

    :param path: The root directory path to represent as a tree
    :type path: str | Path
    :param exclusions: A collection of glob patterns (e.g., '__pycache__', '*cache*', '*.pyc') to exclude from the tree representation
    :type exclusions: Collection[str]
    :return: A nested dictionary with directory structure, file hashes as key-value pairs, and root directory hash
    :rtype: dict
    '''

    root = Path(path)

    def iterate_dir(current_node: Path) -> dict:
        children = {'files': {}}
        for entry in sorted(current_node.iterdir(), key=lambda p: p.name):
            # Skip if entry matches any exclusion pattern
            if any(entry.match(exclusion) for exclusion in exclusions):
                continue
            
            if entry.is_file():
                file_hash = sha256()
                with open(str(entry), 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b''):
                        file_hash.update(chunk)
                children['files'][entry.name] = file_hash.hexdigest()
            elif entry.is_dir():
                children[entry.name] = iterate_dir(entry)
        
        if not children['files']:
            children.pop('files')
            
        return children

    tree_result = iterate_dir(root)
    
    return {
        'root_hash': dirhash(root, 'sha256', ignore=exclusions),
        'tree': tree_result
    }

def check_dicts(integrity_dict: dict, user_dict):

    missing = set()

    for key in integrity_dict:

        integrity_item = integrity_dict[key]
        user_item = user_dict.get(key)
        if user_item == None:
            missing.add(key)
            continue

        if type(integrity_item) == list:
            integrity_item = set(integrity_item)
            user_item = set(user_item)
        else:
            check_dicts(integrity_item, user_item)

        if type(user_item) == set and type(integrity_item) == set:
            if not integrity_item.issubset(user_item) :
                missing.union(integrity_item - user_item)

    return missing

def load_clean_decimal(num: float | int | str) -> Decimal:
        '''
        loads a number as a Decimal object
        
        :param num: number to load
        :type num: float | int | str
        :return: Decimal object
        :rtype: Decimal
        '''

        return Decimal(str(num))

def set_background_color(red: int, green: int, blue: int) -> None:
    print(f'\033[48;2;{red};{green};{blue}m' ,end='')

def lines_used(text, width):
    return sum(max(1, ceil(len(line) / width)) for line in text.splitlines() or [text])

def print_bg_colored_text(text: str, red: int, green: int, blue: int, terminal_width: int) -> None:
    set_background_color(red, green, blue)
    print(text)
    clear_lines(lines_used(text, terminal_width), clear_formatting=True)

import logging
from datetime import datetime, timedelta
from platformdirs import user_log_dir

class RelativeTimeFormatter(logging.Formatter):
    '''A logging formatter that formats log messages with the relative time since the logger was initialized.
    
    :param fmt: The format string for the log messages. Default is '[%(levelname)s] %(asctime)s %(message)s'.
    :type fmt: str, optional
    '''

    def formatTime(self, record, datefmt=None):
        delta = timedelta(milliseconds=record.relativeCreated)
        s = str(delta)
        if '.' not in s: s += '.000000' # Ensure micros are always shown
        return s.zfill(15)


def log_file_path(program: str, author: str) -> str:
    '''Returns the file path for a log file in the user's log directory. The log file is named with the current date and has a .log extension.
    
    :param program: The name of the program for which the log file is being created.
    :type program: str
    :param author: The name of the author of the program.
    :type author: str
    :return: The file path for the log file.
    :rtype: str
    '''

    return f'{user_log_dir(program, author, ensure_exists=True)}/{datetime.date(datetime.now())}.log'

def init_logger(program: str, author: str, log_format: str = '[%(levelname)s] %(asctime)s %(message)s') -> logging.Logger:
    '''Initializes a logger that writes to a file in the user's log directory. The log file is named with the current date. Each log message includes the relative time since the logger was initialized.
    
    :param program: The name of the program for which the logger is being initialized.
    :type program: str
    :param author: The name of the author of the program.
    :type author: str
    :param log_format: The format string for the log messages. Default is '[%(levelname)s] %(asctime)s %(message)s'.
    :type log_format: str, optional
    :return: A logger instance that writes to the specified log file.
    :rtype: logging.Logger
    '''

    log_file_name = log_file_path(program, author)
    with open(log_file_name, 'w') as f:
        f.write(f'______Start of the log {datetime.now()}______\n')
    logger = logging.getLogger(log_file_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_file_name, 'a')
    handler.setFormatter(RelativeTimeFormatter(log_format))
    logger.addHandler(handler)
    logger.info('Initializing logger...')
    return logger

def format_version_text(version: dict) -> str:
    '''Formats a version dictionary into a human-readable string format.
    
    :param version: A dictionary containing version information, with keys 'major', 'minor', and 'patch'.
    :type version: dict
    :return: A formatted string representing the version in the format "major.minor.patch".
    :rtype: str
    '''

    return f'{version["major"]}.{version["minor"]}.{version["patch"]}'

def bool_answer(answer: str | int) -> bool:
    '''
    Determines if a user's answer to a yes/no question is affirmative.

    :param answer: The user's response to a yes/no question, typically 'yes' or 'no', 1 or 0 for affirmative.
    :type answer: str | int
    :return: True if the answer starts with 'y' (case-insensitive) or is 1, otherwise False.
    :rtype: bool
    '''

    if isinstance(answer, str):
        answer = answer.strip().lower()
        if len(answer) == 1:
            if answer == 'y':
                return True
            elif answer == 'n':
                return False
            else:
                return
        else:
            if answer == 'yes':
                return True
            elif answer == 'no':
                return False
            else:
                return
        
    else:
        if answer > 1 or answer < 0:
            return
        else:
            return answer == 1

def prompt_user(question: str, answers: list[str] = ['no', 'yes'], default: str | int = 'y', shorten: set[str] = ('yes', 'no')) -> int:
    '''
    Prompts the user with a question and returns their selected answer as an integer index of the answers list.
    The default answer is used if the user just presses enter.
    
    :param question: The question to ask the user.
    :type question: str
    :param answers: List of valid answers, defaults to ['yes', 'no']
    :type answers: list[str], optional
    :param default: The default answer if the user just presses enter, either an index or a value from the answers list, defaults to 'y'.
    :type default: str | int, optional
    :param shorten: Set of answers to be shortened for input comparison, defaults to ('yes', 'no')
    :type shorten: set[str], optional
    :return: The user's answer as an integer index of the answers list.
    :rtype: int
    '''

    if isinstance(default, str):
        if len(default) == 1:
            def eval_default(answer: str) -> bool:
                return answer[:1] == default
        else:
            def eval_default(answer: str) -> bool:
                return answer == default
        
    else:
        def eval_default(answer: str) -> bool:
            return answers.index(answer) == default


    last_index = len(answers) - 1
    options = '['
    for i, answer in enumerate(answers):

        if answer in shorten:
            display_answer = answer[:1]
        else:
            display_answer = answer

        if eval_default(answer):
            options += display_answer.capitalize()
            default_index = i
        else:
            options += display_answer

        if i < last_index:
            options += '/'

    options += ']'


    user_answer = input(f'{question.capitalize()}? {options} ').strip().lower()

    if user_answer.isdigit():
        user_answer = int(user_answer)
        if user_answer > last_index or user_answer < 0:
            return
        else:
            return user_answer

    if user_answer == '':
        return default if isinstance(default, int) else default_index
    
    if len(user_answer) == 1:
        for i, answer in enumerate(answers):
            if answer.startswith(user_answer):
                return i
    else:
        try:
            return answers.index(user_answer)
        except ValueError:
            return


def simple_prompt(question: str, default: str | int = 'y') -> bool:
    '''
    Prompts the user with a yes/no question and returns their answer as a boolean value.

    :param question: The question to ask the user.
    :type question: str
    :param default: The default answer if the user just presses enter, either 'y' for yes or 'n' for no, defaults to 'y'.
    :type default: str | int
    :return: True if the user answers affirmatively, False otherwise.
    :rtype: bool
    '''

    return bool_answer(prompt_user(question, default=default))

def capitalize(text: str, index: int = 3) -> str:
    '''
    Capitalizes a string at a specific index.

    :param text: The string to capitalize.
    :type text: str
    :param index: The index at which to capitalize the string.
    :type index: int
    :return: The capitalized string.
    :rtype: str
    '''

    return f'{text[:index]}{text[index:index + 1].upper()}{text[index + 1:]}'

def stripped_input(prompt: object) -> str:
    '''
    Gets input from the user and strips it of leading and trailing whitespaces.
    
    :param prompt: The prompt to show to the user.
    :type prompt: object
    :return: The stripped input from the user.
    :rtype: str
    '''

    return input(prompt).strip()

def create_go_file_folder(folder_name: str, GOFILE_USER_TOKEN: str) -> dict:
    '''Creates a folder in the root directory of the GoFile account and returns the response as a dictionary.
    
    :param folder_name: The name of the folder to be created.
    :type folder_name: str
    :param GOFILE_USER_TOKEN: The user token for the GoFile account.
    :type GOFILE_USER_TOKEN: str
    :return: The response from the GoFile API as a dictionary.
    :rtype: dict
    '''

    payload = {'token': GOFILE_USER_TOKEN}

    response = get('https://api.gofile.io/accounts/getid', params=payload)
    account_id = response.json()['data']['id']
    response = get(f'https://api.gofile.io/accounts/{account_id}', params=payload)

    payload = {
        'token': GOFILE_USER_TOKEN,
        'folderName': folder_name,
        'parentFolderId': response.json()['data']['rootFolder']
    }

    response = post('https://api.gofile.io/contents/createFolder', data=payload)

    return response.json()

if __name__ == '__main__':
    # print('This module is not meant to be run directly')
    # print('Import it in your program and use the functions from there')
    # print('For more info use info(func) function on specific functions and classes')
    # input('press enter to exit')

    #generate_points(vertical=False)
    # from time import sleep

    # stop = Event()
    # wait = Event()

    # scrollable_text_display(condition=stop, wait_for_exit=wait, display_colors=True, static_colors=True, moving_static_colors=True, continues=True, spaces=3, once_startup=True, color=[255, 0, 0])
    # sleep(10.4)
    # stop.set()
    # wait.wait()

    # Possible ways to get the background color of the terminal that is running the python script
    import os, sys, time, re, select, termios, tty

    def _parse_osc11_value(val: str) -> str | None:
        val = val.strip()
        if not val:
            return
        if val.startswith('#') and re.fullmatch(r'#?[0-9A-Fa-f]{6}', val):
            return val if val.startswith('#') else '#' + val
        if val.startswith('rgb:'):
            parts = val.split(':', 1)[1].split('/')
            if len(parts) == 3:
                comps = []
                for p in parts:
                    p = p.strip()
                    # handle 2- or 4-hex-digit forms (e.g. 'ff' or 'ffff')
                    if len(p) == 2:
                        v = int(p, 16)
                    elif len(p) == 4:
                        v = int(p, 16) >> 8
                    else:
                        try:
                            v = int(p, 16)
                        except Exception:
                            return
                    comps.append(f'{v:02x}')
                return f'#{comps[0]}{comps[1]}{comps[2]}'
        return

    def get_terminal_bg_color(timeout: float = 0.2) -> str | None:
        # 1) quick env var check (set by some terminals/shells)
        cf = os.environ.get('COLORFGBG') or os.environ.get('COLOR_BG')
        if cf:
            return f'COLORFGBG={cf}'

        # 2) OSC 11 query (xterm-style). Not all terminals reply.
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            # send OSC 11 query; BEL terminator (\a). Some terminals use ESC backslash instead.
            sys.stdout.write('\x1b]11;?\x07')
            sys.stdout.flush()

            resp = ''
            end = time.time() + timeout
            while time.time() < end:
                r, _, _ = select.select([fd], [], [], end - time.time())
                if not r:
                    break
                chunk = os.read(fd, 4096).decode('utf-8', 'ignore')
                resp += chunk
                if '\x07' in resp or '\x1b\\' in resp:
                    break

            # parse OSC reply: "\x1b]11;VALUE\x07" or "\x1b]11;VALUE\x1b\\"
            m = re.search(r'\x1b]11;(?P<v>.*?)(?:\x07|\x1b\\)', resp, re.S)
            if not m:
                return None
            return _parse_osc11_value(m.group('v'))
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    print(get_terminal_bg_color())