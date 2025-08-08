# MoneyPenny - Voice Typing Assistant

> A modern, local voice-to-text application designed to replace Whispr Flow.ai with enhanced features and better user experience.

## ✨ Features

### 🎙️ **Voice Recognition**
- **AssemblyAI Integration**: High-accuracy speech-to-text transcription
- **Hold-to-Record**: Intuitive hotkey system (customizable)
- **Custom Vocabulary**: Add specialized words for better accuracy
- **Sentiment Analysis**: Automatic punctuation and context awareness

### 🖥️ **User Interface**
- **Modern Design**: Clean cream and black theme with Montserrat/Roboto fonts
- **Draggable Recording Indicator**: Always-on-top rectangle widget for manual control
- **System Tray Integration**: Minimize to background while staying operational
- **Silent Success**: No interrupting notifications - only error alerts

### 🔧 **Technical Features**
- **Local Processing**: Runs entirely on your machine
- **Secure API Key Storage**: Encrypted local storage of credentials
- **Multi-Device Support**: Intelligent microphone detection and selection
- **Process Management**: Automatic cleanup with no leftover processes
- **Single Instance**: Prevents multiple app instances

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- AssemblyAI API key ([Get one here](https://www.assemblyai.com/))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/davemontore/moneypenny.git
   cd moneypenny
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python voice_to_text.py
   ```

4. **First-time setup:**
   - Click "Settings" to enter your AssemblyAI API key
   - Select your preferred microphone
   - Customize hotkeys if desired

### Alternative Launch Methods

**Easy Windows Launch:**
```bash
# Double-click this file to run the app
MoneyPenny Voice Typing.bat
```

## 🎯 How to Use

### Basic Operation
1. **Start Recording**: Hold your configured hotkey (default: Ctrl+Shift+R)
2. **Speak Clearly**: Talk into your microphone
3. **Release Hotkey**: Text appears where your cursor is focused
4. **Manual Toggle**: Click the draggable recording indicator

### Advanced Features
- **Custom Words**: Add technical terms or names via Settings → Vocabulary Library
- **Microphone Selection**: Choose from detected audio devices
- **Drag Indicator**: Move the recording widget anywhere on screen
- **System Tray**: Minimize app while keeping it functional

## 📁 Project Structure

```
moneypenny/
├── voice_to_text.py          # Main application
├── requirements.txt          # Python dependencies
├── run_voice_typing.bat      # Windows launcher
├── CHANGELOG.md              # Version history
├── DEBUGGING_REFERENCE.md    # Troubleshooting guide
└── README.md                 # This file
```

## 🛠️ Configuration

### Settings Storage
- **Location**: `settings.json` (created on first run)
- **Encryption**: API keys stored with Fernet encryption
- **Backup**: Keep your `encryption.key` file safe

### Hotkey Customization
- Access via Settings dialog
- Supports modifier combinations (Ctrl, Shift, Alt)
- Hold-to-record functionality

### Microphone Setup
- Automatic device detection
- Filters out system/virtual devices
- Manual selection via dropdown

## 🔍 Troubleshooting

### Common Issues

**App won't start:**
- Check if another instance is running
- Verify Python version (3.8+)
- Install missing dependencies

**No microphone detected:**
- Check audio device permissions
- Try different microphone
- Restart audio services

**Transcription errors:**
- Verify internet connection
- Check AssemblyAI API key validity
- Review microphone input levels

**Recording indicator missing:**
- Look for debug output in terminal
- Check screen resolution settings
- Verify Tkinter installation

### Debug Mode
Run with debug output:
```bash
python voice_to_text.py
```
Check console for detailed status messages.

## 🤝 Contributing

We welcome contributions! Please feel free to:
- Report bugs via GitHub Issues
- Suggest features or improvements
- Submit pull requests
- Share usage feedback

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AssemblyAI** for excellent speech-to-text API
- **Whispr Flow.ai** for inspiration and feature ideas
- Python community for amazing libraries (PyAudio, Tkinter, keyboard)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/davemontore/moneypenny/issues)
- **Discussions**: [GitHub Discussions](https://github.com/davemontore/moneypenny/discussions)
- **Documentation**: See `DEBUGGING_REFERENCE.md` for detailed troubleshooting

---

**Made with ❤️ for better voice typing experiences**