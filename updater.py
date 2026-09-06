import os
import sys
import re
import json
import time
import shutil
import zipfile
import tempfile
import threading
import subprocess
import urllib.request
import urllib.error

from functools import lru_cache

APP_VERSION = "v1.1.2"
GITHUB_REPO = "tokihorokeiya/musicDisplayObs"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

RE_VERSION_CLEAN = re.compile(r'^[^\d]*')
RE_DIGITS = re.compile(r'^\d+')

@lru_cache(maxsize=32)
def parse_version_tuple(v_str):
    """Parses a version string like 'v1.0.3' or '1.2.0' into a comparable tuple of integers (1, 0, 3)."""
    if not v_str:
        return (0, 0, 0)
    clean = RE_VERSION_CLEAN.sub('', str(v_str).strip())
    parts = []
    for p in clean.split('.'):
        digits = RE_DIGITS.match(p)
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
    Returns a unified dict with 'success' flag and normalized key aliases.
    """
    try:
        req = urllib.request.Request(
            GITHUB_API_LATEST,
            headers={
                "User-Agent": f"OBSMusicDisplay-Updater/{APP_VERSION}",
                "Accept": "application/vnd.github+json"
            }
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        latest_tag = data.get("tag_name", "").strip()
        release_name = data.get("name", "") or latest_tag
        body = data.get("body", "")
        html_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases/tag/{latest_tag}")
        published_at = data.get("published_at", "")

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
            "success": True,
            "has_update": has_update,
            "current_version": APP_VERSION,
            "latest_version": latest_tag,
            "release_name": release_name,
            "release_notes": body,
            "html_url": html_url,
            "release_url": html_url,       # Compatibility alias
            "download_url": download_url,
            "asset_url": download_url,     # Compatibility alias
            "asset_name": asset_name,
            "asset_size": asset_size,
            "published_at": published_at,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "has_update": False,
            "current_version": APP_VERSION,
            "latest_version": APP_VERSION,
            "release_name": "",
            "release_notes": "",
            "html_url": f"https://github.com/{GITHUB_REPO}/releases",
            "release_url": f"https://github.com/{GITHUB_REPO}/releases",
            "download_url": None,
            "asset_url": None,
            "asset_name": None,
            "asset_size": 0,
            "published_at": "",
            "error": str(e)
        }

def is_frozen():
    """True if running as a compiled standalone executable (PyInstaller)."""
    return getattr(sys, "frozen", False)

def is_git_repo(base_dir=None):
    """True if base_dir is a git repository with .git directory."""
    if not base_dir:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.isdir(os.path.join(base_dir, ".git"))

def download_file_with_progress(url, dest_path, progress_callback=None, cancel_event=None, log_callback=None):
    """
    Downloads file from URL to dest_path with progress callback.
    progress_callback(percent: float, downloaded_bytes: int, total_bytes: int, speed_str: str)
    log_callback(message: str)
    """
    if log_callback:
        log_callback(f"正在連線伺服器: {url}")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"OBSMusicDisplay-Updater/{APP_VERSION}"}
    )
    start_time = time.time()
    last_log_time = start_time
    with urllib.request.urlopen(req, timeout=30) as resp:
        total_size = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 128 * 1024  # 128KB buffer

        if log_callback:
            size_mb = total_size / (1024 * 1024) if total_size > 0 else 0
            log_callback(f"伺服器連線成功 (HTTP 200)，預計下載檔案大小: {size_mb:.2f} MB")

        with open(dest_path, "wb") as out_f:
            while True:
                if cancel_event and cancel_event.is_set():
                    raise InterruptedError("使用者取消下載作業")
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out_f.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                elapsed = max(now - start_time, 0.001)
                speed_bps = downloaded / elapsed
                speed_str = f"{speed_bps / (1024 * 1024):.1f} MB/s" if speed_bps > 1024 * 1024 else f"{speed_bps / 1024:.0f} KB/s"

                pct = (downloaded / total_size * 100) if total_size > 0 else 0
                if progress_callback:
                    try:
                        progress_callback(pct, downloaded, total_size, speed_str)
                    except TypeError:
                        progress_callback(pct, downloaded, total_size)

                # Output a debug log line every 2.5 seconds or on finish
                if log_callback and (now - last_log_time >= 2.5 or downloaded == total_size):
                    cur_mb = downloaded / (1024 * 1024)
                    tot_mb = total_size / (1024 * 1024)
                    log_callback(f"下載進度: {cur_mb:.1f} MB / {tot_mb:.1f} MB ({pct:.1f}%) - 即時速度: {speed_str}")
                    last_log_time = now

def extract_and_validate_zip(zip_path, extract_dir, log_callback=None):
    """
    Validates zip integrity using zipfile.testzip(), then unpacks into extract_dir.
    Returns the root folder containing OBSMusicDisplay.exe.
    """
    if log_callback:
        log_callback(f"正在驗證壓縮檔完整性: {os.path.basename(zip_path)}...")

    with zipfile.ZipFile(zip_path, "r") as zf:
        bad_file = zf.testzip()
        if bad_file:
            raise RuntimeError(f"ZIP 壓縮檔損壞或 CRC 校驗失敗: {bad_file}")

        namelist = zf.namelist()
        total_files = len(namelist)
        if log_callback:
            log_callback(f"壓縮檔校驗通過！共 {total_files} 個檔案，正在解壓縮...")

        for idx, member in enumerate(namelist, 1):
            zf.extract(member, extract_dir)
            if log_callback and (idx % 150 == 0 or idx == total_files):
                pct = idx / total_files * 100
                log_callback(f"解壓縮進度: {idx}/{total_files} ({pct:.0f}%)")

    # Locate the folder containing OBSMusicDisplay.exe
    for root, dirs, files in os.walk(extract_dir):
        if "OBSMusicDisplay.exe" in files:
            if log_callback:
                log_callback(f"已確認主程式目錄: {root}")
            return root
    return extract_dir

def apply_frozen_update(source_dir, target_app_dir=None, zip_path=None, quit_app_callback=None, log_callback=None):
    """
    Spawns a detached Windows batch script to overwrite files in target_app_dir (preserving config.json)
    and relaunch the application.
    """
    if not target_app_dir:
        if getattr(sys, "frozen", False):
            target_app_dir = os.path.dirname(sys.executable)
        else:
            target_app_dir = os.path.dirname(os.path.abspath(__file__))

    current_pid = os.getpid()
    temp_dir = tempfile.gettempdir()
    unique_id = str(int(time.time()))
    updater_bat_path = os.path.join(temp_dir, f"obs_music_update_{unique_id}.bat")

    if log_callback:
        log_callback(f"正在生成安裝腳本: {updater_bat_path}")
        log_callback(f"來源目錄: {source_dir}")
        log_callback(f"目標目錄: {target_app_dir}")

    zip_cleanup = f'del /f /q "{zip_path}" >nul 2>&1' if zip_path else ""
    extract_parent = os.path.dirname(source_dir)
    extract_root = extract_parent if ("obs_extract" in extract_parent or "obs_music" in extract_parent) else source_dir

    bat_content = f"""@echo off
setlocal enabledelayedexpansion
title OBS Music Display Updater

echo ============================================================
echo   Updating OBS Music Display to Latest Version...
echo ============================================================
echo.

echo [1/3] Waiting for current process (PID {current_pid}) to exit...
timeout /t 1 /nobreak >nul
for /L %%i in (1,1,10) do (
    tasklist /FI "PID eq {current_pid}" 2>nul | findstr /i "{current_pid}" >nul
    if not errorlevel 1 (
        taskkill /PID {current_pid} /F >nul 2>&1
        timeout /t 1 /nobreak >nul
    )
)
timeout /t 1 /nobreak >nul

echo [2/3] Overwriting application files (preserving config.json)...
robocopy "{source_dir}" "{target_app_dir}" /E /IS /IT /XF "config.json" >nul

echo [3/3] Restarting OBS Music Display...
start "" "{target_app_dir}\\OBSMusicDisplay.exe"

echo Cleaning up updater files...
{zip_cleanup}
rd /s /q "{extract_root}" >nul 2>&1

echo Update completed successfully!
(goto) 2>nul & del "%~f0"
exit
"""

    with open(updater_bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)

    if log_callback:
        log_callback("啟動自動更新腳本並關閉當前程序...")

    try:
        os.startfile(updater_bat_path)
    except Exception as e:
        if log_callback:
            log_callback(f"os.startfile 失敗 ({e})，改用 cmd 啟動...")
        subprocess.Popen(
            ["cmd.exe", "/c", updater_bat_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
            close_fds=True
        )

    # Allow batch script a brief instant to spawn, then force exit to release all file locks
    time.sleep(0.5)
    if quit_app_callback:
        try:
            quit_app_callback()
        except Exception:
            pass
    os._exit(0)

def apply_git_update(base_dir=None, log_callback=None):
    """
    Runs git pull origin main in base_dir.
    Returns (success: bool, message: str)
    """
    if not base_dir:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        if log_callback:
            log_callback("正在執行: git pull origin main...")
        res = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=40
        )
        if log_callback:
            for line in res.stdout.splitlines():
                if line.strip():
                    log_callback(f"[Git] {line}")
        if res.returncode == 0:
            return True, res.stdout.strip()
        else:
            err = res.stderr.strip() or res.stdout.strip()
            if log_callback:
                log_callback(f"[Git Error] {err}")
            return False, err
    except Exception as e:
        if log_callback:
            log_callback(f"[Git Exception] {e}")
        return False, str(e)
