import sys
from cx_Freeze import setup, Executable

packages = ["torch"]
file_include = ["config.json", "bindings/", "app.vrmanifest", "ping.wav", "ping2.wav"]

build_exe_options = {"packages": packages, "include_files": file_include}
setup(
    name="TextboxSTT",
    version="0.1",
    description="TextboxSTT",
    options={"build_exe": build_exe_options},
    executables=[Executable("TextboxSTT.py", targetName="TextboxSTT.exe", base=False), Executable("TextboxSTT.py", targetName="TextboxSTT_NoConsole.exe", base="Win32GUI")],
)