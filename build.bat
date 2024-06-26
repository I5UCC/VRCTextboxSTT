@echo off

cd %~dp0

rmdir /S /Q build
mkdir build
cd build

git clone -n --depth=1 --filter=tree:0 https://github.com/I5UCC/VRCTextboxSTT
cd VRCTextboxSTT
git sparse-checkout set --no-cone src TextboxSTT.exe obs_only.exe VRCaptions.exe
git checkout
git fetch --all --tags

cd ..
robocopy VRCTextboxSTT TextboxSTT /MOVE /E /NFL /NDL /NJH /NJS /nc /ns /np
7z x ../git_python.7z -oTextboxSTT
TextboxSTT\python\python.exe -m pip install --upgrade pip
set /p version=< ../src/VERSION
7z a TextboxSTT.zip TextboxSTT