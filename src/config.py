from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Optional

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

@dataclass_json
@dataclass
class device(object):
    type: str = "cuda"
    index: int = 0
    compute_type: Optional[str] = None
    cpu_threads: int = 4
    num_workers: int = 1

@dataclass_json
@dataclass
class osc(object):
    ip: str = "127.0.0.1"
    client_port: int = 9000
    server_port: int = 9001
    use_textbox: bool = True
    use_kat: bool = True
    use_both: bool = False

@dataclass_json
@dataclass
class whisper(object):
    model: str = "base"
    language: str = "english"
    translate_to_english: bool = False

@dataclass_json
@dataclass
class listener(object):
    microphone_index: Optional[int] = None
    dynamic_energy_threshold: bool = False
    energy_threshold: float = 200
    pause_threshold: float = 0.8
    timeout_time: float = 3.0
    hold_time: float = 1.5
    phrase_time_limit: float = 2.0

@dataclass_json
@dataclass
class overlay(object):
    enabled: bool = False
    pos_x: float = 0.0
    pos_y: float = -0.4
    size: float = 1.0
    distance: float = -1.0
    font_color: str = "white"
    border_color: str = "black"
    opacity: float = 1.0

@dataclass_json
@dataclass
class obs(object):
    enabled: bool = False
    port: int = 5000
    update_interval: int = 200
    font: str = "Cascadia Code"
    color: str = "white"
    shadow_color: str = "black"
    align: str = "center"

@dataclass_json
@dataclass
class wordreplacement(object):
    list: Optional[dict]
    enabled: bool = False

@dataclass_json
@dataclass
class emotes(object):
    list: Optional[dict]
    enabled: bool = False

@dataclass_json
@dataclass
class config(object):
    device: device
    osc: osc
    whisper: whisper
    listener: listener
    overlay: overlay
    obs: obs
    wordreplacement: wordreplacement
    emotes: emotes
    hotkey: str = "F1"
    audio_feedback: bool = True
    mode: int = 0
