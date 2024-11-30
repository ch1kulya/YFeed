@echo off
REM Check if Python is installed
echo Checking if Python is installed...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed.
    echo Please download and install Python 3.12.7 from the following link:
    echo https://www.python.org/downloads/release/python-3127/
    pause
    exit /b
) ELSE (
    echo Python is installed.
)

REM Check if pip is available
echo Checking if pip is available...
python -m pip --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Pip is not installed. Installing pip...
    python -m ensurepip --upgrade
    python -m pip install --upgrade pip
) ELSE (
    echo pip is available.
)

REM Check for FFmpeg
echo Checking for FFmpeg installation...
ffmpeg -version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo FFmpeg is not installed.
    echo Please download and install FFmpeg from the following link:
    echo https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z
    pause
    exit /b
) ELSE (
    echo ffmpeg is installed.
)

REM Check for mpv player
echo Checking for mpv installation and version...
mpv --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo mpv is not installed.
    echo Please download and install mpv from the following link:
    echo https://sourceforge.net/projects/mpv-player-windows/files/release/mpv-0.39.0-x86_64.7z
    pause
    exit /b
) ELSE (
    echo mpv is installed.
)

REM Check for required dependencies
echo Checking and installing required dependencies...
python -m pip install -r requirements.txt >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies. Please check your requirements.txt file.
    pause
    exit /b
) ELSE (
    echo dependencies are installed.
)

REM Run the main.py script
echo Running main.py...
python src/main.py
pause
