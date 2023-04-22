@echo off

cd %~dp0

RMDIR /S /Q VRCTextboxSTT
RMDIR /S /Q TextboxSTT

git clone -n --depth=1 --filter=tree:0 https://github.com/I5UCC/VRCTextboxSTT
cd VRCTextboxSTT
git sparse-checkout set --no-cone src TextboxSTT.exe obs_only.exe
git checkout
git fetch --all --tags
cd ..
robocopy VRCTextboxSTT TextboxSTT /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
robocopy python TextboxSTT/python /E /NFL /NDL /NJH /NJS /nc /ns /np
set /p version=< src/VERSION
7z a TextboxSTT_%version%.zip TextboxSTT