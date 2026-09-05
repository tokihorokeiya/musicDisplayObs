import os
import sys
import re
import json
import time
import shutil
import tempfile
import threading
import subprocess
import urllib.request
import urllib.error

APP_VERSION = "v1.0.3"
GITHUB_REPO = "tokihorokeiya/musicDisplayObs"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def parse_version_tuple(v_str):
    """Parses a version string like 'v1.0.3' or '1.2.0' into a comparable tuple of integers (1, 0, 3)."""
    if not v_str:
        return (0, 0, 0)
    clean = re.sub(r'^[^\d]*', '', str(v_str).strip())
    parts = []
    for p in clean.split('.'):
        digits = re.match(r'^\d+', p)
        if digits:
            parts.append(int(digits.group(0)))
        else:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)

def is_newer_version(latest_tag, current_tag=APP_VERSION):
    """Returns True if latest_tag is strictly newer than current_tag."""
    return parse_version_tuple(latest_tag) > parse_version_tuple(current_tag)

def check_github_update():
    """
    Checks GitHub Releases API for the latest release.
    Returns:
        dict: {
            "has_update": bool,
            "current_version": str,
            "latest_version": str,
            "release_name": str,
            "release_notes": str,
            "html_url": str,
            "download_url": str or None,
            "asset_name": str or None,
            "asset_size": int or 0
        }
    Raises:
        Exception on network or parsing failure.
    """
    req = urllib.request.Request(
        GITHUB_API_LATEST,
        headers={
            "User-Agent": f"OBSMusicDisplay-Updater/{APP_VERSION}",
            "Accept": "application/vnd.github+json"
        }
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    latest_tag = data.get("tag_name", "").strip()
    release_name = data.get("name", "") or latest_tag
    body = data.get("body", "")
    html_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases/tag/{latest_tag}")
    
    # Locate Windows ZIP asset
    download_url = None
    asset_name = None
    asset_size = 0

    assets = data.get("assets", [])
    for a in assets:
        name = a.get("name", "")
        if name.endswith(".zip") and ("windows" in name.lower() or "obsmusicdisplay" in name.lower()):
            download_url = a.get("browser_download_url")
            asset_name = name
            asset_size = a.get("size", 0)
            break

    # Fallback to any zip if specific windows zip not matched
    if not download_url and assets:
        for a in assets:
            if a.get("name", "").endswith(".zip"):
                download_url = a.get("browser_download_url")
                asset_name = a.get("name")
                asset_size = a.get("size", 0)
                break

    has_update = is_newer_version(latest_tag, APP_VERSION)

    return {
        "has_update": has_update,
        "current_version": APP_VERSION,
        "latest_version": latest_tag,
        "release_name": release_name,
        "release_notes": body,
        "html_url": html_url,
        "download_url": download_url,
        "asset_name": asset_name,
        "asset_size": asset_size
    }

def is_frozen():
    """True if running as a compiled standalone executable (PyInstaller)."""
    return getattr(sys, "frozen", False)

def is_git_repo(base_dir):
    """True if base_dir is a git repository with .git directory."""
    return os.path.isdir(os.path.join(base_dir, ".git"))

def download_file_with_progress(url, dest_path, progress_callback=None, cancel_event=None):
    """
    Downloads file from URL to dest_path with progress callback.
    progress_callback(percent: float, downloaded_bytes: int, total_bytes: int)
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"OBSMusicDisplay-Updater/{APP_VERSION}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        total_size = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 64 * 1024  # 64KB

        with open(dest_path, "wb") as out_f:
            while True:
                if cancel_event and cancel_event.is_set():
                    raise InterruptedError("Download cancelled by user")
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out_f.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    pct = (downloaded / total_size * 100) if total_size > 0 else 0
                    progress_callback(pct, downloaded, total_size)

def apply_frozen_update(zip_path, target_app_dir, quit_app_callback=None):
    """
    Creates a detached batch script in %TEMP% that:
    1. Waits for current OBSMusicDisplay process to exit.
    2. Extracts the downloaded zip into a temp folder.
    3. Overwrites files in target_app_dir, preserving config.json.
    4. Relaunches target_app_dir\\OBSMusicDisplay.exe.
    5. Cleans up temp updater files and exits.
    """
    current_pid = os.getpid()
    temp_dir = tempfile.gettempdir()
    unique_id = str(int(time.time()))
    updater_bat_path = os.path.join(temp_dir, f"obs_music_update_{unique_id}.bat")
    temp_extract_dir = os.path.join(temp_dir, f"obs_music_extract_{unique_id}")

    bat_content = f"""@echo off
setlocal enabledelayedexpansion
title OBS Music Display Updater

echo ============================================================
echo   Updating OBS Music Display to Latest Version...
echo ============================================================
echo.

echo [1/4] Waiting for application to exit...
set PID={current_pid}
taskkill /PID !PID! /F >nul 2>&1
timeout /t 2 /nobreak >nul

for /L %%i in (1,1,5) do (
    tasklist /FI "PID eq !PID!" 2>nul | findstr /i "!PID!" >nul
    if not errorlevel 1 (
        taskkill /PID !PID! /F >nul 2>&1
        timeout /t 1 /nobreak >nul
    )
)

echo [2/4] Extracting update archive...
if exist "{temp_extract_dir}" rd /s /q "{temp_extract_dir}"
mkdir "{temp_extract_dir}"

powershell -NoProfile -Command "Expand-Archive -LiteralPath '{zip_path}' -DestinationPath '{temp_extract_dir}' -Force"
if not exist "{temp_extract_dir}" (
    echo [ERROR] Failed to extract archive!
    pause
    exit /b 1
)

echo [3/4] Overwriting application files (preserving config.json)...
robocopy "{temp_extract_dir}" "{target_app_dir}" /E /IS /IT /XF "config.json" >nul

rd /s /q "{temp_extract_dir}" >nul 2>&1
del /f /q "{zip_path}" >nul 2>&1

echo [4/4] Starting updated OBS Music Display...
start "" "{target_app_dir}\\OBSMusicDisplay.exe"

echo.
echo Update completed successfully!
(goto) 2>nul & del "%~f0"
exit
"""

    with open(updater_bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)

    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    subprocess.Popen(
        ["cmd.exe", "/c", updater_bat_path],
        creationflags=creation_flags,
        close_fds=True
    )

    if quit_app_callback:
        quit_app_callback()
    else:
        sys.exit(0)

def apply_git_update(base_dir):
    """
    Runs git pull origin main in base_dir.
    Returns (success: bool, message: str)
    """
    try:
        res = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        if res.returncode == 0:
            return True, res.stdout.strip()
        else:
            return False, res.stderr.strip() or res.stdout.strip()
    except Exception as e:
        return False, str(e)
