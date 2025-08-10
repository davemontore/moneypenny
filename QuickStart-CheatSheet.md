# MoneyPenny Voice Typing — One‑Page Cheat Sheet (Windows)

- What it does: Hold RIGHT CTRL to dictate; release to type the text into whatever app you’re focused on.
- Quit anytime: Ctrl+Alt+Q (or close the console window if visible).

## Install (no coding)
1) Install Python
   - Go to https://www.python.org/downloads/
   - Click “Download Python 3.x” → In the installer, check “Add Python to PATH” → Install

2) Get the app
   - Go to https://github.com/davemontore/moneypenny → Code → Download ZIP
   - Right‑click the ZIP → Extract All… → Move the “MoneyPenny” folder to Documents

3) Start the app
   - Open the “MoneyPenny” folder
   - Double‑click “MoneyPenny Voice Typing.bat”
   - First run downloads the voice model; wait for “Whisper model loaded.”

## Use
- Click into any text field (email, browser, Notepad)
- Hold RIGHT CTRL while speaking
- Release RIGHT CTRL → text appears
- Quit: Ctrl+Alt+Q (or close console window)

## Start automatically at login (optional)
- Visible console:
  - Win+R → type `shell:startup` → Enter
  - Create a shortcut for “MoneyPenny Voice Typing.bat” and move it into the Startup folder
- Hidden (no console):
  - Create a file `run_silent.vbs` next to `voice_to_text.py` with:
    ```vbscript
    Set WshShell = CreateObject("WScript.Shell")
    WshShell.Run "cmd /c python voice_to_text.py", 0, False
    ```
  - Create a shortcut to `run_silent.vbs` and move it into the Startup folder

## Add uncommon words (optional)
- Edit `lexicon.txt` in the “MoneyPenny” folder
- Put one word or phrase per line (e.g., names, medical terms)
- Save the file and restart the app

## Tips
- Faster model: edit `voice_to_text.py` → set `MODEL_SIZE = "tiny.en"`
- If hotkeys don’t work: run console “As Administrator” and try again
- If microphone fails: check Windows sound settings (default input device)
