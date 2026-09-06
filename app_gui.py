import io
import base64
import os
import sys
import subprocess
import webbrowser
import threading
import tempfile
import time
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item

# Native Windows OLE drag-and-drop into OBS Studio
from ole_drag import setup_native_drag_and_drop
from i18n import get_text, get_theme_info, TRANSLATIONS
from config import save_config
from updater import (
    APP_VERSION,
    check_github_update,
    download_file_with_progress,
    extract_and_validate_zip,
    apply_frozen_update,
    apply_git_update,
    is_frozen,
    is_git_repo
)

THEME_IDS = [
    "glassmorphism",
    "cyberpunk",
    "vinyl",
    "minimal_pill",
    "cassette",
    "broadcast",
    "cute_kawaii",
    "spotify",
    "lofi_cozy",
    "dynamic_island",
    "minimalism",
    "swiss",
    "editorial",
    "hand_drawn",
    "retro",
    "pixel",
    "flat",
    "eight_bit",
    "bento"
]

# -------------------------------------------------------------
# Notion Design System Design Tokens (notion.design.md)
# -------------------------------------------------------------
NOTION_PURPLE = "#5645d4"          # Notion signature primary CTA
NOTION_PURPLE_HOVER = "#4534b3"    # Pressed state
NOTION_PURPLE_DEEP = "#3a2a99"     # Deep emphasis
NOTION_NAVY = "#0a1530"            # Hero band background
NOTION_NAVY_MID = "#141f3d"        # Hero border / accent
NOTION_CANVAS = "#191919"          # Notion dark workspace canvas
NOTION_SIDEBAR = "#141414"         # Notion sidebar background
NOTION_SIDEBAR_HOVER = "#222222"   # Sidebar hover
NOTION_SIDEBAR_ACTIVE = "#262626"  # Sidebar active item
NOTION_SURFACE = "#202020"         # Notion card surface
NOTION_SURFACE_HOVER = "#272727"   # Card hover
NOTION_HAIRLINE = "#2e2e2e"        # Hairline border (1px)
NOTION_HAIRLINE_STRONG = "#3e3e3e" # Strong border
NOTION_INK = "#ffffff"             # Pure white text
NOTION_CHARCOAL = "#e6e5e3"        # Body text
NOTION_STEEL = "#9b9994"           # Secondary muted text
NOTION_STONE = "#73726e"           # Muted micro text
NOTION_MUTED = "#55534e"           # Disabled text

# Notion Pastel Database Property Badges
TAG_MINT_BG = "#163820"
TAG_MINT_TEXT = "#4ade80"
TAG_MINT_BORDER = "#235832"

TAG_LAVENDER_BG = "#2d2146"
TAG_LAVENDER_TEXT = "#c084fc"
TAG_LAVENDER_BORDER = "#483470"

TAG_PEACH_BG = "#292524"
TAG_PEACH_TEXT = "#a8a29e"
TAG_PEACH_BORDER = "#3e3835"

TAG_PURPLE_BG = "#2b1d42"
TAG_PURPLE_TEXT = "#d6b6f6"
TAG_PURPLE_BORDER = "#452d6b"

TAG_YELLOW_BG = "#3d3314"
TAG_YELLOW_TEXT = "#fde047"
TAG_YELLOW_BORDER = "#63521b"

def get_ui_font_family(lang):
    try:
        import tkinter.font as tkfont
        available = set(tkfont.families())
    except Exception:
        available = set()

    if lang == "ja":
        for f in ["Yu Gothic UI", "Yu Gothic", "Meiryo UI", "Meiryo"]:
            if f in available:
                return f
        return "Yu Gothic UI"
    elif lang == "ko":
        for f in ["Malgun Gothic", "Noto Sans KR"]:
            if f in available:
                return f
        return "Malgun Gothic"
    elif lang == "zh_TW":
        for f in ["Microsoft JhengHei UI", "Microsoft JhengHei", "PingFang TC", "Noto Sans TC"]:
            if f in available:
                return f
        return "Microsoft JhengHei UI"
    elif lang == "th":
        for f in ["Leelawadee UI", "Leelawadee"]:
            if f in available:
                return f
        return "Leelawadee UI"

    for f in ["Segoe UI", "-apple-system", "Helvetica Neue"]:
        if f in available:
            return f
    return "Segoe UI"

RESOLUTION_MODES = [
    ("1920 × 700 (横幅模式)", "1920x700", "&w=1920&h=700&mode=1920x700"),
    ("1000 × 400 (精簡小組件)", "1000x400", "&w=1000&h=400"),
    ("1920 × 1080 (全螢幕底部)", "1920x1080", "&w=1920&h=1080&pos=bottom")
]

LANGUAGE_OPTIONS = [
    ("繁體中文 (Traditional Chinese)", "zh_TW"),
    ("English", "en"),
    ("日本語 (Japanese)", "ja"),
    ("한국어 (Korean)", "ko"),
    ("Español (Spanish)", "es"),
    ("Français (French)", "fr"),
    ("Deutsch (German)", "de"),
    ("Português (Portuguese)", "pt"),
    ("Italiano (Italian)", "it"),
    ("Русский (Russian)", "ru"),
    ("Bahasa Indonesia (Indonesian)", "id"),
    ("Tiếng Việt (Vietnamese)", "vi"),
    ("ไทย (Thai)", "th"),
    ("Polski (Polish)", "pl")
]

def format_time_str(seconds):
    if not seconds or seconds < 0:
        return "00:00"
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"

class UpdateDialog(ctk.CTkToplevel):
    """
    Notion-styled Software Update Window with real-time debug console,
    download progress tracking, and one-click self-update execution.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_gui = parent
        self.title(f"OBS Music Display - {self._t('update_window_title', '線上更新管理')}")
        self.geometry("620x570")
        self.minsize(580, 500)
        self.configure(fg_color=NOTION_SURFACE)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() - 620) // 2
            y = parent.winfo_y() + (parent.winfo_height() - 570) // 2
            self.geometry(f"+{max(x, 50)}+{max(y, 50)}")
        except Exception:
            pass

        self.info = None
        self.is_updating = False
        self._build_ui()
        self.after(300, self._start_check)

    def _t(self, key, default=""):
        return self.parent_gui._t(key, default)

    def log(self, message):
        """Thread-safe append of timestamped message to the debug log terminal."""
        def _append():
            if hasattr(self, "log_box") and self.log_box.winfo_exists():
                ts = time.strftime("%H:%M:%S")
                self.log_box.configure(state="normal")
                self.log_box.insert("end", f"[{ts}] {message}\n")
                self.log_box.see("end")
                self.log_box.configure(state="disabled")
        if threading.current_thread() is not threading.main_thread():
            self.after(0, _append)
        else:
            _append()

    def _build_ui(self):
        root_box = ctk.CTkFrame(self, fg_color="transparent")
        root_box.pack(fill="both", expand=True, padx=24, pady=20)

        # 1. Header with Notion icon box
        head_row = ctk.CTkFrame(root_box, fg_color="transparent")
        head_row.pack(fill="x", pady=(0, 14))

        icon_box = ctk.CTkFrame(
            head_row,
            width=36,
            height=36,
            corner_radius=8,
            fg_color="#222222",
            border_width=1,
            border_color=NOTION_HAIRLINE_STRONG
        )
        icon_box.pack(side="left", padx=(0, 12))
        icon_box.pack_propagate(False)

        ctk.CTkLabel(
            icon_box,
            text="UPD",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#a855f7"
        ).place(relx=0.5, rely=0.5, anchor="center")

        title_meta = ctk.CTkFrame(head_row, fg_color="transparent")
        title_meta.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            title_meta,
            text=self._t("update_dialog_title", "線上軟體版本更新"),
            font=self.parent_gui._font(14, "bold"),
            text_color=NOTION_INK
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_meta,
            text=self._t("update_dialog_sub", "GitHub Releases 即時檢查、解壓縮校驗與自動套用重啟"),
            font=self.parent_gui._font(11),
            text_color=NOTION_STEEL
        ).pack(anchor="w")

        # 2. Version & Release Status Card
        self.status_card = ctk.CTkFrame(
            root_box,
            corner_radius=10,
            fg_color="#181818",
            border_width=1,
            border_color=NOTION_HAIRLINE
        )
        self.status_card.pack(fill="x", pady=(0, 12))

        # Version line
        ver_line = ctk.CTkFrame(self.status_card, fg_color="transparent")
        ver_line.pack(fill="x", padx=16, pady=(12, 6))

        cur_v = APP_VERSION if APP_VERSION.startswith("v") else f"v{APP_VERSION}"
        cur_v_label = f"{self._t('update_cur_ver', '本地目前版本')}: {cur_v}"
        ctk.CTkLabel(
            ver_line,
            text=cur_v_label,
            font=self.parent_gui._font(12, "bold"),
            text_color=NOTION_CHARCOAL
        ).pack(side="left")

        self.latest_badge = ctk.CTkFrame(
            ver_line,
            corner_radius=6,
            fg_color=TAG_PEACH_BG,
            border_width=1,
            border_color=TAG_PEACH_BORDER
        )
        self.latest_badge.pack(side="right")

        self.latest_badge_label = ctk.CTkLabel(
            self.latest_badge,
            text=self._t("update_checking", "正在檢查中..."),
            font=self.parent_gui._font(10, "bold"),
            text_color=TAG_PEACH_TEXT
        )
        self.latest_badge_label.pack(padx=8, pady=2)

        # Release Title & Asset line
        self.release_meta_label = ctk.CTkLabel(
            self.status_card,
            text=self._t("update_connecting", "正在連線 GitHub Releases API..."),
            font=self.parent_gui._font(11),
            text_color=NOTION_STEEL,
            anchor="w"
        )
        self.release_meta_label.pack(fill="x", padx=16, pady=(0, 12))

        # 3. Progress Bar & Real-time Rate
        prog_row = ctk.CTkFrame(root_box, fg_color="transparent")
        prog_row.pack(fill="x", pady=(0, 10))

        self.progress_bar = ctk.CTkProgressBar(
            prog_row,
            height=8,
            corner_radius=4,
            progress_color=NOTION_PURPLE,
            fg_color="#2b2b2b"
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 4))

        self.progress_label = ctk.CTkLabel(
            prog_row,
            text=self._t("update_ready", "準備就緒"),
            font=self.parent_gui._font(11),
            text_color=NOTION_STEEL,
            anchor="w"
        )
        self.progress_label.pack(fill="x")

        # 4. Debug / Progress Terminal Console
        console_box = ctk.CTkFrame(root_box, fg_color="transparent")
        console_box.pack(fill="both", expand=True, pady=(0, 14))

        ctk.CTkLabel(
            console_box,
            text=self._t("update_debug_log_title", "即時進度與除錯紀錄 (Debug Log):"),
            font=self.parent_gui._font(11, "bold"),
            text_color=NOTION_CHARCOAL
        ).pack(anchor="w", pady=(0, 4))

        self.log_box = ctk.CTkTextbox(
            console_box,
            height=160,
            corner_radius=8,
            fg_color="#121212",
            border_width=1,
            border_color=NOTION_HAIRLINE_STRONG,
            text_color="#e2e8f0",
            font=self.parent_gui._font(11),
            wrap="word"
        )
        self.log_box.pack(fill="both", expand=True)
        self.log_box.configure(state="disabled")

        # 5. Bottom Action Buttons
        btn_bar = ctk.CTkFrame(root_box, fg_color="transparent")
        btn_bar.pack(fill="x")

        self.btn_primary = ctk.CTkButton(
            btn_bar,
            text=self._t("update_btn_apply", "立即直接更新"),
            height=34,
            corner_radius=8,
            font=self.parent_gui._font(11, "bold"),
            fg_color=NOTION_PURPLE,
            hover_color=NOTION_PURPLE_HOVER,
            state="disabled",
            command=self._on_start_update
        )
        self.btn_primary.pack(side="left", padx=(0, 8))

        self.btn_force = ctk.CTkButton(
            btn_bar,
            text=self._t("update_btn_force", "重新下載修復"),
            height=34,
            corner_radius=8,
            font=self.parent_gui._font(11),
            fg_color="#242424",
            hover_color="#303030",
            border_width=1,
            border_color=NOTION_HAIRLINE_STRONG,
            state="disabled",
            command=lambda: self._on_start_update(force=True)
        )
        self.btn_force.pack(side="left", padx=(0, 8))

        self.btn_github = ctk.CTkButton(
            btn_bar,
            text=self._t("update_btn_github", "在 GitHub 查看"),
            height=34,
            corner_radius=8,
            font=self.parent_gui._font(11),
            fg_color="#242424",
            hover_color="#303030",
            border_width=1,
            border_color=NOTION_HAIRLINE_STRONG,
            command=self._open_github
        )
        self.btn_github.pack(side="left", padx=(0, 8))

        self.btn_close = ctk.CTkButton(
            btn_bar,
            text=self._t("btn_close", "關閉"),
            width=70,
            height=34,
            corner_radius=8,
            font=self.parent_gui._font(11),
            fg_color="#242424",
            hover_color="#303030",
            border_width=1,
            border_color=NOTION_HAIRLINE_STRONG,
            command=self.destroy
        )
        self.btn_close.pack(side="right")

    def _open_github(self):
        url = "https://github.com/tokihorokeiya/musicDisplayObs/releases"
        if self.info and (self.info.get("html_url") or self.info.get("release_url")):
            url = self.info.get("html_url") or self.info.get("release_url")
        webbrowser.open(url)

    def _start_check(self):
        self.log("正在連線至 GitHub Releases API 檢查更新...")
        def _bg():
            info = check_github_update()
            self.after(0, lambda: self._on_check_finished(info))
        threading.Thread(target=_bg, daemon=True).start()

    def _on_check_finished(self, info):
        self.info = info
        if not info.get("success"):
            err = info.get("error", "未知網路錯誤")
            self.log(f"[錯誤] 檢查更新失敗: {err}")
            self.latest_badge.configure(fg_color="#381a1a", border_color="#582323")
            self.latest_badge_label.configure(text=self._t("update_status_failed", "連線失敗"), text_color="#f87171")
            self.release_meta_label.configure(text=f"{self._t('update_conn_err', '無法連接至 GitHub')}: {err}")
            self.progress_label.configure(text=self._t("update_check_failed", "檢查失敗，請檢查網路連線或前往 GitHub 查看"))
            return

        latest_tag = info.get("latest_version")
        release_name = info.get("release_name")
        asset_size = info.get("asset_size", 0)
        size_mb = f" (檔案大小: {asset_size / (1024*1024):.1f} MB)" if asset_size > 0 else ""

        self.log(f"成功取得版本資訊！GitHub 最新版本: {latest_tag}")
        if info.get("has_update"):
            self.log(f"發現新版本可供更新: {latest_tag}{size_mb}")
            self.log(f"發行標題: {release_name}")
            self.latest_badge.configure(fg_color=TAG_PURPLE_BG, border_color=TAG_PURPLE_BORDER)
            self.latest_badge_label.configure(text=f"{self._t('update_status_found', '發現新版本')}: {latest_tag}", text_color=TAG_PURPLE_TEXT)
            self.release_meta_label.configure(text=f"{release_name}{size_mb}")
            self.progress_label.configure(text=self._t("update_found_hint", "發現新版本！請點選下方「立即直接更新」按鈕"))
            self.btn_primary.configure(state="normal")
        else:
            cur = info.get("current_version", APP_VERSION)
            self.log(f"目前已是最新版本 ({cur})，無需更新。")
            self.latest_badge.configure(fg_color=TAG_MINT_BG, border_color=TAG_MINT_BORDER)
            self.latest_badge_label.configure(text=f"{self._t('update_status_latest', '已是最新')} ({cur})", text_color=TAG_MINT_TEXT)
            self.release_meta_label.configure(text=f"{release_name} - {self._t('update_system_latest', '系統已是最新狀態')}")
            self.progress_label.configure(text=self._t("update_status_latest_msg", "目前已是最新版本"))
            self.btn_force.configure(state="normal")

    def _update_download_progress(self, pct, cur_mb, tot_mb, speed_str=""):
        self.progress_bar.set(pct / 100.0)
        speed_part = f" - 速度: {speed_str}" if speed_str else ""
        self.progress_label.configure(
            text=f"{self._t('update_downloading_file', '正在下載更新檔...')} {pct:.1f}% ({cur_mb:.1f} MB / {tot_mb:.1f} MB){speed_part}"
        )

    def _on_update_error(self, err_msg):
        self.is_updating = False
        self.progress_label.configure(text=f"{self._t('update_failed_prefix', '更新失敗')}：{err_msg}")
        self.btn_close.configure(state="normal")
        self.btn_primary.configure(state="normal")
        self.btn_force.configure(state="normal")

    def _on_start_update(self, force=False):
        if self.is_updating:
            return
        self.is_updating = True
        self.btn_primary.configure(state="disabled")
        self.btn_force.configure(state="disabled")
        self.btn_close.configure(state="disabled")

        def _bg():
            try:
                if is_frozen():
                    asset_url = self.info.get("download_url") or self.info.get("asset_url")
                    if not asset_url:
                        raise RuntimeError("在 GitHub Releases 找不到 Windows 安裝套件 ZIP 檔")

                    temp_dir = tempfile.gettempdir()
                    zip_name = self.info.get("asset_name") or f"OBSMusicDisplay_update_{int(time.time())}.zip"
                    zip_path = os.path.join(temp_dir, zip_name)
                    extract_dir = os.path.join(temp_dir, f"obs_extract_{int(time.time())}")

                    self.log(f"開始下載更新套件: {os.path.basename(zip_path)}...")

                    def _progress_cb(pct, downloaded, total, speed_str=""):
                        cur_mb = downloaded / (1024 * 1024)
                        tot_mb = total / (1024 * 1024)
                        self.after(0, lambda: self._update_download_progress(pct, cur_mb, tot_mb, speed_str))

                    download_file_with_progress(asset_url, zip_path, progress_callback=_progress_cb, log_callback=self.log)

                    self.after(0, lambda: self.progress_label.configure(text=self._t("update_extracting", "下載完成！正在驗證並解壓縮檔案...")))
                    src_app_dir = extract_and_validate_zip(zip_path, extract_dir, log_callback=self.log)

                    self.after(0, lambda: self.progress_label.configure(text=self._t("update_applying", "解壓縮完成！正在套用更新並重啟程式...")))
                    self.log("所有更新檔案已就緒，即將重啟程式...")
                    time.sleep(1.0)
                    apply_frozen_update(src_app_dir, target_app_dir=self.parent_gui.base_dir, zip_path=zip_path, log_callback=self.log)

                elif is_git_repo(self.parent_gui.base_dir):
                    self.log("檢測到目前執行於 Git 原始碼目錄環境。")
                    self.after(0, lambda: self.progress_label.configure(text=self._t("update_git_pulling", "正在透過 git pull 更新程式碼...")))
                    success, msg = apply_git_update(self.parent_gui.base_dir, log_callback=self.log)
                    if not success:
                        raise RuntimeError(f"Git pull 失敗: {msg}")

                    self.log("程式碼更新完成！即將重新啟動應用程式...")
                    self.after(0, lambda: self.progress_label.configure(text=self._t("update_restarting", "更新完成！正在重啟...")))
                    time.sleep(1.0)
                    os.execl(sys.executable, sys.executable, *sys.argv)
                else:
                    self.log("環境無法自動替換，正在為您開啟 GitHub 頁面手動下載...")
                    webbrowser.open(self.info.get("html_url", "https://github.com/tokihorokeiya/musicDisplayObs/releases"))
            except Exception as e:
                err_msg = str(e)
                self.log(f"[嚴重錯誤] 更新作業中斷: {err_msg}")
                self.after(0, lambda: self._on_update_error(err_msg))

        threading.Thread(target=_bg, daemon=True).start()

class AppGUI(ctk.CTk):
    """
    Notion Workspace Design System implementation of OBS Real-Time Music Display.
    - Deep Navy Hero Band (#0a1530)
    - Notion Signature Purple Primary CTA (#5645d4)
    - Sober-editorial 8px rectangular buttons (strictly NOT pills)
    - 12px rounded cards & pastel database property status badges
    - Zero emojis for a professional broadcast studio aesthetic
    """
    def __init__(self, config, on_port_change_callback, on_theme_change_callback, on_exit_callback=None):
        super().__init__()
        self.config = config
        self.on_port_change_callback = on_port_change_callback
        self.on_theme_change_callback = on_theme_change_callback
        self.on_exit_callback = on_exit_callback
        self._exit_dialog = None
        self.current_lang = self.config.get("language", "zh_TW")
        if self.current_lang not in TRANSLATIONS:
            self.current_lang = "zh_TW"

        self.current_res_mode = self.config.get("resolution_mode", "1920x700")
        self.current_page = "dashboard"

        self.title("OBS Real-Time Music Display")
        self.geometry("980x740")
        self.minsize(880, 640)
        self.configure(fg_color=NOTION_CANVAS)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
            bundle_dir = getattr(sys, '_MEIPASS', self.base_dir)
            self.assets_dir = bundle_dir if os.path.exists(os.path.join(bundle_dir, "static")) else self.base_dir
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
            self.assets_dir = self.base_dir

        self.current_thumbnail_data = None
        self._cached_cover_img = None
        self._cached_default_cover_img = None
        self._last_rendered_title = None
        self._last_rendered_artist = None
        self._last_rendered_status = None
        self._last_rendered_time_str = None
        self.tray_icon = None
        self.preview_tk_images = {}
        self.toast_timer = None
        self.latest_media_data = None
        try:
            import tkinter.font as tkfont
            self.available_fonts = set(tkfont.families())
        except Exception:
            self.available_fonts = set()
        self.font_family = get_ui_font_family(self.current_lang)

        # Dynamic widget placeholders
        self.track_title_label = None
        self.track_artist_label = None
        self.time_label = None
        self.progress_bar = None
        self.status_badge = None
        self.status_badge_text = None
        self.cover_label = None
        self.hero_status_chip = None
        self.nav_buttons = {}
        self.gallery_url_entries = {}
        self.gallery_card_widgets = {}

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(3000, self._check_update_background_quiet)

    def _font(self, size, weight="normal"):
        return ctk.CTkFont(family=self.font_family, size=size, weight=weight)

    def _get_dropdown_menu_font(self, is_multilingual=False):
        """
        Returns a clean (family, size) tuple for Tkinter native menus.
        Tkinter menus on Windows fail to parse CTkFont objects with trailing style spaces,
        causing fallback to size 8 and 1-bit bitmap raster fonts (PMingLiU/MS UI Gothic).
        Using a clean tuple directly guarantees standard ClearType vector rendering.
        """
        if is_multilingual:
            for fam in ["Microsoft JhengHei UI", "Microsoft JhengHei", "Yu Gothic UI", "Malgun Gothic"]:
                if fam in getattr(self, "available_fonts", set()):
                    return (fam, 11)
            return ("Segoe UI", 11)
        return (self.font_family, 11)

    def _t(self, key, default=""):
        return get_text(self.current_lang, key, default)

    def _get_res_query_param(self):
        return ""

    def show_inapp_toast(self, message):
        """Displays a floating overlay toast notification at the bottom-right corner."""
        if hasattr(self, "toast_label") and hasattr(self, "toast_frame"):
            self.toast_label.configure(text=message)
            self.toast_frame.place(relx=1.0, rely=1.0, x=-24, y=-24, anchor="se")
            self.toast_frame.lift()
            if self.toast_timer:
                self.after_cancel(self.toast_timer)
            self.toast_timer = self.after(3000, lambda: self.toast_frame.place_forget())

    def _build_ui(self):
        """Constructs the Notion workspace interface layout."""
        # Clear existing widgets if re-building
        for child in self.winfo_children():
            child.destroy()

        self.main_wrapper = ctk.CTkFrame(self, fg_color=NOTION_CANVAS, corner_radius=0)
        self.main_wrapper.pack(fill="both", expand=True)

        # -------------------------------------------------------------
        # 1. Notion Workspace Left Sidebar (width=220, NOTION_SIDEBAR)
        # -------------------------------------------------------------
        self.sidebar_frame = ctk.CTkFrame(
            self.main_wrapper,
            width=220,
            corner_radius=0,
            fg_color=NOTION_SIDEBAR,
            border_width=1,
            border_color=NOTION_HAIRLINE
        )
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        # Workspace brand header
        brand_box = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        brand_box.pack(fill="x", padx=16, pady=(18, 16))

        # Notion-style workspace icon box
        icon_box = ctk.CTkFrame(
            brand_box,
            width=32,
            height=32,
            corner_radius=8,
            fg_color="#222222",
            border_width=1,
            border_color=NOTION_HAIRLINE_STRONG
        )
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)

        ctk.CTkLabel(
            icon_box,
            text="OBS",
            font=self._font(10, "bold"),
            text_color=NOTION_INK
        ).place(relx=0.5, rely=0.5, anchor="center")

        brand_title_box = ctk.CTkFrame(brand_box, fg_color="transparent")
        brand_title_box.pack(side="left", padx=(10, 0))

        ctk.CTkLabel(
            brand_title_box,
            text="OBS Display",
            font=self._font(13, "bold"),
            text_color=NOTION_INK
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_title_box,
            text=self._t("sidebar_workspace", "工作區"),
            font=self._font(10),
            text_color=NOTION_STONE
        ).pack(anchor="w")

        # Hairline divider
        ctk.CTkFrame(
            self.sidebar_frame,
            height=1,
            fg_color=NOTION_HAIRLINE
        ).pack(fill="x", padx=16, pady=(0, 14))

        # Nav items container
        nav_list = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        nav_list.pack(fill="x", padx=12)

        self.nav_buttons = {}
        nav_configs = [
            ("dashboard", self._t("nav_dashboard", "即時控制台")),
            ("gallery", self._t("nav_gallery", "風格模板庫")),
            ("settings", self._t("nav_settings", "系統設定")),
        ]

        for page_id, label_text in nav_configs:
            is_active = (self.current_page == page_id)
            btn = ctk.CTkButton(
                nav_list,
                text=f"   {label_text}",
                anchor="w",
                height=36,
                corner_radius=8,  # Notion 8px rectangular geometry
                font=self._font(12, "bold" if is_active else "normal"),
                fg_color=NOTION_SIDEBAR_ACTIVE if is_active else "transparent",
                text_color=NOTION_INK if is_active else NOTION_STEEL,
                hover_color=NOTION_SIDEBAR_HOVER,
                command=lambda pid=page_id: self._navigate_page(pid)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[page_id] = btn

        # Bottom sidebar container: server status and version
        sidebar_bottom = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=16, pady=16)

        # Server online badge
        port_num = self.config.get("port", 11150)
        status_row = ctk.CTkFrame(sidebar_bottom, fg_color="transparent")
        status_row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            status_row,
            text="●",
            font=self._font(10),
            text_color=TAG_MINT_TEXT
        ).pack(side="left", padx=(0, 6))

        online_txt = self._t("status_online", "在線")
        ctk.CTkLabel(
            status_row,
            text=f"Port {port_num} ({online_txt})",
            font=self._font(11),
            text_color=NOTION_STEEL
        ).pack(side="left")

        # Version label
        ver_str = APP_VERSION if APP_VERSION.startswith("v") else f"v{APP_VERSION}"
        ctk.CTkLabel(
            sidebar_bottom,
            text=ver_str,
            font=self._font(10),
            text_color=NOTION_STONE
        ).pack(anchor="w")

        # -------------------------------------------------------------
        # 2. Right Main Work Area
        # -------------------------------------------------------------
        self.main_content_frame = ctk.CTkFrame(self.main_wrapper, fg_color=NOTION_CANVAS, corner_radius=0)
        self.main_content_frame.pack(side="right", fill="both", expand=True)

        # -------------------------------------------------------------
        # Notion Deep Navy Hero Band (#0a1530)
        # -------------------------------------------------------------
        self.hero_band = ctk.CTkFrame(
            self.main_content_frame,
            height=72,
            corner_radius=0,
            fg_color=NOTION_NAVY,
            border_width=1,
            border_color=NOTION_NAVY_MID
        )
        self.hero_band.pack(fill="x")
        self.hero_band.pack_propagate(False)

        hero_left = ctk.CTkFrame(self.hero_band, fg_color="transparent")
        hero_left.pack(side="left", padx=24, pady=12)

        self.hero_subtitle_label = ctk.CTkLabel(
            hero_left,
            text="OBS REAL-TIME MUSIC DISPLAY",
            font=self._font(9, "bold"),
            text_color=NOTION_STONE
        )
        self.hero_subtitle_label.pack(anchor="w")

        self.hero_title_label = ctk.CTkLabel(
            hero_left,
            text=self._get_page_hero_title(self.current_page),
            font=self._font(17, "bold"),
            text_color=NOTION_INK
        )
        self.hero_title_label.pack(anchor="w")

        # Hero right side: pastel status chip
        hero_right = ctk.CTkFrame(self.hero_band, fg_color="transparent")
        hero_right.pack(side="right", padx=24, pady=16)

        self.hero_status_chip = ctk.CTkLabel(
            hero_right,
            text=f"  {self._t('hero_live_connected', '即時連線中')}  ",
            font=self._font(11, "bold"),
            text_color=TAG_MINT_TEXT,
            fg_color=TAG_MINT_BG,
            corner_radius=6
        )
        self.hero_status_chip.pack(side="right")

        # Floating toast notification overlay at bottom-right (independent of page layout)
        self.toast_frame = ctk.CTkFrame(
            self,
            fg_color="#181818",
            border_color=NOTION_PURPLE,
            border_width=1,
            corner_radius=8
        )
        self.toast_label = ctk.CTkLabel(
            self.toast_frame,
            text="",
            font=self._font(11, "bold"),
            text_color="#f3f4f6"
        )
        self.toast_label.pack(padx=18, pady=10)

        # Persistent Content Container
        self.content_container = ctk.CTkFrame(self.main_content_frame, fg_color=NOTION_CANVAS, corner_radius=0)
        self.content_container.pack(fill="both", expand=True, padx=24, pady=16)

        # Pre-create and keep all 3 pages loaded in memory for 0ms, seamless switching
        self.pages = {}
        self.page_dashboard = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.page_gallery = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.page_settings = ctk.CTkFrame(self.content_container, fg_color="transparent")

        self.pages["dashboard"] = self.page_dashboard
        self.pages["gallery"] = self.page_gallery
        self.pages["settings"] = self.page_settings

        self._build_dashboard_page(self.page_dashboard)
        self._build_gallery_page(self.page_gallery)
        self._build_settings_page(self.page_settings)

        # Display initially active page
        self.pages[self.current_page].pack(fill="both", expand=True)

        if self.latest_media_data:
            self.update_media_display(self.latest_media_data)

    def _get_page_hero_title(self, page_id):
        if page_id == "dashboard":
            return self._t("nav_dashboard", "即時控制台")
        elif page_id == "gallery":
            return self._t("nav_gallery", "風格模板庫")
        elif page_id == "settings":
            return self._t("nav_settings", "系統設定")
        return "Notion Workspace"

    def _navigate_page(self, page_id):
        if self.current_page == page_id:
            return
        old_page = self.current_page
        self.current_page = page_id

        # Update sidebar button states
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.configure(
                    fg_color=NOTION_SIDEBAR_ACTIVE,
                    text_color=NOTION_INK,
                    font=self._font(12, "bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=NOTION_STEEL,
                    font=self._font(12, "normal")
                )

        # Update hero title
        if hasattr(self, "hero_title_label"):
            self.hero_title_label.configure(text=self._get_page_hero_title(page_id))

        # Seamless switch: hide old page, show new page instantly without destroying!
        if old_page in self.pages:
            self.pages[old_page].pack_forget()
        if page_id in self.pages:
            self.pages[page_id].pack(fill="both", expand=True)

    # -------------------------------------------------------------
    # Page 1: Dashboard (Notion Document Card + OBS Quick Connect)
    # -------------------------------------------------------------
    def _build_dashboard_page(self, parent=None):
        if parent is None:
            parent = getattr(self, "page_dashboard", self.content_container)

        # Top Card: Live Media Player Card (Notion 12px rounded card)
        player_card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=NOTION_SURFACE,
            border_width=1,
            border_color=NOTION_HAIRLINE
        )
        player_card.pack(fill="x", pady=(0, 16))

        # Card header with Notion database property pill
        player_header = ctk.CTkFrame(player_card, fg_color="transparent")
        player_header.pack(fill="x", padx=18, pady=(14, 10))

        ctk.CTkLabel(
            player_header,
            text=self._t("now_playing_header", "當前媒體播放狀態"),
            font=self._font(11, "bold"),
            text_color=NOTION_STEEL
        ).pack(side="left")

        # Notion Pastel Property Status Tag
        self.status_badge = ctk.CTkFrame(
            player_header,
            corner_radius=6,
            fg_color=TAG_PEACH_BG,
            border_width=1,
            border_color=TAG_PEACH_BORDER
        )
        self.status_badge.pack(side="right")

        self.status_badge_text = ctk.CTkLabel(
            self.status_badge,
            text=self._t("status_idle", "閒置"),
            font=self._font(10, "bold"),
            text_color=TAG_PEACH_TEXT
        )
        self.status_badge_text.pack(padx=8, pady=2)

        # Player Body: Cover + Metadata + Progress
        player_body = ctk.CTkFrame(player_card, fg_color="transparent")
        player_body.pack(fill="x", padx=18, pady=(0, 16))

        # Album Art Thumbnail (90x90, 8px rounded)
        cover_container = ctk.CTkFrame(
            player_body,
            width=90,
            height=90,
            corner_radius=8,
            fg_color="#121212",
            border_width=1,
            border_color=NOTION_HAIRLINE_STRONG
        )
        cover_container.pack(side="left", padx=(0, 16))
        cover_container.pack_propagate(False)

        self.cover_label = ctk.CTkLabel(cover_container, text="", image=None)
        self.cover_label.place(relx=0.5, rely=0.5, anchor="center")
        self._load_default_cover(target_label=self.cover_label, size=(90, 90))

        # Right side: Metadata & Notion Property Grid
        meta_box = ctk.CTkFrame(player_body, fg_color="transparent")
        meta_box.pack(side="left", fill="both", expand=True)

        self.track_title_label = ctk.CTkLabel(
            meta_box,
            text=self._t("waiting_media", "等待媒體播放中..."),
            font=self._font(16, "bold"),
            text_color=NOTION_INK,
            anchor="w"
        )
        self.track_title_label.pack(fill="x", pady=(0, 2))

        self.track_artist_label = ctk.CTkLabel(
            meta_box,
            text=self._t("play_instruction", "在 YouTube、YouTube Music 或 Spotify 播放音樂"),
            font=self._font(12),
            text_color=NOTION_STEEL,
            anchor="w"
        )
        self.track_artist_label.pack(fill="x", pady=(0, 8))

        # Notion Database Properties Row
        props_row = ctk.CTkFrame(meta_box, fg_color="transparent")
        props_row.pack(fill="x", pady=(0, 10))

        # Active Theme Tag Chip
        active_theme_id = self.config.get("selected_theme", "glassmorphism")
        current_theme_name, _ = get_theme_info(self.current_lang, active_theme_id)

        theme_tag = ctk.CTkFrame(
            props_row,
            corner_radius=6,
            fg_color=TAG_PURPLE_BG,
            border_width=1,
            border_color=TAG_PURPLE_BORDER
        )
        theme_tag.pack(side="left", padx=(0, 8))

        self.player_theme_chip = ctk.CTkLabel(
            theme_tag,
            text=f"{self._t('theme_label', '模板')}: {current_theme_name}",
            font=self._font(10, "bold"),
            text_color=TAG_PURPLE_TEXT
        )
        self.player_theme_chip.pack(padx=8, pady=2)

        # Progress Bar & Timing
        progress_row = ctk.CTkFrame(meta_box, fg_color="transparent")
        progress_row.pack(fill="x")

        self.progress_bar = ctk.CTkProgressBar(
            progress_row,
            height=6,
            corner_radius=3,
            progress_color=NOTION_PURPLE,
            fg_color="#333333"
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.time_label = ctk.CTkLabel(
            progress_row,
            text="00:00 / 00:00",
            font=self._font(11),
            text_color=NOTION_STEEL
        )
        self.time_label.pack(side="right")

        # -------------------------------------------------------------
        # Bottom Card: OBS Quick Connect Dock (Notion 12px rounded card)
        # -------------------------------------------------------------
        dock_card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=NOTION_SURFACE,
            border_width=1,
            border_color=NOTION_HAIRLINE
        )
        dock_card.pack(fill="both", expand=True)

        dock_header = ctk.CTkFrame(dock_card, fg_color="transparent")
        dock_header.pack(fill="x", padx=18, pady=(16, 12))

        ctk.CTkLabel(
            dock_header,
            text=self._t("obs_dock_title", "OBS 快速掛載中心"),
            font=self._font(13, "bold"),
            text_color=NOTION_INK
        ).pack(anchor="w")

        ctk.CTkLabel(
            dock_header,
            text=self._t("global_theme_desc", "在 OBS 中使用此全域網址，您只需在此切換樣式，OBS 畫面將即時自動同步更換！"),
            font=self._font(11),
            text_color=NOTION_STEEL
        ).pack(anchor="w", pady=(2, 0))

        # 2-Column Grid inside dock
        columns_frame = ctk.CTkFrame(dock_card, fg_color="transparent")
        columns_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        # Column 1: Interactive Notion OLE Drag Tile
        self.drag_tile = ctk.CTkFrame(
            columns_frame,
            corner_radius=12,
            fg_color="#181818",
            border_width=2,
            border_color=NOTION_HAIRLINE_STRONG
        )
        self.drag_tile.pack(side="left", fill="both", expand=True, padx=(0, 10))

        drag_inner = ctk.CTkFrame(self.drag_tile, fg_color="transparent")
        drag_inner.place(relx=0.5, rely=0.5, anchor="center")

        # Notion drag card typography
        ctk.CTkLabel(
            drag_inner,
            text=self._t("obs_dock_drag_title", "按住此卡片直接拖入 OBS 畫布"),
            font=self._font(13, "bold"),
            text_color=NOTION_INK
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            drag_inner,
            text=self._t("obs_dock_drag_sub", "OBS 將自動新增為透明瀏覽器來源"),
            font=self._font(11),
            text_color=NOTION_STEEL
        ).pack(pady=(0, 12))

        drag_pill = ctk.CTkFrame(
            drag_inner,
            corner_radius=6,
            fg_color="#242424",
            border_width=1,
            border_color=NOTION_HAIRLINE_STRONG
        )
        drag_pill.pack()

        ctk.CTkLabel(
            drag_pill,
            text=self._t("drag_pill_text", "拖曳至 OBS 畫布"),
            font=self._font(9, "bold"),
            text_color=NOTION_CHARCOAL
        ).pack(padx=12, pady=4)

        # Hook Windows OLE Drag on drag tile
        self._setup_drag_on_widget(self.drag_tile, self._get_global_overlay_url)
        for w in drag_inner.winfo_children():
            self._setup_drag_on_widget(w, self._get_global_overlay_url)
        self._setup_drag_on_widget(drag_pill, self._get_global_overlay_url)

        # Column 2: Global Auto-Sync Template Settings
        sync_tile = ctk.CTkFrame(
            columns_frame,
            corner_radius=12,
            fg_color="#181818",
            border_width=1,
            border_color=NOTION_HAIRLINE
        )
        sync_tile.pack(side="right", fill="both", expand=True, padx=(10, 0))

        sync_inner = ctk.CTkFrame(sync_tile, fg_color="transparent")
        sync_inner.pack(fill="both", expand=True, padx=16, pady=16)

        # Theme selector row
        theme_row = ctk.CTkFrame(sync_inner, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            theme_row,
            text=self._t("active_theme_label", "目前全域模板："),
            font=self._font(11, "bold"),
            text_color=NOTION_INK
        ).pack(side="left")

        current_theme_id = self.config.get("selected_theme", "glassmorphism")
        current_theme_name, _ = get_theme_info(self.current_lang, current_theme_id)
        theme_display_names = [get_theme_info(self.current_lang, tid)[0] for tid in THEME_IDS]

        theme_menu_font = self._get_dropdown_menu_font(is_multilingual=False)
        self.global_theme_dropdown = ctk.CTkOptionMenu(
            theme_row,
            values=theme_display_names,
            width=180,
            height=30,
            corner_radius=8,  # Notion 8px geometry
            font=self._font(11),
            dropdown_font=theme_menu_font,
            fg_color="#242424",
            button_color="#2f2f2f",
            button_hover_color="#3a3a3a",
            command=self._on_global_theme_selected
        )
        try:
            self.global_theme_dropdown._dropdown_menu.configure(font=theme_menu_font)
        except Exception:
            pass
        self.global_theme_dropdown.set(current_theme_name)
        self.global_theme_dropdown.pack(side="right")

        # Global URL Readonly Entry
        self.global_url_entry = ctk.CTkEntry(
            sync_inner,
            height=30,
            corner_radius=8,  # Notion 8px geometry
            font=self._font(11),
            text_color="#c084fc",
            fg_color="#121212",
            border_color=NOTION_HAIRLINE_STRONG
        )
        self.global_url_entry.insert(0, self._get_global_overlay_url())
        self.global_url_entry.configure(state="readonly")
        self.global_url_entry.pack(fill="x", pady=(0, 10))
        self._setup_drag_on_widget(self.global_url_entry, self._get_global_overlay_url)

        # Global auto-hide switch row
        auto_row = ctk.CTkFrame(sync_inner, fg_color="transparent")
        auto_row.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            auto_row,
            text=self._t("autohide_switch", "暫停或停止播放時自動隱藏小組件"),
            font=self._font(11),
            text_color=NOTION_CHARCOAL
        ).pack(side="left")

        self.autohide_switch = ctk.CTkSwitch(
            auto_row,
            text="",
            width=42,
            progress_color=NOTION_PURPLE,
            command=self._on_autohide_toggle
        )
        if self.config.get("autohide_on_pause", False):
            self.autohide_switch.select()
        self.autohide_switch.pack(side="right")

        # Action Buttons
        btn_box = ctk.CTkFrame(sync_inner, fg_color="transparent")
        btn_box.pack(fill="x")

        # Notion Signature Purple Primary CTA Button
        self.btn_copy_global = ctk.CTkButton(
            btn_box,
            text=self._t("btn_copy_global_url", "複製全域網址 (推薦)"),
            height=34,
            corner_radius=8,  # Notion 8px rectangular button
            font=self._font(11, "bold"),
            fg_color=NOTION_PURPLE,
            hover_color=NOTION_PURPLE_HOVER,
            command=self._copy_global_url
        )
        self.btn_copy_global.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Secondary Button (Sober Notion 8px button)
        self.btn_preview_global = ctk.CTkButton(
            btn_box,
            text=self._t("preview_btn", "預覽"),
            width=70,
            height=34,
            corner_radius=8,  # Notion 8px rectangular button
            font=self._font(11),
            fg_color="#242424",
            hover_color="#303030",
            border_width=1,
            border_color=NOTION_HAIRLINE_STRONG,
            command=lambda: webbrowser.open(self._get_global_overlay_url())
        )
        self.btn_preview_global.pack(side="right")

    # -------------------------------------------------------------
    # Page 2: Theme Gallery (Notion Database Gallery View)
    # -------------------------------------------------------------
    def _build_gallery_page(self, parent=None):
        if parent is None:
            parent = getattr(self, "page_gallery", self.content_container)

        top_bar = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=NOTION_SURFACE,
            border_width=1,
            border_color=NOTION_HAIRLINE
        )
        top_bar.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            top_bar,
            text=self._t("drag_banner_text", "直接拖曳任意模板預覽圖至 OBS 視窗即可新增，亦可點選「複製網址」貼上！"),
            font=self._font(11),
            text_color=NOTION_STEEL
        ).pack(side="left", padx=18, pady=12)

        self.autohide_switch = ctk.CTkSwitch(
            top_bar,
            text=self._t("autohide_switch", "暫停或停止播放時自動隱藏小組件"),
            font=self._font(11, "bold"),
            progress_color=NOTION_PURPLE,
            command=self._on_autohide_toggle
        )
        if self.config.get("autohide_on_pause", False):
            self.autohide_switch.select()
        self.autohide_switch.pack(side="right", padx=18, pady=10)

        # Scrollable gallery (Notion database card grid)
        self.scrollable_gallery = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scrollable_gallery.pack(fill="both", expand=True)

        previews_dir = os.path.join(self.assets_dir, "static", "previews")
        self.gallery_url_entries = {}
        self.gallery_card_widgets = {}
        active_theme_id = self.config.get("selected_theme", "glassmorphism")

        for i, theme_id in enumerate(THEME_IDS, 1):
            is_active = (theme_id == active_theme_id)
            title, desc = get_theme_info(self.current_lang, theme_id)

            # Notion Gallery Card (12px rounded, 2px purple border if active)
            card = ctk.CTkFrame(
                self.scrollable_gallery,
                corner_radius=12,
                fg_color=NOTION_SURFACE,
                border_width=2 if is_active else 1,
                border_color=NOTION_PURPLE if is_active else NOTION_HAIRLINE
            )
            card.pack(fill="x", pady=6, padx=4)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=14)

            # Preview Image Thumbnail (160x90, 8px rounded)
            preview_img = self._load_preview_thumbnail(previews_dir, theme_id, (160, 90))
            img_container = ctk.CTkFrame(
                inner,
                width=160,
                height=90,
                corner_radius=8,
                fg_color="#121212",
                border_width=1,
                border_color=NOTION_HAIRLINE_STRONG
            )
            img_container.pack(side="left", padx=(0, 16))
            img_container.pack_propagate(False)

            img_label = ctk.CTkLabel(img_container, text="", image=preview_img)
            img_label.place(relx=0.5, rely=0.5, anchor="center")

            theme_url_getter = lambda tid=theme_id: self._get_theme_url(tid)
            self._setup_drag_on_widget(img_container, theme_url_getter)
            self._setup_drag_on_widget(img_label, theme_url_getter)

            # Details
            details = ctk.CTkFrame(inner, fg_color="transparent")
            details.pack(side="left", fill="both", expand=True)

            title_row = ctk.CTkFrame(details, fg_color="transparent")
            title_row.pack(fill="x", pady=(0, 2))

            ctk.CTkLabel(
                title_row,
                text=f"{i}. {title}",
                font=self._font(13, "bold"),
                text_color=NOTION_INK
            ).pack(side="left")

            badge = ctk.CTkFrame(
                title_row,
                corner_radius=6,
                fg_color=TAG_PURPLE_BG,
                border_width=1,
                border_color=TAG_PURPLE_BORDER
            )
            ctk.CTkLabel(
                badge,
                text=self._t("active_theme_badge", "目前使用中"),
                font=self._font(9, "bold"),
                text_color=TAG_PURPLE_TEXT
            ).pack(padx=6, pady=1)

            if is_active:
                badge.pack(side="left", padx=8)

            ctk.CTkLabel(
                details,
                text=desc,
                font=self._font(11),
                text_color=NOTION_STEEL,
                anchor="w",
                justify="left"
            ).pack(fill="x", pady=(0, 8))

            # URL Bar + Buttons
            url_row = ctk.CTkFrame(details, fg_color="transparent")
            url_row.pack(fill="x")

            entry = ctk.CTkEntry(
                url_row,
                height=30,
                corner_radius=8,
                font=self._font(11),
                fg_color="#121212",
                border_color=NOTION_HAIRLINE_STRONG,
                text_color=NOTION_CHARCOAL
            )
            entry.insert(0, self._get_theme_url(theme_id))
            entry.configure(state="readonly")
            entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self._setup_drag_on_widget(entry, theme_url_getter)
            self.gallery_url_entries[theme_id] = entry

            # Action Buttons
            set_btn = ctk.CTkButton(
                url_row,
                text=self._t("set_active_btn", "設為當前"),
                width=80,
                height=30,
                corner_radius=8,
                font=self._font(11, "bold"),
                fg_color=NOTION_PURPLE if is_active else "#242424",
                hover_color=NOTION_PURPLE_HOVER if is_active else "#303030",
                border_width=0 if is_active else 1,
                border_color=NOTION_HAIRLINE_STRONG,
                command=lambda tid=theme_id: self._on_set_active_theme(tid)
            )
            set_btn.pack(side="left", padx=(0, 6))

            self.gallery_card_widgets[theme_id] = {
                "card": card,
                "badge": badge,
                "btn": set_btn
            }

            ctk.CTkButton(
                url_row,
                text=self._t("copy_url_btn", "複製網址"),
                width=76,
                height=30,
                corner_radius=8,
                font=self._font(11),
                fg_color="#242424",
                hover_color="#303030",
                border_width=1,
                border_color=NOTION_HAIRLINE_STRONG,
                command=lambda tid=theme_id: self._copy_theme_url(tid)
            ).pack(side="left", padx=(0, 6))

            ctk.CTkButton(
                url_row,
                text=self._t("preview_btn", "預覽"),
                width=55,
                height=30,
                corner_radius=8,
                font=self._font(11),
                fg_color="#242424",
                hover_color="#303030",
                border_width=1,
                border_color=NOTION_HAIRLINE_STRONG,
                command=lambda tid=theme_id: webbrowser.open(self._get_theme_url(tid))
            ).pack(side="left")

    # -------------------------------------------------------------
    # Page 3: Settings (Notion Workspace Preferences)
    # -------------------------------------------------------------
    def _build_settings_page(self, parent=None):
        if parent is None:
            parent = getattr(self, "page_settings", self.content_container)
        settings_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        settings_scroll.pack(fill="both", expand=True)

        # Section 1: Language & Region
        self._build_settings_section(
            settings_scroll,
            title=self._t("settings_category_lang", "語言與地區"),
            subtitle=self._t("settings_category_lang_sub", "選擇軟體操作介面顯示語言")
        )
        sec1_card = ctk.CTkFrame(settings_scroll, corner_radius=12, fg_color=NOTION_SURFACE, border_width=1, border_color=NOTION_HAIRLINE)
        sec1_card.pack(fill="x", pady=(0, 20))

        lang_row = ctk.CTkFrame(sec1_card, fg_color="transparent")
        lang_row.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            lang_row,
            text=self._t("language_label", "語言 / Language:"),
            font=self._font(12, "bold"),
            text_color=NOTION_INK
        ).pack(side="left")

        lang_names = [name for name, _ in LANGUAGE_OPTIONS]
        current_name = next((name for name, code in LANGUAGE_OPTIONS if code == self.current_lang), "English")

        lang_menu_font = self._get_dropdown_menu_font(is_multilingual=True)
        self.lang_menu = ctk.CTkOptionMenu(
            lang_row,
            values=lang_names,
            width=240,
            height=32,
            corner_radius=8,
            font=self._font(11),
            dropdown_font=lang_menu_font,
            fg_color="#242424",
            button_color="#2f2f2f",
            button_hover_color="#3a3a3a",
            command=self._on_language_changed
        )
        try:
            self.lang_menu._dropdown_menu.configure(font=lang_menu_font)
        except Exception:
            pass
        self.lang_menu.set(current_name)
        self.lang_menu.pack(side="right")

        # Section 2: Server & Network
        self._build_settings_section(
            settings_scroll,
            title=self._t("settings_category_server", "伺服器與網路"),
            subtitle=self._t("settings_category_server_sub", "管理本機 HTTP 伺服器通訊端口與播放自動隱藏功能")
        )
        sec2_card = ctk.CTkFrame(settings_scroll, corner_radius=12, fg_color=NOTION_SURFACE, border_width=1, border_color=NOTION_HAIRLINE)
        sec2_card.pack(fill="x", pady=(0, 20))

        # Port row
        port_row = ctk.CTkFrame(sec2_card, fg_color="transparent")
        port_row.pack(fill="x", padx=20, pady=(16, 12))

        ctk.CTkLabel(
            port_row,
            text=self._t("server_port", "伺服器端口："),
            font=self._font(12, "bold"),
            text_color=NOTION_INK
        ).pack(side="left")

        self.port_entry = ctk.CTkEntry(
            port_row,
            width=90,
            height=32,
            corner_radius=8,
            font=self._font(11),
            fg_color="#121212",
            border_color=NOTION_HAIRLINE_STRONG
        )
        self.port_entry.insert(0, str(self.config.get("port", 11150)))
        self.port_entry.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            port_row,
            text=self._t("apply_port", "套用端口"),
            width=80,
            height=32,
            corner_radius=8,
            font=self._font(11, "bold"),
            fg_color=NOTION_PURPLE,
            hover_color=NOTION_PURPLE_HOVER,
            command=self._on_apply_port
        ).pack(side="right")

        ctk.CTkFrame(sec2_card, height=1, fg_color=NOTION_HAIRLINE).pack(fill="x", padx=20)

        # Autohide row
        auto_row = ctk.CTkFrame(sec2_card, fg_color="transparent")
        auto_row.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            auto_row,
            text=self._t("autohide_switch", "暫停或停止播放時自動隱藏小組件"),
            font=self._font(12, "bold"),
            text_color=NOTION_INK
        ).pack(side="left")

        self.settings_autohide_switch = ctk.CTkSwitch(
            auto_row,
            text="",
            progress_color=NOTION_PURPLE,
            command=self._on_autohide_toggle_settings
        )
        if self.config.get("autohide_on_pause", False):
            self.settings_autohide_switch.select()
        self.settings_autohide_switch.pack(side="right")

        ctk.CTkFrame(sec2_card, height=1, fg_color=NOTION_HAIRLINE).pack(fill="x", padx=20)

        # Shortcuts row
        sc_row = ctk.CTkFrame(sec2_card, fg_color="transparent")
        sc_row.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(
            sc_row,
            text=self._t("shortcuts_title", "OBS 捷徑快速開啟"),
            font=self._font(12, "bold"),
            text_color=NOTION_INK
        ).pack(side="left")

        ctk.CTkButton(
            sc_row,
            text=self._t("open_folder_btn", "開啟捷徑資料夾"),
            height=32,
            corner_radius=8,
            font=self._font(11),
            fg_color="#242424",
            hover_color="#303030",
            border_width=1,
            border_color=NOTION_HAIRLINE_STRONG,
            command=self._open_shortcuts_folder
        ).pack(side="right")

        # Section 3: Software Version & Updates
        self._build_settings_section(
            settings_scroll,
            title=self._t("settings_category_update", "軟體版本與更新"),
            subtitle=self._t("settings_category_update_sub", "檢查 GitHub 最新發行版本，支援一鍵直接下載重啟更新")
        )
        sec3_card = ctk.CTkFrame(settings_scroll, corner_radius=12, fg_color=NOTION_SURFACE, border_width=1, border_color=NOTION_HAIRLINE)
        sec3_card.pack(fill="x", pady=(0, 20))

        ver_row = ctk.CTkFrame(sec3_card, fg_color="transparent")
        ver_row.pack(fill="x", padx=20, pady=16)

        ver_display = APP_VERSION if APP_VERSION.startswith("v") else f"v{APP_VERSION}"
        ctk.CTkLabel(
            ver_row,
            text=f"{self._t('version_label', '軟體版本：')} {ver_display}",
            font=self._font(12, "bold"),
            text_color=NOTION_INK
        ).pack(side="left")

        self.btn_check_update = ctk.CTkButton(
            ver_row,
            text=self._t("btn_check_update", "檢查與線上更新"),
            height=32,
            corner_radius=8,
            font=self._font(11, "bold"),
            fg_color=NOTION_PURPLE,
            hover_color=NOTION_PURPLE_HOVER,
            command=self._on_check_update_clicked
        )
        self.btn_check_update.pack(side="right")

        hint_row = ctk.CTkFrame(sec3_card, fg_color="transparent")
        hint_row.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            hint_row,
            text=self._t("update_hint_desc", "點選「檢查與線上更新」可開啟專屬更新視窗，自動比對版本並查看即時下載與解壓縮進度日誌。"),
            font=self._font(11),
            text_color=NOTION_STEEL,
            anchor="w"
        ).pack(fill="x")

    def _build_settings_section(self, parent, title, subtitle):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.pack(fill="x", pady=(10, 8))

        ctk.CTkLabel(
            box,
            text=title,
            font=self._font(13, "bold"),
            text_color=NOTION_INK
        ).pack(anchor="w")

        ctk.CTkLabel(
            box,
            text=subtitle,
            font=self._font(10),
            text_color=NOTION_STONE
        ).pack(anchor="w", pady=(2, 0))

    # -------------------------------------------------------------
    # Logic & Event Handlers
    # -------------------------------------------------------------
    def _setup_drag_on_widget(self, widget, url_getter):
        """Attaches native Windows OLE drag to OBS canvas."""
        setup_native_drag_and_drop(widget, url_getter, on_drag_success_callback=self._on_drag_completed)

    def _on_drag_completed(self):
        self.show_inapp_toast(self._t("drag_done_toast", "成功拖曳至 OBS！"))

    def _get_theme_url(self, theme_id):
        port = self.config.get("port", 11150)
        autohide = 1 if self.config.get("autohide_on_pause", False) else 0
        return f"http://localhost:{port}/overlay?theme={theme_id}&autohide={autohide}"

    def _get_global_overlay_url(self):
        port = self.config.get("port", 11150)
        autohide = 1 if self.config.get("autohide_on_pause", False) else 0
        return f"http://localhost:{port}/overlay?autohide={autohide}"

    def _copy_global_url(self):
        url = self._get_global_overlay_url()
        self.clipboard_clear()
        self.clipboard_append(url)
        self.update()
        self.show_inapp_toast(self._t("copied_toast", "已複製全域網址至剪貼簿！可在 OBS 直接貼上"))

    def _copy_theme_url(self, theme_id):
        url = self._get_theme_url(theme_id)
        self.clipboard_clear()
        self.clipboard_append(url)
        self.update()
        self.show_inapp_toast(self._t("copied_toast", "已複製 OBS 網址至剪貼簿！可在 OBS 直接貼上"))

    def _on_global_theme_selected(self, chosen_display_name):
        selected_tid = "glassmorphism"
        for tid in THEME_IDS:
            name, _ = get_theme_info(self.current_lang, tid)
            if name == chosen_display_name:
                selected_tid = tid
                break

        self.config["selected_theme"] = selected_tid
        save_config(self.config)
        if self.on_theme_change_callback:
            self.on_theme_change_callback(selected_tid)

        self._update_active_theme_ui(selected_tid)
        self.show_inapp_toast(self._t("theme_set_toast", f"已將全域模板設為「{chosen_display_name}」！OBS 即時同步生效").format(name=chosen_display_name))

    def _on_set_active_theme(self, theme_id):
        self.config["selected_theme"] = theme_id
        save_config(self.config)
        if self.on_theme_change_callback:
            self.on_theme_change_callback(theme_id)

        theme_name, _ = get_theme_info(self.current_lang, theme_id)
        self._update_active_theme_ui(theme_id)
        self.show_inapp_toast(self._t("theme_set_toast", f"已切換至「{theme_name}」模板！").format(name=theme_name))

    def _update_active_theme_ui(self, theme_id):
        """Updates borders, badges, and buttons of theme cards in-place without re-rendering or duplicating."""
        theme_name, _ = get_theme_info(self.current_lang, theme_id)

        # 1. In-place update for Theme Gallery cards
        if hasattr(self, "gallery_card_widgets"):
            for tid, widgets in self.gallery_card_widgets.items():
                is_active = (tid == theme_id)
                card = widgets.get("card")
                badge = widgets.get("badge")
                btn = widgets.get("btn")
                if card and card.winfo_exists():
                    card.configure(
                        border_width=2 if is_active else 1,
                        border_color=NOTION_PURPLE if is_active else NOTION_HAIRLINE
                    )
                if badge and badge.winfo_exists():
                    if is_active:
                        badge.pack(side="left", padx=8)
                    else:
                        badge.pack_forget()
                if btn and btn.winfo_exists():
                    btn.configure(
                        fg_color=NOTION_PURPLE if is_active else "#242424",
                        hover_color=NOTION_PURPLE_HOVER if is_active else "#303030",
                        border_width=0 if is_active else 1,
                        border_color=NOTION_HAIRLINE_STRONG
                    )

        # 2. Update Dashboard widgets if they exist
        if hasattr(self, "player_theme_chip") and self.player_theme_chip.winfo_exists():
            self.player_theme_chip.configure(text=f"{self._t('theme_label', '模板')}: {theme_name}")

        if hasattr(self, "global_theme_dropdown") and self.global_theme_dropdown.winfo_exists():
            self.global_theme_dropdown.set(theme_name)

    def _on_autohide_toggle(self):
        val = bool(self.autohide_switch.get())
        self.config["autohide_on_pause"] = val
        save_config(self.config)
        if hasattr(self, "settings_autohide_switch") and self.settings_autohide_switch.winfo_exists():
            if val:
                self.settings_autohide_switch.select()
            else:
                self.settings_autohide_switch.deselect()
        self._refresh_all_urls()
        self.show_inapp_toast(self._t("autohide_enabled", "暫停時自動隱藏已開啟") if val else self._t("autohide_disabled", "暫停時自動隱藏已關閉"))

    def _on_autohide_toggle_settings(self):
        val = bool(self.settings_autohide_switch.get())
        self.config["autohide_on_pause"] = val
        save_config(self.config)
        if hasattr(self, "autohide_switch") and self.autohide_switch.winfo_exists():
            if val:
                self.autohide_switch.select()
            else:
                self.autohide_switch.deselect()
        self._refresh_all_urls()
        self.show_inapp_toast(self._t("autohide_enabled", "暫停時自動隱藏已開啟") if val else self._t("autohide_disabled", "暫停時自動隱藏已關閉"))

    def _refresh_all_urls(self):
        if hasattr(self, "global_url_entry") and self.global_url_entry.winfo_exists():
            self.global_url_entry.configure(state="normal")
            self.global_url_entry.delete(0, "end")
            self.global_url_entry.insert(0, self._get_global_overlay_url())
            self.global_url_entry.configure(state="readonly")

        if hasattr(self, "gallery_url_entries"):
            for tid, entry in self.gallery_url_entries.items():
                if entry.winfo_exists():
                    entry.configure(state="normal")
                    entry.delete(0, "end")
                    entry.insert(0, self._get_theme_url(tid))
                    entry.configure(state="readonly")

    def _on_apply_port(self):
        try:
            p = int(self.port_entry.get().strip())
            if 1024 <= p <= 65535:
                self.config["port"] = p
                save_config(self.config)
                if self.on_port_change_callback:
                    self.on_port_change_callback(p)
                self._refresh_all_urls()
                self.show_inapp_toast(self._t("port_updated_toast", f"端口已更新為 {p}！").format(port=p))
            else:
                self.show_inapp_toast(self._t("port_error", "端口號必須介於 1024 至 65535 之間"))
        except ValueError:
            self.show_inapp_toast(self._t("port_error", "端口號必須介於 1024 至 65535 之間"))

    def _on_language_changed(self, chosen_name):
        selected_code = "zh_TW"
        for name, code in LANGUAGE_OPTIONS:
            if name == chosen_name:
                selected_code = code
                break

        if selected_code != self.current_lang:
            self.current_lang = selected_code
            self.config["language"] = selected_code
            save_config(self.config)
            self.font_family = get_ui_font_family(selected_code)
            self._build_ui()

    def _open_shortcuts_folder(self):
        folder = os.path.join(self.assets_dir, "obs_shortcuts")
        if os.path.exists(folder):
            os.startfile(folder)

    # -------------------------------------------------------------
    # Media State Updates
    # -------------------------------------------------------------
    def update_media_display(self, media_data):
        """Called dynamically by backend observer whenever music plays/pauses."""
        # Ensure thread-safety: dispatch to Tkinter main thread if called from async worker thread
        if threading.current_thread() is not threading.main_thread():
            self.after(0, self.update_media_display, media_data)
            return

        self.latest_media_data = media_data
        if not media_data:
            return

        title = media_data.get("title") or self._t("waiting_media", "等待媒體播放中...")
        artist = media_data.get("artist") or self._t("play_instruction", "在 YouTube、YouTube Music 或 Spotify 播放音樂")
        status = (media_data.get("status") or "").strip().lower()
        pos = media_data.get("position", 0)
        dur = media_data.get("duration", 0)
        has_media = media_data.get("has_media", False)
        thumb_b64 = media_data.get("thumbnail")

        # Update Standard Dashboard Page widgets if active (with state-diffing to eliminate redundant Tkinter canvas redraws)
        if hasattr(self, "track_title_label") and self.track_title_label and self.track_title_label.winfo_exists():
            if title != self._last_rendered_title:
                self.track_title_label.configure(text=title)
                self._last_rendered_title = title
            if artist != self._last_rendered_artist:
                self.track_artist_label.configure(text=artist)
                self._last_rendered_artist = artist

            # Update Notion Pastel Status Badge only when status changes
            if status != self._last_rendered_status and hasattr(self, "status_badge") and self.status_badge.winfo_exists():
                self._last_rendered_status = status
                if status == "playing":
                    self.status_badge.configure(fg_color=TAG_MINT_BG, border_color=TAG_MINT_BORDER)
                    self.status_badge_text.configure(text=self._t("status_playing", "播放中"), text_color=TAG_MINT_TEXT)
                elif status == "paused":
                    self.status_badge.configure(fg_color=TAG_LAVENDER_BG, border_color=TAG_LAVENDER_BORDER)
                    self.status_badge_text.configure(text=self._t("status_paused", "已暫停"), text_color=TAG_LAVENDER_TEXT)
                else:
                    self.status_badge.configure(fg_color=TAG_PEACH_BG, border_color=TAG_PEACH_BORDER)
                    self.status_badge_text.configure(text=self._t("status_idle", "閒置"), text_color=TAG_PEACH_TEXT)

            # Progress Bar
            if hasattr(self, "progress_bar") and self.progress_bar.winfo_exists():
                frac = (pos / dur) if (dur and dur > 0) else 0.0
                self.progress_bar.set(max(0.0, min(1.0, frac)))

            # Time label only when formatted string changes
            time_str = f"{format_time_str(pos)} / {format_time_str(dur)}"
            if time_str != self._last_rendered_time_str and hasattr(self, "time_label") and self.time_label.winfo_exists():
                self.time_label.configure(text=time_str)
                self._last_rendered_time_str = time_str

            # Album Art
            if thumb_b64 and thumb_b64 != self.current_thumbnail_data:
                self.current_thumbnail_data = thumb_b64
                self._update_cover_image(thumb_b64, self.cover_label, size=(90, 90))
            elif not has_media and self.current_thumbnail_data is not None:
                self.current_thumbnail_data = None
                self._load_default_cover(target_label=self.cover_label, size=(90, 90))

    def _load_default_cover(self, target_label, size=(90, 90)):
        if not target_label or not target_label.winfo_exists():
            return
        if self._cached_default_cover_img is not None:
            target_label.configure(image=self._cached_default_cover_img)
            self._cached_cover_img = self._cached_default_cover_img
            return
        default_cover_path = os.path.join(self.assets_dir, "songIcon.jpg")
        try:
            if os.path.exists(default_cover_path):
                img = Image.open(default_cover_path).convert("RGBA").resize(size, Image.Resampling.BILINEAR)
                tk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                self._cached_default_cover_img = tk_img
                target_label.configure(image=tk_img)
                self._cached_cover_img = tk_img
        except Exception as e:
            print(f"[GUI] Error loading default cover: {e}")

    def _update_cover_image(self, b64_str, target_label, size=(90, 90)):
        if not target_label or not target_label.winfo_exists():
            return
        if not b64_str:
            self._load_default_cover(target_label=target_label, size=size)
            return
        try:
            # Strip data URI header if present (e.g. data:image/jpeg;base64,...)
            clean_b64 = b64_str.split(",", 1)[1] if "," in b64_str else b64_str
            clean_b64 = clean_b64.strip()
            img_data = base64.b64decode(clean_b64)
            if not img_data or len(img_data) < 32:
                self._load_default_cover(target_label=target_label, size=size)
                return
            bio = io.BytesIO(img_data)
            pil_img = Image.open(bio).convert("RGBA").resize(size, Image.Resampling.BILINEAR)
            tk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            target_label.configure(image=tk_img)
            self._cached_cover_img = tk_img
        except Exception:
            # Gracefully fallback to default cover image without crashing or console error
            self._load_default_cover(target_label=target_label, size=size)

    def _load_preview_thumbnail(self, previews_dir, theme_id, size=(160, 90)):
        if theme_id in self.preview_tk_images:
            return self.preview_tk_images[theme_id]
        img_path = os.path.join(previews_dir, f"{theme_id}.png")
        try:
            if os.path.exists(img_path):
                pil_img = Image.open(img_path).convert("RGBA").resize(size, Image.Resampling.BILINEAR)
            else:
                pil_img = Image.new("RGBA", size, "#1e2238")
        except Exception:
            pil_img = Image.new("RGBA", size, "#1e2238")

        tk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        self.preview_tk_images[theme_id] = tk_img
        return tk_img

    # -------------------------------------------------------------
    # GitHub Updates
    # -------------------------------------------------------------
    def _check_update_background_quiet(self):
        def _bg():
            try:
                info = check_github_update()
                if info.get("has_update"):
                    self.after(0, lambda: self._show_update_available_banner(info))
            except Exception:
                pass
        threading.Thread(target=_bg, daemon=True).start()

    def _show_update_available_banner(self, info):
        latest = info.get("latest_version")
        if hasattr(self, "hero_status_chip") and self.hero_status_chip.winfo_exists():
            self.hero_status_chip.configure(
                text=f"  {self._t('update_available_badge', '發現新版本')}: {latest}  ",
                fg_color=TAG_YELLOW_BG,
                text_color=TAG_YELLOW_TEXT
            )
            try:
                self.hero_status_chip.bind("<Button-1>", lambda e: self._open_update_dialog())
            except Exception:
                pass

    def _on_check_update_clicked(self):
        self._open_update_dialog()

    def _open_update_dialog(self):
        if hasattr(self, "_update_dialog") and self._update_dialog and self._update_dialog.winfo_exists():
            self._update_dialog.focus()
            return
        self._update_dialog = UpdateDialog(self)

    # -------------------------------------------------------------
    # Window Close & System Tray
    # -------------------------------------------------------------
    def _on_close(self):
        if self._exit_dialog is not None and self._exit_dialog.winfo_exists():
            self._exit_dialog.focus()
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(self._t("close_dialog_title", "關閉程式確認"))
        dialog.geometry("440x210")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color=NOTION_SURFACE)
        self._exit_dialog = dialog

        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 440) // 2
        y = self.winfo_y() + (self.winfo_height() - 210) // 2
        dialog.geometry(f"+{x}+{y}")

        content_box = ctk.CTkFrame(dialog, fg_color="transparent")
        content_box.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            content_box,
            text=self._t("close_dialog_title", "關閉程式確認"),
            font=self._font(14, "bold"),
            text_color=NOTION_INK
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            content_box,
            text=self._t("close_dialog_msg", "請問您要將程式最小化至系統匣（以保持 OBS 音樂顯示正常運作），還是完全退出程式？"),
            font=self._font(11),
            text_color=NOTION_STEEL,
            wraplength=390,
            justify="left"
        ).pack(anchor="w", pady=(0, 18))

        btn_box = ctk.CTkFrame(content_box, fg_color="transparent")
        btn_box.pack(fill="x", side="bottom")

        def _do_minimize():
            dialog.destroy()
            self._exit_dialog = None
            self._minimize_to_tray()

        def _do_exit():
            dialog.destroy()
            self._exit_dialog = None
            self._full_exit()

        def _do_cancel():
            dialog.destroy()
            self._exit_dialog = None

        ctk.CTkButton(
            btn_box,
            text=self._t("btn_minimize_tray", "縮小至系統匣"),
            font=self._font(11, "bold"),
            height=34,
            corner_radius=8,
            fg_color=NOTION_PURPLE,
            hover_color=NOTION_PURPLE_HOVER,
            command=_do_minimize
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text=self._t("btn_exit_app", "完全退出程式"),
            font=self._font(11),
            height=34,
            corner_radius=8,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            command=_do_exit
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text=self._t("btn_cancel", "取消"),
            font=self._font(11),
            height=34,
            corner_radius=8,
            fg_color="#242424",
            hover_color="#303030",
            border_width=1,
            border_color=NOTION_HAIRLINE_STRONG,
            command=_do_cancel
        ).pack(side="right")

    def _minimize_to_tray(self):
        self.withdraw()
        self.show_inapp_toast(self._t("minimized_toast", "已最小化至系統匣，可在右下角圖示隨時開啟"))
        if not self.tray_icon:
            self._create_tray_icon()

    def _create_tray_icon(self):
        icon_path = os.path.join(self.assets_dir, "songIcon.jpg")
        try:
            pil_icon = Image.open(icon_path) if os.path.exists(icon_path) else Image.new("RGB", (64, 64), "#5645d4")
        except Exception:
            pil_icon = Image.new("RGB", (64, 64), "#5645d4")

        menu = pystray.Menu(
            item(self._t("app_title", "OBS Real-Time Music Display"), self._restore_from_tray, default=True),
            item(self._t("btn_exit_app", "完全退出"), self._full_exit)
        )
        self.tray_icon = pystray.Icon("OBSMusicDisplay", pil_icon, "OBS Music Display", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _restore_from_tray(self, icon=None, item=None):
        self.after(0, self._restore_main_window)

    def _restore_main_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _full_exit(self, icon=None, item=None):
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        if self.on_exit_callback:
            self.on_exit_callback()
        self.after(50, self.destroy)
