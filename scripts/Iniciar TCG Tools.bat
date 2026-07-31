@echo off

setlocal

set "ROOT=%~dp0.."

set "LOCK=%TEMP%\tcg_tools_instance.lock"

set "TCGTOOLS_DATA_DIR=%APPDATA%\TCGTools"

if not exist "%TCGTOOLS_DATA_DIR%" mkdir "%TCGTOOLS_DATA_DIR%"



if exist "%LOCK%" (

    echo TCG Tools ja parece estar em execucao.

    echo Feche a instancia anterior ou remova %LOCK% se tiver certeza.

    pause

    exit /b 1

)

echo %DATE% %TIME% > "%LOCK%"



cd /d "%ROOT%\backend"



if exist "%ROOT%\runtime\venv\Scripts\python.exe" (

    set "PYTHON=%ROOT%\runtime\venv\Scripts\python.exe"

) else if exist "%ROOT%\runtime\python\python.exe" (

    set "PYTHON=%ROOT%\runtime\python\python.exe"

) else (

    where py >nul 2>&1

    if %ERRORLEVEL%==0 (

        set "PYTHON=py -3.13"

    ) else (

        set "PYTHON=python"

    )

)



echo Iniciando TCG Tools...

start "" "http://127.0.0.1:8000"

"%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000



del "%LOCK%" 2>nul

pause

