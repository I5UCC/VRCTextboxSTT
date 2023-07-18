@echo off

cd %~dp0\..
.\git\bin\git.exe reset --hard
.\git\bin\git.exe pull --rebase
.\python\python.exe -m pip install -U -r .\src\requirements.txt

echo Done! Press any key to exit...
pause >nul