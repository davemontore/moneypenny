# Voice Typing App - Changelog

## Version 3.1.1 - Correction Pipeline
*In development*

### Current Changes
- Split the Dictionary into soft preferred-vocabulary hints and deterministic exact corrections
- Added local heard-as → type-as rules with whole-phrase matching, longest-match priority, and exact output casing/symbols
- Added narrow local repair for impossible punctuation collisions such as `:.` and `,?`
- Added regression coverage and a durable multi-session upgrade plan

---

## Version 3.1 - Context-Aware Cleanup and Transcript History
*Released: August 2026*

### Core Changes
- Added a real windowed `MoneyPenny.exe` build with the application icon embedded, preventing Windows from grouping the running app under Python
- Added a Windows GitHub Actions release pipeline that tests, packages, and publishes a Python-free ZIP for tagged versions
- Added a repeatable Windows shortcut installer that assigns MoneyPenny's icon and AppUserModelID to its Start Menu and taskbar shortcuts
- Added selective Groq `llama-3.1-8b-instant` cleanup for context-aware verbal punctuation; the default Commands-only mode leaves ordinary dictation on the original single-request path
- Cleanup failures and rate limits fall back to the raw transcript so dictation keeps working
- Added a persistent History tab showing raw and final transcripts, backend, timing, and cleanup status
- Added a verbal-command reference to the Dictionary tab

### Technical Notes
- Captured history is stored locally in ignored `transcript_history.jsonl` (maximum 500 entries)
- Raw and final transcripts are logged separately for reproducible regression diagnosis
- The cleanup architecture follows established open-source Wispr Flow alternatives such as FreeFlow and Flow

---

## Version 3.0 - GUI Returns, Cloud Transcription, Custom Dictionary
*Released: August 2026*

### 🚀 Core Changes
- Settings window (CustomTkinter) with system tray integration: Settings, Dictionary, and Status tabs
- Cloud transcription via Groq (`whisper-large-v3-turbo`) or OpenRouter (`openai/gpt-transcribe`); Local mode (faster-whisper) remains as the offline option
- Dictionary tab manages custom vocabulary (stored in `lexicon.txt`, used to bias transcription in both modes)
- Closing the window hides the app to the tray; quit via Ctrl+Alt+Q or tray menu
- Single-instance protection via Windows named mutex (launching a second copy shows an explanatory message and exits)

### 🔧 Technical Notes
- `gui.py` holds all window/tray code; `voice_to_text.py` falls back to headless mode if the GUI fails to load
- Trailing-silence trimming and stock-phrase filtering reduce Whisper hallucinations
- Settings stored in `settings.json` (contains API keys — deliberately NOT tracked in git)
- One-click Windows setup creates a private `.venv` with tested dependency versions; both launchers use it
- Personal `lexicon.txt` contents are no longer tracked; setup creates the file from a safe example without overwriting an existing dictionary

---

## Version 2.2.0 - Local Faster-Whisper, Headless, Hold-to-Record
*Released: August 2025*

### 🚀 Core Changes
- Switched transcription from AssemblyAI (cloud) to local `faster-whisper` for lower latency and offline capability
- Headless operation (no GUI) with global hotkeys
- True hold-to-record using RIGHT CTRL (press to record, release to transcribe)
- Added quit hotkey: Ctrl+Alt+Q for clean shutdown
 - Added lexicon support via `lexicon.txt` using `initial_prompt` biasing

### 🔧 Technical Notes
- Implemented background recording thread with graceful shutdown
- In-memory WAV buffer fed to `WhisperModel.transcribe`
- Default model: `base.en` on CPU `int8` (configurable)
- Typing output via `pynput` keyboard controller
- Windows startup guidance updated: prefer a Startup shortcut to `pyw.exe`/`pythonw.exe` running `voice_to_text.py` with the project folder as “Start in” (hidden launch, no VBS required)

### 📦 Dependencies
- Added: `faster-whisper`
- Legacy: AssemblyAI references removed from runtime path (requirements still lists `assemblyai` but no longer used)

---

## Version 2.1.0 - CustomTkinter Modernization & Critical Fixes
*Released: December 2024*

### 🎨 **Complete UI Modernization**
- **CustomTkinter upgrade**: Migrated from traditional Tkinter to modern CustomTkinter framework
- **Flat design**: Removed all dark gray frames for clean, unified background
- **Modern typography**: Montserrat/Roboto font pairing with proper hierarchy
- **Elegant layout**: Hero section with large title, clean spacing, minimal buttons
- **Professional appearance**: No emojis, sleek borders, contemporary styling

### 🔧 **Critical Bug Fixes**
- **Microphone dropdown fixed**: Resolved data type mismatch preventing dropdown rendering
- **Transcription API fixed**: Corrected content-type headers (was sending `application/json` for binary data)
- **Hotkey system repaired**: Fixed key suppression preventing normal typing
- **Settings persistence**: All settings now save permanently between sessions

### ✨ **Enhanced Features**
- **Built-in test area**: Added text box under Test button for immediate transcription preview
- **Improved error handling**: Detailed API error messages with response details
- **Better audio debugging**: Enhanced logging for microphone and recording issues
- **Smart transcription routing**: Test mode shows results in app, hotkey mode types to external apps

### 🎯 **User Experience Improvements**
- **Simplified interface**: "Test Recording" → "Test", cleaner button hierarchy
- **Consistent theming**: Cream (#F7F5F3) and charcoal (#2C2C2C) throughout
- **Modern dialogs**: Settings and vocabulary windows match main app styling
- **Responsive design**: Proper button sizing and spacing

### 🐛 **Technical Fixes**
- **API headers corrected**: Separate headers for file upload vs JSON requests
- **Data formatting fixed**: Microphone dropdown now receives strings instead of objects
- **Keyboard suppression**: Only suppress exact hotkey combinations, not individual keys
- **Memory management**: Improved widget cleanup and resource handling

---

## Version 2.0.0 - Major Architecture & UI Overhaul
*Released: December 2024*

### 🚀 Major Features Added

#### **Automatic Cleanup System**
- **Complete process management**: App now automatically cleans up ALL resources on exit
- **Multiple cleanup triggers**: Signal handlers (SIGINT, SIGTERM), window close events, and atexit handlers
- **Zero leftover processes**: No more orphaned recording indicators or background processes
- **Lock file system**: Single instance protection with automatic cleanup
- **Force exit failsafe**: Uses `os._exit(0)` as ultimate fallback if normal cleanup fails

#### **Modern UI Design**
- **Custom color scheme**: Cream background (#F7F5F3) with medium black text (#2C2C2C)
- **Smart font system**: Intelligent fallback from Montserrat/Roboto → Segoe UI → Helvetica → Arial → TkDefaultFont
- **Colorless rounded buttons**: Clean, modern button styling with consistent design
- **No emojis**: Professional appearance throughout the interface
- **Symmetric layouts**: Balanced and organized UI components

#### **Enhanced Recording Indicator**
- **Rectangle shape**: Changed from 70x70 square to 120x50 rectangle for better usability
- **Generous padding**: Large draggable area around small centered button
- **Smart drag handling**: Drag events bound to padding frame, not the button itself
- **Visual feedback**: Move cursor on hover, corner dots for drag indication
- **Always on top**: Stays visible above all applications
- **Auto-positioning**: Intelligent screen bounds checking

### 🔧 Technical Improvements

#### **Robust Error Handling**
- **API response validation**: Checks `response.status_code` before JSON parsing
- **Sentiment analysis flexibility**: Handles both list and dictionary formats from AssemblyAI
- **Font fallback system**: Graceful degradation when preferred fonts unavailable
- **Silent success**: No popup notifications for successful operations
- **Noisy failures**: Clear error messages only when something goes wrong

#### **Performance Optimizations**
- **Lazy PyAudio initialization**: Audio resources only created when needed
- **Efficient cleanup**: Comprehensive resource deallocation on exit
- **Memory management**: Proper cleanup of Tkinter widgets and audio streams
- **Reduced UI blocking**: Better threading for audio processing

### 🎯 User Experience Enhancements

#### **Streamlined Operation**
- **Silent success**: No confirmation dialogs for successful transcriptions
- **Fast feedback**: Immediate visual feedback without interrupting workflow
- **X button exits**: Window close button now completely exits app (no minimize to tray)
- **Drag-friendly interface**: Easy to move recording indicator without triggering recording

#### **Better Settings Management**
- **Persistent settings**: Encrypted storage of API keys and preferences
- **Microphone selection**: Improved device detection and filtering
- **Custom vocabulary**: Enhanced word management with silent operations
- **Hotkey configuration**: Reliable hold-to-record functionality

### 🐛 Bug Fixes

#### **Critical Fixes**
- **Transcription crash**: Fixed `'list' object has no attribute 'get'` error in sentiment analysis
- **Process cleanup**: Eliminated orphaned processes and recording indicators
- **Font rendering**: Resolved font availability issues on different systems
- **Hotkey interference**: Fixed keyboard input being blocked during normal typing
- **Recording indicator visibility**: Ensured indicator appears and functions correctly

#### **Minor Fixes**
- **Window sizing**: Improved dialog dimensions and element visibility
- **Error messages**: More informative error reporting
- **Status updates**: Cleaner status text without success notifications
- **Memory leaks**: Proper cleanup of audio and UI resources

### 🔄 Breaking Changes
- **X button behavior**: Now exits completely instead of minimizing to tray
- **Success notifications**: Removed all success popup messages
- **Recording indicator**: Changed from square to rectangle shape
- **Font requirements**: App now works without Montserrat/Roboto installed

### 📋 Known Issues
- None currently reported

### 🛠️ Development Notes
- **Python version**: Tested with Python 3.13
- **Dependencies**: Added `psutil` for process management
- **Architecture**: Implemented comprehensive cleanup system
- **Testing**: Extensive testing on Windows 10/11

---

## Version 1.0.0 - Initial Release
*Previous version with basic functionality*

### Features
- Basic voice-to-text transcription
- AssemblyAI API integration
- Simple GUI interface
- Hotkey support
- Custom vocabulary
- System tray integration

### Known Issues (Fixed in v2.0.0)
- Process cleanup problems
- UI design inconsistencies
- Transcription errors
- Recording indicator issues
