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
    echo FFmpeg is not found.
    echo Please run setup.bat to install binaries.
    pause
    exit /b
) ELSE (
    echo FFmpeg is installed.
)

REM Check for mpv player
echo Checking for mpv installation...
mpv --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo mpv is not found.
    echo Please run setup.bat to install binaries.
    pause
    exit /b
) ELSE (
    echo mpv is installed.
)

REM Check for required Python dependencies
echo Checking and installing required Python dependencies...
python -m pip install -r requirements.txt >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install python dependencies.
    pause
    exit /b
) ELSE (
    echo All python dependencies are installed.
)

REM Run the main.py script
echo Running main.py...
python src/main.py
pause
