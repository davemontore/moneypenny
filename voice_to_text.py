import pyaudio
import keyboard
from faster_whisper import WhisperModel
from pynput.keyboard import Controller
import threading
import time
import io
import wave
import os

# --- Configuration ---
# Audio recording parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000 # Sample rate Whisper was trained on
CHUNK = 1024

# Model configuration
# "tiny.en" is very fast. "base.en" is a great balance of speed and accuracy.
MODEL_SIZE = "base.en"

# --- Global State ---
is_recording = False
audio_frames = []
p = pyaudio.PyAudio()
stream = None
keyboard_controller = Controller()
stop_event = threading.Event()
LEXICON_PROMPT = ""


def load_lexicon_prompt(file_path: str = "lexicon.txt") -> str:
    """Load user-provided terms from a text file and build an initial prompt.
    Each non-empty, non-comment line is treated as a term/phrase.
    """
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            terms = [
                line.strip()
                for line in f.readlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        if not terms:
            return ""
        # Keep prompt reasonably short; take first N terms
        max_terms = 50
        selected = terms[:max_terms]
        # Natural-language context helps whisper biasing more than raw word lists
        prompt = (
            "Transcribe clearly using these domain terms and proper nouns when appropriate: "
            + ", ".join(selected)
            + "."
        )
        return prompt[:600]  # cap length to be safe
    except Exception:
        return ""

# --- Whisper Model Loading ---
# This might take a few seconds the first time you run it as it downloads the model
print(f"Loading Whisper model: '{MODEL_SIZE}'...")
# To run on CPU: device="cpu", compute_type="int8"
# To run on GPU: device="cuda", compute_type="float16"
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
print("Whisper model loaded.")

# Load lexicon prompt if present
LEXICON_PROMPT = load_lexicon_prompt()
if LEXICON_PROMPT:
    print("Lexicon loaded (biasing terms enabled).")


# --- Main Logic ---

def transcribe_audio_chunk():
    """Transcribes the collected audio frames using the local Whisper model."""
    global audio_frames
    if not audio_frames:
        return

    # Create a virtual WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(audio_frames))
    
    wav_buffer.seek(0)

    print("Transcribing... ")
    # Transcribe the audio from the buffer
    if LEXICON_PROMPT:
        segments, info = model.transcribe(
            wav_buffer,
            beam_size=5,
            language="en",
            initial_prompt=LEXICON_PROMPT,
        )
    else:
        segments, info = model.transcribe(
            wav_buffer,
            beam_size=5,
            language="en",
        )

    transcribed_text = "".join(segment.text for segment in segments).strip()
    
    if transcribed_text:
        print(f"Transcribed: '{transcribed_text}'")
        # Add a leading space for natural typing flow
        keyboard_controller.type(" " + transcribed_text)
    
    # Clear the frames for the next recording
    audio_frames = []


def record_thread_func():
    """Continuously records audio into a buffer while is_recording is True."""
    global stream, audio_frames
    while not stop_event.is_set():
        if is_recording:
            if stream is None or not stream.is_active():
                stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                input=True, frames_per_buffer=CHUNK)
            # Record a chunk of audio
            try:
                data = stream.read(CHUNK)
            except Exception:
                # If read fails due to device glitch, back off briefly
                time.sleep(0.05)
                continue
            audio_frames.append(data)
        else:
            if stream is not None and stream.is_active():
                stream.stop_stream()
                stream.close()
                stream = None
            # Sleep when not recording to avoid using CPU
            time.sleep(0.1)


def start_recording():
    """Begin recording when RIGHT CTRL is pressed and held."""
    global is_recording, audio_frames
    if is_recording:
        return
    audio_frames = []
    is_recording = True
    print("\n🎙️ Recording started (hold RIGHT CTRL)...")


def stop_recording():
    """Stop recording on RIGHT CTRL release and transcribe."""
    global is_recording
    if not is_recording:
        return
    is_recording = False
    print("🛑 Recording stopped. Transcribing...")
    threading.Thread(target=transcribe_audio_chunk, daemon=True).start()


def shutdown():
    """Gracefully stop recording, close audio devices, and exit."""
    global is_recording, stream
    if stop_event.is_set():
        return
    print("Shutting down...")
    is_recording = False
    stop_event.set()
    try:
        if stream is not None and stream.is_active():
            stream.stop_stream()
            stream.close()
            stream = None
    except Exception:
        pass
    try:
        p.terminate()
    except Exception:
        pass


def main():
    # Hold-to-record: press RIGHT CTRL to start, release to stop
    keyboard.on_press_key('right ctrl', lambda e: start_recording(), suppress=False)
    keyboard.on_release_key('right ctrl', lambda e: stop_recording(), suppress=False)

    # Quit hotkeys
    keyboard.add_hotkey('esc', lambda: shutdown())
    keyboard.add_hotkey('ctrl+alt+q', lambda: shutdown())

    print("--- Local Whisper Voice Typer ---")
    print("Hold RIGHT CTRL to dictate; release to transcribe.")
    print("Press ESC or CTRL+ALT+Q to exit.")

    # Start the recording thread in the background
    record_thread = threading.Thread(target=record_thread_func, daemon=True)
    record_thread.start()

    # Wait until shutdown is requested
    stop_event.wait()
    print("Exited.")

if __name__ == "__main__":
    main()

