@echo off

cd %~dp0\..
.\git\bin\git.exe reset --hard
.\git\bin\git.exe pull --rebase
if exist ../python/CPU (
	.\python\python.exe -m pip install -U -r .\src\requirements.cpu.txt
) else (
	.\python\python.exe -m pip install -U -r .\src\requirements.txt
)


echo Done! Press any key to exit...
pause >nul