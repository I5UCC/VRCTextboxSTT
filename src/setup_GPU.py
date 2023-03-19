from cx_Freeze import setup, Executable
import sys

sys.setrecursionlimit(sys.getrecursionlimit() * 5)

packages = ["av", "certifi", "charset_normalizer", "click", "colorama", "ctranslate2", "faster_whisper", "filelock", "flask", "functorch", "huggingface_hub", "idna", "itsdangerous", "jinja2", "keyboard", "kthread", "markupsafe", "mpmath", "networkx", "numpy", "nvfuser", "openvr", "packaging", "PIL", "psutil", "pyaudio", "pythonosc", "regex", "requests", "speech_recognition", "sympy", "tokenizers", "torch", "torchgen", "tqdm", "transformers", "urllib3", "waitress", "werkzeug", "yaml"]
excludes = ["distutils", "setuptools"]
file_include = ["config.json", "bindings/", "resources/", "app.vrmanifest", "KAT_Emote_Texture_Sheet/"]
base = "Win32GUI" if sys.platform == "win32" else None

build_exe_options = {"packages": packages, "include_files": file_include, 'include_msvcr': True, 'optimize': 2}
setup(
    name="TextboxSTT",
    version="v1.0.0-Beta",
    description="TextboxSTT",
    options={"build_exe": build_exe_options},
    executables=[Executable("TextboxSTT.py", target_name="TextboxSTT.exe", base=base)],
)
