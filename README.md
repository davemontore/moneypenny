# MoneyPenny - Voice Typing Assistant

> A fast, local voice‑to‑text utility. Hold RIGHT CTRL to dictate, release to transcribe into the current text field.

## ✨ Features

- **Local transcription**: Uses `faster-whisper` (no cloud, low latency)
- **Hold‑to‑record**: Press and hold RIGHT CTRL, release to transcribe
- **Types into any app**: Output is typed into the focused window
- **Headless**: No GUI; runs quietly in the background
- **Quick exit**: Press Ctrl+Alt+Q (or ESC in console) to quit

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