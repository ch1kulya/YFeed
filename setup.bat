@echo off
REM Request administrator privileges
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo This script requires administrator privileges to install dependencies.
    echo Please approve the elevation prompt.
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM Set the binaries directory as the installation path
set INSTALL_PATH=%~dp0binaries

REM Create the binaries directory if it doesn't exist
if not exist "%INSTALL_PATH%" (
    mkdir "%INSTALL_PATH%"
)

REM Initialize NEW_PATH with the current PATH
set "NEW_PATH=%PATH%"

REM Check for FFmpeg
echo Checking for FFmpeg installation...
ffmpeg -version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo FFmpeg is not installed.
    echo Downloading and installing FFmpeg...
    powershell -Command "Invoke-WebRequest -Uri https://github.com/ch1kulya/YFeed/releases/download/binaries/ffmpeg-2024-11-28.zip -OutFile %INSTALL_PATH%\ffmpeg.zip"
    powershell -Command "Expand-Archive -Force -Path %INSTALL_PATH%\ffmpeg.zip -DestinationPath %INSTALL_PATH%\ffmpeg"
    set "NEW_PATH=%NEW_PATH%;%INSTALL_PATH%\ffmpeg\bin"
    del /q "%INSTALL_PATH%\ffmpeg.zip"
    echo FFmpeg has been installed and added to PATH.
) ELSE (
    echo FFmpeg is already installed.
)

REM Check for mpv player
echo Checking for mpv installation...
mpv --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo mpv is not installed.
    echo Downloading and installing mpv...
    powershell -Command "Invoke-WebRequest -Uri https://github.com/ch1kulya/YFeed/releases/download/binaries/mpv-0.39.0-x86_64.zip -OutFile %INSTALL_PATH%\mpv.zip"
    powershell -Command "Expand-Archive -Force -Path %INSTALL_PATH%\mpv.zip -DestinationPath %INSTALL_PATH%\mpv"
    set "NEW_PATH=%NEW_PATH%;%INSTALL_PATH%\mpv"
    del /q "%INSTALL_PATH%\mpv.zip"
    echo mpv has been installed and added to PATH.
) ELSE (
    echo mpv is already installed.
)

REM Update the system PATH variable once
setx PATH "%NEW_PATH%"

echo All dependencies have been installed successfully.
pause
exit /b
