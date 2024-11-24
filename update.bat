@echo off
setlocal enabledelayedexpansion

REM Configuration
set REPO_URL=https://github.com/ch1kulya/YFeed.git
set TEMP_DIR=%~dp0temp_repo
set LOCAL_DIR=%~dp0
set EXCLUDE_DIR=data

REM Check if git is installed
git --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Git is not installed. Please install Git and try again.
    pause
    exit /b
)

REM Delete temp_repo folder if it exists
IF EXIST "%TEMP_DIR%" (
    echo Removing old temporary folder...
    rmdir /s /q "%TEMP_DIR%"
)

REM Clone repository to temp_repo
echo Cloning repository...
git clone %REPO_URL% "%TEMP_DIR%"
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to clone the repository. Please check the URL or your internet connection.
    pause
    exit /b
)

REM Copy files except for the EXCLUDE_DIR
echo Updating application...
FOR /D %%D IN ("%TEMP_DIR%\*") DO (
    set FOLDER_NAME=%%~nxD
    IF /I "!FOLDER_NAME!" NEQ "%EXCLUDE_DIR%" (
        IF EXIST "%LOCAL_DIR%!FOLDER_NAME!" (
            echo Deleting existing folder: !FOLDER_NAME!
            rmdir /s /q "%LOCAL_DIR%!FOLDER_NAME!"
        )
        echo Copying folder: !FOLDER_NAME!
        xcopy /e /i /q "%%D" "%LOCAL_DIR%!FOLDER_NAME!" >nul
    )
)

FOR %%F IN ("%TEMP_DIR%\*") DO (
    set FILE_NAME=%%~nxF
    IF /I "!FILE_NAME!" NEQ "%EXCLUDE_DIR%" (
        IF EXIST "%LOCAL_DIR%!FILE_NAME!" (
            echo Deleting existing file: !FILE_NAME!
            del /q "%LOCAL_DIR%!FILE_NAME!"
        )
        echo Copying file: !FILE_NAME!
        copy /y "%%F" "%LOCAL_DIR%!FILE_NAME!" >nul
    )
)

REM Clean up temp_repo
echo Cleaning up temporary files...
rmdir /s /q "%TEMP_DIR%"

echo Application updated successfully.
pause
