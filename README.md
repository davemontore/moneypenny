# MoneyPenny

Voice typing for Windows: hold Right Ctrl while you speak, then release it to type the transcription into the app you are already using.

MoneyPenny can use a fast cloud transcription provider or run an offline speech model on your computer. It also handles spoken punctuation, preferred vocabulary, exact spelling corrections, transcript history, and optional correction learning.

## Install the Windows app

The packaged release is the shortest path for most people.

1. Open [Releases](https://github.com/davemontore/moneypenny/releases).
2. Download `MoneyPenny-Windows-x64.zip` from the newest release.
3. Choose **Extract All**. Do not run the app from inside the ZIP.
4. Open the extracted folder and double-click `MoneyPenny.exe`.
5. Optional: run `Create MoneyPenny Shortcuts.bat` to add Start Menu and taskbar shortcuts.

The packaged app includes Python. It requires Windows 10 or 11 and a microphone.

## Choose how transcription works

Open the **Settings** tab and select one mode:

- **Cloud:** usually faster. Choose Groq or OpenRouter and provide that service's API key.
- **Local:** runs `faster-whisper` on the computer and does not need a transcription API key. The speech model downloads on first use.

Cloud mode sends each recording to the selected provider for transcription. Local mode keeps transcription on the computer. Settings, vocabulary, correction rules, and captured history are stored locally and excluded from Git.

## Dictate into any text field

1. Put the text cursor in Notepad, email, a browser form, or another text field.
2. Hold **Right Ctrl** and speak.
3. Release **Right Ctrl**. MoneyPenny transcribes the recording and types the result into the focused field.

Closing the settings window hides MoneyPenny in the system tray; it does not quit. Press **Ctrl+Alt+Q**, or right-click the tray icon and choose **Exit**, to stop the app.

### Spoken punctuation

MoneyPenny recognizes commands including `comma`, `period`, `question mark`, `new line`, and paired quotes. Say `new line` twice for a blank line. Use phrases such as `the word comma` when you want the literal word rather than punctuation.

The Dictionary tab contains the full command reference.

### Vocabulary and exact corrections

- Add uncommon names and terms as preferred vocabulary in the **Dictionary** tab.
- Add an **Exact Correction** when one transcription must always be replaced with specific text.
- With correction recognition enabled, immediately backspace and retype the end of a new transcript. MoneyPenny proposes a rule and saves it only after confirmation.

## Start automatically at sign-in

1. Create a shortcut to `MoneyPenny.exe`.
2. Press **Win+R**, enter `shell:startup`, and press Enter.
3. Move the shortcut into the folder that opens.
4. Double-click the shortcut once to confirm it starts correctly.

Keep only one MoneyPenny shortcut in the Startup folder.

## Install from source

Source development supports Python 3.10 through 3.13.

```powershell
git clone https://github.com/davemontore/moneypenny.git
cd moneypenny
& '.\Install MoneyPenny.bat'
```

The installer creates a project-local `.venv`, installs the pinned dependencies, runs checks, and builds `dist\MoneyPenny\MoneyPenny.exe`.

Useful development commands and files:

- `MoneyPenny Voice Typing.bat`: normal source launcher
- `MoneyPenny Headless.bat`: launcher without the settings window or tray
- `Build MoneyPenny.exe.bat`: reproducible Windows build
- `python -m unittest discover -s tests`: transcript and single-instance tests
- `logs\moneypenny.log`: local diagnostic log

## Personal files

MoneyPenny creates these private local files as features are used:

| File | Purpose |
|---|---|
| `settings.json` | App choices and provider settings |
| `lexicon.txt` | Preferred vocabulary |
| `corrections.json` | Exact heard-as to type-as replacements |
| `transcript_history.jsonl` | Captured raw and cleaned transcripts |

They are excluded from the repository. Do not commit API keys, transcripts, or personal dictionaries.

## Troubleshooting

- **The hotkey does nothing:** confirm MoneyPenny is running, place the caret in a text field, and check Windows microphone access.
- **Cloud transcription fails:** verify the selected provider and API key, or switch to Local mode.
- **The first local transcription is slow:** wait for the speech model download to finish.
- **The window disappeared:** double-click the tray icon. Closing the window hides it by design.
- **The app crashed:** inspect the latest entries in `logs\moneypenny.log`.

See [QuickStart-CheatSheet.md](QuickStart-CheatSheet.md) for the one-page operating reference, [CHANGELOG.md](CHANGELOG.md) for release history, and [ROADMAP.md](ROADMAP.md) for planned work.

## License

MoneyPenny is available under the [MIT License](LICENSE).
