from cx_Freeze import setup, Executable

packages = ["torch", "whisper", "numpy", "psutil", "keyboard", "openvr", "pythonosc", "pyaudio", "speech_recognition", "PIL"]
file_include = ["config.json", "bindings/", "resources/", "app.vrmanifest", "KAT_Emote_Texture_Sheet/"]

build_exe_options = {"packages": packages, "include_files": file_include}
setup(
    name="TextboxSTT",
    version="0.8.2",
    description="TextboxSTT",
    options={"build_exe": build_exe_options},
    executables=[Executable("TextboxSTT.py", targetName="TextboxSTT.exe", base="Win32GUI")],
)
