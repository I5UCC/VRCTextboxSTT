from cx_Freeze import setup, Executable

packages = ["torch", "whisper"]
file_include = ["config.json", "bindings/", "resources/", "app.vrmanifest"]

build_exe_options = {"packages": packages, "include_files": file_include}
setup(
    name="TextboxSTT",
    version="0.2",
    description="TextboxSTT",
    options={"build_exe": build_exe_options},
    executables=[Executable("TextboxSTT.py", targetName="TextboxSTT.exe", base="Win32GUI")],
)