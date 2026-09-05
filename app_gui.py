import io
import base64
import os
import subprocess
import webbrowser
import threading
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item

# Import TkinterDnD for native Windows OLE drag-and-drop into OBS
from tkinterdnd2 import TkinterDnD, DND_FILES, DND_TEXT, COPY
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
        return "Yu Gothic"
    elif lang == "ko":
        return "Malgun Gothic"
    elif lang == "zh_TW":
        return "Microsoft JhengHei"
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

def generate_obs_shortcuts(port, base_dir, res_param):
    shortcuts_dir = os.path.join(base_dir, "obs_shortcuts")
    os.makedirs(shortcuts_dir, exist_ok=True)
    
    file_map = {}
    for i, theme_id in enumerate(THEME_IDS, 1):
        filename = f"{i:02d}_{theme_id}.url"
        filepath = os.path.join(shortcuts_dir, filename)
        url = f"http://localhost:{port}/overlay?theme={theme_id}{res_param}"
        content = f"[InternetShortcut]\nURL={url}\n"
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass
        file_map[theme_id] = filepath
    return shortcuts_dir, file_map


class DnDCustomTk(ctk.CTk, TkinterDnD.DnDWrapper):
    """CustomTkinter root window integrated with TkinterDnD OLE drag-and-drop"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


class AppGUI(DnDCustomTk):
    def __init__(self, config, on_port_change_callback, on_theme_change_callback):
        super().__init__()
        self.config = config
        self.on_port_change_callback = on_port_change_callback
        self.on_theme_change_callback = on_theme_change_callback
        self.current_lang = self.config.get("language", "zh_TW")
        if self.current_lang not in TRANSLATIONS:
            self.current_lang = "zh_TW"

        self.current_res_mode = self.config.get("resolution_mode", "1920x700")

        self.title("Real-Time Music Display for OBS Studio")
        self.geometry("980x820")
        self.minsize(900, 740)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.shortcuts_dir, self.shortcut_file_map = generate_obs_shortcuts(
            self.config.get("port", 11150), self.base_dir, self._get_res_query_param()
        )

        self.current_thumbnail_data = None
        self.tray_icon = None
        self.preview_tk_images = {}
        self.toast_timer = None
        self.font_family = get_ui_font_family(self.current_lang)

    def _font(self, size, weight="normal"):
        return ctk.CTkFont(family=self.font_family, size=size, weight=weight)

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _t(self, key, default=""):
        return get_text(self.current_lang, key, default)

    def _get_res_query_param(self):
        for label, mode_id, param in RESOLUTION_MODES:
            if mode_id == self.current_res_mode:
                return param
        return "&w=1920&h=700&mode=1920x700"

    def show_inapp_toast(self, message):
        """Displays a clean in-app toast notification bar (NO modal alert popup!)"""
        if hasattr(self, "toast_label"):
            self.toast_label.configure(text=message)
            self.toast_frame.pack(fill="x", padx=20, pady=(0, 8), before=self.tabview)
            
            if self.toast_timer:
                self.after_cancel(self.toast_timer)
            self.toast_timer = self.after(3000, lambda: self.toast_frame.pack_forget())

    def _build_ui(self):
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

        self.lang_menu = ctk.CTkOptionMenu(
            header_right,
            values=lang_names,
            command=self._on_language_changed,
            width=210,
            height=30,
            corner_radius=8,
            font=self._font(12),
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

        # Tabview
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=14,
            fg_color="#131722",
            segmented_button_selected_color="#4f46e5",
            segmented_button_unselected_color="#1e1e2d"
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.tab_playing = self.tabview.add(self._t("tab_playing"))
        self.tab_gallery = self.tabview.add(self._t("tab_gallery"))

        self._build_now_playing_tab()
        self._build_gallery_tab()

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

        # Right Column: Controls & OBS Integration
        self.controls_card = ctk.CTkFrame(content, corner_radius=16, fg_color="#181824")
        self.controls_card.pack(side="right", fill="both", expand=True, padx=(10, 0))

        ctk.CTkLabel(
            self.controls_card,
            text=self._t("obs_section_header"),
            font=self._font(11, "bold"),
            text_color="#6366f1"
        ).pack(anchor="w", padx=20, pady=(16, 10))

        # Resolution Mode Selector
        ctk.CTkLabel(
            self.controls_card,
            text=self._t("canvas_size_label"),
            font=self._font(13, "bold")
        ).pack(anchor="w", padx=20, pady=(0, 4))

        res_labels = [r[0] for r in RESOLUTION_MODES]
        current_res_label = next((r[0] for r in RESOLUTION_MODES if r[1] == self.current_res_mode), res_labels[0])

        self.res_menu = ctk.CTkOptionMenu(
            self.controls_card,
            values=res_labels,
            command=self._on_res_mode_changed,
            height=34,
            corner_radius=8,
            font=self._font(12),
            fg_color="#27273a",
            button_color="#373752"
        )
        self.res_menu.set(current_res_label)
        self.res_menu.pack(fill="x", padx=20, pady=(0, 12))

        # Active Theme Dropdown
        ctk.CTkLabel(
            self.controls_card,
            text=self._t("active_theme"),
            font=self._font(13, "bold")
        ).pack(anchor="w", padx=20, pady=(0, 4))
        
        theme_display_names = [get_theme_info(self.current_lang, tid)[0] for tid in THEME_IDS]
        active_theme_id = self.config.get("selected_theme", "glassmorphism")
        active_display_name = get_theme_info(self.current_lang, active_theme_id)[0]

        self.theme_dropdown = ctk.CTkOptionMenu(
            self.controls_card,
            values=theme_display_names,
            command=self._on_theme_dropdown_selected,
            height=36,
            corner_radius=10,
            font=self._font(13),
            fg_color="#312e81",
            button_color="#4338ca",
            button_hover_color="#4f46e5"
        )
        self.theme_dropdown.set(active_display_name)
        self.theme_dropdown.pack(fill="x", padx=20, pady=(0, 14))

        # Quick Copy OBS Button
        self.copy_btn = ctk.CTkButton(
            self.controls_card,
            text=self._t("copy_obs_url"),
            font=self._font(14, "bold"),
            height=44,
            corner_radius=10,
            fg_color="#4f46e5",
            hover_color="#4338ca",
            command=self._copy_obs_url
        )
        self.copy_btn.pack(fill="x", padx=20, pady=(0, 6))

        ctk.CTkLabel(
            self.controls_card,
            text=self._t("obs_tip"),
            font=self._font(11),
            text_color="#94a3b8",
            wraplength=380,
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 16))

        # Server Settings Frame
        server_box = ctk.CTkFrame(self.controls_card, corner_radius=12, fg_color="#12121c")
        server_box.pack(fill="x", padx=20, pady=(0, 16))

        port_row = ctk.CTkFrame(server_box, fg_color="transparent")
        port_row.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            port_row,
            text=self._t("server_port"),
            font=self._font(13, "bold")
        ).pack(side="left")

        self.port_entry = ctk.CTkEntry(port_row, width=80, height=32, corner_radius=8)
        self.port_entry.insert(0, str(self.config.get("port", 11150)))
        self.port_entry.pack(side="left", padx=10)

        self.port_save_btn = ctk.CTkButton(
            port_row,
            text=self._t("apply_port"),
            width=90,
            height=32,
            corner_radius=8,
            font=self._font(12),
            fg_color="#374151",
            hover_color="#4b5563",
            command=self._apply_port
        )
        self.port_save_btn.pack(side="right")

        # Auto-Hide Toggle
        self.autohide_switch = ctk.CTkSwitch(
            self.controls_card,
            text=self._t("autohide_switch"),
            font=self._font(12),
            command=self._on_autohide_toggle
        )
        if self.config.get("autohide_on_pause", False):
            self.autohide_switch.select()
        self.autohide_switch.pack(anchor="w", padx=20, pady=(0, 16))

    def _build_gallery_tab(self):
        top_bar = ctk.CTkFrame(self.tab_gallery, corner_radius=12, fg_color="#181824")
        top_bar.pack(fill="x", padx=10, pady=(10, 12))

        ctk.CTkLabel(
            top_bar,
            text=self._t("drag_banner_text"),
            font=self._font(12, "bold"),
            text_color="#a5b4fc"
        ).pack(side="left", padx=16, pady=12)

        open_folder_btn = ctk.CTkButton(
            top_bar,
            text=self._t("open_folder_btn"),
            font=self._font(12, "bold"),
            height=34,
            corner_radius=8,
            fg_color="#059669",
            hover_color="#047857",
            command=self._open_shortcuts_folder
        )
        open_folder_btn.pack(side="right", padx=16, pady=10)

        # Scrollable gallery
        self.scrollable_gallery = ctk.CTkScrollableFrame(self.tab_gallery, fg_color="transparent")
        self.scrollable_gallery.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        port = self.config.get("port", 11150)
        previews_dir = os.path.join(self.base_dir, "static", "previews")
        res_param = self._get_res_query_param()

        for i, theme_id in enumerate(THEME_IDS, 1):
            name, desc = get_theme_info(self.current_lang, theme_id)
            url = f"http://localhost:{port}/overlay?theme={theme_id}{res_param}"

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
                    cursor="fleur"
                )
                img_label.pack(fill="both", expand=True)
            else:
                img_label = tk.Label(
                    preview_container,
                    text=f"Drag to OBS\n({name})",
                    fg="#6366f1",
                    bg="#0f111a",
                    font=("Segoe UI", 12, "bold"),
                    cursor="fleur"
                )
                img_label.pack(fill="both", expand=True)

            # Bind native drag on the preview image (NO alert popups on click!)
            self._setup_drag_on_widget(img_label, url, theme_id)

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

            # Dedicated Draggable Handle Badge
            drag_handle_box = tk.Label(
                center_box,
                text=f"⠿ {self._t('drag_hint')}",
                bg="#1e293b",
                fg="#4ade80",
                font=(self.font_family, 10, "bold"),
                padx=8,
                pady=2,
                cursor="fleur"
            )
            drag_handle_box.pack(anchor="w", pady=(0, 4))
            self._setup_drag_on_widget(drag_handle_box, url, theme_id)

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
                command=lambda t=theme_id, u=url: self._copy_specific_theme(t, u)
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
                command=lambda u=url: webbrowser.open(u)
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

    def _setup_drag_on_widget(self, widget, url, theme_id):
        """Sets up smooth drag-and-drop into OBS without blocking mouse clicks or opening modal dialogs"""
        shortcut_file = self.shortcut_file_map.get(theme_id, "")
        norm_shortcut = os.path.normpath(os.path.abspath(shortcut_file)) if shortcut_file else ""

        try:
            widget.drag_source_register(1, DND_FILES, DND_TEXT)
            
            def on_drag_init(event):
                if norm_shortcut and os.path.exists(norm_shortcut):
                    return (COPY, DND_FILES, norm_shortcut)
                return (COPY, DND_TEXT, url)
                
            widget.dnd_bind('<<DragInitCmd>>', on_drag_init)

            def on_drag_end(event):
                self.show_inapp_toast(self._t("drag_done_toast", "✔ Dragged into OBS!"))

            widget.dnd_bind('<<DragEndCmd>>', on_drag_end)
        except Exception as e:
            print("DnD register note:", e)

        def on_click(event):
            self.clipboard_clear()
            self.clipboard_append(url)
            self.show_inapp_toast(self._t("copied_toast"))

        widget.bind("<ButtonRelease-1>", on_click, add="+")

    def _on_language_changed(self, chosen_label):
        lang_code = next((opt[1] for opt in LANGUAGE_OPTIONS if opt[0] == chosen_label), "zh_TW")
        self.current_lang = lang_code
        self.config["language"] = lang_code
        self.font_family = get_ui_font_family(lang_code)
        save_config(self.config)
        self._build_ui()

    def _on_res_mode_changed(self, chosen_label):
        mode_id = next((r[1] for r in RESOLUTION_MODES if r[0] == chosen_label), "1920x700")
        self.current_res_mode = mode_id
        self.config["resolution_mode"] = mode_id
        save_config(self.config)
        
        self.shortcuts_dir, self.shortcut_file_map = generate_obs_shortcuts(
            self.config.get("port", 11150), self.base_dir, self._get_res_query_param()
        )
        self._build_ui()

    def _open_shortcuts_folder(self):
        try:
            os.startfile(self.shortcuts_dir)
        except Exception:
            subprocess.Popen(["explorer", self.shortcuts_dir])

    def _set_default_thumbnail(self):
        # Uses songIcon.jpg directly!
        icon_path = os.path.join(self.base_dir, "songIcon.jpg")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(self.base_dir, "static", "sample_cover.png")

        if os.path.exists(icon_path):
            try:
                pil_img = Image.open(icon_path).convert("RGBA")
                pil_img = pil_img.resize((170, 170), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(170, 170))
                self.cover_label.configure(image=ctk_img)
                return
            except Exception:
                pass

        img = Image.new("RGBA", (170, 170), (30, 27, 75, 255))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(170, 170))
        self.cover_label.configure(image=ctk_img)

    def _get_current_obs_url(self):
        port = self.config.get("port", 11150)
        theme = self.config.get("selected_theme", "glassmorphism")
        autohide = 1 if self.config.get("autohide_on_pause", False) else 0
        res_param = self._get_res_query_param()
        return f"http://localhost:{port}/overlay?theme={theme}&autohide={autohide}{res_param}"

    def _copy_obs_url(self):
        url = self._get_current_obs_url()
        self.clipboard_clear()
        self.clipboard_append(url)
        self.show_inapp_toast(self._t("copied_toast"))
        self.copy_btn.configure(text=f"✔ {self._t('copied_title')}", fg_color="#10b981")
        self.after(2000, lambda: self.copy_btn.configure(text=self._t("copy_obs_url"), fg_color="#4f46e5"))

    def _copy_specific_theme(self, theme_id, url):
        self.clipboard_clear()
        self.clipboard_append(url)
        # Non-blocking in-app notification! NO modal alert popup window!
        self.show_inapp_toast(self._t("copied_toast"))

    def _set_theme_from_gallery(self, theme_id):
        self.config["selected_theme"] = theme_id
        save_config(self.config)
        name, _ = get_theme_info(self.current_lang, theme_id)
        if hasattr(self, "theme_dropdown"):
            self.theme_dropdown.set(name)
        if self.on_theme_change_callback:
            self.on_theme_change_callback(theme_id)
        self.show_inapp_toast(self._t("theme_set_toast").format(name=name))

    def _on_theme_dropdown_selected(self, chosen_display_name):
        for tid in THEME_IDS:
            name, _ = get_theme_info(self.current_lang, tid)
            if name == chosen_display_name:
                self.config["selected_theme"] = tid
                save_config(self.config)
                if self.on_theme_change_callback:
                    self.on_theme_change_callback(tid)
                self.show_inapp_toast(self._t("theme_set_toast").format(name=name))
                break

    def _apply_port(self):
        try:
            new_port = int(self.port_entry.get().strip())
            if new_port < 1024 or new_port > 65535:
                self.show_inapp_toast(self._t("port_error"))
                return
            self.config["port"] = new_port
            save_config(self.config)
            self.shortcuts_dir, self.shortcut_file_map = generate_obs_shortcuts(
                new_port, self.base_dir, self._get_res_query_param()
            )
            if self.on_port_change_callback:
                self.on_port_change_callback(new_port)
            self.show_inapp_toast(self._t("port_updated_toast").format(port=new_port))
        except Exception as e:
            self.show_inapp_toast(str(e))

    def _on_autohide_toggle(self):
        self.config["autohide_on_pause"] = bool(self.autohide_switch.get())
        save_config(self.config)

    def update_media_display(self, data):
        def _update():
            if not data:
                return
            has_media = data.get("has_media", False)
            title = data.get("title", "") or (self._t("waiting_media") if not has_media else "Untitled Track")
            artist = data.get("artist", "") or (self._t("play_instruction") if not has_media else "Unknown Artist")
            status = data.get("status", "Stopped")

            self.track_title_label.configure(text=title)
            self.track_artist_label.configure(text=artist)

            pos = data.get("position", 0)
            dur = data.get("duration", 0)
            cur_str = format_time_str(pos)
            dur_str = format_time_str(dur) if dur > 0 else "--:--"
            self.time_label.configure(text=f"{cur_str} / {dur_str}")
            
            if dur > 0:
                self.progress_bar.set(min(1.0, max(0.0, pos / dur)))
            else:
                self.progress_bar.set(0)

            if status == "Playing":
                self.status_badge.configure(text=self._t("status_playing"), text_color="#4ade80", fg_color="#143422")
            elif status == "Paused":
                self.status_badge.configure(text=self._t("status_paused"), text_color="#facc15", fg_color="#362d08")
            else:
                self.status_badge.configure(text=self._t("status_idle"), text_color="#94a3b8", fg_color="#1e293b")

            thumb_b64 = data.get("thumbnail", "")
            if thumb_b64 and thumb_b64 != self.current_thumbnail_data:
                self.current_thumbnail_data = thumb_b64
                try:
                    raw_b64 = thumb_b64.split(",", 1)[1] if "," in thumb_b64 else thumb_b64
                    img_bytes = base64.b64decode(raw_b64)
                    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                    pil_img = pil_img.resize((170, 170), Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(170, 170))
                    self.cover_label.configure(image=ctk_img)
                except Exception:
                    self._set_default_thumbnail()
            elif not thumb_b64 and not self.current_thumbnail_data:
                self._set_default_thumbnail()

        self.after(0, _update)

    def _on_close(self):
        self.withdraw()
        self._setup_tray()

    def _setup_tray(self):
        if self.tray_icon:
            return
        img = Image.new("RGB", (64, 64), color=(99, 102, 241))
        menu = (
            item("Open Controller", self._restore_from_tray),
            item("Copy Active OBS URL", self._copy_obs_url),
            item("Open Drag & Drop Folder", lambda icon, item: self._open_shortcuts_folder()),
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
            self.tray_icon.stop()
        self.after(0, self.destroy)
