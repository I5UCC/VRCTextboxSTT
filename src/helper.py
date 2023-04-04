import os
import sys
import logging
import psutil
import shutil
from ctypes import windll, byref, create_unicode_buffer, create_string_buffer
from ctranslate2 import get_supported_compute_types
from datetime import datetime
from glob import glob
import traceback

log = logging.getLogger('TextboxSTT')

class LogToFile(object):
    def __init__(self, cache_path):
        logfile = os.path.join(cache_path, 'latest.log')
        process_cache(cache_path, logfile)

        self.logger = log
        self.level = logging.DEBUG
        self.linebuf = ''
        self.ui_output = None

        logging.basicConfig(
            level=self.level,
            format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
            filename=logfile,
            filemode='a'
        )

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())
            if self.ui_output:
                self.ui_output(line.rstrip())

    def flush(self):
        pass

    def set_ui_output(self, output_method):
        self.ui_output = output_method
    
    def remove_ui_output(self):
        self.ui_output = None


def process_cache(cache_path, latest_log):
    try:
        os.mkdir(cache_path)
    except FileExistsError:
        pass
    except Exception:
        log.fatal("Failed to create cache directory: ")
        log.error(traceback.format_exc())

    try:
        logs = glob(cache_path + "/*.log")
        if len(logs) >= 5:
            logs.sort(key=os.path.getmtime)
            for log in logs[:-5]:
                os.remove(log)

        if os.path.isfile(latest_log):
            shutil.copy(latest_log, os.path.join(cache_path, datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log")))
    except Exception:
        logging.error("Error processing old logs:")
        log.error(traceback.format_exc())

    open(latest_log, 'w').close()


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

    try:
        _pid = os.getpid()
        _procname = psutil.Process(_pid).name()

        if "python" in _procname:
            return

        for proc in psutil.process_iter():
            if proc.name() == _procname and proc.pid != _pid:
                proc.kill()
    except Exception:
        pass
