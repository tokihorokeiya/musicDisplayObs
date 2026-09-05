import io
import base64
import os
import sys
import subprocess
import webbrowser
import threading
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item

# Native Windows OLE drag-and-drop into OBS Studio (UniformResourceLocator / URL)
from ole_drag import setup_native_drag_and_drop
from i18n import get_text, get_theme_info, TRANSLATIONS
from config import save_config

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
    "dynamic_island"
]

def get_ui_font_family(lang):
    if lang == "ja":
        return "Yu Gothic UI"
    elif lang == "ko":
        return "Malgun Gothic"
    elif lang == "zh_TW":
        return "Microsoft JhengHei UI"
    elif lang == "th":
        return "Leelawadee UI"
    return "Segoe UI"


RESOLUTION_MODES = [
    ("1920 × 700 (Stream Banner / 橫幅模式)", "1920x700", "&w=1920&h=700&mode=1920x700"),
    ("1000 × 400 (Compact Widget / 精簡小組件)", "1000x400", "&w=1000&h=400"),
    ("1920 × 1080 (Full Screen Bottom / 底部全螢幕)", "1920x1080", "&w=1920&h=1080&pos=bottom")
]

# 8 Major Languages (Excluding Simplified Chinese)
# 14 Major Global Languages (Excluding Simplified Chinese)
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

class AppGUI(ctk.CTk):
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

        self.title("Real-Time Music Display for OBS Studio")
        self.geometry("980x820")
        self.minsize(900, 740)

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
        self.tray_icon = None
        self.preview_tk_images = {}
        self.toast_timer = None
        self.latest_media_data = None
        self.font_family = get_ui_font_family(self.current_lang)

        # Dynamic widget placeholders
        self.track_title_label = None
        self.track_artist_label = None
        self.time_label = None
        self.progress_bar = None
        self.status_badge = None
        self.cover_label = None

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _font(self, size, weight="normal"):
        return ctk.CTkFont(family=self.font_family, size=size, weight=weight)

    def _t(self, key, default=""):
        return get_text(self.current_lang, key, default)

    def _get_res_query_param(self):
        return ""

    def show_inapp_toast(self, message):
        """Displays a clean in-app toast notification bar (NO modal alert popup!)"""
        if hasattr(self, "toast_label"):
            self.toast_label.configure(text=message)
            self.toast_frame.pack(fill="x", padx=20, pady=(0, 8), before=self.tabview)
            
            if self.toast_timer:
                self.after_cancel(self.toast_timer)
            self.toast_timer = self.after(3000, lambda: self.toast_frame.pack_forget())

    def _build_ui(self):
        self.current_thumbnail_data = None
        for child in self.winfo_children():
            child.destroy()

        # Top App Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=14, fg_color="#181824", height=64)
        self.header_frame.pack(fill="x", padx=20, pady=(16, 10))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=self._t("app_title"),
            font=self._font(19, "bold"),
            text_color="#ffffff"
        )
        self.title_label.pack(side="left", padx=20, pady=12)

        # Right side: Language selector + Status Badge
        header_right = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_right.pack(side="right", padx=16, pady=12)

        lang_names = [opt[0] for opt in LANGUAGE_OPTIONS]
        current_lang_name = next((opt[0] for opt in LANGUAGE_OPTIONS if opt[1] == self.current_lang), lang_names[0])

        # Standard multilingual font for clean rendering of Traditional Chinese and Japanese in dropdown
        multilingual_font = ctk.CTkFont(family="Microsoft JhengHei UI", size=12)
        self.lang_menu = ctk.CTkOptionMenu(
            header_right,
            values=lang_names,
            command=self._on_language_changed,
            width=210,
            height=30,
            corner_radius=8,
            font=multilingual_font,
            dropdown_font=multilingual_font,
            fg_color="#27273a",
            button_color="#373752"
        )
        self.lang_menu.set(current_lang_name)
        self.lang_menu.pack(side="left", padx=(0, 12))

        self.status_badge = ctk.CTkLabel(
            header_right,
            text=self._t("status_idle"),
            font=self._font(12, "bold"),
            text_color="#94a3b8",
            fg_color="#1e293b",
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.status_badge.pack(side="left")

        # In-App Non-blocking Toast Banner (Hidden by default)
        self.toast_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#064e3b", height=36)
        self.toast_label = ctk.CTkLabel(
            self.toast_frame,
            text="",
            font=self._font(13, "bold"),
            text_color="#6ee7b7"
        )
        self.toast_label.pack(pady=6)

        # Tabview with standard UI font for tabs
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=14,
            fg_color="#131722",
            segmented_button_selected_color="#4f46e5",
            segmented_button_unselected_color="#1e1e2d",
            segmented_button_font=self._font(13, "bold")
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.tab_playing = self.tabview.add(self._t("tab_playing"))
        self.tab_gallery = self.tabview.add(self._t("tab_gallery"))

        self._build_now_playing_tab()
        self._build_gallery_tab()

        if self.latest_media_data:
            self.update_media_display(self.latest_media_data)

    def _build_now_playing_tab(self):
        content = ctk.CTkFrame(self.tab_playing, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=10)

        # Left Column: Media Information Card
        self.media_card = ctk.CTkFrame(content, corner_radius=16, fg_color="#181824", width=420)
        self.media_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(
            self.media_card,
            text=self._t("now_playing_header"),
            font=self._font(11, "bold"),
            text_color="#6366f1"
        ).pack(anchor="w", padx=20, pady=(16, 10))

        # Album Artwork (Uses songIcon.jpg)
        self.cover_label = ctk.CTkLabel(self.media_card, text="", width=170, height=170)
        self.cover_label.pack(pady=6)
        self._set_default_thumbnail()

        # Song Title (Pure White Text & Normal Font)
        self.track_title_label = ctk.CTkLabel(
            self.media_card,
            text=self._t("waiting_media"),
            font=self._font(17, "bold"),
            text_color="#ffffff",
            wraplength=380,
            justify="center"
        )
        self.track_title_label.pack(padx=16, pady=(10, 4))

        # Artist(s) / Singers
        self.track_artist_label = ctk.CTkLabel(
            self.media_card,
            text=self._t("play_instruction"),
            font=self._font(13),
            text_color="#94a3b8",
            wraplength=380,
            justify="center"
        )
        self.track_artist_label.pack(padx=16, pady=(0, 10))

        # Progress bar & Timestamp
        self.progress_frame = ctk.CTkFrame(self.media_card, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=26, pady=(0, 16))

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=8, corner_radius=4, progress_color="#6366f1")
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 4))

        self.time_label = ctk.CTkLabel(
            self.progress_frame,
            text="00:00 / 00:00",
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color="#cbd5e1"
        )
        self.time_label.pack()

        # Right Column: Global Active Overlay & Server Settings
        self.controls_card = ctk.CTkFrame(content, corner_radius=16, fg_color="#181824", width=390)
        self.controls_card.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # --- Section 1: Global Active Overlay (OBS Auto-Sync) ---
        ctk.CTkLabel(
            self.controls_card,
            text=self._t("global_theme_header", "🌐 全域使用中模板 (OBS 自動同步)"),
            font=self._font(13, "bold"),
            text_color="#6366f1"
        ).pack(anchor="w", padx=20, pady=(16, 6))

        global_box = ctk.CTkFrame(self.controls_card, corner_radius=12, fg_color="#12121c")
        global_box.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(
            global_box,
            text=self._t("global_theme_desc"),
            font=self._font(11),
            text_color="#94a3b8",
            wraplength=350,
            justify="left"
        ).pack(anchor="w", padx=14, pady=(12, 8))

        # Active Theme Dropdown Row
        theme_row = ctk.CTkFrame(global_box, fg_color="transparent")
        theme_row.pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkLabel(
            theme_row,
            text=self._t("active_theme_label", "目前全域模板："),
            font=self._font(12, "bold")
        ).pack(side="left")

        current_theme_id = self.config.get("selected_theme", "glassmorphism")
        current_theme_name, _ = get_theme_info(self.current_lang, current_theme_id)
        theme_display_names = [get_theme_info(self.current_lang, tid)[0] for tid in THEME_IDS]

        theme_dropdown_font = self._font(12)
        self.global_theme_dropdown = ctk.CTkOptionMenu(
            theme_row,
            values=theme_display_names,
            width=220,
            height=30,
            corner_radius=8,
            font=theme_dropdown_font,
            dropdown_font=theme_dropdown_font,
            fg_color="#312e81",
            button_color="#4338ca",
            button_hover_color="#4f46e5",
            command=self._on_global_theme_selected
        )
        try:
            self.global_theme_dropdown._dropdown_menu.configure(font=theme_dropdown_font)
        except Exception:
            pass
        self.global_theme_dropdown.set(current_theme_name)
        self.global_theme_dropdown.pack(side="right")

        # Global URL Entry
        global_url = self._get_global_overlay_url()
        self.global_url_entry = ctk.CTkEntry(
            global_box,
            height=28,
            font=ctk.CTkFont(size=11),
            text_color="#a5b4fc",
            fg_color="#0a0a10"
        )
        self.global_url_entry.insert(0, global_url)
        self.global_url_entry.configure(state="readonly")
        self.global_url_entry.pack(fill="x", padx=14, pady=(0, 6))
        self._setup_drag_on_widget(self.global_url_entry, self._get_global_overlay_url)

        # Global Drag Hint Badge
        drag_global_badge = tk.Label(
            global_box,
            text=f"⠿ {self._t('drag_hint')}",
            bg="#1e293b",
            fg="#4ade80",
            font=(self.font_family, 10, "bold"),
            padx=8,
            pady=2,
            cursor="hand2"
        )
        drag_global_badge.pack(anchor="w", padx=14, pady=(0, 8))
        self._setup_drag_on_widget(drag_global_badge, self._get_global_overlay_url)

        # Global Action Buttons
        global_btn_row = ctk.CTkFrame(global_box, fg_color="transparent")
        global_btn_row.pack(fill="x", padx=14, pady=(0, 12))

        self.btn_copy_global = ctk.CTkButton(
            global_btn_row,
            text=self._t("btn_copy_global_url", "📋 複製全域網址"),
            height=32,
            corner_radius=8,
            font=self._font(12, "bold"),
            fg_color="#4f46e5",
            hover_color="#4338ca",
            command=self._copy_global_url
        )
        self.btn_copy_global.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_preview_global = ctk.CTkButton(
            global_btn_row,
            text=self._t("btn_preview_global", "👁️ 預覽"),
            width=70,
            height=32,
            corner_radius=8,
            font=self._font(12),
            fg_color="#27273a",
            hover_color="#373752",
            command=lambda: webbrowser.open(self._get_global_overlay_url())
        )
        self.btn_preview_global.pack(side="right", padx=(4, 0))

        # --- Section 2: Server Settings ---
        ctk.CTkLabel(
            self.controls_card,
            text=self._t("server_settings_header", "⚙️ 系統與伺服器設定"),
            font=self._font(13, "bold"),
            text_color="#6366f1"
        ).pack(anchor="w", padx=20, pady=(4, 6))

        server_box = ctk.CTkFrame(self.controls_card, corner_radius=12, fg_color="#12121c")
        server_box.pack(fill="x", padx=20, pady=(0, 12))

        port_row = ctk.CTkFrame(server_box, fg_color="transparent")
        port_row.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            port_row,
            text=self._t("server_port"),
            font=self._font(12, "bold")
        ).pack(side="left")

        self.port_entry = ctk.CTkEntry(port_row, width=80, height=30, corner_radius=8)
        self.port_entry.insert(0, str(self.config.get("port", 11150)))
        self.port_entry.pack(side="left", padx=10)

        self.port_save_btn = ctk.CTkButton(
            port_row,
            text=self._t("apply_port"),
            width=80,
            height=30,
            corner_radius=8,
            font=self._font(12),
            fg_color="#374151",
            hover_color="#4b5563",
            command=self._apply_port
        )
        self.port_save_btn.pack(side="right")

        # Quick navigation button to Gallery
        self.go_gallery_btn = ctk.CTkButton(
            self.controls_card,
            text=self._t("btn_go_gallery", "🎨 前往「模板庫」探索各樣式 ➔"),
            height=36,
            corner_radius=8,
            font=self._font(12, "bold"),
            fg_color="#1e1e2f",
            hover_color="#2d2d44",
            border_width=1,
            border_color="#4338ca",
            command=lambda: self.tabview.set(self._t("tab_gallery"))
        )
        self.go_gallery_btn.pack(fill="x", padx=20, pady=(0, 16))

    def _build_gallery_tab(self):
        top_bar = ctk.CTkFrame(self.tab_gallery, corner_radius=12, fg_color="#181824")
        top_bar.pack(fill="x", padx=10, pady=(10, 12))

        ctk.CTkLabel(
            top_bar,
            text=self._t("drag_banner_text"),
            font=self._font(12, "bold"),
            text_color="#a5b4fc"
        ).pack(side="left", padx=16, pady=12)

        # Auto-Hide Toggle moved to template gallery top bar!
        self.autohide_switch = ctk.CTkSwitch(
            top_bar,
            text=self._t("autohide_switch"),
            font=self._font(12, "bold"),
            progress_color="#4f46e5",
            command=self._on_autohide_toggle
        )
        if self.config.get("autohide_on_pause", False):
            self.autohide_switch.select()
        self.autohide_switch.pack(side="right", padx=16, pady=10)

        # Scrollable gallery
        self.scrollable_gallery = ctk.CTkScrollableFrame(self.tab_gallery, fg_color="transparent")
        self.scrollable_gallery.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        previews_dir = os.path.join(self.assets_dir, "static", "previews")
        self.gallery_url_entries = {}

        for i, theme_id in enumerate(THEME_IDS, 1):
            name, desc = get_theme_info(self.current_lang, theme_id)
            url = self._get_theme_url(theme_id)

            card = ctk.CTkFrame(self.scrollable_gallery, corner_radius=14, fg_color="#181824")
            card.pack(fill="x", pady=8, padx=6)

            # Left: Preview Image Frame
            preview_container = tk.Frame(card, bg="#0f111a", width=340, height=136)
            preview_container.pack(side="left", padx=14, pady=12)
            preview_container.pack_propagate(False)

            preview_img_path = os.path.join(previews_dir, f"{theme_id}.png")
            photo_img = None

            if os.path.exists(preview_img_path):
                try:
                    pil_img = Image.open(preview_img_path)
                    pil_img = pil_img.resize((340, 136), Image.Resampling.LANCZOS)
                    photo_img = ImageTk.PhotoImage(pil_img)
                    self.preview_tk_images[theme_id] = photo_img
                except Exception:
                    pass

            if photo_img:
                img_label = tk.Label(
                    preview_container,
                    image=photo_img,
                    bg="#0f111a",
                    cursor="hand2"
                )
                img_label.pack(fill="both", expand=True)
            else:
                img_label = tk.Label(
                    preview_container,
                    text=f"({name})",
                    fg="#6366f1",
                    bg="#0f111a",
                    font=("Segoe UI", 12, "bold"),
                    cursor="hand2"
                )
                img_label.pack(fill="both", expand=True)

            # Bind native drag on the preview image, container, and entry (click=copy, drag=add to OBS)
            self._setup_drag_on_widget(img_label, lambda t=theme_id: self._get_theme_url(t))
            self._setup_drag_on_widget(preview_container, lambda t=theme_id: self._get_theme_url(t))

            # Center: Information & Direct URL field
            center_box = ctk.CTkFrame(card, fg_color="transparent")
            center_box.pack(side="left", fill="both", expand=True, padx=12, pady=12)

            ctk.CTkLabel(
                center_box,
                text=f"{i}. {name}",
                font=self._font(15, "bold"),
                text_color="#ffffff"
            ).pack(anchor="w")

            ctk.CTkLabel(
                center_box,
                text=desc,
                font=self._font(12),
                text_color="#94a3b8",
                wraplength=270,
                justify="left"
            ).pack(anchor="w", pady=(2, 4))

            # Dedicated Drag Handle Badge
            drag_handle_box = tk.Label(
                center_box,
                text=f"⠿ {self._t('drag_hint')}",
                bg="#1e293b",
                fg="#4ade80",
                font=(self.font_family, 10, "bold"),
                padx=8,
                pady=2,
                cursor="hand2"
            )
            drag_handle_box.pack(anchor="w", pady=(0, 4))
            self._setup_drag_on_widget(drag_handle_box, lambda t=theme_id: self._get_theme_url(t))

            drag_entry = ctk.CTkEntry(
                center_box,
                height=26,
                font=ctk.CTkFont(size=11),
                text_color="#a5b4fc",
                fg_color="#12121c"
            )
            drag_entry.insert(0, url)
            drag_entry.configure(state="readonly")
            drag_entry.pack(fill="x", pady=(2, 0))
            self._setup_drag_on_widget(drag_entry, lambda t=theme_id: self._get_theme_url(t))
            self.gallery_url_entries[theme_id] = drag_entry

            # Right: Action Buttons
            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(side="right", padx=14, pady=12)

            copy_btn = ctk.CTkButton(
                btn_box,
                text=self._t("copy_url_btn"),
                width=100,
                height=32,
                corner_radius=8,
                font=self._font(12),
                fg_color="#4f46e5",
                hover_color="#4338ca",
                command=lambda t=theme_id: self._copy_specific_theme(t)
            )
            copy_btn.pack(pady=3)

            preview_btn = ctk.CTkButton(
                btn_box,
                text=self._t("preview_btn"),
                width=100,
                height=30,
                corner_radius=8,
                font=self._font(12),
                fg_color="#27273a",
                hover_color="#373752",
                command=lambda t=theme_id: webbrowser.open(self._get_theme_url(t))
            )
            preview_btn.pack(pady=3)

            set_btn = ctk.CTkButton(
                btn_box,
                text=self._t("set_active_btn"),
                width=100,
                height=30,
                corner_radius=8,
                font=self._font(12),
                fg_color="#374151",
                hover_color="#4b5563",
                command=lambda t=theme_id: self._set_theme_from_gallery(t)
            )
            set_btn.pack(pady=3)

    def _setup_drag_on_widget(self, widget, get_url_func):
        """Sets up native Windows OLE drag-and-drop into OBS Studio as a Browser Source with direct HTTP URL."""
        setup_native_drag_and_drop(
            widget=widget,
            get_url_func=get_url_func,
            on_drag_success_callback=lambda: self.show_inapp_toast(self._t("drag_done_toast", "✔ 已拖曳至 OBS！")),
            on_click_callback=self._copy_url_to_clipboard
        )

    def _copy_url_to_clipboard(self, url):
        if not url:
            return
        self.clipboard_clear()
        self.clipboard_append(url)
        self.show_inapp_toast(self._t("copied_toast"))

    def _on_language_changed(self, chosen_label):
        lang_code = next((opt[1] for opt in LANGUAGE_OPTIONS if opt[0] == chosen_label), "zh_TW")
        self.current_lang = lang_code
        self.config["language"] = lang_code
        self.font_family = get_ui_font_family(lang_code)
        save_config(self.config)
        self._build_ui()

    def _get_global_overlay_url(self):
        port = self.config.get("port", 11150)
        autohide = 1 if self.config.get("autohide_on_pause", False) else 0
        return f"http://localhost:{port}/overlay?autohide={autohide}"

    def _get_theme_url(self, theme_id):
        port = self.config.get("port", 11150)
        autohide = 1 if self.config.get("autohide_on_pause", False) else 0
        return f"http://localhost:{port}/overlay?theme={theme_id}&autohide={autohide}"

    def _update_all_url_fields(self):
        """Refreshes all displayed URL entry fields when port or autohide changes."""
        if hasattr(self, "global_url_entry") and self.global_url_entry and self.global_url_entry.winfo_exists():
            g_url = self._get_global_overlay_url()
            self.global_url_entry.configure(state="normal")
            self.global_url_entry.delete(0, "end")
            self.global_url_entry.insert(0, g_url)
            self.global_url_entry.configure(state="readonly")

        for tid, entry in getattr(self, "gallery_url_entries", {}).items():
            if entry and entry.winfo_exists():
                new_url = self._get_theme_url(tid)
                entry.configure(state="normal")
                entry.delete(0, "end")
                entry.insert(0, new_url)
                entry.configure(state="readonly")

    def _set_default_thumbnail(self):
        # songIcon.jpg is only used in template gallery, NOT on the main page.
        # Main page has NO placeholder/temp image - kept clean and empty as requested.
        if hasattr(self, "cover_label") and self.cover_label and self.cover_label.winfo_exists():
            if hasattr(self, "_cached_cover_img") and self._cached_cover_img:
                self.cover_label.configure(image=self._cached_cover_img, text="")
            else:
                empty_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
                ctk_empty = ctk.CTkImage(light_image=empty_img, dark_image=empty_img, size=(1, 1))
                self.cover_label.configure(image=ctk_empty, text="")

    def _get_current_obs_url(self):
        return self._get_global_overlay_url()

    def _copy_obs_url(self):
        self._copy_global_url()

    def _copy_global_url(self):
        url = self._get_global_overlay_url()
        self.clipboard_clear()
        self.clipboard_append(url)
        self.show_inapp_toast(self._t("copied_toast"))
        if hasattr(self, "btn_copy_global") and self.btn_copy_global and self.btn_copy_global.winfo_exists():
            self.btn_copy_global.configure(text=f"✔ {self._t('copied_title')}", fg_color="#10b981")
            self.after(2000, lambda: self.btn_copy_global.configure(text=self._t("btn_copy_global_url"), fg_color="#4f46e5"))

    def _copy_specific_theme(self, theme_id, url=None):
        target_url = self._get_theme_url(theme_id)
        self.clipboard_clear()
        self.clipboard_append(target_url)
        # Non-blocking in-app notification! NO modal alert popup window!
        self.show_inapp_toast(self._t("copied_toast"))

    def _set_theme_from_gallery(self, theme_id):
        self.config["selected_theme"] = theme_id
        save_config(self.config)
        name, _ = get_theme_info(self.current_lang, theme_id)
        if hasattr(self, "global_theme_dropdown") and self.global_theme_dropdown and self.global_theme_dropdown.winfo_exists():
            self.global_theme_dropdown.set(name)
        if self.on_theme_change_callback:
            self.on_theme_change_callback(theme_id)
        self.show_inapp_toast(self._t("set_active_toast", f"⭐ 已將「{name}」設為全域使用中模板！").format(name=name))

    def _on_global_theme_selected(self, chosen_display_name):
        for tid in THEME_IDS:
            name, _ = get_theme_info(self.current_lang, tid)
            if name == chosen_display_name:
                self.config["selected_theme"] = tid
                save_config(self.config)
                if self.on_theme_change_callback:
                    self.on_theme_change_callback(tid)
                self.show_inapp_toast(self._t("set_active_toast", f"⭐ 已將「{name}」設為全域使用中模板！").format(name=name))
                break

    def _apply_port(self):
        try:
            new_port = int(self.port_entry.get().strip())
            if new_port < 1024 or new_port > 65535:
                self.show_inapp_toast(self._t("port_error"))
                return
            self.config["port"] = new_port
            save_config(self.config)
            self._update_all_url_fields()
            if self.on_port_change_callback:
                self.on_port_change_callback(new_port)
            self.show_inapp_toast(self._t("port_updated_toast").format(port=new_port))
        except Exception as e:
            self.show_inapp_toast(str(e))

    def _on_autohide_toggle(self):
        enabled = bool(self.autohide_switch.get())
        self.config["autohide_on_pause"] = enabled
        save_config(self.config)
        self._update_all_url_fields()

    def update_media_display(self, data):
        self.latest_media_data = data
        def _update():
            if not data:
                return
            if getattr(self, "track_title_label", None) is None:
                return
            try:
                if not self.track_title_label.winfo_exists():
                    return
            except Exception:
                return

            has_media = data.get("has_media", False)
            title = data.get("title", "") or (self._t("waiting_media") if not has_media else "Untitled Track")
            artist = data.get("artist", "") or (self._t("play_instruction") if not has_media else "Unknown Artist")
            status = data.get("status", "Stopped")

            try:
                self.track_title_label.configure(text=title)
                if hasattr(self, "track_artist_label") and self.track_artist_label and self.track_artist_label.winfo_exists():
                    self.track_artist_label.configure(text=artist)

                pos = data.get("position", 0)
                dur = data.get("duration", 0)
                cur_str = format_time_str(pos)
                dur_str = format_time_str(dur) if dur > 0 else "--:--"
                if hasattr(self, "time_label") and self.time_label and self.time_label.winfo_exists():
                    self.time_label.configure(text=f"{cur_str} / {dur_str}")
                
                if hasattr(self, "progress_bar") and self.progress_bar and self.progress_bar.winfo_exists():
                    if dur > 0:
                        self.progress_bar.set(min(1.0, max(0.0, pos / dur)))
                    else:
                        self.progress_bar.set(0)

                if hasattr(self, "status_badge") and self.status_badge and self.status_badge.winfo_exists():
                    if status == "Playing":
                        self.status_badge.configure(text=self._t("status_playing"), text_color="#4ade80", fg_color="#143422")
                    elif status == "Paused":
                        self.status_badge.configure(text=self._t("status_paused"), text_color="#facc15", fg_color="#362d08")
                    else:
                        self.status_badge.configure(text=self._t("status_idle"), text_color="#94a3b8", fg_color="#1e293b")

                thumb_b64 = data.get("thumbnail", "")
                if hasattr(self, "cover_label") and self.cover_label and self.cover_label.winfo_exists():
                    if thumb_b64:
                        if thumb_b64 != self.current_thumbnail_data or not getattr(self, "_cached_cover_img", None):
                            self.current_thumbnail_data = thumb_b64
                            try:
                                raw_b64 = thumb_b64.split(",", 1)[1] if "," in thumb_b64 else thumb_b64
                                img_bytes = base64.b64decode(raw_b64)
                                pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                                pil_img = pil_img.resize((170, 170), Image.Resampling.LANCZOS)
                                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(170, 170))
                                self._cached_cover_img = ctk_img
                                self.cover_label.configure(image=ctk_img, text="")
                            except Exception:
                                self._cached_cover_img = None
                                self._set_default_thumbnail()
                        elif hasattr(self, "_cached_cover_img") and self._cached_cover_img:
                            self.cover_label.configure(image=self._cached_cover_img, text="")
                    else:
                        self._cached_cover_img = None
                        self.current_thumbnail_data = None
                        self._set_default_thumbnail()
            except Exception:
                pass

        self.after(0, _update)

    def _on_close(self):
        self._show_exit_dialog()

    def _show_exit_dialog(self):
        if hasattr(self, "_exit_dialog") and self._exit_dialog and self._exit_dialog.winfo_exists():
            self._exit_dialog.lift()
            self._exit_dialog.focus_force()
            return

        dialog = ctk.CTkToplevel(self)
        self._exit_dialog = dialog
        dialog.title(self._t("close_dialog_title", "Close Application"))
        dialog.geometry("490x230")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.transient(self)

        # Center over main window
        try:
            x = self.winfo_x() + (self.winfo_width() // 2) - 245
            y = self.winfo_y() + (self.winfo_height() // 2) - 115
            dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        content = ctk.CTkFrame(dialog, fg_color="#181824", corner_radius=14)
        content.pack(fill="both", expand=True, padx=12, pady=12)

        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            header_frame,
            text=f"❓ {self._t('close_dialog_title', 'Close Application')}",
            font=self._font(15, "bold"),
            text_color="#ffffff"
        ).pack(anchor="w")

        ctk.CTkLabel(
            content,
            text=self._t("close_dialog_msg", "Do you want to minimize to the system tray to keep music displaying in OBS, or exit the application completely?"),
            font=self._font(12),
            text_color="#cbd5e1",
            wraplength=430,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 16))

        btn_row = ctk.CTkFrame(content, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(6, 12))

        def on_minimize():
            dialog.destroy()
            self.withdraw()
            self._setup_tray()
            self.show_inapp_toast(self._t("minimized_toast", "Minimized to system tray"))

        def on_exit():
            dialog.destroy()
            self._quit_app()

        def on_cancel():
            dialog.destroy()

        exit_btn = ctk.CTkButton(
            btn_row,
            text=self._t("btn_exit_app", "Exit Completely"),
            font=self._font(12, "bold"),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            width=130,
            height=34,
            corner_radius=8,
            command=on_exit
        )
        exit_btn.pack(side="right", padx=(6, 0))

        min_btn = ctk.CTkButton(
            btn_row,
            text=self._t("btn_minimize_tray", "Minimize to Tray"),
            font=self._font(12, "bold"),
            fg_color="#4f46e5",
            hover_color="#4338ca",
            width=135,
            height=34,
            corner_radius=8,
            command=on_minimize
        )
        min_btn.pack(side="right", padx=(6, 0))

        cancel_btn = ctk.CTkButton(
            btn_row,
            text=self._t("btn_cancel", "Cancel"),
            font=self._font(12),
            fg_color="#374151",
            hover_color="#4b5563",
            width=80,
            height=34,
            corner_radius=8,
            command=on_cancel
        )
        cancel_btn.pack(side="right")

        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        dialog.grab_set()

    def _setup_tray(self):
        if self.tray_icon:
            return
        img = Image.new("RGB", (64, 64), color=(99, 102, 241))
        menu = (
            item("Open Controller", self._restore_from_tray),
            item("Copy Global OBS URL", self._copy_obs_url),
            item("Exit", self._quit_app)
        )
        self.tray_icon = pystray.Icon("OBSMusicDisplay", img, "OBS Music Display", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _restore_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.after(0, self.deiconify)

    def _quit_app(self, icon=None, item=None):
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
        if hasattr(self, "on_exit_callback") and self.on_exit_callback:
            try:
                self.on_exit_callback()
            except Exception:
                pass
        self.after(0, self.destroy)
