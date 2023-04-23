@echo off

TITLE TextboxSTT Launcher

cd %~dp0

if NOT exist python\INSTALLED echo NOT INSTALLED YET, STARTING INSTALLER

if NOT exist python\INSTALLED set /p CPU=Install CPU only? [y/N]: 

if NOT exist python\INSTALLED (
	if /I "%CPU%" EQU "Y" (
		echo "" > python\CPU
		echo installing CPU only Packages
		python\python.exe -m pip install -U -r .\src\requirements.cpu.txt --no-warn-script-location
	) else (
		echo installing all Packages
		python\python.exe -m pip install -U -r .\src\requirements.txt --no-warn-script-location
	)
	echo Clear Cache
	python\python.exe -m pip cache purge
	echo "" > python\INSTALLED
)

if NOT exist config.json (
	powershell -c "copy src\config.json config.json"
)

echo Starting TextboxSTT obs_only %version% ...
cd src
start ..\python\obs_only.exe .\OBSWSTT.py _ _ _


