'''Initialize shared Packer services and runtime availability settings.'''

__all__ = [
    'notification_sound',
    'send_notification',
    'exception_handler',
    'ollama_available',
    'available_models',
    'default_model',
    'available_text_editors',
    'default_text_editor',
]


import sys
import threading
import ollama
import pygame
from httpx import HTTPError, get
from os import environ

from packer.constants import TEXT_EDITORS
from packer.paths import assets_dir, log_path, error_report_path
from shutil import which
from plyer import notification
from packer.exceptions import Global_exception_handler
from packer.config import packer_version, all_settings


pygame.mixer.init()

notification_sound = pygame.mixer.Sound(f'{assets_dir}/audio/sounds/new notification {all_settings.notification_sound_path}.wav'
                                        if len(all_settings.notification_sound_path.strip()) == 1
                                        else all_settings.notification_sound_path)
notification_sound.set_volume(all_settings.notification_volume)

def send_notification(title: str, message: str, timeout: int = 5):
    '''
    Send a desktop notification.

    :param title: the title of the notification
    :type title: str
    :param message: the message of the notification
    :type message: str
    :param timeout: the duration (in seconds) for which the notification should be displayed
    :type timeout: int
    '''

    notification.notify(
        title=title,
        message=message,
        app_name='Packer',
        app_icon=f'{assets_dir}/images/Packer icon.png',
        timeout=timeout
    )

    notification_sound.play()


exception_handler = Global_exception_handler(packer_version, log_path, error_report_path,
                                             'https://formspree.io/f/xjgqgqbz' if all_settings.automatic_error_reporting else None, 'emilspro888@gmail.com', 'EMILIO888real/Packer')


def get_ollama_host() -> str:
    '''Resolve the server address the same way the ollama CLI does.'''
    host = environ.get('OLLAMA_HOST', '127.0.0.1:11434').strip()
    if '://' not in host:
        host = f'http://{host}'
    host = host.replace('0.0.0.0', '127.0.0.1') # bind address, not connectable
    if host.count(':') == 1: # scheme only, no port given
        host += ':11434'
    return host.rstrip('/')

def is_ollama_running(host: str) -> bool:
    try:
        return get(f'{host}/api/version').status_code == 200
    except HTTPError: # covers ConnectError, timeouts, etc.
        return False

ollama_available = is_ollama_running(get_ollama_host())

if ollama_available:
    available_models = [model.model for model in sorted(
        [model for model in ollama.list().models
         if 'completion' in (ollama.show(model.model).capabilities or [])],
        key=lambda model: model.size)]
    default_model = (('mistral:latest' if 'mistral:latest' in available_models
                      else available_models[0]) if available_models else None)
else:
    available_models = None
    default_model = None


available_text_editors = [
    (name, exe, wait_flag)
    for name, exe, wait_flag in TEXT_EDITORS
    if which(exe)
]

default_text_editor = available_text_editors[0][1]

def thread_excepthook(args):
    sys.excepthook(args.exc_type, args.exc_value, args.exc_traceback)

threading.excepthook = thread_excepthook # Also, so other threads access the same handler