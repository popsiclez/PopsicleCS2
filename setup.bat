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
    echo Detected Python version %INSTALLED_VERSION%.
    if "%INSTALLED_VERSION%"=="%PYTHON_VERSION%" (
        echo Correct Python version already installed.
        
        :: Ask user if they want to install/update Python packages
        echo.
        echo Do you want to install/update Python packages? (Y/N)
        set /p "INSTALL_PACKAGES=Enter your choice: "
        
        if /i "%INSTALL_PACKAGES%"=="N" (
            echo Skipping Python package installation...
            goto download_files
        )
        
        if /i "%INSTALL_PACKAGES%"=="NO" (
            echo Skipping Python package installation...
            goto download_files
        )
        
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

:: Verify all packages are installed correctly
echo Verifying package installation...
"%PYTHON_EXE%" -c "import requests, pymem, pynput, PySide6, numpy, PIL, pyautogui, keyboard, scipy, win32api, win32con, win32gui; print('All packages verified successfully!')" || (
    echo ERROR: Some packages failed to install correctly!
    echo Please run setup.bat again or install packages manually.
    pause
    exit /b 1
)

:: Clear console after packages installation
cls
echo Python and all packages installed successfully.

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

set "POPSICLE_EXE=%~dp0loader.exe"

echo Downloading script...
powershell -Command "Invoke-WebRequest -Uri '%POPSICLE_URL%' -OutFile '%POPSICLE_EXE%' -UseBasicParsing"

:: -----------------------------
:: Get cleanup file download link from GitHub raw
:: -----------------------------
set "CLEANUP_LINK_FILE=%TEMP%\cleanuplink.txt"
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/cleanuplink' -OutFile '%CLEANUP_LINK_FILE%' -UseBasicParsing"
set /p CLEANUP_URL=<"%CLEANUP_LINK_FILE%"
del "%CLEANUP_LINK_FILE%"

set "CLEANUP_BAT=%~dp0cleanup.bat"

echo Downloading cleanup file...
powershell -Command "Invoke-WebRequest -Uri '%CLEANUP_URL%' -OutFile '%CLEANUP_BAT%' -UseBasicParsing"

echo Script setup complete

:: Final prompt before exit
echo.
echo Press any key to exit...
pause >nul

endlocal
