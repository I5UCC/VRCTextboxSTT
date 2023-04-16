from torch.cuda import is_available
import sys

sys.setrecursionlimit(sys.getrecursionlimit() * 5)

packages = [
    "av",
    "certifi",
    "charset_normalizer",
    "click",
    "colorama",
    "ctranslate2",
    "dataclasses_json",
    "faster_whisper",
    "filelock",
    "flask",
    "flatbuffers",
    "functorch",
    "google",
    "huggingface_hub",
    "humanfriendly",
    "idna",
    "itsdangerous",
    "jinja2",
    "keyboard",
    "kthread",
    "markupsafe",
    "marshmallow",
    "marshmallow_enum",
    "mpmath",
    "networkx",
    "numpy",
    "openvr",
    "packaging",
    "PIL",
    "psutil",
    "pyaudio",
    "pydub",
    "pyreadline3",
    "pythonosc",
    "regex",
    "requests",
    "sentencepiece",
    "speech_recognition",
    "sympy",
    "tokenizers",
    "torch",
    "torchgen",
    "tqdm",
    "transformers",
    "urllib3",
    "waitress",
    "werkzeug",
    "yaml"
]
gpu_packages = ["nvfuser"]
if is_available():
    packages.extend(gpu_packages)
print(packages)

version = open("VERSION").readline().rstrip()

excludes = [
    "distutils",
    "setuptools"
]

file_include = [
    "../LICENSE",
    "VERSION",
    "config.json",
    "bindings/",
    "resources/",
    "app.vrmanifest",
    "KAT_Emote_Texture_Sheet/"
]

base = "Win32GUI" if sys.platform == "win32" else None

build_exe_options = {
    "packages": packages,
    "include_files": file_include,
    'include_msvcr': True,
    'optimize': 1
}

from cx_Freeze import setup, Executable

setup(
    name="TextboxSTT",
    version=version,
    description="TextboxSTT",
    options={"build_exe": build_exe_options},
    executables=[Executable("TextboxSTT.py", target_name="TextboxSTT.exe", base=base, icon="resources/icon.ico"), Executable("OBSWSTT.py", target_name="OBS_only.exe", base=None)],
)
