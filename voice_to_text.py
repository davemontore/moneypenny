"""MoneyPenny v3.0 — cloud or local voice typing for Windows."""

import pyaudio
import keyboard
import requests
from faster_whisper import WhisperModel
from pynput.keyboard import Controller
import threading
import time
import io
import wave
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
import traceback
from pathlib import Path
import signal
import atexit
import re
import json
import socket


def _force_ipv4():
    """Force outbound connections to use IPv4.

    Some networks have a broken IPv6 route to Hugging Face, which causes
    Python's SSL connection to be reset (WinError 10054) during model
    downloads. Preferring IPv4 works around this. IPv4 is universally
    supported, so this is safe to apply globally for this app's only
    network use (model downloads).
    """
    _orig_getaddrinfo = socket.getaddrinfo

    def _ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

    socket.getaddrinfo = _ipv4_getaddrinfo


_force_ipv4()

# --- Logging & App Paths ---
APP_DIR = Path(__file__).resolve().parent
LOG_DIR = APP_DIR / "logs"
LOG_FILE = LOG_DIR / "moneypenny.log"
SETTINGS_FILE = APP_DIR / "settings.json"
LEXICON_FILE = APP_DIR / "lexicon.txt"


def configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    logger = logging.getLogger("moneypenny")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        # Console output only when a console exists (python.exe).
        # When launched via pythonw.exe (no console window), sys.stdout is None,
        # so we skip the console handler to avoid crashing.
        if sys.stdout is not None:
            console_handler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setFormatter(log_formatter)
            console_handler.setLevel(logging.INFO)
            logger.addHandler(console_handler)
        logger.propagate = False
    return logger


logger = configure_logging()


def _log_unhandled_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        return
    logger.critical(
        "Unhandled exception:\n%s",
        "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
    )


sys.excepthook = _log_unhandled_exception


def _acquire_single_instance_lock():
    """Ensure only one copy of MoneyPenny runs at a time.

    Uses a Windows named mutex: the first copy to start owns it, and any
    later copy detects it and exits instead of becoming a duplicate.
    (Two copies both listening for the hotkey causes double typing.)
    Returns the mutex handle, or None if another copy is already running.
    """
    try:
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        mutex = kernel32.CreateMutexW(None, False, "Global\\MoneyPennyVoiceTypingMutex")
        ERROR_ALREADY_EXISTS = 183
        if not mutex or ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            # Another copy owns the lock. IMPORTANT: CreateMutexW opened a
            # handle to the existing mutex — close it immediately. If we
            # kept it, this (short-lived) process would keep the named
            # mutex alive even after the real app exits, and every future
            # launch would wrongly report "already running".
            if mutex:
                kernel32.CloseHandle(mutex)
            return None
        return mutex
    except Exception:
        # If the check itself fails, don't block the app from starting.
        logger.exception("Single-instance check failed; continuing anyway")
        return True


def _notify_already_running():
    """Tell the user MoneyPenny is already running, then exit."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "MoneyPenny",
            "MoneyPenny is already running — no need to open it again.\n\n"
            "Note: closing the MoneyPenny window does NOT quit the app.\n"
            "It hides to the system tray so it can keep listening for your "
            "hotkey. Look for its icon near the clock (you may need to click "
            "the small ^ arrow to see it).\n\n"
            "To fully quit: right-click the tray icon and choose Exit, "
            "or press Ctrl+Alt+Q.",
        )
        root.destroy()
    except Exception:
        logger.warning("MoneyPenny is already running; second instance exiting.")


# --- Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

# Default settings
DEFAULT_SETTINGS = {
    "transcription_mode": "local",  # "local" (offline, CPU) or "cloud" (API)
    "model_size": "tiny.en",
    "beam_size": 1,
    "cloud_provider": "groq",  # "groq" (fastest) or "openrouter"
    "openrouter_api_key": "",
    "cloud_model": "openai/gpt-transcribe",
    "groq_api_key": "",
    "groq_model": "whisper-large-v3-turbo",
    "record_hotkey": "right ctrl",
    "selected_microphone": None,  # None = system default
}


class Settings:
    """Manages application settings persistence."""

    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # Merge with defaults, keeping only known keys
                for key in DEFAULT_SETTINGS:
                    if key in saved:
                        self.settings[key] = saved[key]
                logger.info("Settings loaded from %s", SETTINGS_FILE)
        except Exception:
            logger.exception("Failed to load settings, using defaults")

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
            logger.info("Settings saved")
        except Exception:
            logger.exception("Failed to save settings")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value


class Lexicon:
    """Manages the lexicon/dictionary for transcription biasing."""

    def __init__(self):
        self.terms = []
        self.load()

    def load(self):
        self.terms = []
        if not LEXICON_FILE.exists():
            return
        try:
            with open(LEXICON_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self.terms.append(line)
            logger.info("Lexicon loaded: %d terms", len(self.terms))
        except Exception:
            logger.exception("Failed to load lexicon")

    def save(self):
        try:
            with open(LEXICON_FILE, "w", encoding="utf-8") as f:
                f.write("# Add one term or phrase per line to bias transcription.\n")
                f.write("# Lines starting with # are ignored.\n\n")
                for term in self.terms:
                    f.write(term + "\n")
            logger.info("Lexicon saved: %d terms", len(self.terms))
        except Exception:
            logger.exception("Failed to save lexicon")

    def add(self, term: str):
        term = term.strip()
        if term and term not in self.terms:
            self.terms.append(term)
            self.save()
            return True
        return False

    def remove(self, term: str):
        if term in self.terms:
            self.terms.remove(term)
            self.save()
            return True
        return False

    def get_prompt(self) -> str:
        if not self.terms:
            return ""
        max_terms = 50
        selected = self.terms[:max_terms]
        prompt = (
            "Transcribe clearly using these domain terms and proper nouns when appropriate: "
            + ", ".join(selected)
            + "."
        )
        return prompt[:600]


class Transcriber:
    """Handles local Whisper and cloud transcription."""

    def __init__(self, settings: Settings, lexicon: Lexicon):
        self.settings = settings
        self.lexicon = lexicon
        self.model = None
        # RLock (re-entrant) so transcribe_buffer's self-heal can call
        # load_model() while already holding the lock without deadlocking.
        self.model_lock = threading.RLock()
        # Model is loaded explicitly via load_model() / load_model_async().

    def load_model(self):
        model_size = self.settings.get("model_size", "tiny.en")
        logger.info("Loading Whisper model: '%s'...", model_size)
        try:
            with self.model_lock:
                self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
            logger.info("Whisper model loaded.")
            return True
        except Exception:
            logger.exception("Failed to load Whisper model")
            return False

    def reload_model(self):
        """Reload model after settings change."""
        return self.load_model()

    def transcribe(self, audio_frames: list) -> str:
        """Transcribe audio frames using the configured backend (local or cloud)."""
        if not audio_frames:
            return ""

        wav_buffer = self._frames_to_wav(audio_frames)
        mode = self.settings.get("transcription_mode", "local")
        if mode == "cloud":
            return self._transcribe_cloud(wav_buffer)
        return self._transcribe_local(wav_buffer)

    def _frames_to_wav(self, audio_frames: list) -> io.BytesIO:
        """Package raw audio frames into an in-memory WAV buffer.

        Trailing silence is trimmed first: Whisper tends to hallucinate
        stock phrases like "Thank you." when a recording ends with dead
        air, and cutting that silence removes the trigger without ever
        touching actual speech.
        """
        frames = self._trim_trailing_silence(audio_frames)
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # paInt16 = 2 bytes
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
        wav_buffer.seek(0)
        return wav_buffer

    def _trim_trailing_silence(self, audio_frames: list) -> list:
        """Drop near-silent chunks from the END of the recording only."""
        if not audio_frames:
            return audio_frames

        from array import array
        SILENCE_PEAK = 500   # int16 amplitude below this counts as silence
        MIN_CHUNKS = 5       # always keep at least ~0.3s of audio

        cut = len(audio_frames)
        while cut > MIN_CHUNKS:
            samples = array("h", audio_frames[cut - 1])
            peak = max((abs(s) for s in samples), default=0)
            if peak >= SILENCE_PEAK:
                break
            cut -= 1

        if cut < len(audio_frames):
            logger.info(
                "Trimmed %.2fs of trailing silence",
                (len(audio_frames) - cut) * CHUNK / RATE,
            )
        return audio_frames[:cut]

    def _transcribe_local(self, wav_buffer: io.BytesIO) -> str:
        """Transcribe locally with faster-whisper (CPU)."""
        try:
            with self.model_lock:
                if self.model is None:
                    # Model failed to load earlier (e.g. download interrupted).
                    # Try once more so the app can recover without a restart.
                    logger.warning("Model not loaded; attempting reload...")
                    if not self.load_model():
                        return ""

                beam_size = self.settings.get("beam_size", 1)
                prompt = self.lexicon.get_prompt()

                # Speed-oriented options for short dictation:
                # - vad_filter skips silence so Whisper processes less audio
                # - without_timestamps skips timestamp calculation
                # - condition_on_previous_text=False avoids extra context passes
                transcribe_kwargs = dict(
                    beam_size=beam_size,
                    language="en",
                    vad_filter=True,
                    without_timestamps=True,
                    condition_on_previous_text=False,
                )
                if prompt:
                    transcribe_kwargs["initial_prompt"] = prompt

                segments, info = self.model.transcribe(wav_buffer, **transcribe_kwargs)
                return "".join(segment.text for segment in segments).strip()
        except Exception:
            logger.exception("Local transcription failed")
            return ""

    def _transcribe_cloud(self, wav_buffer: io.BytesIO) -> str:
        """Transcribe via the configured cloud provider (Groq or OpenRouter)."""
        provider = self.settings.get("cloud_provider", "openrouter")

        if provider == "groq":
            api_key = (self.settings.get("groq_api_key") or "").strip()
            if not api_key:
                logger.error("Cloud mode is on (Groq) but no Groq API key is set.")
                return ""
            return self._cloud_request(
                wav_buffer,
                url="https://api.groq.com/openai/v1/audio/transcriptions",
                api_key=api_key,
                model=self.settings.get("groq_model", "whisper-large-v3-turbo"),
                extra_headers={},
                provider_name="Groq",
            )

        # Default: OpenRouter
        api_key = (self.settings.get("openrouter_api_key") or "").strip()
        if not api_key:
            logger.error("Cloud mode is on but no OpenRouter API key is set.")
            return ""
        return self._cloud_request(
            wav_buffer,
            url="https://openrouter.ai/api/v1/audio/transcriptions",
            api_key=api_key,
            model=self.settings.get("cloud_model", "openai/gpt-transcribe"),
            extra_headers={
                # Optional attribution headers OpenRouter recommends.
                "HTTP-Referer": "https://github.com/davemontore/moneypenny",
                "X-Title": "MoneyPenny Voice Typing",
            },
            provider_name="OpenRouter",
        )

    def _cloud_request(
        self,
        wav_buffer: io.BytesIO,
        url: str,
        api_key: str,
        model: str,
        extra_headers: dict,
        provider_name: str,
    ) -> str:
        """Send audio to an OpenAI-compatible transcription endpoint."""
        headers = {"Authorization": f"Bearer {api_key}"}
        headers.update(extra_headers)
        data = {
            "model": model,
            "response_format": "json",
            "language": "en",
        }
        # Reuse the lexicon as a biasing prompt, same as local mode.
        prompt = self.lexicon.get_prompt()
        if prompt:
            data["prompt"] = prompt

        wav_buffer.seek(0)
        files = {"file": ("audio.wav", wav_buffer, "audio/wav")}

        try:
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            if resp.status_code == 200:
                return resp.json().get("text", "").strip()
            logger.error("%s API error %s: %s", provider_name, resp.status_code, resp.text[:300])
            return ""
        except Exception:
            logger.exception("Cloud transcription request failed (%s)", provider_name)
            return ""


class MoneyPennyApp:
    """Main application class."""

    def __init__(self):
        self.settings = Settings()
        self.lexicon = Lexicon()
        self.transcriber = Transcriber(self.settings, self.lexicon)

        # Audio state
        self.is_recording = False
        self.audio_frames = []
        self.frames_lock = threading.Lock()
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.stop_event = threading.Event()
        self.keyboard_controller = Controller()

        # GUI state
        self.gui = None
        self.tray_icon = None

        # Status callbacks
        self.status_callbacks = []

    def add_status_callback(self, callback):
        """Register a callback for status updates."""
        self.status_callbacks.append(callback)

    def load_model_async(self):
        """Load the Whisper model in a background thread.

        Used in GUI mode so the window appears immediately instead of
        waiting for the model to finish loading.
        """
        def _load():
            if self.settings.get("transcription_mode", "local") == "cloud":
                # Cloud mode needs no local model, so startup is instant.
                self._notify_status("idle", "Ready (cloud)")
                return
            self._notify_status("loading", "Loading speech model...")
            success = self.transcriber.load_model()
            if success:
                self._notify_status("idle", "Ready")
            else:
                self._notify_status("error", "Model failed to load")
        threading.Thread(target=_load, daemon=True).start()

    def _notify_status(self, status: str, detail: str = ""):
        """Notify all registered callbacks of a status change."""
        logger.info("Status: %s %s", status, detail)
        for callback in self.status_callbacks:
            try:
                callback(status, detail)
            except Exception:
                pass

    def get_microphones(self) -> list:
        """Get list of available microphone devices."""
        devices = []
        try:
            for i in range(self.p.get_device_count()):
                info = self.p.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    devices.append({
                        "index": i,
                        "name": info.get("name", f"Device {i}"),
                    })
        except Exception:
            logger.exception("Failed to enumerate microphones")
        return devices

    def start_recording(self):
        """Begin recording when hotkey is pressed."""
        if self.is_recording:
            return
        with self.frames_lock:
            self.audio_frames = []
        self.is_recording = True
        self._notify_status("recording", "Hold hotkey, speak now...")

    def stop_recording(self):
        """Stop recording and transcribe."""
        if not self.is_recording:
            return
        self.is_recording = False
        self._notify_status("transcribing", "Processing audio...")
        threading.Thread(target=self._transcribe_and_type, daemon=True).start()

    def _transcribe_and_type(self):
        """Transcribe recorded audio and type it."""
        with self.frames_lock:
            frames = list(self.audio_frames)
            self.audio_frames = []

        if not frames:
            self._notify_status("idle", "No audio recorded")
            return

        start_time = time.time()
        text = self.transcriber.transcribe(frames)
        elapsed = time.time() - start_time

        if text:
            text = self._normalize_transcript(text)
            text = self._strip_stock_phrases(text)
        if text:
            logger.info("Transcribed (%.2fs): %s", elapsed, text)
            self._notify_status("typing", f"Typed: {text[:50]}...")

            # Wait for modifier keys to release
            self._wait_for_modifiers_release()

            # Type the text
            self.keyboard_controller.type(" " + text)
        else:
            logger.info("No speech detected (%.2fs)", elapsed)
            self._notify_status("idle", "No speech detected")

    # Whisper was trained on huge amounts of subtitled video, so it loves
    # to append stock sign-off phrases ("Thank you.", "Thanks for watching.")
    # especially when the recording has trailing silence. Filter them out.
    _STOCK_PHRASES = {
        "thank you", "thanks", "thank you for watching", "thanks for watching",
        "thank you so much", "bye", "bye bye", "see you", "you",
    }

    def _strip_stock_phrases(self, text: str) -> str:
        """Remove Whisper's stock sign-off phrases from a transcript."""
        # Case 1: the ENTIRE transcript is a stock phrase (usually produced
        # from silence or background noise). Discard it completely.
        if text.strip().lower().rstrip(".!").strip() in self._STOCK_PHRASES:
            logger.info("Discarded stock-phrase hallucination: %r", text)
            return ""
        # We deliberately do NOT trim stock phrases from the end of real
        # content: there is no reliable way to tell a hallucinated "Thank
        # you." from one the user actually said, and deleting real words
        # is worse than the occasional phantom. (The trailing-silence
        # trim in _frames_to_wav prevents most of these at the source.)
        return text

    def _normalize_transcript(self, text: str) -> str:
        """Convert spoken punctuation to symbols."""
        normalized = text
        normalized = self._replace_word_boundary(normalized, "forward slash", "/")
        normalized = self._replace_word_boundary(normalized, "slash", "/")
        normalized = self._replace_word_boundary(normalized, "backslash", "\\")
        normalized = self._replace_word_boundary(normalized, "dot", ".")
        return normalized

    def _replace_word_boundary(self, text: str, spoken: str, symbol: str) -> str:
        pattern = re.compile(rf"\b{re.escape(spoken)}\b", flags=re.IGNORECASE)
        return pattern.sub(lambda _: symbol, text)

    def _wait_for_modifiers_release(self, max_wait_seconds: float = 0.5) -> bool:
        start_time = time.time()
        modifier_keys = [
            "ctrl", "right ctrl", "left ctrl",
            "alt", "right alt", "left alt",
            "windows", "left windows", "right windows", "cmd",
        ]
        while time.time() - start_time < max_wait_seconds:
            if not any(keyboard.is_pressed(k) for k in modifier_keys):
                return True
            time.sleep(0.01)
        return False

    def _record_thread_func(self):
        """Background thread for audio recording."""
        while not self.stop_event.is_set():
            if self.is_recording:
                if self.stream is None or not self.stream.is_active():
                    try:
                        mic_index = self.settings.get("selected_microphone")
                        self.stream = self.p.open(
                            format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK,
                            input_device_index=mic_index,
                        )
                    except Exception:
                        logger.exception("Failed to open audio stream")
                        time.sleep(0.5)
                        continue

                try:
                    data = self.stream.read(CHUNK, exception_on_overflow=False)
                    with self.frames_lock:
                        self.audio_frames.append(data)
                except Exception:
                    logger.warning("Audio read failed")
                    time.sleep(0.05)
            else:
                if self.stream is not None and self.stream.is_active():
                    try:
                        self.stream.stop_stream()
                        self.stream.close()
                    except Exception:
                        pass
                    self.stream = None
                time.sleep(0.05)

    def _setup_hotkeys(self):
        """Register keyboard hotkeys."""
        hotkey = self.settings.get("record_hotkey", "right ctrl")
        try:
            keyboard.on_press_key(hotkey, lambda e: self.start_recording(), suppress=False)
            keyboard.on_release_key(hotkey, lambda e: self.stop_recording(), suppress=False)
            logger.info("Hotkey registered: %s", hotkey)
        except Exception:
            logger.exception("Failed to register hotkeys")
            raise

    def shutdown(self):
        """Gracefully shut down the application."""
        if self.stop_event.is_set():
            return
        logger.info("Shutting down...")
        self._notify_status("shutdown", "Exiting...")
        self.is_recording = False
        self.stop_event.set()

        # Force exit after short delay if graceful shutdown fails
        def force_exit():
            time.sleep(2)
            logger.warning("Forcing exit")
            os._exit(0)
        threading.Thread(target=force_exit, daemon=True).start()

        try:
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
        except Exception:
            pass

        try:
            self.p.terminate()
        except Exception:
            pass

        # Stop tray icon
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass

    def run_headless(self):
        """Run without the settings window or system tray."""
        logger.info("MoneyPenny starting up (headless mode).")
        # No GUI to show progress, so load the model now (blocking).
        self.transcriber.load_model()
        self._setup_hotkeys()

        keyboard.add_hotkey("esc", lambda: self.shutdown())
        keyboard.add_hotkey("ctrl+alt+q", lambda: self.shutdown())

        logger.info("--- MoneyPenny Voice Typing v3.0 ---")
        logger.info("Hold %s to dictate; release to transcribe.",
                   self.settings.get("record_hotkey", "right ctrl"))
        logger.info("Press ESC or CTRL+ALT+Q to exit.")

        record_thread = threading.Thread(target=self._record_thread_func, daemon=True)
        record_thread.start()

        self.stop_event.wait()
        logger.info("Exited.")

    def run_with_gui(self):
        """Run with GUI and system tray."""
        # Import GUI components
        try:
            from gui import MoneyPennyGUI, create_tray_icon
        except Exception:
            # Catch ANY failure (missing package, syntax error, etc.) so the
            # app still works headless instead of dying silently.
            logger.exception("GUI failed to load; falling back to headless mode")
            self.run_headless()
            return

        logger.info("MoneyPenny starting up (GUI mode).")
        self._setup_hotkeys()

        keyboard.add_hotkey("ctrl+alt+q", lambda: self._quit_from_gui())

        record_thread = threading.Thread(target=self._record_thread_func, daemon=True)
        record_thread.start()

        # Create and show the GUI immediately so the window appears right away.
        self.gui = MoneyPennyGUI(self)
        self.tray_icon = create_tray_icon(self, self.gui)

        # Run tray in background thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()

        # Load the speech model in the background so the window isn't blocked.
        self.load_model_async()

        # Run GUI main loop
        self.gui.run()

    def _quit_from_gui(self):
        """Handle quit from GUI or hotkey."""
        logger.info("Quit requested via hotkey")
        if self.gui:
            # Use GUI's quit which handles window cleanup
            try:
                if self.gui.window:
                    self.gui.window.after(0, self.gui.quit_app)
                else:
                    self.gui.quit_app()
            except Exception:
                self.shutdown()
        else:
            self.shutdown()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MoneyPenny Voice Typing")
    parser.add_argument("--headless", action="store_true",
                       help="Run without the settings window or system tray")
    args = parser.parse_args()

    instance_lock = _acquire_single_instance_lock()
    if instance_lock is None:
        _notify_already_running()
        sys.exit(0)

    app = MoneyPennyApp()

    # Install signal handlers
    try:
        signal.signal(signal.SIGINT, lambda s, f: app.shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: app.shutdown())
    except Exception:
        pass

    atexit.register(app.shutdown)

    if args.headless:
        app.run_headless()
    else:
        app.run_with_gui()


if __name__ == "__main__":
    main()