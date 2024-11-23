@echo off
setlocal enabledelayedexpansion

:: Set title
title YFeed Installer

:: Check if running with administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
) else (
    echo Please run this script as administrator
    echo Right click on the script and select "Run as administrator"
    pause
    exit
)

:: Create temporary directory
set "TEMP_DIR=%TEMP%\yfeed_install"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

:: Check if Python is installed
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo Python is already installed
    goto :INSTALL_DEPENDENCIES
)

:INSTALL_PYTHON
echo Installing Python...
:: Download Python installer
curl -L "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe" -o "%TEMP_DIR%\python_installer.exe"

:: Install Python
echo Installing Python...
"%TEMP_DIR%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: Verify Python installation
echo Verifying Python installation...
python --version >nul 2>&1
if %errorLevel% == 1 (
    echo Failed to install Python
    goto :ERROR
)

:INSTALL_DEPENDENCIES
:: Create application directory
set "INSTALL_DIR=%USERPROFILE%\YFeed"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\data" mkdir "%INSTALL_DIR%\data"

:: Download main.py
echo Downloading YFeed...
curl -L "https://raw.githubusercontent.com/ch1kulya/YFeed/refs/heads/main/src/main.py" -o "%INSTALL_DIR%\main.py"

:: Install required packages
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install feedparser pyfiglet colorama google-api-python-client

:: Create launcher script
echo @echo off > "%INSTALL_DIR%\YFeed.bat"
echo cd /d "%INSTALL_DIR%" >> "%INSTALL_DIR%\YFeed.bat"
echo python main.py >> "%INSTALL_DIR%\YFeed.bat"
echo pause >> "%INSTALL_DIR%\YFeed.bat"

:: Create desktop shortcut
echo Creating desktop shortcut...
set "SHORTCUT=%USERPROFILE%\Desktop\YFeed.lnk"
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%SHORTCUT%'); $SC.TargetPath = '%INSTALL_DIR%\YFeed.bat'; $SC.WorkingDirectory = '%INSTALL_DIR%'; $SC.IconLocation = '%SystemRoot%\System32\SHELL32.dll,41'; $SC.Save()"

:: Cleanup
echo Cleaning up...
if exist "%TEMP_DIR%" rd /s /q "%TEMP_DIR%"

echo Installation completed successfully!
echo You can now run YFeed from your desktop shortcut
echo or from %INSTALL_DIR%\YFeed.bat
pause
exit /b 0

:ERROR
echo An error occurred during installation
pause
exit /b 1
