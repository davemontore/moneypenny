# MoneyPenny v3.1 — QuickStart Cheat Sheet (Windows)

## What it does

- Hold **RIGHT CTRL** while speaking; release it to type the transcription into the app you are using.
- Choose fast cloud transcription or a slower offline local model in MoneyPenny's Settings tab.
- The default **Commands only** cleanup keeps ordinary dictation on the fast single-request path and invokes contextual cleanup only for likely verbal punctuation.
- Closing the settings window hides MoneyPenny to the system tray; it does not quit the app.

## Install and start

1. On GitHub's **Releases** page, download `MoneyPenny-Windows-x64.zip` from the newest release.
2. Right-click the ZIP and choose **Extract All**.
3. Open the extracted folder and double-click `MoneyPenny.exe`.
4. Optional: run `Create MoneyPenny Shortcuts.bat` to add branded Start Menu and taskbar shortcuts.
5. In Settings, choose one transcription method:
   - **Cloud / Groq (recommended):** create a free key at `console.groq.com`, paste it into the Groq API Key field, and save.
   - **Local:** no key is needed; the speech model downloads on first use.

## Use

1. Click in any text field, such as Notepad, email, or a browser form.
2. Hold **RIGHT CTRL** and speak.
3. Release **RIGHT CTRL**; the text appears after transcription finishes.
4. Quit with **Ctrl+Alt+Q** or by right-clicking the tray icon and choosing **Exit**.

### Spoken punctuation

- Say `quote hello quote` to type `"hello"`.
- You can also say `open quote hello close quote` or `open quote hello end quote`.
- Other commands include `comma`, `period`, `question mark`, `exclamation point`, `colon`, `semicolon`, `new line` / `new paragraph` (line break; works in every app, never sends — say twice for a blank line), `open parenthesis`, `close parenthesis`, `slash`, and `backslash`.
- To discuss punctuation as words, use natural context such as `the word comma` or `a comma`.
- The full command reference is on the Dictionary tab.

## Start automatically at login (optional)

1. Right-click the MoneyPenny Start Menu shortcut or `MoneyPenny.exe` and choose **Create shortcut**.
2. Press **Win+R**, enter `shell:startup`, and press **Enter**.
3. Move the shortcut into the folder that opens.
4. Double-click the shortcut once to test it. Keep only one MoneyPenny shortcut there.

## Personal files

- `settings.json` stores your choices and API keys.
- `lexicon.txt` stores your custom vocabulary.
- `transcript_history.jsonl` stores raw and cleaned captured transcripts for the History tab.
- All three files remain on your computer and are excluded from GitHub.

## Quick troubleshooting

- **Windows shows a safety warning:** tagged builds are currently unsigned; choose **More info → Run anyway** only when downloaded from the official repository.
- **Source installation fails:** install Python 3.10–3.13, check **Add Python to PATH**, confirm internet access, and rerun `Install MoneyPenny.bat`.
- **Hotkey does nothing:** confirm MoneyPenny is running, click inside a text field, and check the Windows microphone settings.
- **Need diagnostic details:** open `logs\moneypenny.log` and review the latest entries.

## Reference

- **Version:** 3.1.1
- **Default hotkey:** RIGHT CTRL (hold to record, release to transcribe)
- **Quit:** Ctrl+Alt+Q or tray icon → Exit
- **Normal release launcher:** `MoneyPenny.exe`
- **Source installer/repair:** `Install MoneyPenny.bat`
