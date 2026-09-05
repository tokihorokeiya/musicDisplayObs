@echo off
title Build Real-Time Music Display Executable
echo ===================================================
echo Building Real-Time Music Display Executable (.exe)
echo ===================================================
echo.

pyinstaller --noconfirm --onedir --windowed ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "songIcon.jpg;." ^
    --add-data "config.json;." ^
    --collect-all "customtkinter" ^
    --collect-all "winsdk" ^
    --name "OBSMusicDisplay" ^
    main.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo ===================================================
    echo Build Successful!
    echo Output directory: dist\OBSMusicDisplay\OBSMusicDisplay.exe
    echo ===================================================
) else (
    echo Build failed with error code %ERRORLEVEL%.
)
