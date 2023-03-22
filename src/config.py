from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Optional
from json import load

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
class audio(object):
    enabled: bool = True
    file: Optional[str] = None
    gain: int = 0

@dataclass_json
@dataclass
class audio_feedback_config(object):
    enabled: bool = True
    sound_clear: audio = audio(True, "clear.wav", 0)
    sound_donelisten: audio = audio(True, "donelisten.wav", 0)
    sound_finished: audio = audio(True, "finished.wav", 0)
    sound_listen: audio = audio(True, "listen.wav", 0)
    sound_timeout: audio = audio(True, "timeout.wav", 0)
    

@dataclass_json
@dataclass
class device_config(object):
    type: str = "cuda"
    index: int = 0
    compute_type: Optional[str] = None
    cpu_threads: int = 4
    num_workers: int = 1


@dataclass_json
@dataclass
class osc_config(object):
    ip: str = "127.0.0.1"
    client_port: int = 9000
    server_port: int = 9001
    use_textbox: bool = True
    use_kat: bool = True
    use_both: bool = False


@dataclass_json
@dataclass
class whisper_config(object):
    model: str = "base"
    language: str = "english"
    translate_to_english: bool = False


@dataclass_json
@dataclass
class listener_config(object):
    microphone_index: Optional[int] = None
    dynamic_energy_threshold: bool = False
    energy_threshold: float = 200
    pause_threshold: float = 0.8
    timeout_time: float = 3.0
    hold_time: float = 1.5
    phrase_time_limit: float = 2.0


@dataclass_json
@dataclass
class overlay_config(object):
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
class obs_config(object):
    enabled: bool = False
    port: int = 5000
    update_interval: int = 200
    font: str = "Cascadia Code"
    color: str = "white"
    shadow_color: str = "black"
    align: str = "center"


@dataclass_json
@dataclass
class wordreplacement_config(object):
    enabled: bool = False
    list: dict = field(default_factory=dict)

@dataclass_json
@dataclass
class emotes_config(object):
    enabled: bool = False
    list: dict = field(default_factory=lambda: {
        "0": "wicked emoji",
        "1": "clueless emoji",
        "2": "aware emoji",
        "3": "shy emoji",
        "4": "pog emoji",
        "5": "happy emoji",
        "6": "cry emoji",
        "7": "weird emoji",
        "8": "okay emoji",
        "9": "think emoji",
        "10": "dead emoji",
        "11": "sleep emoji",
        "12": "woke emoji",
        "13": "heart emoji",
        "14": "stare emoji",
        "15": "",
        "16": "",
        "17": "",
        "18": "",
        "19": "",
        "20": "",
        "21": "",
        "22": "",
        "23": "",
        "24": "",
        "25": "",
        "26": "",
        "27": "",
        "28": "",
        "29": "",
        "30": "",
        "31": "",
        "32": "",
        "33": "",
        "34": "",
        "35": "",
        "36": "",
        "37": "",
        "38": "",
        "39": "",
        "40": "",
        "41": "",
        "42": "",
        "43": "",
        "44": "",
        "45": "",
        "46": "",
        "47": "",
        "48": "",
        "49": "",
        "50": "",
        "51": "",
        "52": "",
        "53": "",
        "54": "",
        "55": "",
        "56": "",
        "57": "",
        "58": "",
        "59": "",
        "60": "",
        "61": "",
        "62": "",
        "63": "",
        "64": "",
        "65": "",
        "66": "",
        "67": "",
        "68": "",
        "69": "",
        "70": "",
        "71": "",
        "72": "",
        "73": "",
        "74": "",
        "75": "",
        "76": "",
        "77": "",
        "78": "",
        "79": ""
    })
    

@dataclass_json
@dataclass
class config_struct(object):
    mode: int = 0
    hotkey: str = "f1"
    audio_feedback: audio_feedback_config = field(default_factory=audio_feedback_config)
    device: device_config = field(default_factory=device_config)
    osc: osc_config = field(default_factory=osc_config)
    whisper: whisper_config = field(default_factory=whisper_config)
    listener: listener_config = field(default_factory=listener_config)
    overlay: overlay_config = field(default_factory=overlay_config)
    obs: obs_config = field(default_factory=obs_config)
    wordreplacement: wordreplacement_config = field(default_factory=wordreplacement_config)
    emotes: emotes_config = field(default_factory=emotes_config)

    @staticmethod
    def load(path: str):
        """Load a config from a file path. Returns a config_struct object."""
        return config_struct.from_dict(load(open(path)))
