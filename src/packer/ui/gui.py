# TEMP

from json import load
from os import environ
from pathlib import Path
from warnings import filterwarnings

filterwarnings(
    "ignore",
    message=r".*Your system is avx2 capable but pygame was not built with support for it.*",
    category=RuntimeWarning,
)

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1' # Turns off pygame hello message

# TEMP ENDS

from time import sleep
import pygame
import queue
from multiprocessing import Event, Process, Queue
import threading
from functools import wraps
from typing import Callable, Literal, ParamSpec, TypeVar
from inspect import signature

from packer.config import Project, all_settings, all_settings_status, projects_configurations
from packer.custom_modules.et import format_time, noop, normalize_settings_keys, resolve_version
from packer.custom_modules.etf import clear_lines, print_colored_text
from packer.custom_modules.ege import create_text_blit, format_size, Advanced_clock
from packer import actions


P = ParamSpec('P')
R = TypeVar('R')

def inherits_signature(target: Callable[P, R]):
    '''Copies parameter signature, type annotations, and docstring from target.'''

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(target)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def while_running(func: Callable[P, R]) -> Callable:
    @wraps(func)
    def wrapper(running: threading.Event, *args: P.args, **kwargs: P.kwargs) -> None:
        while running.is_set():
            func(*args, **kwargs)
            sleep(0.01)

    return wrapper



class Gui():
    def __init__(self):
        pygame.init()

        self.display_stats = threading.Event()
        self.fps_clock = Advanced_clock(all_settings.window_fps)
        self.running = threading.Event()
        self.running.set()
        self.actions = [actions.run]
        self.user_position_menu: Literal['main menu'] = 'main menu'
        self.user_inputted_text = ''
        self.displayed_user_inputted_text = ''
        self.input_user_text = False
        self.text_font = pygame.font.Font(all_settings.font_name, all_settings.font_size)
        self.projects_configurations = None
        self.full_output = []

        self.screen = pygame.display.set_mode(all_settings.window_resolution, pygame.RESIZABLE, vsync=1 if all_settings.vsync else 0)
        self.screen_size = self.screen.get_size()
        pygame.display.set_caption('Packer')


        self.menu_button_texts = {'main menu': ['run'], # Later add these as well, once packer.actions has them as well: 'change', 'setup', 'edit', 'import', 'export', 'clear'
                                  }

        self.menus_buttons_actions = {'main menu': [self._run_action]}

        self._refresh_screen = self._refresh_menu
        self._refresh_screen()
        self._draw = self._draw_menu


    def _refresh_buttons(self):
        self.button_rect = pygame.Rect(0, 0, *format_size(all_settings.button_size, self.screen_size))

    def _refresh_menu(self):
        self._refresh_buttons()
        self.menu_buttons: list[tuple[pygame.Surface, pygame.Rect, pygame.Rect]] = []
        menu_buttons_text = self.menu_button_texts[self.user_position_menu]
        for i in range(1, len(menu_buttons_text) + 1):
            rect = self.button_rect.copy()
            rect.center = format_size((0.5, 0.1 * i), self.screen_size)
            text_blit = create_text_blit(self._get_shrunk_text(menu_buttons_text[i - 1], rect), all_settings.text_color, self.text_font)
            self.menu_buttons.append((text_blit[0], rect, text_blit[0].get_rect(center=rect.center)))

    def _handle_output(self, input_queue: queue.Queue, output_queue: queue.Queue):
        while self.running.is_set():
            output: dict = input_queue.get()
            if 'text' in output:
                output['text'] = output['text'] + output['end']
                output.pop('end')
                self.full_output.append(output)
            elif 'question' in output:
                answer = self._prompt(f'{output['question']} [{'Y/n' if output['default'] == 'y' else 'y/N'}]')
                output_queue.put(int(answer) if answer.isdigit() else answer)
            else:
                self.full_output.append({'text': output['chunk'], 'color': output['color']})
            self._refresh_screen()


    def _refresh_output(self):
        self._refresh_buttons()
        self.output_rect = pygame.Rect(0, 0, self.screen_size[0] // 1.2, self.screen_size[1] // 1.2)
        self.output_rect.center = (self.screen_size[0] // 2, self.screen_size[1] // 2)
        self.output_lines = []
        line_height = self.button_rect.height
        last_x_cords = {'blits': [0], 'word warping': [0]}
        outputs = []

        for text_i, output in enumerate(self.full_output):
            color = output['color'] or all_settings.text_color

            word_warped_lines = []

            end_of_last_line_character = 0
            while True:
                i = -1
                size = self.text_font.size(output['text'][end_of_last_line_character:])
                while size[0] + (last_x_cords['word warping'][text_i] if type(last_x_cords['word warping'][text_i]) == int else 0) > self.output_rect.width:
                    size = self.text_font.size(output['text'][end_of_last_line_character:i])
                    i -= 1
                word_warped_lines.append(output['text'][end_of_last_line_character:i])
                last_x_cords['word warping'][text_i] = False
                end_of_last_line_character = i
                if i == -1:
                    last_x_cords['blits'].append(size[0])
                    last_x_cords['word warping'].append(size[0])
                    break
            outputs.append((word_warped_lines, color))

        for text_i, word_warped_lines in enumerate(outputs):
            color = word_warped_lines[1]
            for text in word_warped_lines[0]:
                text_blit = create_text_blit(text, color, self.text_font)[0]
                line_y = self.output_rect.y + line_height * (len(self.output_lines) - (text_i))
                if line_y > self.output_rect.y + self.output_rect.height:
                    return
                self.output_lines.append((text_blit, (self.output_rect.x + (last_x_cords['blits'][text_i] if type(last_x_cords['blits'][text_i]) == int else 0), line_y)))
                last_x_cords['blits'][text_i] = False

    
    def _draw_output(self):
        pygame.draw.rect(self.screen, all_settings.button_color, self.output_rect)
        for blit, rect in self.output_lines:
            self.screen.blit(blit, rect)


    def _draw_menu(self):
        for text, rect, text_rect in self.menu_buttons:
            self._draw_button(rect)
            self.screen.blit(text, text_rect)


    def _draw_button(self, rect: pygame.Rect):
        '''
        Draws a button on the screen.
        
        :param rect: The rectangle defining the button's position and size.
        :type rect: pygame.Rect
        '''

        pygame.draw.rect(self.screen, all_settings.button_color, rect, border_radius=50)


    def _run_action(self):
        if not self.projects_configurations:
            self.projects_configurations = self._get_projects_configurations()
        self.projects = list(self.projects_configurations.keys())
        self._change_menu('choose project menu', [Path(project).name for project in self.projects], [self._choose_project_action for _ in range(len(self.projects))])

    def _choose_project_action(self, i: int):
        self.chosen_project = self.projects[i]
        self._change_menu('choose version menu', ['x', 'y', 'z', 'full'], [self._choose_version_bump_action for _ in range(3)] + [self._choose_version_full_action])

    def _choose_version_bump_action(self, i: int):
        with open(f'{self.chosen_project}/src/{Path(self.chosen_project).name}/assets/version.json') as f:
            self.chosen_version = resolve_version(load(f), ['x', 'y', 'z'][i])
        self._run_packer()

    def _choose_version_full_action(self):
        self.chosen_version = {['major', 'minor', 'patch'][i]: version_number for i, version_number in enumerate(self._prompt('Enter version (format: x.y.z): ').split('.'))}
        self._run_packer()

    def _run_packer(self):
        self._refresh_screen = self._refresh_output
        self._refresh_screen()
        self._draw = self._draw_output
        input_queue = Queue()
        output_queue = Queue()
        Process(target=actions.run, args=(self.chosen_version, self.chosen_project, Project(**normalize_settings_keys(self.projects_configurations[self.chosen_project])), input_queue, output_queue)).start()
        threading.Thread(target=self._handle_output, args=(output_queue, input_queue)).start()

    def _change_menu(self, menu: str, menu_texts: str, actions: list[Callable]):
        self.menu_button_texts[menu] = menu_texts
        self.menus_buttons_actions[menu] = actions
        self.user_position_menu = menu
        self._refresh_screen()

    def _draw_input_text_rect(self):
        self._draw_button(self.input_text_rect)

    def _blit_user_input_prompt_text_blit(self):
        self.screen.blit(self.user_input_prompt_text_blit, self.user_input_prompt_text_blit_rect)
    

    def _draw_sensitive_user_input(self):
        self._draw_input_text_rect()
        self.screen.blit(all_settings.getpass_echo_char * self.user_inputted_text, self.user_input_text_blit_rect)
        
    def _draw_user_input(self):
        self._draw_input_text_rect()
        self.screen.blit(self.user_input_text_blit, self.user_input_text_blit_rect)

    def _draw_user_input_with_prompt(self):
        self._blit_user_input_prompt_text_blit()
        self._draw_user_input()

    def _draw_sensitive_user_input_with_prompt(self):
        self._blit_user_input_prompt_text_blit()
        self._draw_sensitive_user_input()


    def _refresh_user_inputted_text_display(self):
        self._refresh_buttons()
        self.input_text_rect = self.button_rect.copy()
        self.input_text_rect.center = (self.screen_size[0] // 2, self.screen_size[1] // 2)
        text_blit = create_text_blit(self._get_shrunk_text(self.user_inputted_text, self.input_text_rect), all_settings.text_color, self.text_font)
        self.user_input_text_blit_rect = text_blit[0].get_rect(center=self.input_text_rect.center)
        self.user_input_text_blit = text_blit[0]

    def _get_shrunk_text(self, text: str, rect: pygame.Rect) -> str:
        '''
        Shrinks the text to fit within the given rectangle, by removing characters from the beginning of the string until it fits.

        :param text: The text to shrink.
        :type text: str
        :param rect: The rectangle to fit the text within.
        :type rect: pygame.Rect
        :return: The shrunk text.
        :rtype: str
        '''

        i = 0
        while self.text_font.size(text[i:])[0] > rect.width:
            i += 1
        return text[i:]

    def _refresh_user_inputted_text_display_with_prompt(self):
        self._refresh_user_inputted_text_display()
        self.user_input_prompt_text_blit = create_text_blit(self.user_input_prompt_text, all_settings.text_color, self.text_font)[0]
        self.user_input_prompt_text_blit_rect = self.user_input_prompt_text_blit.get_rect(center=(self.screen_size[0] // 2, self.screen_size[1] // 2 - self.input_text_rect.height))



    def _prompt(self, text: str = '', sensitive: bool = False) -> str:
        '''
        Prompts the user for input and returns the inputted text. **Note.** This function must be called from another thread, as it will block the main thread until the user has inputted text and pressed enter or escape.

        :param text: The prompt text to display to the user.
        :return: The text inputted by the user.
        '''
        previous_refresh_func = self._refresh_screen
        previous_draw_func = self._draw
        self.user_input_prompt_text = text

        self._refresh_screen = self._refresh_user_inputted_text_display_with_prompt if text else self._refresh_user_inputted_text_display
        self._refresh_screen()
        self._draw = (self._draw_sensitive_user_input_with_prompt if sensitive else self._draw_user_input_with_prompt) if text else (self._draw_sensitive_user_input if sensitive else self._draw_user_input)
        self.input_user_text = True
        while self.input_user_text and self.running.is_set():
            sleep(all_settings.gui_subsystem_speed)
        if not self.running.is_set():
            exit()
        self._refresh_screen = previous_refresh_func
        self._draw = previous_draw_func
        return self.user_inputted_text

    
    def _get_projects_configurations(self) -> dict:
        configs = projects_configurations.content
        while type(configs) == str:
            configs = projects_configurations.decrypt(self._prompt('Password: '))
        return configs


    def _handle_events(self) -> None:
        '''Processes pending Pygame events.
        '''

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._exit()
                self.running.clear()

            elif event.type == pygame.VIDEORESIZE:
                self.screen_size = self.screen.get_size()
                self._refresh_screen()


            elif event.type == pygame.KEYDOWN:


                if self.input_user_text:
                    if event.key == pygame.K_BACKSPACE:
                        self.user_inputted_text = self.user_inputted_text[:-1]
                        self._refresh_screen()
                        
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        self.input_user_text = False



                elif event.key == pygame.K_F3:
                    if not self.display_stats.is_set():
                        self.display_stats.set()
                        self.debug_menu_thread = threading.Thread(target=self._stats_display)
                        self.debug_menu_thread.start()
                    else:
                        self.display_stats.clear()

                elif self.display_stats.is_set():
                    if event.key == pygame.K_F2:
                        self.input_user_text = True



            elif self.input_user_text and event.type == pygame.TEXTINPUT:
                self.user_inputted_text += event.text
                self._refresh_screen()


            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    if 'menu' in self.user_position_menu:
                        for i, rect in enumerate(self.menu_buttons):
                            rect = rect[1]
                            if rect.collidepoint(event.pos):
                                user_chosen_function = self.menus_buttons_actions[self.user_position_menu][i]
                                threading.Thread(target=user_chosen_function, args=(i,) if signature(user_chosen_function).parameters else ()).start()


    @inherits_signature(_handle_events)
    def _thread_handle_events(self, *args, **kwargs):
        while self.running.is_set():
            self._handle_events()
            sleep(all_settings.event_handler_speed)



    def run(self):
        if all_settings.slow_events:
            threading.Thread(target=self._thread_handle_events).start()
            gui_handle_events = noop
        else:
            def _handle_events():
                self._handle_events()
            gui_handle_events = _handle_events
    

        while self.running.is_set():
            gui_handle_events()
            self.screen.fill(all_settings.window_background_color)

            self._draw()

            pygame.display.flip()
            self.fps_clock.tick()
        pygame.display.quit()



    def _exit(self):
        if self.display_stats.is_set():
            self.display_stats.clear()
            self.debug_menu_thread.join()


    def _stats_display(self):
        target_frame_time = 1 / all_settings.window_fps
        while self.display_stats.is_set():
            print('Fps:', end=' ')
            print_colored_text(str(int(self.fps_clock.get_fps())), [0, 0, 255])
            print('Frame time:', end=' ')
            print_colored_text(str(round(self.fps_clock.frame_time * 1000)), end=' ')
            print('ms')
            print('Raw frame time:', end=' ')
            print_colored_text(format_time(self.fps_clock.raw_time))
            print('Main CPU usage:', end=' ')
            print_colored_text(str(round((self.fps_clock.raw_time / target_frame_time) * 100, 1)), [0, 0, 255], end='')
            print('%')
            print('Screen size:', end=' ')
            print_colored_text(str(self.screen_size), [0, 0, 255])
            print('Text input:', end=' ')
            print_colored_text(self.user_inputted_text)
            sleep(0.1)
            clear_lines(6)



def main():
    instance = Gui()
    instance.run()

    # This is for the all_settings_status prompting and so on.

    # def create_window(title):
    #     screen = pygame.display.set_mode((800, 600))
    #     pygame.display.set_caption(title)
    #     return screen

    # # Create first window
    # screen = create_window('Settings setup wizard')

    # running = True
    # while running:
    #     for event in pygame.event.get():
    #         if event.type == pygame.QUIT:
    #             running = False

    # # Close only the display
    # pygame.display.quit()

    # print('Window closed.')

    # # Reinitialize the display
    # pygame.display.init()

if __name__ == '__main__':
    main()