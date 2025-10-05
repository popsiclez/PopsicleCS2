@echo off
setlocal

:: -----------------------------
:: Setup version and version check
:: -----------------------------
set "SETUP_VERSION=1"
set "VERSION_URL=https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/setupversion.txt"
set "VERSION_FILE=%TEMP%\setupversion.txt"

echo Checking setup version...
powershell -Command "try { Invoke-WebRequest -Uri '%VERSION_URL%' -OutFile '%VERSION_FILE%' -UseBasicParsing -TimeoutSec 10 } catch { exit 1 }"

if exist "%VERSION_FILE%" (
    set /p REMOTE_VERSION=<"%VERSION_FILE%"
    del "%VERSION_FILE%"
    
    if not "!REMOTE_VERSION!"=="%SETUP_VERSION%" (
        echo.
        echo ===============================================
        echo   SETUP OUTDATED
        echo ===============================================
        echo Current version: %SETUP_VERSION%
        echo Latest version:  !REMOTE_VERSION!
        echo.
        echo This setup file is outdated. Please download
        echo the latest version to ensure compatibility.
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo Setup version is up to date.
) else (
    echo Warning: Could not check setup version. Continuing anyway...
)

echo.

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
        echo Do you want to install/update Python packages? Y/N
        choice /c YN /n /m "Press Y for Yes or N for No: "
        
        if errorlevel 2 (
            echo Skipping Python package installation...
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
