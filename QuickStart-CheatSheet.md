# MoneyPenny v3.0 — QuickStart Cheat Sheet (Windows)

## What it does

- Hold **RIGHT CTRL** while speaking; release it to type the transcription into the app you are using.
- Choose fast cloud transcription or a slower offline local model in MoneyPenny's Settings tab.
- Closing the settings window hides MoneyPenny to the system tray; it does not quit the app.

## Install and start

1. Install Python 3.10, 3.11, 3.12, or 3.13 from [python.org](https://www.python.org/downloads/windows/). Check **Add Python to PATH** in its installer.
2. On GitHub, choose **Code → Download ZIP**, then right-click the ZIP and choose **Extract All**.
3. Open the extracted MoneyPenny folder and double-click `MoneyPenny Voice Typing.bat`.
4. Wait while the first launch installs MoneyPenny's tested components inside its private `.venv` folder.
5. In Settings, choose one transcription method:
   - **Cloud / Groq (recommended):** create a free key at `console.groq.com`, paste it into the Groq API Key field, and save.
   - **Local:** no key is needed; the speech model downloads on first use.

## Use

1. Click in any text field, such as Notepad, email, or a browser form.
2. Hold **RIGHT CTRL** and speak.
3. Release **RIGHT CTRL**; the text appears after transcription finishes.
4. Quit with **Ctrl+Alt+Q** or by right-clicking the tray icon and choosing **Exit**.

## Start automatically at login (optional)

1. Right-click `MoneyPenny Voice Typing.bat` and choose **Create shortcut**.
2. Press **Win+R**, enter `shell:startup`, and press **Enter**.
3. Move the shortcut into the folder that opens.
4. Double-click the shortcut once to test it. Keep only one MoneyPenny shortcut there.

## Personal files

- `settings.json` stores your choices and API keys.
- `lexicon.txt` stores your custom vocabulary.
- Both files remain on your computer and are excluded from GitHub.

## Quick troubleshooting

- **Python missing or unsupported:** install Python 3.10–3.13 and check **Add Python to PATH**, then rerun `Install MoneyPenny.bat`.
- **Setup fails:** check the internet connection and rerun `Install MoneyPenny.bat`.
- **Hotkey does nothing:** confirm MoneyPenny is running, click inside a text field, and check the Windows microphone settings.
- **Need diagnostic details:** open `logs\moneypenny.log` and review the latest entries.

## Reference

- **Version:** 3.0
- **Default hotkey:** RIGHT CTRL (hold to record, release to transcribe)
- **Quit:** Ctrl+Alt+Q or tray icon → Exit
- **Normal launcher:** `MoneyPenny Voice Typing.bat`
- **Installer/repair:** `Install MoneyPenny.bat`
