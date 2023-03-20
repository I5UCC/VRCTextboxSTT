import os
import sys
import winsound
import logging
import psutil
from ctypes import windll, byref, create_unicode_buffer, create_string_buffer
from ctranslate2 import get_supported_compute_types
import json


class LogToFile(object):
    def __init__(self, logger, level, logfile):
        self.logger = logger
        self.level = level
        self.linebuf = ''

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
            filename=logfile,
            filemode='a'
        )

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


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


def play_sound(filename, script_path=__file__):
    """Plays a wave file."""
    filename = f"resources/{filename}.wav"
    winsound.PlaySound(get_absolute_path(filename, script_path), winsound.SND_FILENAME | winsound.SND_ASYNC)


def get_best_compute_type(device, device_index=0) -> str:
    types = list(get_supported_compute_types(device, device_index))

    if "int8_float16" in types:
        return "int8_float16"
    
    if "int8" in types:
        return "int8"

    if "float16" in types:
        return "float16"

    return "float32"


def force_single_instance():
    """Force single instance by killing other instances of the same Name."""

    _pid = os.getpid()
    PROCNAME = psutil.Process(_pid).name()

    if PROCNAME == "python.exe":
        return

    print(f"Current process: {_pid}, {PROCNAME}")
    for proc in psutil.process_iter():
        if proc.name() == PROCNAME and proc.pid != _pid:
            proc.kill()
            print("killed", proc.pid)


def get_config(config_path: str, default_config_path: str) -> dict:
    _default_config = json.load(open(default_config_path))
    try:
        _config = json.load(open(config_path))
    except FileNotFoundError:
        json.dump(_default_config, open(config_path, "w"), indent=4)
        return _default_config

    _tmp = check_config(_config, _default_config)

    _res = dict()
    for key in _default_config:
        _res[key] = _tmp[key]

    json.dump(_res, open(config_path, "w"), indent=4)

    return _res


def check_config(config: dict, default_config: dict) -> dict:
    for key in default_config: 
        try:
            if isinstance(config[key], dict):
                config[key] = check_config(config[key], default_config[key])
        except KeyError:
            print(f"Config key \"{key}\" not found. Using default value.")
            config[key] = default_config[key]

    return config