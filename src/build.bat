@echo off

set /p CPU=Build CPU Version [Y/n]: 

if /I "%CPU%" NEQ "N" set /p CPU7z=Create CPU 7z file? [Y/n]: 
if /I "%CPU%" NEQ "N" (
	if /I "%CPU7z%" NEQ "N" set /p CPUDel=Delete Folder after build? [Y/n]: 
)

set /p GPU=Build GPU Version [Y/n]: 

if /I "%GPU%" NEQ "N" set /p GPU7z=Create GPU 7z file? [Y/n]: 
if /I "%GPU%" NEQ "N" (
	if /I "%GPU7z%" NEQ "N" set /p GPUDel=Delete Folder after build? [Y/n]: 
)

set /p version=< VERSION
echo %version%

RMDIR /S /Q build

:: BUILD CPU
if /I "%CPU%" NEQ "N" (
	..\.venv_cpu\Scripts\python.exe -m pip install cx_freeze
	..\.venv_cpu\Scripts\python.exe .\setup.py build
	robocopy ..\.venv_cpu\Lib\site-packages\av.libs build\exe.win-amd64-3.10\lib\av.libs /E /NFL /NDL /NJH /NJS /nc /ns /np
	robocopy build\exe.win-amd64-3.10 TextboxSTT /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
	if /I "%CPU7z%" NEQ "N" (
		if /I "%CPUDel%" NEQ "N" (
			7z a TextboxSTT_%version%_CPU.7z TextboxSTT -mx9 -sdel
		) else (
			7z a TextboxSTT_%version%_CPU.7z TextboxSTT -mx9
		)
		move TextboxSTT_%version%_CPU.7z build
	)
	robocopy TextboxSTT build\TextboxSTT_CPU /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
)

:: BUILD GPU
if /I "%GPU%" NEQ "N" (
	..\.venv_gpu\Scripts\python.exe -m pip install cx_freeze
	..\.venv_gpu\Scripts\python.exe .\setup.py build
	robocopy ..\.venv_gpu\Lib\site-packages\av.libs build\exe.win-amd64-3.10\lib\av.libs /E /NFL /NDL /NJH /NJS /nc /ns /np
	robocopy build\exe.win-amd64-3.10 TextboxSTT /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
	if /I "%GPU7z%" NEQ "N" (
		if /I "%GPUDel%" NEQ "N" (
			7z a TextboxSTT_%version%_GPU.7z TextboxSTT -mx9 -sdel
		) else (
			7z a TextboxSTT_%version%_GPU.7z TextboxSTT -mx9
		)
		move TextboxSTT_%version%_GPU.7z build
	)
	robocopy TextboxSTT build\TextboxSTT_GPU /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
)

echo Done building TextboxSTT %version%
pause