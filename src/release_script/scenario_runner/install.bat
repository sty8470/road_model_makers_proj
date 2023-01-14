@echo off
set SCRIPT="%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"

echo sLinkFile = "%~dp0scenario runner.lnk" >> %SCRIPT%
echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%~dp0program\scenario runner.exe" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT%
del %SCRIPT%
echo Installation is done. Press any key to exit.
pause