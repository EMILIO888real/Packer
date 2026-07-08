"""Enhanced Terminal Formatting (ETF) Module.

A comprehensive module providing terminal manipulation utilities including:
- Color and formatting controls (RGB color support, text styles)
- Terminal cursor management (hide, show, clear)
- Loading animations (character and dot-based animations)
- Text effects (cinematic dialogue, dissolving text, scrollable text)
- User input handling and prompts
- Terminal mode configuration (raw mode, terminal settings)
- Graph drawing and point generation utilities

This module is designed for creating interactive terminal user interfaces with
advanced visual effects and user interaction capabilities.

All functions use ANSI escape codes for cross-platform terminal support.
Note: Some functions are Linux-specific.
"""

from collections.abc import Callable
from itertools import cycle
from math import ceil
from typing import Any, Optional
from threading import Thread, Event
from time import sleep
from random import randint
from sys import stdin, platform
from select import select
from string import punctuation, digits, ascii_letters
from datetime import datetime, timedelta
from atexit import register

if platform != 'win32':
    from termios import tcsetattr, tcgetattr, ECHO, ICANON, TCSAFLUSH


def change_color(color: list = [138, 43, 226]) -> None:
    """Change the color of the terminal text using RGB values.

    Sets the terminal text color to the specified RGB values.
    Example: [138, 43, 226] produces blue violet color.

    :param color: A list of three integers [R, G, B] representing the RGB color.
    :type color: list
    """
    print(f'\033[38;2;{color[0]};{color[1]};{color[2]}m', end='')

def reset_formatting() -> None:
    """Reset the formatting of the terminal text.

    Resets all terminal text formatting to default (color, style, etc.).
    """
    print('\033[0m', end='')

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

def flush_input_linux() -> None:
    """Flush the input buffer on Linux.

    Clears any pending input from the input buffer by reading and discarding it.
    Only works on Linux systems.
    """
    def kbhit():
        return bool(select([stdin], [], [], 0)[0])

    def getch():
        return stdin.read(1)

    while kbhit():
        getch()

def hide_cursor() -> None:
    """Hide the terminal cursor.

    Hides the cursor using ANSI escape codes.
    """
    print('\033[?25l', end='')

def show_cursor() -> None:
    """Show the terminal cursor.

    Shows the cursor using ANSI escape codes.
    """
    print('\033[?25h', end='')

def clear_terminal() -> None:
    """Clear the entire terminal screen.

    Clears the terminal and moves cursor to home position using ANSI escape codes.
    """
    print('\033[2J\033[H', end='')

def clear_lines(lines_to_clear: int = 1, force_clear: bool = True, clear_formatting: bool = False) -> None:
    """Clear specified lines of text from the terminal.

    Clears specified lines using ANSI escape codes and optionally moves cursor back.

    :param lines_to_clear: The count of lines to clear.
    :type lines_to_clear: int
    :param force_clear: Whether to truly clear specified lines or just move the cursor back.
    :type force_clear: bool
    :param clear_formatting: Whether to reset formatting before clearing.
    :type clear_formatting: bool
    """
    if clear_formatting:
        reset_formatting()

    text_clearer = '\033[F'
    if force_clear:
        text_clearer += '\033[2K'
    for _ in range(lines_to_clear):
        print(text_clearer, end='')

class Loading_animations():
    """A class for terminal loading animations.

    Contains loading animation functions and state management for terminal-based animations.
    You can customize the animation type and text via attributes.

    Attributes:
        animation_type (str): The type of animation ('character' or 'dots').
        text (str): The text to display with the animation.
        allow_multiple (bool): If True, allows multiple instances to run simultaneously.

    Methods:
        character_loading_animation: Rotating character animation (| / - \\).
        loading_terminal_animation: Rotating dot animation (. .. ...).
        run: Start the animation.
        stop: Stop the animation.
        restart: Restart the animation.

    Example:
        animation = Loading_animations()
        animation.run(text='Cooking ', type='character')
        # Do some work here
        animation.stop()
    """
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
        """Display a simple terminal character loading animation.

        Displays a rotating character animation (| / - \\) in a separate thread.
        Use with the flag.wait() method in main thread for correct functionality.
        Warning: if you hide the cursor, you must call show_cursor() yourself after animation finishes.

        Example:
            stop_condition = Event()
            wait_for_animation = Event()
            # Task running...
            # Task finished running!
            stop_condition.set()
            wait_for_animation.wait()
            # Program continuation!

        :param stop_condition: Event to stop the animation (set to stop).
        :type stop_condition: Event
        :param wait_for_animation: Internal flag to determine when sub thread has finished.
        :type wait_for_animation: Event
        :param speed: Time to wait before going to next phase of animation in seconds.
        :type speed: float
        :param to_hide_cursor: If True, hides the cursor during animation and shows it after.
        :type to_hide_cursor: bool
        :param text: Text to display before the animation character.
        :type text: str
        """
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

    def loading_terminal_animation(self, stop_condition: Event, wait_for_animation: Event, speed: float = 0.4, to_hide_cursor: bool = True, text: str = '') -> None:
        """Display a simple terminal 3-dot loading animation.

        Displays a rotating dot animation (. .. ...) in a separate thread.
        Use with the flag.wait() method in main thread for correct functionality.

        Example:
            stop_condition = Event()
            wait_for_animation = Event()
            # Task running...
            # Task finished running!
            stop_condition.set()
            wait_for_animation.wait()
            # Program continuation!

        :param stop_condition: Event to stop the animation (set to stop).
        :type stop_condition: Event
        :param wait_for_animation: Internal flag to determine when sub thread has finished.
        :type wait_for_animation: Event
        :param speed: Time to wait before going to next phase of animation in seconds.
        :type speed: float
        :param to_hide_cursor: If True, hides the cursor during animation and shows it after.
        :type to_hide_cursor: bool
        :param text: Text to display before the animation dots.
        :type text: str
        """
        def thread_func():
            loading_list = ['.', '..', '...']
            loading_list_loop = 0
            if to_hide_cursor:
                hide_cursor()
            while not stop_condition.is_set():
                print(f'{text + loading_list[loading_list_loop]:<{3 + len(text)}}', end='\r')
                loading_list_loop += 1
                if loading_list_loop == len(loading_list):
                    loading_list_loop = 0
                sleep(speed)
            print()
            clear_lines(1)
            wait_for_animation.set()

        if to_hide_cursor:
            show_cursor()

        thread = Thread(target=thread_func, daemon=True)
        thread.start()
    
    def run(self, text: str = '', type: str = '') -> None:
        """Start the loading animation.

        Runs a standardized function to start the animation in a separate thread.

        :param text: The text to display with the animation.
        :type text: str
        :param type: The type of animation to initiate ('character' or 'dots').
        :type type: str
        """
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
        """Stop the loading animation.

        This is a standardized function to stop the animation thread.

        :param to_hide_cursor: If True, hides the cursor; if False, shows it after stopping.
        :type to_hide_cursor: bool
        """
        if self.already_running or self.allow_multiple:
            self.already_running = False
            self.stop_condition.set()
            self.wait_for_animation.wait()
            if to_hide_cursor:
                show_cursor()
        else:
            raise self.RunError('The animation isn\'t running! If you still want to stop it you can change the attribute: allow_multiple.')
    
    def restart(self, text: str = '') -> None:
        """Restart the loading animation.

        Stops the current animation and starts a new one.

        :param text: The text to display with the animation. If not specified, uses self.text attribute.
        :type text: str
        """
        self.stop()
        if text != '':
            self.text = text
        self.run()

def print_with_delay(text: str, colors: cycle[list[int]] = cycle([None]), delay: float = 0.03, end='\n') -> None:
    """Print a cinematic dialogue with a delay between each character.

    Displays text character one at a time after a delay with optional colors

    :param text: The text to print with delay.
    :type text: str
    :param colors: Cycle of color to apply to characters.
    :type colors: cycle[list[int]]
    :param delay: Delay between each character in seconds.
    :type delay: float
    :param end: Character to append at the end of the text.
    :type end: str
    """

    for char in text:
        color = next(colors)
        if color:
            print_colored_text(char, color, flush=True, end='')
        else:
            print(char, flush=True, end='')
        sleep(delay)
    print(end=end)


def dissolve_text(text: str = 'Average sentence is about this long, not really longer!', delay: float = 0.04,
                  randomize_color: bool = False, single_character_color: bool = False,
                  cinematic_display: bool = False, cinematic_delay: float = 0.001, dynamic_cinematic_display: bool = False,
                  multi_character_replace: bool = False, max_characters_to_replace: int = 3, stop_too_many_reroll: bool = False, chance_to_repeat: int = 2,
                  limit_time: bool = False, max_time: float = 5.0, cinematic_time_text: bool = False, time_text_delay: float = 1.0,
                  multiple_lines: bool = False, do_reset_formatting: bool = True, do_hide_cursor: bool = True) -> None:
    """Dissolve text in the terminal using random characters.

    Gradually replaces random characters in text with the correct characters to create a dissolving effect.
    This is a goofy and not very efficient function, just a fun little project.

    :param text: The text to dissolve.
    :type text: str
    :param delay: The delay between each character replacement in seconds.
    :type delay: float
    :param randomize_color: If True, randomizes the color of the text.
    :type randomize_color: bool
    :param single_character_color: If True, randomizes the color of each character. Only active if cinematic_display is True.
    :type single_character_color: bool
    :param cinematic_display: If True, displays the text in a cinematic way.
    :type cinematic_display: bool
    :param cinematic_delay: The delay between each character in cinematic display in seconds.
    :type cinematic_delay: float
    :param dynamic_cinematic_display: If True, displays the text in a cinematic way rewriting the text every time.
    :type dynamic_cinematic_display: bool
    :param multi_character_replace: If True, replaces multiple characters at the same time.
    :type multi_character_replace: bool
    :param max_characters_to_replace: The maximum number of characters to replace at the same time.
    :type max_characters_to_replace: int
    :param stop_too_many_reroll: If True, won't allow the same specific character to be rerolled multiple times in a row.
    :type stop_too_many_reroll: bool
    :param chance_to_repeat: The chance to repeat the same character. 2 = 33.3% chance, 3 = 25% chance, etc.
    :type chance_to_repeat: int
    :param limit_time: If True, limits the time for the animation to finish.
    :type limit_time: bool
    :param max_time: The maximum time for the animation to finish in seconds.
    :type max_time: float
    :param cinematic_time_text: If True, displays the text in a cinematic way after time limit expires.
    :type cinematic_time_text: bool
    :param time_text_delay: The delay multiplier for cinematic display with a time limit.
    :type time_text_delay: float
    :param multiple_lines: If True, clears the screen more often to prevent text duplication.
    :type multiple_lines: bool
    :param do_reset_formatting: If True, resets formatting after the animation.
    :type do_reset_formatting: bool
    :param do_hide_cursor: If True, hides the cursor during the animation.
    :type do_hide_cursor: bool
    """

    # To do list:
    #   1. Fix the multiple lines, it doesn't clear the entire screen, and when it does it doesn't work as intended. New lines characters disappear?
    
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
                print_with_delay(dissolved_text, delay=cinematic_delay, end='\r')
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
    """A decorator to style the terminal for a function.

    Configures terminal settings (raw mode, echo, input buffering) for the decorated function.
    Note: This decorator only works on Linux systems.

    :param raw_mode: If True, expects unbuffered input for the function.
    :type raw_mode: bool
    :param terminal_settings: If not None, sets the terminal to the specified settings. Otherwise changes to enable echo and input buffering.
    :type terminal_settings: list
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            match platform:
                case 'linux':
                    if raw_mode:
                        fd = stdin.fileno()
                        if terminal_settings is None:
                            current_terminal = tcgetattr(fd)
                            current_terminal[3] |= current_terminal[3] | ECHO | ICANON
                            tcsetattr(fd, TCSAFLUSH, current_terminal)
                        else:
                            tcsetattr(fd, TCSAFLUSH, terminal_settings)
            results = func(*args, **kwargs)
            set_raw_mode()
            return results
        return wrapper
    return decorator

@style_terminal()
def user_input(values: object = '', lower_it: bool = True) -> str:
    """Flush input buffer and return the user input.

    This is a more polished version of the input function for more typical use cases.
    Automatically flushes the input buffer before reading.

    :param values: The prompt to display to the user.
    :type values: object
    :param lower_it: If True, converts the input to lowercase.
    :type lower_it: bool
    :return: The user input as a stripped string.
    :rtype: str
    """

    flush_input_linux()
    if lower_it:
        user_input_data = input(values).lower().strip()
    else:
        user_input_data = input(values).strip()
    return user_input_data

def ask_user_repeatedly(question: str, default: str = 'y', valid_answers: list = ['y', 'n'], delay: float = 1.0, lower_it: bool = True, do_hide_cursor: bool = True) -> str:
    """Ask the user a question and wait for a valid answer.

    Repeatedly prompts the user until a valid answer is provided.

    :param question: The question to ask the user.
    :type question: str
    :param default: The default answer if the user just presses enter.
    :type default: str
    :param valid_answers: List of valid answers to accept.
    :type valid_answers: list
    :param delay: The delay between each question when the answer is invalid in seconds.
    :type delay: float
    :param lower_it: If True, converts the input to lowercase before validation.
    :type lower_it: bool
    :param do_hide_cursor: If True, hides the cursor when displaying invalid input message.
    :type do_hide_cursor: bool
    :return: The valid user answer.
    :rtype: str
    """
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
    """Print colored text to the terminal.

    Prints text in the specified RGB color with optional formatting reset.

    :param text: The text to print out.
    :type text: str
    :param color: The RGB color the text will be printed in.
    :type color: list[int]
    :param reset: If True, resets the terminal formatting after printing.
    :type reset: bool
    :param flush: If True, flushes the output buffer.
    :type flush: bool
    :param end: The ending character(s) after the text.
    :type end: str
    """
    change_color(color)
    print(text, flush=flush, end=end)
    if reset:
        reset_formatting()

def set_raw_mode() -> list:
    """Set the terminal to raw mode with unbuffered input.

    Configures the terminal for unbuffered input and disables echo.
    Automatically restores terminal settings on program exit.
    Note: This function only works on Linux systems.

    :return: The previous terminal settings as a list (not mandatory to use).
    :rtype: list
    """

    fd = stdin.fileno()
    default_terminal = tcgetattr(fd)
    raw_terminal = tcgetattr(fd)
    raw_terminal[3] = raw_terminal[3] & ~ICANON & ~ECHO

    register(lambda : tcsetattr(fd, TCSAFLUSH, default_terminal)) # execute's once at the end of the program to reset the terminal to previous settings.
    tcsetattr(fd, TCSAFLUSH, raw_terminal) # sets the terminal to unbuffered or changes it's settings.

    return default_terminal

def graph_drawer(points: list[list[int]], size: int = 10, background: str = '~', multiplier: int = 1):
    """Draw a simple graph in the terminal using ASCII characters.

    Plots points on a terminal-based graph and connects them with lines.

    :param points: A list of coordinate pairs [x, y] to plot on the graph.
    :type points: list[list[int]]
    :param size: The size of the graph (size x size).
    :type size: int
    :param background: The character to use for the background of the graph.
    :type background: str
    :param multiplier: The multiplier to use for the x-axis to adjust aspect ratio.
    :type multiplier: int
    """

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

def generate_points(size: int = 10, fps: int = 10, multiplier: int = 4, vertical: bool = True, back_ground: str = '~', smooth_turns: bool = True) -> None:
    """Generate and display random graph points with animation.

    Creates a continuously updating graph with random points in a separate thread.
    Press Ctrl+C to stop the animation and show the cursor again.

    :param size: The size of the graph (size x size).
    :type size: int
    :param fps: The frames per second for the animation speed.
    :type fps: int
    :param multiplier: The multiplier to use for the x-axis to adjust aspect ratio.
    :type multiplier: int
    :param vertical: If True, varies the y-coordinate randomly; otherwise varies x.
    :type vertical: bool
    :param back_ground: The character to use for the background of the graph.
    :type back_ground: str
    :param smooth_turns: If True, smooths out rapid direction changes in the graph.
    :type smooth_turns: bool
    """

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
            clear_terminal()
    except KeyboardInterrupt:
        show_cursor()

def scrollable_text_display(text: str = 'You can even win a reward! Awesome right? To sign up just call +371 26 634 954', condition: Event | Callable[[], bool] = lambda: True,
                            size: int = 30, speed: float = 0.05,
                            continues: bool = False, start_up: bool = True, wait_for_exit: Optional[Event] = None, spaces: int = 0, hidden_cursor: bool = True,
                            once_startup: bool = False,
                            display_colors: bool = False, color: Optional[list[int] | list[list[int]] | str] = 'random', single_char_color: bool = True, static_colors: bool = False,
                            moving_static_colors: bool = False, remember_colors: bool = False) -> None:
    """Display scrollable text in the terminal.

    Displays text that scrolls through a viewing window with optional color effects.
    Runs in a separate thread for non-blocking execution.

    :param text: The text to display and scroll.
    :type text: str
    :param condition: The condition to stop the scrolling (Event or callable returning bool).
    :type condition: Event | Callable[[], bool]
    :param size: The size of the display window in characters.
    :type size: int
    :param speed: The speed of the scrolling in seconds per frame.
    :type speed: float
    :param continues: If True, text will continue scrolling from the beginning after reaching the end.
    :type continues: bool
    :param start_up: If True, text is displayed character by character at the start.
    :type start_up: bool
    :param wait_for_exit: If not None, an Event that will be set when scrolling stops.
    :type wait_for_exit: Optional[Event]
    :param spaces: The number of spaces to add at the end of the text.
    :type spaces: int
    :param hidden_cursor: If True, hides the cursor during the scrolling.
    :type hidden_cursor: bool
    :param once_startup: If True, startup animation only happens once.
    :type once_startup: bool
    :param display_colors: If True, applies color effects to the text.
    :type display_colors: bool
    :param color: Color specification (RGB list, list of RGB lists, or 'random').
    :type color: Optional[list[int] | list[list[int]] | str]
    :param single_char_color: If True, each character can have a different color.
    :type single_char_color: bool
    :param static_colors: If True, colors stay static throughout animation.
    :type static_colors: bool
    :param moving_static_colors: If True, static colors shift position each frame.
    :type moving_static_colors: bool
    :param remember_colors: If True, remembers colors from previous cycles.
    :type remember_colors: bool
    """

    # Also would like to optimize and write this function in a more clean way! <!>
    # Fix a bug where the colors are incorrectly used for the next cycle with continues and remember colors.

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

def set_background_color(red: int, green: int, blue: int) -> None:
    """Set the terminal background color using RGB values.

    Sets the background color using ANSI escape codes.

    :param red: The red component of the RGB color (0-255).
    :type red: int
    :param green: The green component of the RGB color (0-255).
    :type green: int
    :param blue: The blue component of the RGB color (0-255).
    :type blue: int
    """
    print(f'\033[48;2;{red};{green};{blue}m', end='')

def lines_used(text: str, width: int) -> int:
    """Calculate the number of lines text would occupy with a given width.

    Determines how many lines are needed to display text when wrapped to a specific width.

    :param text: The text to measure.
    :type text: str
    :param width: The maximum width of each line in characters.
    :type width: int
    :return: The number of lines needed.
    :rtype: int
    """
    return sum(max(1, ceil(len(line) / width)) for line in text.splitlines() or [text])

def print_bg_colored_text(text: str, red: int, green: int, blue: int, terminal_width: int) -> None:
    """Print text with a colored background.

    Prints text with the specified background color and clears appropriately.

    :param text: The text to print.
    :type text: str
    :param red: The red component of the background RGB color (0-255).
    :type red: int
    :param green: The green component of the background RGB color (0-255).
    :type green: int
    :param blue: The blue component of the background RGB color (0-255).
    :type blue: int
    :param terminal_width: The width of the terminal in characters for line wrapping calculation.
    :type terminal_width: int
    """
    set_background_color(red, green, blue)
    print(text)
    clear_lines(lines_used(text, terminal_width), clear_formatting=True)

def prompt_user(question: str, answers: list[str] = ['no', 'yes'], default: str | int = 'y', shorten: set[str] = ('yes', 'no')) -> int | None:
    """Prompt the user with a question and return the selected answer.

    Returns the user's selected answer as an integer index of the answers list.
    The default answer is used if the user just presses enter.

    :param question: The question to ask the user.
    :type question: str
    :param answers: List of valid answers.
    :type answers: list[str]
    :param default: The default answer if the user just presses enter (index or value from answers list).
    :type default: str | int
    :param shorten: Set of answers to be shortened for input comparison.
    :type shorten: set[str]
    :return: The user's answer as an integer index of the answers list.
    :rtype: int
    """

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

def bool_answer(answer: str | int | None) -> bool | None:
    """Determine if a user's yes/no answer is affirmative.

    Determines if a user's answer to a yes/no question is affirmative.

    :param answer: The user's response to a yes/no question ('yes', 'no', 'y', 'n', 1, or 0).
    :type answer: str | int
    :return: True if the answer is affirmative (starts with 'y' or is 1), False otherwise.
    :rtype: bool
    """

    if answer is None:
        return

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


def simple_prompt(question: str, default: str | int = 'y') -> bool | None:
    """Prompt the user with a yes/no question and return the answer as a boolean.

    Prompts the user with a yes/no question and returns their answer as a boolean value.

    :param question: The question to ask the user.
    :type question: str
    :param default: The default answer if user presses enter ('y' for yes or 'n' for no).
    :type default: str | int
    :return: True if the user answers affirmatively, False otherwise.
    :rtype: bool
    """

    return bool_answer(prompt_user(question, default=default))

def simple_prompt_retries(question: str, default: str | int = 'y', retry_count: int = -1) -> bool | None:
    attempt = 0
    answer = simple_prompt(question, default)
    while answer is None and retry_count != attempt:
        answer = simple_prompt(question, default)
        attempt += 1
    return answer

def stripped_input(prompt: object) -> str:
    """Get user input and strip leading and trailing whitespace.

    Gets input from the user and strips it of leading and trailing whitespaces.

    :param prompt: The prompt to show to the user.
    :type prompt: object
    :return: The stripped input from the user.
    :rtype: str
    """
    return input(prompt).strip()

def fade_animation(background_color: list[int] = None) -> None:
    """Fade text animation (placeholder).

    Try to make an animation to fade in and out text. The text could start at the same
    color as the background and gradually change to the desired color, or vice versa.

    :param background_color: The RGB color of the background.
    :type background_color: list[int]
    """
    pass

if __name__ == '__main__':
    print('This module is not meant to be run directly')
    print('Import it in your program and use the functions from there')
    input('press enter to exit')