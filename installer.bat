@echo off
setlocal EnableDelayedExpansion

set "PYTHON_DIR=demo"
set "PYTHON_URL=https://www.python.org/ftp/python/3.12.1/python-3.12.1-embed-amd64.zip"
set "MAIN_FILE_URL=https://raw.githubusercontent.com/ch1kulya/YFeed/main/src/main.py"

if not exist "%PYTHON_DIR%" (
    echo Creating directory %PYTHON_DIR%...
    mkdir "%PYTHON_DIR%"
)

cd "%PYTHON_DIR%"

echo Downloading portable Python...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile 'python_embed.zip'"
if errorlevel 1 (
    echo Error downloading Python!
    cd ..
    exit /b 1
)

echo Extracting Python...
powershell -Command "Expand-Archive -Path 'python_embed.zip' -DestinationPath '.' -Force"
if errorlevel 1 (
    echo Error extracting Python!
    cd ..
    exit /b 1
)
del "python_embed.zip"

mkdir "Lib"
mkdir "Lib\site-packages"

for /f "delims=" %%i in ('dir /b python*._pth') do (
    echo Modifying %%i
    (
        echo python312.zip
        echo .
        echo Lib\site-packages
        echo .
        echo import site
    ) > "%%i"
)

echo Downloading setuptools and pip...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
if errorlevel 1 (
    echo Error downloading get-pip.py!
    cd ..
    exit /b 1
)

echo Installing pip...
python.exe get-pip.py --no-warn-script-location
if errorlevel 1 (
    echo Error installing pip!
    cd ..
    exit /b 1
)
del "get-pip.py"

echo Installing dependencies...
python.exe -m pip install --no-warn-script-location feedparser colorama google-api-python-client pyfiglet wcwidth
if errorlevel 1 (
    echo Error installing dependencies!
    cd ..
    exit /b 1
)

echo Downloading main.py...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%MAIN_FILE_URL%' -OutFile 'main.py'"
if errorlevel 1 (
    echo Error downloading main.py!
    cd ..
    exit /b 1
)

echo Creating launch script...
(
    echo @echo off
    echo MODE CON: COLS=120 LINES=30
    echo cd /d "%%~dp0"
    echo python.exe main.py
    echo pause
) > "start.bat"

echo Installation complete! Please run start.bat to launch the program.
cd ..
pause
exit /b 0
