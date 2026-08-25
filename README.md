# MoneyPenny - Voice Typing Assistant

> A fast voice‑to‑text utility for Windows. Hold RIGHT CTRL to dictate, release to transcribe into the current text field.

## ✨ Features

- **Hold‑to‑record**: Press and hold RIGHT CTRL, release to transcribe
- **Types into any app**: Output is typed into the focused window
- **Cloud or local transcription**: Cloud mode (Groq or OpenRouter) is fast and accurate; Local mode (faster-whisper) works offline. Choose in the Settings tab.
- **Reliable spoken punctuation**: Common commands and paired quotations run locally; ambiguous literal phrases such as "the word comma" can still use selective AI cleanup
- **Settings window + system tray**: A GUI with Settings, Dictionary, History, and Status tabs. Closing the window hides it to the tray so it keeps listening.
- **Single-instance window restore**: Launching MoneyPenny again restores and focuses the existing window instead of opening a duplicate or an informational dialog.
- **Preferred vocabulary and exact corrections**: Bias uncommon terminology, or guarantee local replacements such as `Whisper Flow` → `Wispr Flow` and `C sharp` → `C#`
- **Correction recognition**: Immediately Backspace and retype the end of a new transcript; MoneyPenny asks whether to learn the change as an exact correction
- **Captured transcript history**: Review raw and cleaned transcripts locally in the History tab
- **Spoken punctuation**: Say commands such as `comma`, `question mark`, `new line` (a safe Shift+Enter break; say it twice for a blank line), or `quote ... end quote`; see the reference in the Dictionary tab
- **Quick exit**: Press Ctrl+Alt+Q, or right-click the tray icon → Exit

## 🚀 Quick Start

### Install the Windows app (recommended)

1. Open the repository's [**Releases** page](https://github.com/davemontore/moneypenny/releases) and download `MoneyPenny-Windows-x64.zip` from the newest release.
2. Choose **Extract All**. Do not run MoneyPenny from inside the ZIP.
3. Open the extracted folder and double-click `MoneyPenny.exe`.
4. Optionally run `Create MoneyPenny Shortcuts.bat` to add branded Start Menu and taskbar shortcuts.

This route needs only Windows 10/11 and a microphone—Python is already included in the release.

### Install from source (developers and contributors)

1. Install Python 3.10, 3.11, 3.12, or 3.13 from [python.org](https://www.python.org/downloads/windows/).
2. Download the source with **Code → Download ZIP** and choose **Extract All**, or clone the repository with Git.
3. Open the project folder and double-click `Install MoneyPenny.bat`.
   - Setup creates a private `.venv`, installs pinned dependencies, runs checks, and builds the branded `dist\MoneyPenny\MoneyPenny.exe`.
   - Setup creates branded Start Menu and taskbar shortcuts and refreshes Explorer once.
   - Later launches can use the taskbar shortcut or `MoneyPenny Voice Typing.bat`.
   - Run `Fix MoneyPenny Taskbar Icon.bat` to rebuild the executable and refresh its shortcuts after icon-related changes.

### First run

1. In MoneyPenny, choose how to transcribe:
   - **Cloud mode (recommended, fastest)**: Get a free API key at `console.groq.com`, then in the app's Settings tab set Transcription Mode = Cloud, Provider = Groq, paste the key, and click Save Settings
   - **Local mode (offline)**: No setup needed — the speech model downloads automatically on first run (takes a minute), then it's ready

2. Use it:
   - Place the cursor in any text field
   - Hold RIGHT CTRL to dictate
   - Release to transcribe; text will be typed automatically
   - For quoted text, say `quote this is quoted quote` or `open quote this is quoted end quote`; MoneyPenny types `"this is quoted"`
   - For a line break, say `new line`, `newline`, or `new paragraph`; all use safe Shift+Enter and never submit a chat message. Say the command twice for a blank line.
   - When discussing punctuation itself, use natural context such as `the word comma` or `a comma`
   - Note: closing the window does NOT quit the app — it hides to the tray. To quit: Ctrl+Alt+Q or right-click the tray icon → Exit

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
- **AI Transcript Cleanup**: Local commands do not need AI. `Commands only` (default) invokes `openai/gpt-oss-20b` only for remaining likely verbal punctuation; `Off` never invokes it and `Always` cleans every transcript
- **Correction Recognition**: Enabled by default for this trial. It watches only the same focused text control for 10 seconds after dictation and asks before saving any rule. Disable it independently in Settings.
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

Preferred vocabulary is a soft hint to the transcription model. For guaranteed spelling, add an **Exact Correction** in the same tab: enter what transcription usually produces under **Heard as**, and the required output under **Type as**. Exact corrections run locally and are stored privately in `corrections.json`.

To teach an immediate correction, use Backspace at the end of a freshly typed transcript and retype the corrected ending without clicking elsewhere or moving the caret. Pause for about one second; MoneyPenny shows the proposed heard-as → type-as rule and saves it only if you confirm.

Captured transcripts are stored locally in `transcript_history.jsonl`, shown in the **History** tab, and excluded from Git.

## 📁 Project Structure

```
MoneyPenny/
├── voice_to_text.py            # Main application (recording, hotkeys, transcription)
├── gui.py                      # Settings window and system tray
├── Install MoneyPenny.bat      # One-click setup and repair
├── Build MoneyPenny.exe.bat    # Reproducible branded Windows build
├── MoneyPenny.spec             # PyInstaller build definition
├── requirements.txt            # Python dependencies
├── requirements-build.txt      # Pinned Windows build dependency
├── MoneyPenny Voice Typing.bat # Windows launcher (recommended)
├── MoneyPenny Headless.bat     # Launcher without settings window/tray
├── lexicon.example.txt         # Safe starter for the private dictionary
├── corrections.example.json   # Example deterministic spelling corrections
├── CHANGELOG.md                # Version history
├── QuickStart-CheatSheet.md    # One-page usage reference
├── ROADMAP.md                  # Product and installation direction
├── DECISIONS.md                # Significant decisions and their reasons
├── LESSONS_LEARNED.md          # Reusable engineering lessons
├── SESSION_CLOSEOUT.md         # End-of-day release checklist
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
   - Open the app's Dictionary tab and add a preferred word as a soft recognition hint
   - For guaranteed spelling, add an Exact Correction with **Heard as** and **Type as**
   - (Or edit `lexicon.txt` in the “MoneyPenny” folder — one word or phrase per line — then restart the app)

### Copy‑and‑paste prompts for an AI helper (optional)

- “I’m on Windows 11. Help me install Python with ‘Add to PATH’ checked and confirm it’s installed.”
- “I downloaded `moneypenny` as a ZIP from GitHub. Walk me through extracting it to Documents and running ‘MoneyPenny Voice Typing.bat’.”
- “Help me create a shortcut to `MoneyPenny Voice Typing.bat` and put it in my Windows `shell:startup` folder.”
- “I want to add words to improve transcription. Show me how to edit `lexicon.txt`, save it, and restart the app.”
