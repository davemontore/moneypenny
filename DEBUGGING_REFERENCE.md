# Voice Typing App - Debugging Reference

> Note: As of v2.2.0 the app is headless (no GUI) and uses local faster-whisper.
> Hotkeys: hold RIGHT CTRL to record; Ctrl+Alt+Q to quit.

## Quick Checks

- App running? If launched hidden via Startup, confirm a `python` process exists in Task Manager
- Hotkeys need elevation? Try running console as Administrator
- Focus: caret must be in a text field to see typing output
- Mic: check default input device and input level in Windows

## Common Issues & Fixes

### Nothing happens on RIGHT CTRL
- Start the app (console or launcher)
- Try Administrator console
- Ensure keyboard has a distinct RIGHT CTRL; we can remap if needed

### Audio device errors
- Switch default recording device in Windows
- Close other apps using the mic
- Reboot audio service or the machine

### Exit/Shutdown
- Ctrl+Alt+Q quits cleanly
- If unresponsive, end `python` in Task Manager

## Diagnostics

- Console output shows: model loading, recording start/stop, and transcription events
- To verify hotkeys: temporarily add a print in `start_recording()` and `stop_recording()`
