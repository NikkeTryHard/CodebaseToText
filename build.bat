@echo off
title CodebaseToText Build Script
cls

REM =================================================
REM                MAIN SCRIPT LOGIC
REM =================================================

call :print_header "CodebaseToText Build Script"
echo This script will build the application using PyInstaller.
echo.

REM --- Step 1: Cleaning ---
set "choice="
set /p choice="Do you want to CLEAN previous build artifacts (dist, build, .spec)? (y/n): "
if /i "%choice%"=="y" (
    call :clean_artifacts
) else (
    echo.
    echo Skipping the cleaning step.
)

REM --- Step 2: Confirmation to Build ---
echo.
echo Press any key to start the build process...
pause >nul
echo.

REM --- Step 3: Check for PyInstaller ---
call :print_header "Checking for PyInstaller..."
where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller command not found.
    echo.
    echo Please ensure PyInstaller is installed (pip install pyinstaller^)
    echo and that your Python scripts directory is in your system's PATH.
    goto :end_script
)
echo PyInstaller found.

REM --- Step 4: Run the Build ---
call :print_header "Starting PyInstaller build..."
echo The full output from PyInstaller will be displayed below.
echo.

REM This command rebuilds the application from scratch.
REM Using --noupx to explicitly disable UPX and avoid the ambiguous option bug.
REM ADDED assets folder to --add-data
pyinstaller main.py ^
    --name "CodebaseToText" ^
    --windowed ^
    --add-data "theme;theme" ^
    --add-data "assets;assets" ^
    --add-data "azure.tcl;." ^
    --noupx ^
    --noconfirm

REM Check if the build command was successful
if %errorlevel% neq 0 (
    call :print_header "Build FAILED!"
    echo There was an error during the PyInstaller build process.
    echo Please review the output above for details.
    goto :end_script
)

REM --- Step 5: Success Message ---
call :print_header "Build Successful!"
echo The executable can be found in the 'dist\CodebaseToText' directory.

:end_script
echo.
echo Press any key to exit...
pause >nul
goto :eof

REM =================================================
REM                   SUBROUTINES
REM (The script should not fall through to here)
REM =================================================

:clean_artifacts
    call :print_header "Cleaning previous build artifacts..."
    
    if exist "dist" (
        echo -^> Deleting 'dist' directory...
        rmdir /s /q "dist"
    )
    
    if exist "build" (
        echo -^> Deleting 'build' directory...
        rmdir /s /q "build"
    )
    
    if exist "CodebaseToText.spec" (
        echo -^> Deleting 'CodebaseToText.spec' file...
        del /q "CodebaseToText.spec"
    )
    
    echo.
    echo Cleaning complete.
    goto :eof

:print_header
    echo.
    echo =================================================
    echo %~1
    echo =================================================
    echo.
    goto :eof