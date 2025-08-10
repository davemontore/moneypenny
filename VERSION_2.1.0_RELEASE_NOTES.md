# Voice Typing App - Version 2.2.0 Release Notes

## 🎉 Major Update: Local Faster-Whisper, Headless, Hold-to-Record

### 📅 Release Date: August 2025

---

## 🚀 **Core Changes**

### Local Transcription
- Replaced cloud AssemblyAI with on-device `faster-whisper`
- Default model: `base.en` (CPU, int8) for good speed/accuracy balance
- Configurable to `tiny.en` (faster) or GPU (`device="cuda"`)

### Headless Operation
- No GUI; runs in background
- Global hotkeys:
  - Hold RIGHT CTRL to record; release to transcribe
  - Ctrl+Alt+Q to quit cleanly

### Startup Options
- Windows Startup support via Startup folder shortcut
- Hidden launch using `run_silent.vbs` (recommended for no console window)

---

## 🔧 **Technical Notes**

### Audio Pipeline
- PyAudio 16kHz mono stream; background thread collects frames
- In-memory WAV buffer; passed to Whisper for transcription
### Output
- Types transcribed text into focused window via `pynput` controller

### 2. Transcription API Failure ✅ FIXED
**Problem**: HTTP 400 errors due to incorrect content-type headers
**Solution**:
- Separated headers for file upload vs JSON requests
- Fixed binary data upload with proper headers
- Enhanced error reporting with API response details

### 3. Hotkey System Blocking Normal Typing ✅ FIXED
**Problem**: Keyboard suppression preventing regular text input
**Solution**:
- Smart combination-only suppression
- Preserved normal typing functionality
- Maintained hold-to-record behavior

---

## ✨ **User Experience**
- Faster dictation with minimal latency
- No API keys or internet required
- Simple start/stop and quit hotkeys

### Enhanced Debugging
- **Detailed Logging**: Comprehensive audio and API debugging
- **Error Context**: API responses included in error messages
- **Resource Monitoring**: Better tracking of audio streams and processes

---

## 📦 **Dependencies**
- Added: `faster-whisper`
- Existing: `pyaudio`, `keyboard`, `pynput`, `psutil`

---

## 📋 **Migration Notes**
- Remove any old expectation of GUI/settings; app is now headless
- For startup at login, use shortcut to `.bat` (console) or `run_silent.vbs` (no console)
- No API key required anymore

---

## 🔍 **Testing Completed**
- ✅ Hold-to-record works with RIGHT CTRL
- ✅ Ctrl+Alt+Q exits cleanly
- ✅ Transcription types into focused app
- ✅ Startup via `.bat` and hidden via `run_silent.vbs`

---

## 🎯 **What's Next**

### Planned Improvements
- Additional transcription service integrations
- Enhanced vocabulary management
- More customization options
- Performance optimizations

### Known Issues
- None currently reported

---

## 📞 **Support**

If you encounter any issues with this update:

1. **Check troubleshooting guide**: `SETTINGS_DIALOG_TROUBLESHOOTING.md`
2. **Review changelog**: `CHANGELOG.md` for detailed changes
3. **Submit issues**: GitHub Issues for bug reports
4. **Join discussions**: GitHub Discussions for questions

---

**Enjoy the modern, reliable Voice Typing experience!** 🎉
