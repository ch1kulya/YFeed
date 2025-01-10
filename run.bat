@echo off
set "LOCKFILE=dependencies.lock"
set "REQUIREMENTS=requirements.txt"

echo Checking if Python is installed...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python.
    pause
    exit /b
)

python -m venv --help >nul 2>&1
if errorlevel 1 (
    echo venv module is not available.
    pause
    exit /b
)

if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Installing pip...
    python -m ensurepip >nul 2>&1
    python -m pip install --upgrade pip --disable-pip-version-check >nul 2>&1
)

if not exist "%LOCKFILE%" (
    echo Lock file not found. Installing dependencies...
    python -m pip install --disable-pip-version-check -r "%REQUIREMENTS%"
    if errorlevel 1 (
        echo Failed to install dependencies.
        pause
        exit /b
    )
    copy /Y "%REQUIREMENTS%" "%LOCKFILE%" >nul
) else (
    fc /b "%REQUIREMENTS%" "%LOCKFILE%" >nul
    if errorlevel 1 (
        echo Requirements have changed. Updating dependencies...
        python -m pip install --disable-pip-version-check -r "%REQUIREMENTS%"
        if errorlevel 1 (
            echo Failed to update dependencies.
            pause
            exit /b
        )
        copy /Y "%REQUIREMENTS%" "%LOCKFILE%" >nul
    ) else (
        echo Python dependencies are up to date.
    )
)

python src\main.py
pause
exit /b
