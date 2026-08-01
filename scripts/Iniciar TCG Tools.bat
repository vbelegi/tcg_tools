@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1" %*
set ERR=%ERRORLEVEL%
if %ERR% neq 0 pause
exit /b %ERR%
