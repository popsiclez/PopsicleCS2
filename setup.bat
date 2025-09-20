@echo off
setlocal

:: -----------------------------
:: Start setup
:: -----------------------------
echo Press Enter to start setup...
pause >nul

:: -----------------------------
:: Python settings
:: -----------------------------
set "PYTHON_VERSION=3.11.9"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe"
set "TEMP_INSTALLER=%TEMP%\python-installer.exe"
set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"

:: -----------------------------
:: Check installed Python version
:: -----------------------------
if exist "%PYTHON_EXE%" (
    for /f "tokens=2 delims= " %%v in ('"%PYTHON_EXE%" --version 2^>nul') do set "INSTALLED_VERSION=%%v"
) else (
    set "INSTALLED_VERSION="
)

if defined INSTALLED_VERSION (
    echo Detected Python version %INSTALLED_VERSION%.
    if "%INSTALLED_VERSION%"=="%PYTHON_VERSION%" (
        echo Correct Python version already installed.
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

:: Clear console after Python installation
cls

:: -----------------------------
:: Install Python libraries
:: -----------------------------
:install_libs
echo Installing/updating pip...
"%PYTHON_EXE%" -m ensurepip --upgrade
"%PYTHON_EXE%" -m pip install --upgrade pip

echo Installing required libraries...
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

:: Clear console after packages installation
cls
echo Python and all packages installed successfully.

:: -----------------------------
:: Get Dropbox download link from GitHub raw
:: -----------------------------
set "LINK_FILE=%TEMP%\dropboxlink.txt"
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/rawdownloadlink' -OutFile '%LINK_FILE%' -UseBasicParsing"
set /p POPSICLE_URL=<"%LINK_FILE%"
del "%LINK_FILE%"

set "POPSICLE_EXE=%~dp0loader.exe"

echo Downloading script...
powershell -Command "Invoke-WebRequest -Uri '%POPSICLE_URL%' -OutFile '%POPSICLE_EXE%' -UseBasicParsing"

echo Script setup complete

:: Final prompt before exit
echo.
echo Press any key to exit...
pause >nul

endlocal
