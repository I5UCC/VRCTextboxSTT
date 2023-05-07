@echo off
cd %~dp0

del /f .\TextboxSTT.exe
del /f .\obs_only.exe

Bat_To_Exe_Converter.exe /bat .\TextboxSTT.bat /exe .\TextboxSTT.exe /icon .\src\resources\icon.ico /x64 /copyright I5UCC
Bat_To_Exe_Converter.exe /bat .\obs_only.bat /exe .\obs_only.exe /icon .\src\resources\icon.ico /x64 /copyright I5UCC

timeout 10