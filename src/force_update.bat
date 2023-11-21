@echo off

TITLE TextboxSTT Updater

cd /d %~dp0\..
.\git\bin\git.exe reset --hard
.\git\bin\git.exe pull --rebase
.\python\python.exe -m pip install --upgrade pip
if exist python/CPU (
	echo reinstalling CPU dependencies
	.\python\python.exe -m pip install -U -r .\src\requirements.cpu.txt --no-warn-script-location
) else (
	echo reinstalling all dependencies
	.\python\python.exe -m pip install -U -r .\src\requirements.txt --no-warn-script-location
)

echo.
echo.
echo Done!
timeout /T 15
exit /b %errorlevel%