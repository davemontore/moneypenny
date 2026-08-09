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
- Python 3.10, 3.11, 3.12, or 3.13 from [python.org](https://www.python.org/downloads/windows/)

### Installation

1. Download the project from GitHub with **Code → Download ZIP**, then choose **Extract All**. Do not run it from inside the ZIP.
2. Open the extracted folder and double-click `MoneyPenny Voice Typing.bat`.
   - The first launch installs MoneyPenny's tested components inside its own folder. This can take several minutes.
   - Later launches open the settings window directly and place an icon in the system tray near the clock.
   - You can also double-click `Install MoneyPenny.bat` to install or repair the components without starting the app.

3. In MoneyPenny, choose how to transcribe:
   - **Cloud mode (recommended, fastest)**: Get a free API key at `console.groq.com`, then in the app's Settings tab set Transcription Mode = Cloud, Provider = Groq, paste the key, and click Save Settings
   - **Local mode (offline)**: No setup needed — the speech model downloads automatically on first run (takes a minute), then it's ready

4. Use it:
   - Place the cursor in any text field
   - Hold RIGHT CTRL to dictate
   - Release to transcribe; text will be typed automatically
   - Note: closing the window does NOT quit the app — it hides to the tray. To quit: Ctrl+Alt+Q or right‑click the tray icon → Exit

### Start automatically at login

1. Right-click `MoneyPenny Voice Typing.bat` and choose **Create shortcut**.
2. Press Win+R, enter `shell:startup`, and press Enter.
3. Move the new shortcut into the folder that opens.
4. Test the shortcut by double-clicking it. MoneyPenny should open without a black console window.

Keep only one MoneyPenny shortcut in the Startup folder. Remove it whenever you no longer want MoneyPenny to start at login.

## ⚙️ Configuration

All settings live in the app's **Settings tab** (double‑click the tray icon to open the window):

- **Transcription Mode**: Cloud (fast, needs internet + API key) or Local (offline, slower)
- **Cloud Provider**: Groq (usually fastest) or OpenRouter, with separate API key and model fields for each
- **Local Model**: `tiny.en` (fastest) or `base.en` (more accurate) — used in Local mode
- **Microphone**: System default or a specific device
- **Record Hotkey**: RIGHT CTRL by default; several alternatives available (a change takes effect after restarting the app)

Custom words: use the **Dictionary tab**, or edit your private `lexicon.txt` file directly (one term or phrase per line). The file remains on your computer and is not uploaded to GitHub. Example:

```
# organization
Acme Corporation
# project
Project Skylark
```

## 📁 Project Structure

```
MoneyPenny/
├── voice_to_text.py            # Main application (recording, hotkeys, transcription)
├── gui.py                      # Settings window and system tray
├── Install MoneyPenny.bat      # One-click setup and repair
├── requirements.txt            # Python dependencies
├── MoneyPenny Voice Typing.bat # Windows launcher (recommended)
├── MoneyPenny Headless.bat     # Launcher without settings window/tray
├── lexicon.example.txt         # Safe starter for the private dictionary
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

- Setup says Python is missing or unsupported:
  - Install Python 3.10 through 3.13 from python.org and check **Add Python to PATH** in its installer
  - Then double-click `Install MoneyPenny.bat` again

- Setup fails while installing components:
  - Make sure the computer is online, then double-click `Install MoneyPenny.bat` again
  - The setup changes only the `.venv` folder inside MoneyPenny; delete that folder and rerun setup if a repair is needed

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
   - Install Python 3.10, 3.11, 3.12, or 3.13
   - In the installer: check “Add Python to PATH”, then click “Install Now”

2) Get the app
   - Go to the project page: `https://github.com/davemontore/moneypenny`
   - Click the green “Code” button → “Download ZIP”
   - Right‑click the downloaded ZIP → “Extract All...”
   - Put the extracted “MoneyPenny” folder in your Documents folder

3) Start the app
   - Open the “MoneyPenny” folder
   - Double‑click “MoneyPenny Voice Typing.bat”
   - The first launch sets up MoneyPenny inside its own folder; wait for the setup window to say it is complete
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
   - Press Windows key + R → type `shell:startup` → Enter
   - In another window, open your “MoneyPenny” folder
   - Right‑click “MoneyPenny Voice Typing.bat” → “Create shortcut”
   - Drag that shortcut into the Startup folder you opened
   - Next time you sign in, the app starts automatically
   - The launcher opens MoneyPenny without a black console window after setup is complete

7) Add uncommon words (optional)
   - Open the app's Dictionary tab, type a word, click Add
   - (Or edit `lexicon.txt` in the “MoneyPenny” folder — one word or phrase per line — then restart the app)

### Copy‑and‑paste prompts for an AI helper (optional)

- “I’m on Windows 11. Help me install Python with ‘Add to PATH’ checked and confirm it’s installed.”
- “I downloaded `moneypenny` as a ZIP from GitHub. Walk me through extracting it to Documents and running ‘MoneyPenny Voice Typing.bat’.”
- “Help me create a shortcut to `MoneyPenny Voice Typing.bat` and put it in my Windows `shell:startup` folder.”
- “I want to add words to improve transcription. Show me how to edit `lexicon.txt`, save it, and restart the app.”