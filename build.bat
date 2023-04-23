@echo off

cd %~dp0

RMDIR /S /Q VRCTextboxSTT
RMDIR /S /Q build

git clone -n --depth=1 --filter=tree:0 https://github.com/I5UCC/VRCTextboxSTT
cd VRCTextboxSTT
git sparse-checkout set --no-cone src TextboxSTT.exe obs_only.exe
git checkout
git fetch --all --tags
cd ..
robocopy VRCTextboxSTT build/TextboxSTT /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
7z x python.zip -obuild/TextboxSTT
set /p version=< src/VERSION
cd build
7z a TextboxSTT_%version%.zip TextboxSTT