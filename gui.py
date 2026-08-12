"""
MoneyPenny GUI Module
Provides the tabbed settings window and system tray integration.
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import threading
from pathlib import Path
from PIL import Image, ImageDraw
import pystray


# Appearance settings
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Colors
BG_COLOR = "#F7F5F3"
TEXT_COLOR = "#2C2C2C"
ACCENT_COLOR = "#4A90D9"
BUTTON_COLOR = "#E8E6E4"
BUTTON_HOVER = "#D8D6D4"


class MoneyPennyGUI:
    """Main GUI window with tabbed interface."""

    def __init__(self, app):
        self.app = app
        self.window = None
        self.status_label = None
        self.status_detail = None
        self.log_text = None
        self.history_text = None
        self.recent_activity = []

        # Register for status updates
        self.app.add_status_callback(self._on_status_update)
        self.app.add_history_callback(self._on_history_update)

    def create_window(self):
        """Create the main window."""
        if self.window is not None:
            try:
                self.window.deiconify()
                self.window.lift()
                self.window.focus_force()
                return
            except Exception:
                self.window = None

        # Give the app its own Windows identity so the TASKBAR uses our
        # icon instead of the generic Python one (Windows groups taskbar
        # buttons by app identity, not by window).
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "MoneyPenny.VoiceTyping"
            )
        except Exception:
            pass

        self.window = ctk.CTk()
        self.window.title("MoneyPenny Voice Typing")
        self.window.geometry("620x600")
        self.window.minsize(560, 520)
        self.window.configure(fg_color=BG_COLOR)

        # Window + taskbar icon
        self._set_window_icon()

        # Handle window close (minimize to tray)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Header
        header_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="MoneyPenny",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=TEXT_COLOR,
        )
        title_label.pack(side="left")

        version_label = ctk.CTkLabel(
            header_frame,
            text=f"v{getattr(self.app, 'version', '3.1.1')}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#888888",
        )
        version_label.pack(side="left", padx=(10, 0), pady=(8, 0))

        # Status bar at top
        status_frame = ctk.CTkFrame(self.window, fg_color=BUTTON_COLOR, corner_radius=8)
        status_frame.pack(fill="x", padx=20, pady=5)

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        )
        self.status_label.pack(side="left", padx=15, pady=8)

        self.status_detail = ctk.CTkLabel(
            status_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#666666",
        )
        self.status_detail.pack(side="left", padx=5, pady=8)

        # Tab view
        self.tabview = ctk.CTkTabview(
            self.window,
            fg_color=BG_COLOR,
            segmented_button_fg_color=BUTTON_COLOR,
            segmented_button_selected_color=ACCENT_COLOR,
            segmented_button_selected_hover_color=ACCENT_COLOR,
            segmented_button_unselected_color=BUTTON_COLOR,
            segmented_button_unselected_hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
        )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        # Create tabs
        self._create_settings_tab()
        self._create_dictionary_tab()
        self._create_history_tab()
        self._create_status_tab()

        # Bottom buttons
        button_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 15))

        hide_btn = ctk.CTkButton(
            button_frame,
            text="Hide to Tray",
            command=self._on_close,
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
            width=120,
        )
        hide_btn.pack(side="left")

        quit_btn = ctk.CTkButton(
            button_frame,
            text="Quit",
            command=self.quit_app,
            fg_color="#D9534F",
            hover_color="#C9302C",
            text_color="white",
            width=80,
        )
        quit_btn.pack(side="right")

        # Bring the window to the front on startup so the user actually sees it
        # (instead of it opening behind other windows or going unnoticed).
        self.window.lift()
        self.window.attributes("-topmost", True)
        self.window.after(200, lambda: self.window.attributes("-topmost", False))
        self.window.focus_force()

    def _set_window_icon(self):
        """Show the MoneyPenny image on the window title bar and taskbar.

        The bundled PNG is converted once to moneypenny.ico next to the
        app, because Windows taskbar icons work most reliably from .ico
        files. If anything fails, the app keeps the default icon.
        """
        try:
            app_dir = Path(__file__).resolve().parent
            png_path = app_dir / "moneypenny icon.png"
            ico_path = app_dir / "moneypenny.ico"
            if not png_path.exists():
                return
            if not ico_path.exists():
                img = Image.open(png_path).convert("RGBA")
                img.save(
                    ico_path,
                    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
                )
            self.window.iconbitmap(str(ico_path))
            # CustomTkinter resets the window icon shortly after creation,
            # so re-apply ours a moment later to make it stick.
            self.window.after(400, lambda: self.window.iconbitmap(str(ico_path)))
        except Exception:
            pass

    def _create_settings_tab(self):
        """Create the Settings tab."""
        tab = self.tabview.add("Settings")
        tab.configure(fg_color=BG_COLOR)

        # Scrollable container so all options fit comfortably.
        container = ctk.CTkScrollableFrame(tab, fg_color=BG_COLOR)
        container.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Transcription mode ---
        ctk.CTkLabel(
            container,
            text="Transcription Mode",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            container,
            text="Cloud = fast & accurate (needs internet + API key). Local = offline but slower.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
            wraplength=400,
            justify="left",
        ).pack(anchor="w", padx=5)

        self.mode_var = ctk.StringVar(
            value=self.app.settings.get("transcription_mode", "local").capitalize()
        )
        mode_btn = ctk.CTkSegmentedButton(
            container,
            values=["Local", "Cloud"],
            variable=self.mode_var,
            fg_color=BUTTON_COLOR,
            selected_color=ACCENT_COLOR,
            selected_hover_color=ACCENT_COLOR,
            unselected_color=BUTTON_COLOR,
            unselected_hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
        )
        mode_btn.pack(anchor="w", padx=5, pady=(5, 12))

        # --- Cloud provider ---
        ctk.CTkLabel(
            container,
            text="Cloud Provider (Cloud mode)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            container,
            text="Groq is usually the fastest. OpenRouter routes to other providers (e.g. OpenAI).",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
            wraplength=400,
            justify="left",
        ).pack(anchor="w", padx=5)

        self.provider_var = ctk.StringVar(
            value=self.app.settings.get("cloud_provider", "openrouter").capitalize()
        )
        provider_btn = ctk.CTkSegmentedButton(
            container,
            values=["Groq", "OpenRouter"],
            variable=self.provider_var,
            fg_color=BUTTON_COLOR,
            selected_color=ACCENT_COLOR,
            selected_hover_color=ACCENT_COLOR,
            unselected_color=BUTTON_COLOR,
            unselected_hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
        )
        provider_btn.pack(anchor="w", padx=5, pady=(5, 12))

        # --- Groq API key ---
        ctk.CTkLabel(
            container,
            text="Groq API Key (used when Provider = Groq)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            container,
            text="Free key from console.groq.com — starts with gsk_",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
            wraplength=400,
            justify="left",
        ).pack(anchor="w", padx=5)

        self.groq_apikey_var = ctk.StringVar(value=self.app.settings.get("groq_api_key", ""))
        self.groq_apikey_entry = ctk.CTkEntry(
            container,
            textvariable=self.groq_apikey_var,
            placeholder_text="gsk_...",
            show="•",
            fg_color=BG_COLOR,
            border_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
            width=330,
        )
        self.groq_apikey_entry.pack(anchor="w", padx=5, pady=(5, 12))

        # --- Groq model ---
        ctk.CTkLabel(
            container,
            text="Groq Model",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            container,
            text="whisper-large-v3-turbo is the fastest. Use whisper-large-v3 for maximum accuracy.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
            wraplength=400,
            justify="left",
        ).pack(anchor="w", padx=5)

        self.groq_model_var = ctk.StringVar(
            value=self.app.settings.get("groq_model", "whisper-large-v3-turbo")
        )
        groq_model_entry = ctk.CTkEntry(
            container,
            textvariable=self.groq_model_var,
            placeholder_text="whisper-large-v3-turbo",
            fg_color=BG_COLOR,
            border_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
            width=330,
        )
        groq_model_entry.pack(anchor="w", padx=5, pady=(5, 12))

        # --- Context-aware cleanup ---
        ctk.CTkLabel(
            container,
            text="AI Transcript Cleanup",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            container,
            text=(
                "Commands only keeps normal dictation fast and uses a second Groq request only "
                "when verbal punctuation is detected. Always cleans every transcript."
            ),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
            wraplength=500,
            justify="left",
        ).pack(anchor="w", padx=5)

        cleanup_labels = {
            "off": "Off",
            "commands": "Commands only",
            "always": "Always",
        }
        self.cleanup_mode_var = ctk.StringVar(
            value=cleanup_labels.get(
                self.app.settings.get("cleanup_mode", "commands"),
                "Commands only",
            )
        )
        cleanup_selector = ctk.CTkSegmentedButton(
            container,
            values=["Off", "Commands only", "Always"],
            variable=self.cleanup_mode_var,
            selected_color=ACCENT_COLOR,
            text_color=TEXT_COLOR,
        )
        cleanup_selector.pack(anchor="w", padx=5, pady=(5, 8))

        self.cleanup_model_var = ctk.StringVar(
            value=self.app.settings.get("cleanup_model", "llama-3.1-8b-instant")
        )
        cleanup_model_entry = ctk.CTkEntry(
            container,
            textvariable=self.cleanup_model_var,
            placeholder_text="llama-3.1-8b-instant",
            fg_color=BG_COLOR,
            border_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
            width=330,
        )
        cleanup_model_entry.pack(anchor="w", padx=5, pady=(0, 12))

        # --- OpenRouter API key ---
        ctk.CTkLabel(
            container,
            text="OpenRouter API Key (used when Provider = OpenRouter)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=5, pady=(5, 0))

        self.apikey_var = ctk.StringVar(value=self.app.settings.get("openrouter_api_key", ""))
        self.apikey_entry = ctk.CTkEntry(
            container,
            textvariable=self.apikey_var,
            placeholder_text="sk-or-...",
            show="•",
            fg_color=BG_COLOR,
            border_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
            width=330,
        )
        self.apikey_entry.pack(anchor="w", padx=5, pady=(5, 12))

        # --- Cloud model ---
        ctk.CTkLabel(
            container,
            text="Cloud Model",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            container,
            text="Paste the model ID exactly as shown on OpenRouter (e.g. openai/gpt-transcribe)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
            wraplength=400,
            justify="left",
        ).pack(anchor="w", padx=5)

        self.cloud_model_var = ctk.StringVar(
            value=self.app.settings.get("cloud_model", "openai/gpt-transcribe")
        )
        cloud_model_entry = ctk.CTkEntry(
            container,
            textvariable=self.cloud_model_var,
            placeholder_text="openai/gpt-transcribe",
            fg_color=BG_COLOR,
            border_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
            width=330,
        )
        cloud_model_entry.pack(anchor="w", padx=5, pady=(5, 12))

        # --- Local model ---
        ctk.CTkLabel(
            container,
            text="Local Model (Local mode)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            container,
            text="Smaller = faster, Larger = more accurate",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
        ).pack(anchor="w", padx=5)

        self.model_var = ctk.StringVar(value=self.app.settings.get("model_size", "tiny.en"))
        model_menu = ctk.CTkOptionMenu(
            container,
            values=["tiny.en", "base.en"],
            variable=self.model_var,
            fg_color=BUTTON_COLOR,
            button_color=BUTTON_COLOR,
            button_hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
            dropdown_fg_color=BG_COLOR,
            dropdown_text_color=TEXT_COLOR,
            width=200,
        )
        model_menu.pack(anchor="w", padx=5, pady=(5, 12))

        # --- Microphone ---
        ctk.CTkLabel(
            container,
            text="Microphone",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=5, pady=(5, 0))

        self.mic_devices = self.app.get_microphones()
        mic_names = ["System Default"] + [f"{d['name']}" for d in self.mic_devices]

        current_mic = self.app.settings.get("selected_microphone")
        if current_mic is None:
            default_mic = "System Default"
        else:
            default_mic = next(
                (d["name"] for d in self.mic_devices if d["index"] == current_mic),
                "System Default"
            )

        self.mic_var = ctk.StringVar(value=default_mic)
        mic_menu = ctk.CTkOptionMenu(
            container,
            values=mic_names,
            variable=self.mic_var,
            fg_color=BUTTON_COLOR,
            button_color=BUTTON_COLOR,
            button_hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
            dropdown_fg_color=BG_COLOR,
            dropdown_text_color=TEXT_COLOR,
            width=330,
        )
        mic_menu.pack(anchor="w", padx=5, pady=(5, 12))

        # --- Hotkey ---
        ctk.CTkLabel(
            container,
            text="Record Hotkey (hold to dictate)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=5, pady=(5, 0))

        self.hotkey_var = ctk.StringVar(
            value=self.app.settings.get("record_hotkey", "right ctrl")
        )
        hotkey_menu = ctk.CTkOptionMenu(
            container,
            values=["right ctrl", "right alt", "right shift", "f9", "f10", "f11", "f12"],
            variable=self.hotkey_var,
            fg_color=BUTTON_COLOR,
            button_color=BUTTON_COLOR,
            button_hover_color=BUTTON_HOVER,
            text_color=TEXT_COLOR,
            dropdown_fg_color=BG_COLOR,
            dropdown_text_color=TEXT_COLOR,
            width=200,
        )
        hotkey_menu.pack(anchor="w", padx=5, pady=(5, 0))

        ctk.CTkLabel(
            container,
            text="Note: Hotkey changes require app restart",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
        ).pack(anchor="w", padx=5)

        # --- Save button ---
        save_btn = ctk.CTkButton(
            container,
            text="Save Settings",
            command=self._save_settings,
            fg_color=ACCENT_COLOR,
            hover_color="#3A7BC8",
            text_color="white",
            width=150,
        )
        save_btn.pack(pady=15)

    def _create_dictionary_tab(self):
        """Create the Dictionary tab with vocabulary and verbal-command help."""
        tab = self.tabview.add("Dictionary")
        tab.configure(fg_color=BG_COLOR)

        container = ctk.CTkScrollableFrame(tab, fg_color=BG_COLOR)
        container.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(
            container,
            text="Preferred Vocabulary",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=10, pady=(10, 0))

        ctk.CTkLabel(
            container,
            text="Soft hints that make uncommon names and terminology more likely",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # Word list
        list_frame = ctk.CTkFrame(container, fg_color=BUTTON_COLOR, corner_radius=8, height=120)
        list_frame.pack(fill="x", padx=10, pady=5)
        list_frame.pack_propagate(False)

        self.word_listbox = tk.Listbox(
            list_frame,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Segoe UI", 12),
            selectbackground=ACCENT_COLOR,
            selectforeground="white",
            activestyle="none",
            highlightthickness=0,
            bd=0,
        )
        self.word_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self._refresh_word_list()

        # Add word entry
        add_frame = ctk.CTkFrame(container, fg_color="transparent")
        add_frame.pack(fill="x", padx=10, pady=10)

        self.word_entry = ctk.CTkEntry(
            add_frame,
            placeholder_text="Type a word or phrase to add...",
            fg_color=BG_COLOR,
            border_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
            width=250,
        )
        self.word_entry.pack(side="left", fill="x", expand=True)
        self.word_entry.bind("<Return>", lambda e: self._add_word())

        add_btn = ctk.CTkButton(
            add_frame,
            text="Add",
            command=self._add_word,
            fg_color=ACCENT_COLOR,
            hover_color="#3A7BC8",
            text_color="white",
            width=70,
        )
        add_btn.pack(side="left", padx=(10, 0))

        # Remove button
        remove_btn = ctk.CTkButton(
            container,
            text="Remove Selected Word",
            command=self._remove_word,
            fg_color="#D9534F",
            hover_color="#C9302C",
            text_color="white",
            width=150,
        )
        remove_btn.pack(pady=(0, 10))

        ctk.CTkLabel(
            container,
            text="Exact Corrections",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=10, pady=(10, 0))

        ctk.CTkLabel(
            container,
            text="Guaranteed local replacements, such as Whisper Flow → Wispr Flow or C sharp → C#",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
            wraplength=500,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 10))

        correction_list_frame = ctk.CTkFrame(
            container, fg_color=BUTTON_COLOR, corner_radius=8, height=130
        )
        correction_list_frame.pack(fill="x", padx=10, pady=5)
        correction_list_frame.pack_propagate(False)

        self.correction_listbox = tk.Listbox(
            correction_list_frame,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Segoe UI", 12),
            selectbackground=ACCENT_COLOR,
            selectforeground="white",
            activestyle="none",
            highlightthickness=0,
            bd=0,
        )
        self.correction_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self._refresh_correction_list()

        correction_entry_frame = ctk.CTkFrame(container, fg_color="transparent")
        correction_entry_frame.pack(fill="x", padx=10, pady=10)

        self.heard_entry = ctk.CTkEntry(
            correction_entry_frame,
            placeholder_text="Heard as...",
            fg_color=BG_COLOR,
            border_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
        )
        self.heard_entry.pack(side="left", fill="x", expand=True)

        self.written_entry = ctk.CTkEntry(
            correction_entry_frame,
            placeholder_text="Type as...",
            fg_color=BG_COLOR,
            border_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
        )
        self.written_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.heard_entry.bind("<Return>", lambda e: self.written_entry.focus_set())
        self.written_entry.bind("<Return>", lambda e: self._add_correction())

        correction_add_btn = ctk.CTkButton(
            correction_entry_frame,
            text="Add",
            command=self._add_correction,
            fg_color=ACCENT_COLOR,
            hover_color="#3A7BC8",
            text_color="white",
            width=70,
        )
        correction_add_btn.pack(side="left", padx=(8, 0))

        correction_remove_btn = ctk.CTkButton(
            container,
            text="Remove Selected Correction",
            command=self._remove_correction,
            fg_color="#D9534F",
            hover_color="#C9302C",
            text_color="white",
            width=190,
        )
        correction_remove_btn.pack(pady=(0, 10))

        ctk.CTkLabel(
            container,
            text="Verbal Commands",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=10, pady=(10, 0))

        ctk.CTkLabel(
            container,
            text="AI cleanup interprets these from context; say the term normally when discussing it.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
            wraplength=500,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 5))

        commands_text = (
            "quote ... quote / open quote ... close quote    Wrap words in quotation marks\n"
            "comma / period / question mark                  ,  .  ?\n"
            "exclamation point / colon / semicolon           !  :  ;\n"
            "new line / new paragraph                        Start a new line or paragraph\n"
            "open parenthesis / close parenthesis            (  )\n"
            "slash / backslash                               /  \\\n"
            "the word comma / a comma                        Keep punctuation terms as words"
        )
        commands_box = ctk.CTkTextbox(
            container,
            height=175,
            fg_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word",
        )
        commands_box.pack(fill="x", padx=10, pady=(0, 10))
        commands_box.insert("1.0", commands_text)
        commands_box.configure(state="disabled")

    def _create_history_tab(self):
        """Create the persistent captured-transcript history tab."""
        tab = self.tabview.add("History")
        tab.configure(fg_color=BG_COLOR)

        ctk.CTkLabel(
            tab,
            text="Captured Transcripts",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=10, pady=(10, 0))

        ctk.CTkLabel(
            tab,
            text="Stored locally. Shows the raw speech recognition and final cleaned text.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#888888",
        ).pack(anchor="w", padx=10, pady=(0, 8))

        self.history_text = ctk.CTkTextbox(
            tab,
            fg_color=BUTTON_COLOR,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            wrap="word",
        )
        self.history_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.history_text.configure(state="disabled")

        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=8)

        ctk.CTkButton(
            button_frame,
            text="Copy Latest",
            command=self._copy_latest_transcript,
            fg_color=ACCENT_COLOR,
            hover_color="#3A7BC8",
            text_color="white",
            width=110,
        ).pack(side="left")

        ctk.CTkButton(
            button_frame,
            text="Clear History",
            command=self._clear_history,
            fg_color="#D9534F",
            hover_color="#C9302C",
            text_color="white",
            width=110,
        ).pack(side="right")

        self._refresh_history_display()

    def _create_status_tab(self):
        """Create the Status tab."""
        tab = self.tabview.add("Status")
        tab.configure(fg_color=BG_COLOR)

        ctk.CTkLabel(
            tab,
            text="Recent Activity",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Activity log
        log_frame = ctk.CTkFrame(tab, fg_color=BUTTON_COLOR, corner_radius=8)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_text = ctk.CTkTextbox(
            log_frame,
            fg_color=BG_COLOR,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.configure(state="disabled")

        # Info
        info_frame = ctk.CTkFrame(tab, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)

        hotkey = self.app.settings.get("record_hotkey", "right ctrl")
        ctk.CTkLabel(
            info_frame,
            text=f"Hotkey: Hold {hotkey.upper()} to dictate, release to transcribe",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_COLOR,
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_frame,
            text="Quit: Ctrl+Alt+Q or right-click tray icon → Exit",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_COLOR,
        ).pack(anchor="w")

    def _refresh_word_list(self):
        """Refresh the word list display."""
        self.word_listbox.delete(0, "end")
        for term in self.app.lexicon.terms:
            self.word_listbox.insert("end", term)

    def _add_word(self):
        """Add a word to the dictionary."""
        word = self.word_entry.get().strip()
        if word:
            if self.app.lexicon.add(word):
                self.word_entry.delete(0, "end")
                self._refresh_word_list()
                self._log_activity(f"Added word: {word}")
            else:
                messagebox.showinfo("MoneyPenny", "Word already exists in dictionary")

    def _remove_word(self):
        """Remove selected word from dictionary."""
        selection = self.word_listbox.curselection()
        if selection:
            word = self.word_listbox.get(selection[0])
            if self.app.lexicon.remove(word):
                self._refresh_word_list()
                self._log_activity(f"Removed word: {word}")
        else:
            messagebox.showinfo("MoneyPenny", "Please select a word to remove")

    def _refresh_correction_list(self):
        """Refresh deterministic heard-as -> type-as rules."""
        self.correction_listbox.delete(0, "end")
        self.correction_display_rules = list(self.app.corrections.rules)
        for rule in self.correction_display_rules:
            self.correction_listbox.insert(
                "end", f'{rule["heard"]}  →  {rule["written"]}'
            )

    def _add_correction(self):
        """Add an exact local correction rule."""
        heard = self.heard_entry.get().strip()
        written = self.written_entry.get().strip()
        if not heard or not written:
            messagebox.showinfo(
                "MoneyPenny", "Enter both the phrase MoneyPenny heard and what it should type."
            )
            return
        if self.app.corrections.add(heard, written):
            self.heard_entry.delete(0, "end")
            self.written_entry.delete(0, "end")
            self._refresh_correction_list()
            self._log_activity(f"Added exact correction: {heard} → {written}")
        else:
            messagebox.showinfo(
                "MoneyPenny", "A correction for that heard phrase already exists."
            )

    def _remove_correction(self):
        """Remove the selected exact correction rule."""
        selection = self.correction_listbox.curselection()
        if not selection:
            messagebox.showinfo("MoneyPenny", "Please select a correction to remove")
            return
        rule = self.correction_display_rules[selection[0]]
        if self.app.corrections.remove(rule["heard"]):
            self._refresh_correction_list()
            self._log_activity(f'Removed exact correction: {rule["heard"]}')

    def _on_history_update(self):
        """Schedule a history refresh from the transcription worker thread."""
        if self.window and self.history_text:
            try:
                self.window.after(0, self._refresh_history_display)
            except Exception:
                pass

    def _refresh_history_display(self):
        """Render newest captured transcripts first."""
        if not self.history_text:
            return
        entries = self.app.history.get_entries()
        blocks = []
        for entry in reversed(entries):
            timestamp = entry.get("timestamp", "").replace("T", " ")
            timestamp = timestamp[:19]
            provider = entry.get("provider", "local").capitalize()
            elapsed = entry.get("elapsed_seconds", 0)
            cleaned = "AI cleaned" if entry.get("cleanup_used") else "no cleanup"
            block = [f"{timestamp}  |  {provider}  |  {elapsed:.2f}s  |  {cleaned}"]
            raw = entry.get("raw", "")
            final = entry.get("final", "")
            block.append(f"Final: {final}")
            if raw != final:
                block.append(f"Raw:   {raw}")
            blocks.append("\n".join(block))

        display = "\n\n".join(blocks) if blocks else "No captured transcripts yet."
        try:
            self.history_text.configure(state="normal")
            self.history_text.delete("1.0", "end")
            self.history_text.insert("1.0", display)
            self.history_text.configure(state="disabled")
        except Exception:
            pass

    def _copy_latest_transcript(self):
        entries = self.app.history.get_entries()
        if not entries:
            messagebox.showinfo("MoneyPenny", "No captured transcripts yet")
            return
        self.window.clipboard_clear()
        self.window.clipboard_append(entries[-1].get("final", ""))
        self._log_activity("Copied latest transcript")

    def _clear_history(self):
        if not messagebox.askyesno(
            "MoneyPenny",
            "Clear all captured transcript history? This cannot be undone.",
        ):
            return
        self.app.history.clear()
        self._refresh_history_display()
        self._log_activity("Cleared transcript history")

    def _save_settings(self):
        """Save settings and apply changes."""
        # Transcription mode (Local / Cloud)
        new_mode = self.mode_var.get().lower()  # "local" or "cloud"
        self.app.settings.set("transcription_mode", new_mode)

        # Cloud provider + keys + models
        new_provider = self.provider_var.get().lower()  # "groq" or "openrouter"
        self.app.settings.set("cloud_provider", new_provider)
        self.app.settings.set("openrouter_api_key", self.apikey_var.get().strip())
        self.app.settings.set("cloud_model", self.cloud_model_var.get())
        self.app.settings.set("groq_api_key", self.groq_apikey_var.get().strip())
        self.app.settings.set("groq_model", self.groq_model_var.get().strip() or "whisper-large-v3-turbo")
        cleanup_modes = {
            "Off": "off",
            "Commands only": "commands",
            "Always": "always",
        }
        self.app.settings.set(
            "cleanup_mode",
            cleanup_modes.get(self.cleanup_mode_var.get(), "commands"),
        )
        self.app.settings.set(
            "cleanup_model",
            self.cleanup_model_var.get().strip() or "llama-3.1-8b-instant",
        )

        # Local model
        new_model = self.model_var.get()
        old_model = self.app.settings.get("model_size")
        self.app.settings.set("model_size", new_model)

        # Microphone
        mic_name = self.mic_var.get()
        if mic_name == "System Default":
            self.app.settings.set("selected_microphone", None)
        else:
            for device in self.mic_devices:
                if device["name"] == mic_name:
                    self.app.settings.set("selected_microphone", device["index"])
                    break

        # Hotkey
        new_hotkey = self.hotkey_var.get()
        old_hotkey = self.app.settings.get("record_hotkey")
        self.app.settings.set("record_hotkey", new_hotkey)

        # Save to file
        self.app.settings.save()

        # Reload the local model if it changed, or if we switched to Local mode
        # and no model is loaded yet.
        if new_mode == "local" and (new_model != old_model or self.app.transcriber.model is None):
            self._log_activity(f"Loading model: {new_model}...")
            threading.Thread(target=self._reload_model, daemon=True).start()

        # Confirmation / warning
        active_key_missing = (
            (new_provider == "groq" and not self.groq_apikey_var.get().strip())
            or (new_provider == "openrouter" and not self.apikey_var.get().strip())
        )
        if new_mode == "cloud" and active_key_missing:
            messagebox.showwarning(
                "MoneyPenny",
                f"Settings saved, but Cloud mode needs a {self.provider_var.get()} API key.\n\n"
                f"Paste your key into the {self.provider_var.get()} API Key field, then Save again."
            )
        elif new_hotkey != old_hotkey:
            messagebox.showinfo(
                "MoneyPenny",
                "Settings saved!\n\nHotkey change will take effect after restarting the app."
            )
        else:
            messagebox.showinfo("MoneyPenny", "Settings saved!")

        self._log_activity("Settings saved")

    def _reload_model(self):
        """Reload the transcription model."""
        self.app.transcriber.reload_model()
        self._log_activity("Model loaded")

    def _on_status_update(self, status: str, detail: str):
        """Handle status updates from the app."""
        status_map = {
            "idle": "Ready",
            "loading": "⏳ Loading speech model...",
            "recording": "🎙️ Recording...",
            "transcribing": "⏳ Transcribing...",
            "cleaning": "Cleaning up...",
            "typing": "✓ Done",
            "error": "⚠️ Error",
            "shutdown": "Shutting down...",
        }

        status_text = status_map.get(status, status)

        if self.window and self.status_label:
            try:
                self.window.after(0, lambda: self._update_status_display(status_text, detail))
            except Exception:
                pass

        self._log_activity(f"{status_text} {detail}")

    def _update_status_display(self, status_text: str, detail: str):
        """Update the status display (must be called on main thread)."""
        try:
            if self.status_label:
                self.status_label.configure(text=status_text)
            if self.status_detail:
                self.status_detail.configure(text=detail[:60] if detail else "")
        except Exception:
            pass

    def _log_activity(self, message: str):
        """Add message to activity log."""
        import time
        timestamp = time.strftime("%H:%M:%S")
        self.recent_activity.append(f"[{timestamp}] {message}")
        if len(self.recent_activity) > 50:
            self.recent_activity.pop(0)

        if self.log_text:
            try:
                self.window.after(0, lambda: self._update_log_display())
            except Exception:
                pass

    def _update_log_display(self):
        """Update the log display (must be called on main thread)."""
        try:
            if self.log_text:
                self.log_text.configure(state="normal")
                self.log_text.delete("1.0", "end")
                self.log_text.insert("end", "\n".join(self.recent_activity))
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception:
            pass

    def show_window(self):
        """Show the main window (thread-safe, callable from tray thread)."""
        if self.window:
            try:
                self.window.after(0, self._deiconify)
                return
            except Exception:
                pass
        self.create_window()

    def _deiconify(self):
        """Restore the window (must run on the main thread)."""
        try:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
        except Exception:
            pass

    def _on_close(self):
        """Handle window close - minimize to tray."""
        if self.window:
            self.window.withdraw()

    def quit_app(self):
        """Quit the application completely (thread-safe)."""
        self.app.shutdown()
        if self.window:
            try:
                self.window.after(0, self._destroy_window)
            except Exception:
                pass

    def _destroy_window(self):
        """Destroy the window (must run on the main thread)."""
        try:
            self.window.destroy()
        except Exception:
            pass

    def run(self):
        """Run the GUI main loop."""
        # Show the window at startup; closing it later hides it to the tray.
        self.create_window()
        if self.window:
            self.window.mainloop()


def create_tray_icon(app, gui):
    """Create the system tray icon."""

    def load_icon_image():
        """Load the bundled MoneyPenny icon, falling back to the drawn mic."""
        try:
            icon_path = Path(__file__).resolve().parent / "moneypenny icon.png"
            if icon_path.exists():
                # convert() forces the file to be read now and ensures a
                # format pystray can display.
                return Image.open(icon_path).convert("RGBA")
        except Exception:
            pass
        return create_drawn_icon()

    # Create a simple microphone icon (fallback if the PNG is missing)
    def create_drawn_icon():
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw a simple microphone shape
        # Mic body (rounded rectangle)
        draw.rounded_rectangle([24, 8, 40, 36], radius=8, fill="#4A90D9")
        # Mic stand arc
        draw.arc([18, 20, 46, 48], start=0, end=180, fill="#4A90D9", width=4)
        # Mic stand
        draw.line([32, 48, 32, 56], fill="#4A90D9", width=4)
        # Base
        draw.line([24, 56, 40, 56], fill="#4A90D9", width=4)

        return image

    icon_image = load_icon_image()

    def on_show_window(icon, item):
        gui.show_window()

    def on_quit(icon, item):
        app.shutdown()
        gui.quit_app()

    menu = pystray.Menu(
        pystray.MenuItem("Show MoneyPenny", on_show_window, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", on_quit),
    )

    icon = pystray.Icon(
        "moneypenny",
        icon_image,
        "MoneyPenny Voice Typing",
        menu,
    )

    return icon
