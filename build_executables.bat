@echo off
cd %~dp0

del /f .\TextboxSTT.exe
del /f .\obs_only.exe

cd TextboxSTT_Launcher\TextboxSTT_Launcher
dotnet publish -r win-x64
cd ../..
powershell -c "copy TextboxSTT_Launcher\TextboxSTT_Launcher\bin\Debug\net4.8.1\win-x64\publish\TextboxSTT_Launcher.exe ./TextboxSTT.exe"

cd TextboxSTT_Launcher\obs_only_Launcher
dotnet publish -r win-x64
cd ../..
powershell -c "copy TextboxSTT_Launcher\obs_only_Launcher\bin\Debug\net4.8.1\win-x64\publish\obs_only_Launcher.exe ./obs_only.exe"

timeout 3