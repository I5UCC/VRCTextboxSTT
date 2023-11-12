@echo off

TITLE TextboxSTT Updater

cd %~dp0\..
.\git\bin\git.exe reset --hard
.\git\bin\git.exe pull --rebase
if exist ../python/CPU (
	echo reinstalling CPU dependencies
	.\python\python.exe -m pip install -U -r .\src\requirements.cpu.txt --no-warn-script-location
) else (
	echo reinstalling all dependencies
	.\python\python.exe -m pip install -U -r .\src\requirements.txt --no-warn-script-location
)

echo.
echo.
echo Done! Press any key to exit...
pause >nul
exit /b %errorlevel%