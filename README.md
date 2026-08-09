# MoneyPenny - Voice Typing Assistant

> A fast voice‑to‑text utility for Windows. Hold RIGHT CTRL to dictate, release to transcribe into the current text field.

## ✨ Features

- **Hold‑to‑record**: Press and hold RIGHT CTRL, release to transcribe
- **Types into any app**: Output is typed into the focused window
- **Cloud or local transcription**: Cloud mode (Groq or OpenRouter) is fast and accurate; Local mode (faster-whisper) works offline. Choose in the Settings tab.
- **Settings window + system tray**: A simple GUI with Settings, Dictionary, and Status tabs. Closing the window hides it to the tray so it keeps listening.
- **Custom dictionary**: Add names, jargon, and uncommon words (Dictionary tab or `lexicon.txt`) to improve recognition
- **Quick exit**: Press Ctrl+Alt+Q, or right‑click the tray icon → Exit
- **One copy at a time**: Launching a second copy just reminds you it's already running

## 🚀 Quick Start

### Prerequisites
- Windows 10/11 with a microphone
- Python 3.8 or higher

### Installation

1. Clone and install dependencies:
   ```bash
   git clone https://github.com/davemontore/moneypenny.git
   cd moneypenny
   pip install -r requirements.txt
   ```

2. Start the app:
   - Double‑click `MoneyPenny Voice Typing.bat` (recommended), or run `python voice_to_text.py`
   - The settings window opens, and an icon appears in the system tray (near the clock)

3. First‑run setup (choose one):
   - **Cloud mode (recommended, fastest)**: Get a free API key at `console.groq.com`, then in the app's Settings tab set Transcription Mode = Cloud, Provider = Groq, paste the key, and click Save Settings
   - **Local mode (offline)**: No setup needed — the speech model downloads automatically on first run (takes a minute), then it's ready

4. Use it:
   - Place the cursor in any text field
   - Hold RIGHT CTRL to dictate
   - Release to transcribe; text will be typed automatically
   - Note: closing the window does NOT quit the app — it hides to the tray. To quit: Ctrl+Alt+Q or right‑click the tray icon → Exit

### Start automatically at login

- Console visible at login (simple):
  1) Press Win+R → `shell:startup` → Enter
  2) Copy your desktop shortcut for `MoneyPenny Voice Typing.bat` into that folder

- Hidden at login (no console window):
  1) Press Win+R → type `shell:startup` → press Enter (a folder opens)
  2) In that folder: right‑click empty space → New → Shortcut
  3) In “Type the location of the item”, paste:
     "C:\\Windows\\pyw.exe" -3 "C:\\Users\\Owner\\Documents\\MoneyPenny\\voice_to_text.py"
     - If this shows an error, your system may not have `pyw.exe`. Use your Python’s `pythonw.exe` instead, for example:
       "C:\\Users\\Owner\\AppData\\Local\\Programs\\Python\\Python311\\pythonw.exe" "C:\\Users\\Owner\\Documents\\MoneyPenny\\voice_to_text.py"
  4) Click Next → name it: `MoneyPenny Voice Typing (hidden)` → Finish
  5) Right‑click the new shortcut → Properties → in “Start in” paste:
     C:\\Users\\Owner\\Documents\\MoneyPenny
     → Click OK
  6) Test by double‑clicking the shortcut: no window should appear. Put the caret in a text field, hold RIGHT CTRL, then release to transcribe. Quit with Ctrl+Alt+Q.

Note: Keep only one Startup entry (either the `.bat` shortcut or this hidden shortcut) to avoid two copies.

## ⚙️ Configuration

All settings live in the app's **Settings tab** (double‑click the tray icon to open the window):

- **Transcription Mode**: Cloud (fast, needs internet + API key) or Local (offline, slower)
- **Cloud Provider**: Groq (usually fastest) or OpenRouter, with separate API key and model fields for each
- **Local Model**: `tiny.en` (fastest) or `base.en` (more accurate) — used in Local mode
- **Microphone**: System default or a specific device
- **Record Hotkey**: RIGHT CTRL by default; several alternatives available (a change takes effect after restarting the app)

Custom words: use the **Dictionary tab**, or edit `lexicon.txt` directly (one term/phrase per line). Example:

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
├── voice_to_text.py            # Main application (recording, hotkeys, transcription)
├── gui.py                      # Settings window and system tray
├── requirements.txt            # Python dependencies
├── MoneyPenny Voice Typing.bat # Windows launcher (recommended)
├── MoneyPenny Headless.bat     # Console-mode launcher (no GUI)
├── lexicon.txt                 # Custom dictionary (one term per line)
├── CHANGELOG.md                # Version history
├── QuickStart-CheatSheet.md    # One-page usage reference
└── README.md                   # This file
```

## 🔍 Troubleshooting

- Nothing happens when holding RIGHT CTRL:
  - Ensure the app is running (via console or launcher)
  - Try running the console as Administrator (hotkeys may need elevation)
  - Make sure the text caret is in a text field
  - Check microphone default device and levels in Windows

- The window closed but the app seems to still be running:
  - That's by design — closing the window hides the app to the system tray so it keeps listening
  - To quit fully: Ctrl+Alt+Q, or right‑click the tray icon → Exit

- To stop the app:
  - Ctrl+Alt+Q (works in every mode)
  - Or right‑click the tray icon → Exit

- Logs (for crash diagnosis):
  - A detailed log file is written to `logs/moneypenny.log` next to `voice_to_text.py`.
  - After a crash, open that file and review the last 100 lines.
  - If you need help, share those last 100 lines here so we can pinpoint the cause.

## 📄 License

MIT License - see the [LICENSE](LICENSE)

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
   - A settings window opens, and a small icon appears near the clock (the system tray)
   - If Windows warns you (SmartScreen), click “More info” → “Run anyway”

4) Choose how it transcribes (one time)
   - **Recommended — Cloud (fastest):** go to `https://console.groq.com`, sign up free, create an API key. In the app's Settings tab: Transcription Mode = Cloud, Provider = Groq, paste the key, click Save Settings
   - **Or — Local (offline, slower):** nothing to do; the first run downloads the voice model automatically (takes a minute)

5) Use it
   - Click into any text field (Notepad, email, browser)
   - Hold the RIGHT CTRL key while you speak
   - Release RIGHT CTRL to finish; your words will appear
   - Important: closing the window does NOT quit the app — it hides to the tray so it can keep listening
   - To quit fully: press Ctrl+Alt+Q, or right‑click the tray icon → Exit

6) Make it start automatically (optional)
   - Option A (shows a black window):
     - Press Windows key + R → type `shell:startup` → Enter
     - In another window, open your “MoneyPenny” folder
     - Right‑click “MoneyPenny Voice Typing.bat” → “Create shortcut”
     - Drag that shortcut into the Startup folder you opened
     - Next time you sign in, the app starts automatically
   - Option B (hidden, no window):
     - Follow the “Hidden at login (no console window)” steps above. It uses `pyw.exe/pythonw.exe` and a shortcut with the correct “Start in” folder.

7) Add uncommon words (optional)
   - Open the app's Dictionary tab, type a word, click Add
   - (Or edit `lexicon.txt` in the “MoneyPenny” folder — one word or phrase per line — then restart the app)

### Copy‑and‑paste prompts for an AI helper (optional)

- “I’m on Windows 11. Help me install Python with ‘Add to PATH’ checked and confirm it’s installed.”
- “I downloaded `moneypenny` as a ZIP from GitHub. Walk me through extracting it to Documents and running ‘MoneyPenny Voice Typing.bat’.”
- “Create a Startup shortcut that runs `pyw.exe` (or `pythonw.exe`) with `voice_to_text.py`, set the ‘Start in’ folder to my MoneyPenny folder, and place it in `shell:startup` so it runs hidden at login.”
- “I want to add words to improve transcription. Show me how to edit `lexicon.txt`, save it, and restart the app.”