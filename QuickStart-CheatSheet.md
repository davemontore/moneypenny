# MoneyPenny v3.1 — QuickStart Cheat Sheet (Windows)

## What it does

- Hold **RIGHT CTRL** while speaking; release it to type the transcription into the app you are using.
- Choose fast cloud transcription or a slower offline local model in MoneyPenny's Settings tab.
- Common punctuation commands run locally. The default **Commands only** cleanup keeps ordinary dictation on the fast path and invokes contextual cleanup only for remaining ambiguous punctuation.
- Closing the settings window hides MoneyPenny to the system tray; it does not quit the app.

## Install and start

1. On GitHub's **Releases** page, download `MoneyPenny-Windows-x64.zip` from the newest release.
2. Right-click the ZIP and choose **Extract All**.
3. Open the extracted folder and double-click `MoneyPenny.exe`.
4. Optional: run `Create MoneyPenny Shortcuts.bat` to add branded Start Menu and taskbar shortcuts.
5. In Settings, choose one transcription method:
   - **Cloud / Groq (recommended):** create a free key at `console.groq.com`, paste it into the Groq API Key field, and save.
   - **Cloud / Deepgram Nova-3:** paste a Deepgram API key to test native spoken punctuation and paragraph commands.
   - **Local:** no key is needed; the speech model downloads on first use.

### Compare punctuation engines

1. Add the cloud API keys you want to compare in Settings.
2. Enable **Punctuation Lab: compare configured cloud engines** and save.
3. Use the normal hotkey and read the same punctuation test script once.
4. MoneyPenny saves the WAV and comparable results under `punctuation_lab`. It types nothing while the lab is enabled.
5. Disable Punctuation Lab and save before returning to normal dictation.

Lab recordings and transcripts stay in the app folder, but each comparison consumes the configured providers' credits.

## Use

1. Click in any text field, such as Notepad, email, or a browser form.
2. Hold **RIGHT CTRL** and speak.
3. Release **RIGHT CTRL**; the text appears after transcription finishes.
4. Quit with **Ctrl+Alt+Q** or by right-clicking the tray icon and choosing **Exit**.

### Spoken punctuation

> **Pre-public limitation:** isolated commands work locally, but dense
> coding-oriented punctuation is still being hardened. Review dictated code
> before running or submitting it.

- Quotes: say `quote ... end quote`, `quote ... quote`, or `open quote ... close quote`.
- Other commands include `comma`, `period`, `question mark`, `exclamation point`, `colon`, `semicolon`, `new line` (one safe Shift+Enter break), `new paragraph` (two safe breaks with a blank line), `open parenthesis`, `close parenthesis`, `slash`, and `backslash`.
- To discuss punctuation as words, use natural context such as `the word comma`, `a comma`, or `the words new paragraph`.
- The full command reference is on the Dictionary tab.

### Teach an immediate correction

1. Within 10 seconds of a transcript appearing, press Backspace and retype its ending.
2. Do not click elsewhere or move the caret during the correction.
3. Pause for about one second and confirm MoneyPenny's proposed correction.

MoneyPenny saves nothing if you decline. Turn this trial feature off with **Suggest corrections after immediate Backspace and retype** in Settings.

## Start automatically at login (optional)

1. Right-click the MoneyPenny Start Menu shortcut or `MoneyPenny.exe` and choose **Create shortcut**.
2. Press **Win+R**, enter `shell:startup`, and press **Enter**.
3. Move the shortcut into the folder that opens.
4. Double-click the shortcut once to test it. Keep only one MoneyPenny shortcut there.

## Personal files

- `settings.json` stores your choices and API keys.
- `lexicon.txt` stores your custom vocabulary.
- `corrections.json` stores guaranteed heard-as → type-as replacements.
- `transcript_history.jsonl` stores raw and cleaned captured transcripts for the History tab.
- `punctuation_lab` stores opt-in test recordings and comparison results.
- These files remain on your computer and are excluded from GitHub.

## Quick troubleshooting

- **Windows shows a safety warning:** tagged builds are currently unsigned; choose **More info → Run anyway** only when downloaded from the official repository.
- **Source installation fails:** install Python 3.10–3.13, check **Add Python to PATH**, confirm internet access, and rerun `Install MoneyPenny.bat`.
- **Hotkey does nothing:** confirm MoneyPenny is running, click inside a text field, and check the Windows microphone settings.
- **Need diagnostic details:** open `logs\moneypenny.log` and review the latest entries.

## Reference

- **Version:** 3.1.2
- **Default hotkey:** RIGHT CTRL (hold to record, release to transcribe)
- **Quit:** Ctrl+Alt+Q or tray icon → Exit
- **Normal release launcher:** `MoneyPenny.exe`
- **Source installer/repair:** `Install MoneyPenny.bat`
