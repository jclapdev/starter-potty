@echo off
REM Double-click this file to install the system. Sets everything up for you.
powershell -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/jclapdev/starter-potty/main/install.ps1 | iex"
echo.
echo All done. You can close this window.
pause
