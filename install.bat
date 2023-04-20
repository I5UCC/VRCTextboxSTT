@echo off
cd %~dp0
TITLE TextboxSTT Installer/Updater

if NOT exist python/INSTALLED (
	if exist python/CPU del /f python\CPU
	set /p CPU=CPU only? [y/N]: 
	echo "" > python/CPU
) else if exist python/CPU (
	set CPU=true
) else (
	set CPU=false
)

echo Check git.
git\bin\git.exe pull --rebase --autostash
if /I "%CPU%" EQU "Y" (
	echo installing CPU only Packages
	python\python.exe -m pip install -U -r .\src\requirements.cpu.txt
) else (
	echo installing Packages
	python\python.exe -m pip install -U -r .\src\requirements.txt
)
echo Clear Cache
python\python.exe -m pip cache purge

if NOT exist config.json (
	echo Creating Config.
	powershell -c "copy src/config.json config.json"
)

if NOT exist python/INSTALLED (
	echo "" > python/INSTALLED
)

echo.
echo Installation/Update successful.
echo.

timeout 15