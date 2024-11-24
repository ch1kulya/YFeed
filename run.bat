@echo off
REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed.
    echo Please download and install Python 3.12.7 from the following link:
    echo https://www.python.org/downloads/release/python-3127/
    pause
    exit /b
)

REM Check if pip is available
python -m pip --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Pip is not installed. Installing pip...
    python -m ensurepip --upgrade
    python -m pip install --upgrade pip
)

REM Check for required dependencies
echo Checking and installing required dependencies...
python -m pip install -r requirements.txt >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies. Please check your requirements.txt file.
    pause
    exit /b
)

REM Run the main.py script
echo Running main.py...
python src/main.py
pause
