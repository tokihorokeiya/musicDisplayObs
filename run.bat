@echo off
title Real-Time Music Display for OBS Studio
echo Starting Real-Time Music Display for OBS...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred. Please make sure python and required dependencies are installed.
    pause
)
