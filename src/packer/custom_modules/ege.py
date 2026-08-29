from random import randint
import sys
import threading
from time import perf_counter, sleep
from typing import Callable, Optional, Sequence
import pygame

def noop():
    pass

def scale_position(position: Sequence[float], screen_size: Sequence[int]) -> list[int, int]:
    '''
    scales a position from relative (0.0 to 1.0) to absolute (pixels)
    
    :param position: position to scale
    :type position: Sequence[float]
    :param screen_size: size of the screen
    :type screen_size: Sequence[int]
    :return: scaled position
    :rtype: list[float, float]
    '''

    return [int(screen_size[0] * position[0]), int(screen_size[1] * position[1])]

def format_size(size: list[int | float, int | float], screen_size: list[int, int]) -> list[int, int]:
    '''
    formats a size from relative (0.0 to 1.0) to absolute (pixels)
    
    :param size: size to format
    :type size: list[int | float, int | float]
    :param screen_size: size of the screen
    :type screen_size: list[int, int]
    :return: formatted size
    :rtype: list[int, int]
    '''

    return [axis if type(axis) == int else screen_size[i] * axis for i, axis in enumerate(size)]

def create_text_blit(text: str, text_color: list[int, int, int], font: pygame.font.Font, **anchor: tuple[int | float, int | float]) -> tuple[pygame.Surface, pygame.Rect]:
   '''
    creates a text blit tuple for rendering on the screen

   :param text: text to render 
   :type text: str
   :param text_color: color of the text
   :type text_color: list[int, int, int]
   :param font: font to render the text with
   :type font: pygame.font
   :param position: position to render the text at
   :type position: Sequence[int, int]
   :return: text blit tuple
   :rtype: tuple[pygame.Surface, pygame.Rect]
   '''

   text_render = font.render(text, True, text_color)
   return (text_render, text_render.get_rect(**anchor))

def rect_to_tuple(rect: pygame.rect) -> tuple[int, int, int, int]:
    '''
    converts a pygame rect to a tuple
    
    :param rect: rect to convert
    :type rect: pygame.rect
    :return: tuple representation of the rect
    :rtype: tuple[int, int, int, int]
    '''

    return (rect.x, rect.y, rect.w, rect.h)

def tuple_to_rect(serialized_data: tuple) -> pygame.Rect:
    '''
    converts a tuple of (x, y, width, height) to a pygame.Rect object. This is used because when using processes, the data is serialized and sent as tuples instead of rects.

    :param serialized_data: The serialized data of a rect, in the form of a tuple (x, y, width, height)
    :type serialized_data: tuple
    :return: The deserialized rect
    :rtype: Rect
    '''

    return pygame.Rect(serialized_data[0], serialized_data[1], serialized_data[2], serialized_data[3])

class Advanced_clock():
    '''
    A custom clock class that allows for more accurate timing and fps/ups calculation. It uses a combination of sleep and busy waiting to achieve the desired frame time.
    
    :param fps: frames per second or updates per second to maintain
    :type fps: int
    :param busy_loop_threshold: the amount of time in seconds to busy wait before sleeping, defaults to 0.001
    :type busy_loop_threshold: float, optional
    '''

    def __init__(self, fps: int, busy_loop_threshold: float = 0.001):
        self._last_frame = perf_counter()
        self.desired_frame_time = 1 / (fps + 1)
        self.busy_loop_threshold = busy_loop_threshold

        # Preset to any value, just in case the attribute is accessed before the tick method is called even once
        self.frame_time = 0.00001
        self.raw_time = 0.00001

    def tick(self) -> None:
        '''Sleeps and busy waits until the desired frame time has passed since the last frame. It also updates the actual frame time for fps/ups calculation.'''

        self.raw_time = perf_counter() - self._last_frame
        remaining = self.desired_frame_time - (perf_counter() - self._last_frame)
        if remaining > self.busy_loop_threshold:
            sleep(remaining - self.busy_loop_threshold)
        while perf_counter() - self._last_frame < self.desired_frame_time:
            pass

        finish_time = perf_counter()
        self.frame_time = finish_time - self._last_frame
        self._last_frame = finish_time
    
    def get_fps(self) -> float:
        '''Returns the current frames per second or updates per second based on frame time.'''

        return 1 / self.frame_time

    def update(self, fps: int) -> None:
        '''Updates the target fps/ups and recalculates the frame time.'''

        self.desired_frame_time = 1 / (fps + 1)
    
def playlist(music_files: Sequence[str], music_mixer: pygame.mixer.music, played_music: Sequence[str],
            play_last_song: threading.Event, queue_song: threading.Event, repeat_song: threading.Event, pause: threading.Event, exit_event: Callable,
            playlist_sleep_time: float | int, sequential_playlist: bool, fade_ms: int, action_function: Optional[Callable] = noop) -> None:
    '''
    Function that runs in a separate thread to handle music playback, including playing songs sequentially or randomly, repeating songs, and queuing songs. It checks for various events to control the music playback and uses a sleep time to avoid busy waiting.

    :param music_files: a list of the music files to play, should be in a format that pygame can load (e.g. .mp3, .ogg, etc.)
    :type music_files: Sequence[str]
    :param music_mixer: the pygame mixer music object to control the music playback
    :type music_mixer: pygame.mixer.music
    :param played_music: a list of the music files that have been played, used for the play last song feature
    :type played_music: Sequence[str]
    :param play_last_song: an event that signals when the play last song feature should be activated
    :type play_last_song: threading.Event
    :param queue_song: an event that signals when the queue song feature should be activated
    :type queue_song: threading.Event
    :param repeat_song: an event that signals when the repeat song feature should be activated
    :type repeat_song: threading.Event
    :param pause: an event that signals when the music should be paused
    :type pause: threading.Event
    :param exit_event: a function that returns a boolean indicating when the thread should exit, used to safely exit the thread when the game is closed
    :type exit_event: Callable
    :param playlist_sleep_time: the amount of time in seconds that the thread should sleep for when waiting for a song to finish or when paused
    :type playlist_sleep_time: float | int
    :param sequential_playlist: whether the playlist should play songs sequentially or randomly
    :type sequential_playlist: bool
    :param fade_ms: the amount of time in milliseconds that the music should take to fade in when a new song starts
    :type fade_ms: int
    :param action_function: an optional function that can be called after each song is played, for example to update the UI or something, defaults to a no operation function
    :type action_function: Optional[Callable]
    
    '''

    music_index = 0

    while True:
        while music_mixer.get_busy() or pause.is_set(): # Got to be a better way to do this to only check one of them at a time
            sleep(playlist_sleep_time)

        if exit_event():
            sys.exit()

        if not play_last_song.is_set() and not repeat_song.is_set() and not queue_song.is_set():
            music_name = music_files[music_index if sequential_playlist else randint(0, len(music_files) - 1)]
            played_music.append(music_name)
        
        if repeat_song.is_set() or queue_song.is_set():
            music_index -= 1

        queue_song.clear() # reset so we don't repeat anymore

        if play_last_song.is_set():
            if len(played_music) > 1:
                played_music.pop()
                music_name = played_music[-1]
            play_last_song.clear()
            music_index -= 1 if music_index == 1 else 2

        pygame.mixer.music.load(music_name)
        pygame.mixer.music.play(fade_ms=fade_ms)

        music_index += 1
        if music_index == len(music_files):
            music_index = 0

        action_function()