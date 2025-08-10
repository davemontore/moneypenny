# MoneyPenny - Voice Typing Assistant

> A fast, local voice‑to‑text utility. Hold RIGHT CTRL to dictate, release to transcribe into the current text field.

## ✨ Features

- **Local transcription**: Uses `faster-whisper` (no cloud, low latency)
- **Hold‑to‑record**: Press and hold RIGHT CTRL, release to transcribe
- **Types into any app**: Output is typed into the focused window
- **Headless**: No GUI; runs quietly in the background
- **Quick exit**: Press Ctrl+Alt+Q (or ESC in console) to quit
 - **Lexicon biasing**: Add your own terms in `lexicon.txt` to bias transcription

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher

### Installation

1. Clone and install dependencies:
   ```bash
   git clone https://github.com/davemontore/moneypenny.git
   cd moneypenny
   pip install -r requirements.txt
   ```

2. Start the app (choose one):
   - Console: `python voice_to_text.py`
   - Double‑click: `MoneyPenny Voice Typing.bat`

3. Use it:
   - Place the cursor in any text field
   - Hold RIGHT CTRL to dictate
   - Release to transcribe; text will be typed automatically
   - Quit: Ctrl+Alt+Q (or ESC if running in console)

### Start automatically at login

- Console visible at login (simple):
  1) Press Win+R → `shell:startup` → Enter
  2) Copy your desktop shortcut for `MoneyPenny Voice Typing.bat` into that folder

- Hidden at login (no console window):
  1) Create `run_silent.vbs` in the project folder with:
     ```vbscript
     Set WshShell = CreateObject("WScript.Shell")
     WshShell.Run "cmd /c python voice_to_text.py", 0, False
     ```
  2) Right‑click `run_silent.vbs` → Create shortcut
  3) Move that shortcut into the Startup folder (`shell:startup`)

Note: Use either the `.bat` shortcut OR the VBS shortcut in Startup, not both, to avoid launching two copies.

## ⚙️ Configuration

- Default model: `base.en` on CPU (`int8`) for a good speed/accuracy balance
- Faster option: set `MODEL_SIZE = "tiny.en"` in `voice_to_text.py`
- GPU option: change model init to `device="cuda", compute_type="float16"`
 - Lexicon: create `lexicon.txt` (one term/phrase per line). Example:
   ```
   # military terms
   JTAC
   ISR
   CAS
   # medical
   psilocybin
   ibogaine
   # places
   Pattaya
   Khost
   ```

## 📁 Project Structure

```
MoneyPenny/
├── voice_to_text.py            # Main application (headless, hotkeys)
├── requirements.txt            # Python dependencies
├── MoneyPenny Voice Typing.bat # Windows launcher (console)
├── run_silent.vbs              # Optional hidden launcher (no console)
├── CHANGELOG.md                # Version history
├── DEBUGGING_REFERENCE.md      # Troubleshooting guide
└── README.md                   # This file
```

## 🔍 Troubleshooting

- Nothing happens when holding RIGHT CTRL:
  - Ensure the app is running (via console or launcher)
  - Try running the console as Administrator (hotkeys may need elevation)
  - Make sure the text caret is in a text field
  - Check microphone default device and levels in Windows

- To stop the app:
  - Ctrl+Alt+Q (works for both console and hidden)
  - Or close the console window if running via `.bat`

## 📄 License

MIT License - see the [LICENSE](LICENSE)

## Notes

- Previous GUI and cloud API features are deprecated in v2.2.0 in favor of a faster, simpler, local workflow.

---

## 🟢 Simple Setup for Non‑Technical Users (Windows)

These steps avoid any coding or commands. You’ll click and open files like any normal app.

- What you need:
  - A Windows 10/11 PC with a microphone
  - Internet connection the first time (to download the voice model)

1) Install Python
   - Go to `https://www.python.org/downloads/`
   - Click “Download Python 3.x”
   - In the installer: check “Add Python to PATH”, then click “Install Now”

2) Get the app
   - Go to the project page: `https://github.com/davemontore/moneypenny`
   - Click the green “Code” button → “Download ZIP”
   - Right‑click the downloaded ZIP → “Extract All...”
   - Put the extracted “MoneyPenny” folder in your Documents folder

3) Start the app
   - Open the “MoneyPenny” folder
   - Double‑click “MoneyPenny Voice Typing.bat”
   - The first run will download the voice model (takes a minute). When you see “Whisper model loaded.” it’s ready
   - If Windows warns you (SmartScreen), click “More info” → “Run anyway”

4) Use it
   - Click into any text field (Notepad, email, browser)
   - Hold the RIGHT CTRL key while you speak
   - Release RIGHT CTRL to finish; your words will appear
   - To stop the app: press Ctrl+Alt+Q (or close the black window if it’s open)

5) Make it start automatically (optional)
   - Press the Windows key + R → type `shell:startup` → press Enter
   - In another window, find your “MoneyPenny” folder
   - Right‑click “MoneyPenny Voice Typing.bat” → “Create shortcut”
   - Drag that shortcut into the Startup folder you opened
   - That’s it. Next time you sign in, the app starts for you
   - Want no black window? See “Hidden at login” instructions above; if that’s confusing, use the AI prompts below

6) Add uncommon words (optional)
   - In the “MoneyPenny” folder, double‑click `lexicon.txt`
   - Type one word or phrase per line (e.g., names, medical terms)
   - Save the file and restart the app

### Copy‑and‑paste prompts for an AI helper (optional)

- “I’m on Windows 11. Help me install Python with ‘Add to PATH’ checked and confirm it’s installed.”
- “I downloaded `moneypenny` as a ZIP from GitHub. Walk me through extracting it to Documents and running ‘MoneyPenny Voice Typing.bat’.”
- “Create a `run_silent.vbs` file next to `voice_to_text.py` that starts the app hidden, and help me put a shortcut to it in `shell:startup` so it runs at login.”
- “I want to add words to improve transcription. Show me how to edit `lexicon.txt`, save it, and restart the app.”