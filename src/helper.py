import os
import sys
import logging
from ctypes import windll, byref, create_unicode_buffer, create_string_buffer
from ctranslate2 import get_supported_compute_types
import re
import time

log = logging.getLogger(__name__)


def measure_time(func):
    """Decorator to measure the time of a function."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        log.debug(f"{func.__qualname__} took {time.time() - start:.4f} seconds")
        return result
    return wrapper


def loadfont(fontpath, private=True, enumerable=False) -> bool:
    '''
    Makes fonts located in file `fontpath` available to the font system.

    `private`     if True, other processes cannot see this font, and this
                  font will be unloaded when the process dies
    `enumerable`  if True, this font will appear when enumerating fonts

    See https://msdn.microsoft.com/en-us/library/dd183327(VS.85).aspx

    '''
    # This function was taken from
    # https://github.com/ifwe/digsby/blob/f5fe00244744aa131e07f09348d10563f3d8fa99/digsby/src/gui/native/win/winfonts.py#L15
    # "Copyright (c) 2006-2012 Tagged, Inc; All Rights Reserved"
    FR_PRIVATE  = 0x10
    FR_NOT_ENUM = 0x20

    if isinstance(fontpath, bytes):
        pathbuf = create_string_buffer(fontpath)
        add_font_resource_ex = windll.gdi32.AddFontResourceExA
    elif isinstance(fontpath, str):
        pathbuf = create_unicode_buffer(fontpath)
        add_font_resource_ex = windll.gdi32.AddFontResourceExW
    else:
        raise TypeError('fontpath must be of type str or bytes')

    flags = (FR_PRIVATE if private else 0) | (FR_NOT_ENUM if not enumerable else 0)
    num_fonts_added = add_font_resource_ex(byref(pathbuf), flags, 0)
    return bool(num_fonts_added)


def get_absolute_path(relative_path, script_path=__file__) -> str:
    """Gets absolute path from relative path"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(script_path)))
    return os.path.join(base_path, relative_path)


def get_best_compute_type(device, device_index=0) -> str:
    supported_types = set(get_supported_compute_types(device, device_index))
    preferred_types = ["int8_float16", "int8", "float16", "float32"]

    for compute_type in preferred_types:
        if compute_type in supported_types:
            return compute_type


def replace_emotes(text, emote_list, emote_keys):
    """Replaces emotes in the text with the configured emotes."""

    if not text:
        return None

    if emote_list is None:
        return text

    for i in range(len(emote_list)):
        word = emote_list[str(i)]
        if word == "":
            continue
        tmp = re.compile(word, re.IGNORECASE)
        text = tmp.sub(emote_keys[i], text)

    return text


def replace_words(text: str, replacement_dict: dict):
    """Replaces words in the text with the configured replacements."""

    if not text or not replacement_dict:
        return text

    for key, value in replacement_dict.items():
        text = key.sub(value, text)

    text = re.sub(' +', ' ', text)
    text = text.strip()

    return text
