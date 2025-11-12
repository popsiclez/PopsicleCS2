@echo off
setlocal enabledelayedexpansion
color 0F
title SETUP

:: -----------------------------
:: Setup version and version check
:: -----------------------------
set "SETUP_VERSION=2"
set "VERSION_URL=https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/setupversion.txt"
set "VERSION_FILE=%TEMP%\setupversion.txt"

echo [SETUP] Checking version...
powershell -Command "try { Invoke-WebRequest -Uri '%VERSION_URL%' -OutFile '%VERSION_FILE%' -UseBasicParsing -TimeoutSec 10 } catch { exit 1 }"

if exist "%VERSION_FILE%" (
    set /p REMOTE_VERSION=<"%VERSION_FILE%"
    del "%VERSION_FILE%"
    
    if not "!REMOTE_VERSION!"=="%SETUP_VERSION%" (
        echo [SETUP] Version outdated. Run start.bat again
        echo [SETUP] Press any key to exit.
        pause >nul
        exit /b 1
    )
    echo [SETUP] Setup version is up to date
    timeout /t 2 /nobreak >nul
    cls
) else (
    echo [SETUP] Warning: Could not check setup version. Continuing...
)

:: -----------------------------
:: Start setup
:: -----------------------------
echo [SETUP] Press (ENTER) to start...
pause >nul
cls
timeout /t 2 /nobreak >nul
:: -----------------------------
:: Python settings
:: -----------------------------
set "PYTHON_VERSION=3.13.7"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe"
set "TEMP_INSTALLER=%TEMP%\python-installer.exe"
set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python313\python.exe"

:: -----------------------------
:: Check installed Python version
:: -----------------------------
if exist "%PYTHON_EXE%" (
    for /f "tokens=2 delims= " %%v in ('"%PYTHON_EXE%" --version 2^>nul') do set "INSTALLED_VERSION=%%v"
) else (
    set "INSTALLED_VERSION="
)

if defined INSTALLED_VERSION (
    echo [PYTHON SETUP] Detected Python version: %INSTALLED_VERSION%
    if "%INSTALLED_VERSION%"=="%PYTHON_VERSION%" (

        echo.
        echo [PYTHON SETUP] Install/Update Python packages?
        choice /c YN /n /m "[PYTHON SETUP] Waiting for input... (Y/N)"
        
        if errorlevel 2 (
            echo [PYTHON SETUP] Skipping package installation...
            timeout /t 2 /nobreak >nul
            cls
            goto download_files
        )
        
        cls
        goto install_libs
    ) else (
        echo Incorrect Python version detected. Updating to %PYTHON_VERSION%...
    )
) else (
    echo Python not found. Installing Python %PYTHON_VERSION%... Please wait
)

:: -----------------------------
:: Download Python installer
:: -----------------------------
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%TEMP_INSTALLER%'"

:: -----------------------------
:: Install Python silently
:: -----------------------------
"%TEMP_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
timeout /t 10 /nobreak >nul
del "%TEMP_INSTALLER%"

::lear console after Python installation
cls

:: Go directly to package installation after Python install
goto install_libs

:: -----------------------------
:: Install Python libraries
:: -----------------------------
:install_libs
echo [PYTHON SETUP] Installing/updating pip...
"%PYTHON_EXE%" -m ensurepip --upgrade
"%PYTHON_EXE%" -m pip install --upgrade pip

echo [PYTHON SETUP] Installing libraries...
"%PYTHON_EXE%" -m pip install --upgrade requests
"%PYTHON_EXE%" -m pip install --upgrade pymem
"%PYTHON_EXE%" -m pip install --upgrade pynput
"%PYTHON_EXE%" -m pip install --upgrade PySide6
"%PYTHON_EXE%" -m pip install --upgrade qt-material
"%PYTHON_EXE%" -m pip install --upgrade pywin32
"%PYTHON_EXE%" -m pip install --upgrade numpy
"%PYTHON_EXE%" -m pip install --upgrade pillow
"%PYTHON_EXE%" -m pip install --upgrade pyautogui
"%PYTHON_EXE%" -m pip install --upgrade keyboard
"%PYTHON_EXE%" -m pip install --upgrade scipy

:: Verify all packages are installed correctly
echo [PYTHON SETUP] Verifying package installation...
"%PYTHON_EXE%" -c "import requests, pymem, pynput, PySide6, numpy, PIL, pyautogui, keyboard, scipy, win32api, win32con, win32gui; print('All packages verified successfully!')" || (
    echo [PYTHON SETUP] ERROR: Some packages failed to install correctly!
    echo [PYTHON SETUP] Please run setup.bat again or install packages manually.
    pause
    exit /b 1
)

:: Clear console after packages installation
cls
echo [PYTHON SETUP] Python and packages installed
timeout /t 2 /nobreak >nul
cls
:: -----------------------------
:: Download files section
:: -----------------------------
:download_files
:: -----------------------------
:: Get loader download link from GitHub raw
:: -----------------------------
set "LINK_FILE=%TEMP%\loaderlink.txt"
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/loaderlink' -OutFile '%LINK_FILE%' -UseBasicParsing"
set /p POPSICLE_URL=<"%LINK_FILE%"
del "%LINK_FILE%"

:: Generate random loader name
set "LOADER_NAMES=discord notepad chrome edge calculator paint winrar steam spotify teamspeak skype vlc obs explorer"
set /a "RANDOM_NUM=%RANDOM% %% 13 + 1"
set "COUNT=0"
for %%a in (%LOADER_NAMES%) do (
    set /a "COUNT+=1"
    if !COUNT! equ !RANDOM_NUM! set "LOADER_NAME=%%a"
)

set "POPSICLE_EXE=%~dp0!LOADER_NAME!.exe"

echo [SETUP] Creating loader...
powershell -Command "Invoke-WebRequest -Uri '%POPSICLE_URL%' -OutFile '%POPSICLE_EXE%' -UseBasicParsing"

cls

echo [SETUP] Loader created: !LOADER_NAME!.exe

:: Final prompt before exit
echo.
echo [SETUP] Press any key to exit...
pause >nul

endlocal
