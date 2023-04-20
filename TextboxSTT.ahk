RunWait, %A_ScriptDir%\check_install.bat, ,hide

Switch ErrorLevel
{
    case -1:
        MsgBox, 16, TextboxSTT, TextboxSTT is not installed. Please run 'install.bat' first.
        Exit % ErrorLevel
    case 1:
        TrayTip, TextboxSTT, New Update Available. Run 'install.bat' to update., 1
}

If Not Errorlevel = -1
{
    Run, %A_ScriptDir%/python/TextboxSTT.exe TextboxSTT.py _ _ _, %A_ScriptDir%/src
}