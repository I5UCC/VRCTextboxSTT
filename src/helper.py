import os
import sys
import winsound
import logging
import json
from ctypes import windll, byref, create_unicode_buffer, create_string_buffer
from ctranslate2 import get_supported_compute_types

LANGUAGE_TO_KEY = {
    'english': 'en',
    'chinese': 'zh',
    'german': 'de',
    'spanish': 'es',
    'russian': 'ru',
    'korean': 'ko',
    'french': 'fr',
    'japanese': 'ja',
    'portuguese': 'pt',
    'turkish': 'tr',
    'polish': 'pl',
    'catalan': 'ca',
    'dutch': 'nl',
    'arabic': 'ar',
    'swedish': 'sv',
    'italian': 'it',
    'indonesian': 'id',
    'hindi': 'hi',
    'finnish': 'fi',
    'vietnamese': 'vi',
    'hebrew': 'he',
    'ukrainian': 'uk',
    'greek': 'el',
    'malay': 'ms',
    'czech': 'cs',
    'romanian': 'ro',
    'danish': 'da',
    'hungarian': 'hu',
    'tamil': 'ta',
    'norwegian': 'no',
    'thai': 'th',
    'urdu': 'ur',
    'croatian': 'hr',
    'bulgarian': 'bg',
    'lithuanian': 'lt',
    'latin': 'la',
    'maori': 'mi',
    'malayalam': 'ml',
    'welsh': 'cy',
    'slovak': 'sk',
    'telugu': 'te',
    'persian': 'fa',
    'latvian': 'lv',
    'bengali': 'bn',
    'serbian': 'sr',
    'azerbaijani': 'az',
    'slovenian': 'sl',
    'kannada': 'kn',
    'estonian': 'et',
    'macedonian': 'mk',
    'breton': 'br',
    'basque': 'eu',
    'icelandic': 'is',
    'armenian': 'hy',
    'nepali': 'ne',
    'mongolian': 'mn',
    'bosnian': 'bs',
    'kazakh': 'kk',
    'albanian': 'sq',
    'swahili': 'sw',
    'galician': 'gl',
    'marathi': 'mr',
    'punjabi': 'pa',
    'sinhala': 'si',
    'khmer': 'km',
    'shona': 'sn',
    'yoruba': 'yo',
    'somali': 'so',
    'afrikaans': 'af',
    'occitan': 'oc',
    'georgian': 'ka',
    'belarusian': 'be',
    'tajik': 'tg',
    'sindhi': 'sd',
    'gujarati': 'gu',
    'amharic': 'am',
    'yiddish': 'yi',
    'lao': 'lo',
    'uzbek': 'uz',
    'faroese': 'fo',
    'haitian creole': 'ht',
    'pashto': 'ps',
    'turkmen': 'tk',
    'nynorsk': 'nn',
    'maltese': 'mt',
    'sanskrit': 'sa',
    'luxembourgish': 'lb',
    'myanmar': 'my',
    'tibetan': 'bo',
    'tagalog': 'tl',
    'malagasy': 'mg',
    'assamese': 'as',
    'tatar': 'tt',
    'hawaiian': 'haw',
    'lingala': 'ln',
    'hausa': 'ha',
    'bashkir': 'ba',
    'javanese': 'jw',
    'sundanese': 'su'
}

KEY_TO_LANGUAGE = dict((v, k) for k, v in LANGUAGE_TO_KEY.items())

MODELS = {
    'tiny': 'openai/whisper-tiny',
    'tiny.en': 'openai/whisper-tiny.en',
    'base': 'openai/whisper-base',
    'base.en': 'openai/whisper-base.en',
    'small': 'openai/whisper-small',
    'small.en': 'openai/whisper-small.en',
    'medium': 'openai/whisper-medium',
    'medium.en': 'openai/whisper-medium.en',
    'large': 'openai/whisper-large',
    'large-v2': 'openai/whisper-large-v2',
}

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

def get_best_compute_type(device, device_index=0) -> str:
    types = list(get_supported_compute_types(device, device_index))

    if "int8_float16" in types:
        return "int8_float16"
    
    if "int8" in types:
        return "int8"

    if "float16" in types:
        return "float16"

    return "float32"