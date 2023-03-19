@echo off

set /p version=Version: 

RMDIR /S /Q build

:: BUILD CPU
..\.venv_cpu\Scripts\python.exe -m pip install cx_freeze
..\.venv_cpu\Scripts\python.exe .\setup_CPU.py build
robocopy ..\.venv_cpu\Lib\site-packages\av.libs build\exe.win-amd64-3.10\lib\av.libs /E /NFL /NDL /NJH /NJS /nc /ns /np
robocopy build\exe.win-amd64-3.10 build\CPU\TextboxSTT /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
7z a TextboxSTT_%version%_CPU.7z build\CPU\TextboxSTT -mx9
move TextboxSTT_%version%_CPU.7z build

:: BUILD GPU
..\.venv_gpu\Scripts\python.exe -m pip install cx_freeze
..\.venv_gpu\Scripts\python.exe .\setup_GPU.py build
robocopy ..\.venv_gpu\Lib\site-packages\av.libs build\exe.win-amd64-3.10\lib\av.libs /E /NFL /NDL /NJH /NJS /nc /ns /np
robocopy build\exe.win-amd64-3.10 build\GPU\TextboxSTT /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
7z a TextboxSTT_%version%_GPU.7z build\GPU\TextboxSTT -mx9
move TextboxSTT_%version%_GPU.7z build

pause