@echo off
cd %~dp0
TITLE TextboxSTT checker

for /f "usebackq delims=" %%i in (`
  powershell -c "Invoke-WebRequest -uri https://raw.githubusercontent.com/I5UCC/VRCTextboxSTT/main/src/VERSION -Headers @{'Cache-Control'='no-cache'} | Select-Object -ExpandProperty Content"
`) do set latest=%%i

set /p version=< src\VERSION

echo Latest Version:  %latest%
echo Current Version: %version%

if NOT exist python/INSTALLED (
	echo.
	echo NOT INSTALLED YET, PLEASE RUN "install.bat" FIRST.
	echo.
	exit /B -1
)

if /I "%version%" NEQ "%latest%" (
	echo.
	echo New version %latest% available, run "install.bat" to update
	exit /B 1
)

echo Already up do date.
exit /B 0