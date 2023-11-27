@echo off

TITLE TextboxSTT Updater

cd /d %~dp0\..

.\git\bin\git.exe status --porcelain --untracked-files=no | find /i "M"

if not errorlevel 1  (
	set /p "answer=You've made changes to some base files, do you want to stash your changes [Y/n] "
) else (
	set answer=n
)

if /i "%answer%" EQU "n" (
	.\git\bin\git.exe reset --hard
	.\git\bin\git.exe pull --rebase
) else (
	.\git\bin\git.exe stash
	.\git\bin\git.exe pull --rebase
	.\git\bin\git.exe stash pop
)

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