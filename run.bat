@echo off
set "LOCKFILE=dependencies.lock"
set "REQUIREMENTS=requirements.txt"

REM Check if Python is installed
echo Checking if Python is installed...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed.
    echo Please download and install Python 3.12.7 from the following link:
    echo https://www.python.org/downloads/release/python-3127/
    pause
    exit /b
)
echo Python is installed.

REM Check if pip is available
echo Checking if pip is available...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Pip is not installed. Installing pip...
    python -m ensurepip --upgrade >nul 2>&1
    python -m pip install --upgrade pip >nul 2>&1
    if errorlevel 1 (
        echo Failed to install pip.
        pause
        exit /b
    )
)
echo Pip is available.

REM Check for required Python dependencies
if not exist "%LOCKFILE%" (
    echo Lock file not found. Installing dependencies...
    python -m pip install -r "%REQUIREMENTS%"
    if errorlevel 1 (
        echo Failed to install Python dependencies.
        pause
        exit /b
    )
    echo Dependencies installed. Creating lock file...
    copy /Y "%REQUIREMENTS%" "%LOCKFILE%" >nul
) else (
    REM Compare the current requirements with the lock file
    fc /b "%REQUIREMENTS%" "%LOCKFILE%" >nul
    if errorlevel 1 (
        echo Requirements have changed. Installing updated dependencies...
        python -m pip install -r "%REQUIREMENTS%"
        if errorlevel 1 (
            echo Failed to install updated Python dependencies.
            pause
            exit /b
        )
        echo Dependencies updated. Updating lock file...
        copy /Y "%REQUIREMENTS%" "%LOCKFILE%" >nul
    ) else (
        echo All Python dependencies are already up to date.
    )
)

REM Run the main.py script
echo Running main.py...
python src/main.py
pause
