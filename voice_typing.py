import tkinter as tk
from tkinter import messagebox
import threading
import time
import keyboard
import pyaudio
import wave
import requests
import json
import os
import sys
from datetime import datetime
from cryptography.fernet import Fernet

class VoiceTyping:
    def __init__(self):
        # Configuration
        self.api_key = None
        self.is_recording = False
        self.audio_frames = []
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        
        # Hotkey configuration
        self.record_hotkey = 'ctrl+shift+r'
        
        # Microphone configuration
        self.selected_microphone = 0  # Default to first microphone
        
        # Custom vocabulary library
        self.custom_vocabulary = []  # List of specialized words for AssemblyAI
        
        # Security setup
        self.encryption_key = self.get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Draggable recording indicator
        self.recording_indicator = None
        self.drag_data = {"x": 0, "y": 0, "dragging": False}
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("Voice Typing")
        self.root.geometry("500x500")
        self.root.configure(bg='#2b2b2b')
        self.root.resizable(False, False)
        
        # Set up system tray behavior
        self.setup_system_tray_behavior()
        
        # Center the window on screen
        self.center_window()
        
        # Load saved settings
        self.load_settings()
        
        # Create GUI elements
        self.setup_gui()
        
        # Setup hotkeys
        self.setup_hotkeys()
        
        # Create draggable recording indicator
        self.create_recording_indicator()
        
        # Check for API key
        self.check_api_key()
    
    def setup_system_tray_behavior(self):
        """Set up system tray behavior for the application"""
        # Handle window close button - minimize to system tray instead of closing
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # Handle minimize button - minimize to system tray
        self.root.bind("<Unmap>", self.on_minimize)
        
        # Handle window state changes
        self.root.bind("<Configure>", self.on_window_configure)
        
        # Handle application destruction
        self.root.bind("<Destroy>", self.on_destroy)
    
    def on_destroy(self, event):
        """Handle application destruction"""
        if event.widget == self.root:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources when application is destroyed"""
        try:
            # Destroy recording indicator
            if hasattr(self, 'recording_indicator') and self.recording_indicator:
                self.recording_indicator.destroy()
            
            # Clean up audio resources
            if hasattr(self, 'audio') and self.audio:
                self.audio.terminate()
        except:
            pass
    
    def minimize_to_tray(self):
        """Minimize the application to system tray"""
        self.root.withdraw()  # Hide the main window
        
        # Change recording indicator appearance to show it's in background
        if hasattr(self, 'recording_button'):
            self.recording_button.config(bg='#555555', text="🎤")
        
        self.show_system_tray_notification("Voice Typing is running in the background")
    
    def on_minimize(self, event):
        """Handle minimize event"""
        if self.root.state() == 'iconic':
            self.minimize_to_tray()
    
    def on_window_configure(self, event):
        """Handle window configuration changes"""
        # Keep recording indicator on top when main window is shown
        if self.recording_indicator and self.root.state() != 'withdrawn':
            self.recording_indicator.lift()
    
    def show_system_tray_notification(self, message):
        """Show a system tray notification"""
        try:
            # Try to show a Windows notification
            import win10toast
            toaster = win10toast.ToastNotifier()
            toaster.show_toast("Voice Typing", message, duration=3, threaded=True)
        except ImportError:
            # Fallback to messagebox if win10toast is not available
            messagebox.showinfo("Voice Typing", message)
    
    def create_recording_indicator(self):
        """Create a draggable recording indicator that stays on top"""
        self.recording_indicator = tk.Toplevel(self.root)
        self.recording_indicator.title("Recording Indicator")
        self.recording_indicator.geometry("80x80")  # Increased size for padding
        self.recording_indicator.configure(bg='#2b2b2b')
        self.recording_indicator.overrideredirect(True)  # Remove window decorations
        self.recording_indicator.attributes('-topmost', True)  # Always on top
        self.recording_indicator.attributes('-alpha', 0.8)  # Semi-transparent
        
        # Position in top-right corner initially
        screen_width = self.recording_indicator.winfo_screenwidth()
        screen_height = self.recording_indicator.winfo_screenheight()
        x = screen_width - 100  # Adjusted for new size
        y = 20
        self.recording_indicator.geometry(f"80x80+{x}+{y}")
        
        # Create a frame for padding around the button with visible border
        padding_frame = tk.Frame(
            self.recording_indicator, 
            bg='#404040',  # Slightly lighter background to show the draggable area
            relief=tk.RAISED,
            bd=2,
            padx=8, 
            pady=8
        )
        padding_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Add subtle drag indicator dots in corners
        for corner in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            dot = tk.Label(
                padding_frame,
                text="•",
                font=("Segoe UI", 8),
                bg='#404040',
                fg='#666666'
            )
            dot.place(relx=corner[0], rely=corner[1], anchor="nw" if corner == (0, 0) else "ne" if corner == (1, 0) else "sw" if corner == (0, 1) else "se")
        
        # Create the recording button (smaller to allow padding for dragging)
        self.recording_button = tk.Button(
            padding_frame,
            text="🎤",
            font=("Segoe UI", 20),  # Slightly smaller font
            bg='#e74c3c',
            fg='white',
            relief=tk.FLAT,
            bd=0,
            cursor='hand2',
            command=self.toggle_recording
        )
        self.recording_button.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for dragging to the padding frame (not the button)
        padding_frame.bind("<Button-1>", self.start_drag)
        padding_frame.bind("<B1-Motion>", self.on_drag)
        padding_frame.bind("<ButtonRelease-1>", self.stop_drag)
        padding_frame.bind("<Enter>", lambda e: padding_frame.config(cursor="fleur"))  # Show move cursor
        padding_frame.bind("<Leave>", lambda e: padding_frame.config(cursor=""))  # Reset cursor
        
        # Bind right-click for context menu to both frame and button
        padding_frame.bind("<Button-3>", self.show_context_menu)
        self.recording_button.bind("<Button-3>", self.show_context_menu)
        
        # Make the indicator always visible
        self.recording_indicator.lift()
        self.recording_indicator.attributes('-topmost', True)
    
    def start_drag(self, event):
        """Start dragging the recording indicator"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["dragging"] = True
    
    def on_drag(self, event):
        """Handle dragging of the recording indicator"""
        if self.drag_data["dragging"]:
            # Calculate new position
            x = self.recording_indicator.winfo_x() + (event.x - self.drag_data["x"])
            y = self.recording_indicator.winfo_y() + (event.y - self.drag_data["y"])
            
            # Keep within screen bounds
            screen_width = self.recording_indicator.winfo_screenwidth()
            screen_height = self.recording_indicator.winfo_screenheight()
            x = max(0, min(x, screen_width - 80)) # Adjusted for new size
            y = max(0, min(y, screen_height - 80)) # Adjusted for new size
            
            self.recording_indicator.geometry(f"80x80+{x}+{y}")
    
    def stop_drag(self, event):
        """Stop dragging the recording indicator"""
        self.drag_data["dragging"] = False
    
    def show_context_menu(self, event):
        """Show context menu for the recording indicator"""
        context_menu = tk.Menu(self.recording_indicator, tearoff=0)
        context_menu.add_command(label="🎤 Start/Stop Recording", command=self.toggle_recording)
        context_menu.add_separator()
        context_menu.add_command(label="📋 Show Main Window", command=self.show_main_window)
        context_menu.add_command(label="⚙️ Settings", command=self.show_settings)
        context_menu.add_command(label="📚 Vocabulary Library", command=self.show_vocabulary_library)
        context_menu.add_separator()
        context_menu.add_command(label="❌ Exit Voice Typing", command=self.quit_application, 
                                font=("Segoe UI", 10, "bold"))
        
        # Show menu at cursor position
        context_menu.tk_popup(event.x_root, event.y_root)
    
    def show_main_window(self):
        """Show the main application window"""
        self.root.deiconify()  # Show the main window
        self.root.lift()  # Bring to front
        self.root.focus_force()  # Give focus
        
        # Restore recording indicator appearance
        if hasattr(self, 'recording_button'):
            if self.is_recording:
                self.recording_button.config(bg='#f39c12', text="⏹️")
            else:
                self.recording_button.config(bg='#e74c3c', text="🎤")
    
    def quit_application(self):
        """Quit the application completely"""
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit Voice Typing?"):
            # Properly destroy the recording indicator
            if hasattr(self, 'recording_indicator') and self.recording_indicator:
                self.recording_indicator.destroy()
            
            # Clean up audio resources
            if hasattr(self, 'audio') and self.audio:
                self.audio.terminate()
            
            self.root.quit()
            sys.exit()
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def get_or_create_encryption_key(self):
        """Get existing encryption key or create a new one"""
        key_file = 'encryption.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        if not data:
            return None
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        if not encrypted_data:
            return None
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except:
            return None
    
    def load_settings(self):
        """Load saved settings from file"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    encrypted_api_key = settings.get('encrypted_api_key')
                    if encrypted_api_key:
                        self.api_key = self.decrypt_data(encrypted_api_key)
                    self.record_hotkey = settings.get('record_hotkey', 'ctrl+shift+r')
                    self.selected_microphone = settings.get('selected_microphone', 0)
                    self.custom_vocabulary = settings.get('custom_vocabulary', [])
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to file with encrypted API key"""
        try:
            settings = {
                'encrypted_api_key': self.encrypt_data(self.api_key) if self.api_key else None,
                'record_hotkey': self.record_hotkey,
                'selected_microphone': self.selected_microphone,
                'custom_vocabulary': self.custom_vocabulary
            }
            with open('settings.json', 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_available_microphones(self):
        """Get list of available microphone devices"""
        microphones = []
        try:
            device_count = self.audio.get_device_count()
            print(f"Found {device_count} total audio devices")
            
            # Track unique microphone names to avoid duplicates
            seen_names = set()
            
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                name = device_info['name'].lower()
                
                # Only include actual microphone devices with strict filtering
                if (device_info['maxInputChannels'] > 0 and 
                    ('mic' in name or 'microphone' in name) and
                    not any(exclude in name for exclude in [
                        'virtual', 'system', 'stereo mix', 'what u hear', 'loopback',
                        'mapper', 'array', 'realtek', 'intel', 'sst', 'solo'
                    ])):
                    
                    # Check if we've already seen this microphone name
                    clean_name = device_info['name'].split('(')[0].strip()
                    if clean_name not in seen_names:
                        seen_names.add(clean_name)
                        microphones.append({
                            'index': i,
                            'name': device_info['name'],
                            'channels': device_info['maxInputChannels'],
                            'sample_rate': int(device_info['defaultSampleRate'])
                        })
                        print(f"Added microphone: {device_info['name']}")
            
            # If still no microphones, try very basic filtering
            if not microphones:
                print("No microphones found with strict filtering, trying basic approach...")
                for i in range(device_count):
                    device_info = self.audio.get_device_info_by_index(i)
                    name = device_info['name'].lower()
                    
                    if (device_info['maxInputChannels'] > 0 and 
                        'mic' in name and
                        not any(exclude in name for exclude in ['virtual', 'stereo mix', 'what u hear', 'loopback'])):
                        
                        clean_name = device_info['name'].split('(')[0].strip()
                        if clean_name not in seen_names:
                            seen_names.add(clean_name)
                            microphones.append({
                                'index': i,
                                'name': device_info['name'],
                                'channels': device_info['maxInputChannels'],
                                'sample_rate': int(device_info['defaultSampleRate'])
                            })
                            print(f"Added basic microphone: {device_info['name']}")
            
            print(f"Found {len(microphones)} usable microphone devices")
        except Exception as e:
            print(f"Error getting microphones: {e}")
        return microphones
    
    def add_custom_word(self, word):
        """Add a word to custom vocabulary"""
        word = word.strip().lower()
        if word and word not in self.custom_vocabulary:
            self.custom_vocabulary.append(word)
            self.save_settings()
            return True
        return False
    
    def remove_custom_word(self, word):
        """Remove a word from custom vocabulary"""
        word = word.strip().lower()
        if word in self.custom_vocabulary:
            self.custom_vocabulary.remove(word)
            self.save_settings()
            return True
        return False
    
    def setup_gui(self):
        """Create the modern graphical user interface"""
        # Main container with padding
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Title with modern styling
        title_label = tk.Label(
            main_frame, 
            text="🎤 Voice Typing", 
            font=("Segoe UI", 32, "bold"),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        title_label.pack(pady=(0, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_frame,
            text="Type with your voice in any application",
            font=("Segoe UI", 14),
            bg='#2b2b2b',
            fg='#cccccc'
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Status indicator with modern styling
        status_frame = tk.Frame(main_frame, bg='#2b2b2b')
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready to voice type",
            font=("Segoe UI", 18, "bold"),
            bg='#2b2b2b',
            fg='#4CAF50'
        )
        self.status_label.pack()
        
        # Clear instructions
        instructions_frame = tk.Frame(main_frame, bg='#2b2b2b')
        instructions_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Hotkey instruction
        hotkey_label = tk.Label(
            instructions_frame,
            text=f"Hold {self.record_hotkey.upper()} to record voice",
            font=("Segoe UI", 16, "bold"),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        hotkey_label.pack(pady=(0, 10))
        
        # Clear workflow instructions
        workflow_text = """How to use:
1. Click in any text field (email, document, etc.)
2. Hold down Ctrl+Shift+R to start recording
3. Speak clearly into your microphone
4. Release Ctrl+Shift+R to stop recording
5. Your words appear directly in the text field"""
        
        workflow_label = tk.Label(
            instructions_frame,
            text=workflow_text,
            font=("Segoe UI", 12),
            bg='#2b2b2b',
            fg='#cccccc',
            justify=tk.LEFT,
            wraplength=400
        )
        workflow_label.pack()
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg='#2b2b2b')
        button_frame.pack(pady=10)
        
        # Record button with modern styling
        self.record_button = tk.Button(
            button_frame,
            text="🎤 Test Recording",
            command=self.toggle_recording,
            font=("Segoe UI", 14, "bold"),
            bg='#e74c3c',
            fg='white',
            relief=tk.FLAT,
            padx=30,
            pady=15,
            cursor='hand2',
            activebackground='#c0392b',
            activeforeground='white',
            bd=0,
            highlightthickness=0
        )
        self.record_button.pack(side=tk.LEFT, padx=10)
        
        # Settings button with modern styling
        settings_button = tk.Button(
            button_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            font=("Segoe UI", 14, "bold"),
            bg='#3498db',
            fg='white',
            relief=tk.FLAT,
            padx=30,
            pady=15,
            cursor='hand2',
            activebackground='#2980b9',
            activeforeground='white',
            bd=0,
            highlightthickness=0
        )
        settings_button.pack(side=tk.LEFT, padx=10)
        
        # Vocabulary Library button with modern styling
        vocab_button = tk.Button(
            button_frame,
            text="📚 Vocabulary",
            command=self.show_vocabulary_library,
            font=("Segoe UI", 14, "bold"),
            bg='#9b59b6',
            fg='white',
            relief=tk.FLAT,
            padx=30,
            pady=15,
            cursor='hand2',
            activebackground='#8e44ad',
            activeforeground='white',
            bd=0,
            highlightthickness=0
        )
        vocab_button.pack(side=tk.LEFT, padx=10)
    
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Voice Typing Settings")
        settings_window.geometry("600x700")
        settings_window.configure(bg='#2b2b2b')
        settings_window.resizable(False, False)
        
        # Center the settings window
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Center on screen
        settings_window.update_idletasks()
        width = settings_window.winfo_width()
        height = settings_window.winfo_height()
        x = (settings_window.winfo_screenwidth() // 2) - (width // 2)
        y = (settings_window.winfo_screenheight() // 2) - (height // 2)
        settings_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Main container with scrollbar
        canvas = tk.Canvas(settings_window, bg='#2b2b2b', highlightthickness=0)
        scrollbar = tk.Scrollbar(settings_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        
        # Main container
        main_frame = scrollable_frame
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Settings",
            font=("Segoe UI", 24, "bold"),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        title_label.pack(pady=(0, 20))
        
        # API Key section
        api_frame = tk.LabelFrame(
            main_frame,
            text="AssemblyAI API Key",
            font=("Segoe UI", 14, "bold"),
            bg='#2b2b2b',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=2
        )
        api_frame.pack(fill=tk.X, pady=(0, 20))
        
        api_label = tk.Label(
            api_frame,
            text="Enter your API key:",
            font=("Segoe UI", 12),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        api_label.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        api_entry = tk.Entry(
            api_frame,
            font=("Segoe UI", 12),
            width=45,
            show="*",
            relief=tk.RAISED,
            bd=2,
            bg='#404040',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        api_entry.pack(padx=20, pady=(0, 20))
        
        if self.api_key:
            api_entry.insert(0, self.api_key)
        
        # Show/Hide button
        show_button = tk.Button(
            api_frame,
            text="👁️ Show/Hide",
            command=lambda: self.toggle_api_visibility(api_entry),
            font=("Segoe UI", 10),
            bg='#555555',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2',
            bd=0
        )
        show_button.pack(pady=(0, 20))
        
        # Hotkeys section
        hotkey_frame = tk.LabelFrame(
            main_frame,
            text="Keyboard Shortcut",
            font=("Segoe UI", 14, "bold"),
            bg='#2b2b2b',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=2
        )
        hotkey_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Record hotkey
        record_label = tk.Label(
            hotkey_frame,
            text="Voice typing hotkey:",
            font=("Segoe UI", 12),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        record_label.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        record_entry = tk.Entry(
            hotkey_frame,
            font=("Segoe UI", 12),
            width=35,
            relief=tk.RAISED,
            bd=2,
            bg='#404040',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        record_entry.pack(padx=20, pady=(0, 20))
        record_entry.insert(0, self.record_hotkey)
        
        # Microphone section
        mic_frame = tk.LabelFrame(
            main_frame,
            text="Microphone Selection",
            font=("Segoe UI", 14, "bold"),
            bg='#2b2b2b',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=2
        )
        mic_frame.pack(fill=tk.X, pady=(0, 20))
        
        mic_label = tk.Label(
            mic_frame,
            text="Select your microphone:",
            font=("Segoe UI", 12),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        mic_label.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        # Get available microphones
        microphones = self.get_available_microphones()
        print(f"DEBUG: Found {len(microphones)} microphones for dropdown")
        
        # Create microphone dropdown
        mic_var = tk.StringVar()
        
        # Create dropdown options
        mic_options = [f"{mic['index']}: {mic['name']}" for mic in microphones]
        if not mic_options:
            mic_options = ["No microphones found"]
        
        print(f"DEBUG: Dropdown options: {mic_options}")
        
        # Create a frame for the dropdown to make it more visible
        dropdown_frame = tk.Frame(mic_frame, bg='#2b2b2b')
        dropdown_frame.pack(padx=20, pady=(10, 20), fill=tk.X)
        
        # Add a label to make it clear this is a dropdown
        dropdown_label = tk.Label(
            dropdown_frame,
            text="Click to select:",
            font=("Segoe UI", 10),
            bg='#2b2b2b',
            fg='#cccccc'
        )
        dropdown_label.pack(anchor=tk.W, pady=(0, 5))
        
        mic_dropdown = tk.OptionMenu(
            dropdown_frame,
            mic_var,
            *mic_options,
            command=lambda x: self.on_microphone_selected(x, microphones)
        )
        mic_dropdown.config(
            font=("Segoe UI", 12, "bold"),
            bg='#404040',
            fg='#ffffff',
            relief=tk.RAISED,
            bd=3,
            highlightthickness=3,
            highlightbackground='#3498db',
            activebackground='#555555',
            activeforeground='#ffffff',
            width=50
        )
        mic_dropdown.pack(fill=tk.X, expand=True, pady=(0, 10))
        
        # Set current selection
        if microphones:
            current_mic = f"{self.selected_microphone}: {next((mic['name'] for mic in microphones if mic['index'] == self.selected_microphone), 'Unknown')}"
            mic_var.set(current_mic)
        elif mic_options:
            mic_var.set(mic_options[0])
        
        # Microphone info
        if microphones:
            current_mic_info = next((mic for mic in microphones if mic['index'] == self.selected_microphone), microphones[0])
            mic_info_label = tk.Label(
                mic_frame,
                text=f"Channels: {current_mic_info['channels']} | Sample Rate: {current_mic_info['sample_rate']} Hz",
                font=("Segoe UI", 10),
                bg='#2b2b2b',
                fg='#cccccc'
            )
            mic_info_label.pack(anchor=tk.W, padx=20, pady=(0, 20))
        
        # Save button
        save_button = tk.Button(
            main_frame,
            text="💾 Save Settings",
            command=lambda: self.save_settings_from_dialog(
                settings_window, api_entry, record_entry
            ),
            font=("Segoe UI", 14, "bold"),
            bg='#27ae60',
            fg='white',
            relief=tk.FLAT,
            padx=40,
            pady=12,
            cursor='hand2',
            bd=0
        )
        save_button.pack()
    
    def show_vocabulary_library(self):
        """Show vocabulary library dialog"""
        vocab_window = tk.Toplevel(self.root)
        vocab_window.title("Custom Vocabulary Library")
        vocab_window.geometry("600x500")
        vocab_window.configure(bg='#2b2b2b')
        vocab_window.resizable(False, False)
        
        # Center the vocabulary window
        vocab_window.transient(self.root)
        vocab_window.grab_set()
        
        # Center on screen
        vocab_window.update_idletasks()
        width = vocab_window.winfo_width()
        height = vocab_window.winfo_height()
        x = (vocab_window.winfo_screenwidth() // 2) - (width // 2)
        y = (vocab_window.winfo_screenheight() // 2) - (height // 2)
        vocab_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Main container
        main_frame = tk.Frame(vocab_window, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="📚 Custom Vocabulary Library",
            font=("Segoe UI", 24, "bold"),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_label = tk.Label(
            main_frame,
            text="Add specialized words to improve transcription accuracy.\nAssemblyAI will learn to recognize these words better.",
            font=("Segoe UI", 12),
            bg='#2b2b2b',
            fg='#cccccc',
            justify=tk.CENTER
        )
        desc_label.pack(pady=(0, 30))
        
        # Add word section
        add_frame = tk.LabelFrame(
            main_frame,
            text="Add New Word",
            font=("Segoe UI", 14, "bold"),
            bg='#2b2b2b',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=2
        )
        add_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Word entry
        word_label = tk.Label(
            add_frame,
            text="Enter specialized word or phrase:",
            font=("Segoe UI", 12),
            bg='#2b2b2b',
            fg='#ffffff'
        )
        word_label.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        word_entry = tk.Entry(
            add_frame,
            font=("Segoe UI", 12),
            width=40,
            relief=tk.FLAT,
            bd=0,
            bg='#404040',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        word_entry.pack(padx=20, pady=(0, 20))
        
        # Add button
        add_button = tk.Button(
            add_frame,
            text="➕ Add Word",
            command=lambda: self.add_word_from_dialog(word_entry, word_listbox),
            font=("Segoe UI", 12, "bold"),
            bg='#27ae60',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2',
            bd=0
        )
        add_button.pack(pady=(0, 20))
        
        # Current vocabulary section
        vocab_frame = tk.LabelFrame(
            main_frame,
            text=f"Current Vocabulary ({len(self.custom_vocabulary)} words)",
            font=("Segoe UI", 14, "bold"),
            bg='#2b2b2b',
            fg='#ffffff',
            relief=tk.FLAT,
            bd=2
        )
        vocab_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Word listbox with scrollbar
        list_frame = tk.Frame(vocab_frame, bg='#2b2b2b')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        word_listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 12),
            bg='#404040',
            fg='#ffffff',
            selectbackground='#3498db',
            selectforeground='#ffffff',
            relief=tk.FLAT,
            bd=0,
            height=10
        )
        word_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=word_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        word_listbox.config(yscrollcommand=scrollbar.set)
        
        # Populate listbox
        for word in self.custom_vocabulary:
            word_listbox.insert(tk.END, word)
        
        # Remove button
        remove_button = tk.Button(
            vocab_frame,
            text="🗑️ Remove Selected",
            command=lambda: self.remove_word_from_dialog(word_listbox),
            font=("Segoe UI", 12, "bold"),
            bg='#e74c3c',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2',
            bd=0
        )
        remove_button.pack(pady=(0, 20))
        
        # Close button
        close_button = tk.Button(
            main_frame,
            text="✅ Done",
            command=vocab_window.destroy,
            font=("Segoe UI", 14, "bold"),
            bg='#3498db',
            fg='white',
            relief=tk.FLAT,
            padx=40,
            pady=12,
            cursor='hand2',
            bd=0
        )
        close_button.pack()
    
    def add_word_from_dialog(self, entry, listbox):
        """Add word from vocabulary dialog"""
        word = entry.get().strip()
        if not word:
            messagebox.showerror("Error", "Please enter a word")
            return
        
        if self.add_custom_word(word):
            listbox.insert(tk.END, word)
            entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Added '{word}' to vocabulary")
        else:
            messagebox.showerror("Error", f"'{word}' is already in vocabulary")
    
    def remove_word_from_dialog(self, listbox):
        """Remove word from vocabulary dialog"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a word to remove")
            return
        
        word = listbox.get(selection[0])
        if self.remove_custom_word(word):
            listbox.delete(selection[0])
            messagebox.showinfo("Success", f"Removed '{word}' from vocabulary")
        else:
            messagebox.showerror("Error", f"Could not remove '{word}'")
    
    def toggle_api_visibility(self, entry):
        """Toggle API key visibility"""
        if entry.cget('show') == '*':
            entry.config(show='')
        else:
            entry.config(show='*')
    
    def on_microphone_selected(self, selection, microphones):
        """Handle microphone selection"""
        try:
            mic_index = int(selection.split(':')[0])
            self.selected_microphone = mic_index
        except:
            pass
    
    def save_settings_from_dialog(self, window, api_entry, record_entry):
        """Save settings from dialog"""
        # Get values
        new_api_key = api_entry.get().strip()
        new_record_hotkey = record_entry.get().strip().lower()
        
        if not new_api_key:
            messagebox.showerror("Error", "Please enter your API key")
            return
        
        if not new_record_hotkey:
            messagebox.showerror("Error", "Please enter the hotkey")
            return
        
        # Update settings
        self.api_key = new_api_key
        self.record_hotkey = new_record_hotkey
        
        # Save to file
        self.save_settings()
        
        # Update hotkeys
        self.setup_hotkeys()
        
        # Update instructions
        self.update_instructions()
        
        messagebox.showinfo("Success", "Settings saved successfully!")
        window.destroy()
    
    def update_instructions(self):
        """Update the instructions with current hotkeys"""
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and "Hold" in child.cget('text'):
                        child.config(text=f"Hold {self.record_hotkey.upper()} to record voice")
                        break
    
    def setup_hotkeys(self):
        """Setup keyboard hotkeys for hold-to-record functionality"""
        # Remove existing hotkeys
        try:
            keyboard.remove_hotkey(self.record_hotkey)
        except:
            pass
        
        # Parse the hotkey to get individual keys
        keys = self.record_hotkey.split('+')
        if len(keys) >= 2:
            # For combined hotkeys like 'ctrl+shift+r', we need to track key states
            self.hotkey_keys = keys
            self.hotkey_pressed = False
            
            # Set up individual key listeners WITHOUT suppress=True to allow normal typing
            for key in keys:
                keyboard.on_press_key(key, self.on_key_press, suppress=False)
                keyboard.on_release_key(key, self.on_key_release, suppress=False)
        else:
            # Single key hotkey
            keyboard.add_hotkey(self.record_hotkey, self.toggle_recording, suppress=True)
    
    def toggle_recording(self):
        """Toggle recording - start if not recording, stop if recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def on_key_press(self, e):
        """Handle key press for hold-to-record"""
        if hasattr(self, 'hotkey_keys'):
            # Only trigger if this is the last key in the combination
            # and all other keys are already pressed
            current_key = e.name.lower()
            if current_key in self.hotkey_keys:
                other_keys = [k for k in self.hotkey_keys if k != current_key]
                if all(keyboard.is_pressed(key) for key in other_keys):
                    if not self.hotkey_pressed and not self.is_recording:
                        self.hotkey_pressed = True
                        self.start_recording()
    
    def on_key_release(self, e):
        """Handle key release for hold-to-record"""
        if hasattr(self, 'hotkey_keys'):
            # Only stop if this is one of the hotkey keys and any key in the combination is released
            current_key = e.name.lower()
            if current_key in self.hotkey_keys:
                if not all(keyboard.is_pressed(key) for key in self.hotkey_keys):
                    if self.hotkey_pressed and self.is_recording:
                        self.hotkey_pressed = False
                        self.stop_recording()
    
    def check_api_key(self):
        """Check if API key is set"""
        if not self.api_key:
            messagebox.showinfo("Welcome!", "Please click Settings to enter your AssemblyAI API key")
    
    def start_recording(self):
        """Start recording audio"""
        if not self.api_key:
            messagebox.showerror("Error", "Please set your API key in Settings first")
            return
        
        self.is_recording = True
        self.audio_frames = []
        
        # Update GUI
        self.status_label.config(text="🔴 Recording... Speak now!", fg='#e74c3c')
        self.record_button.config(text="⏹️ Stop Test", bg='#f39c12')
        
        # Update recording indicator
        if hasattr(self, 'recording_button'):
            self.recording_button.config(text="⏹️", bg='#f39c12')
        
        # Start recording in a separate thread
        self.record_thread = threading.Thread(target=self.record_audio)
        self.record_thread.daemon = True
        self.record_thread.start()
    
    def stop_recording(self):
        """Stop recording and transcribe"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # Update GUI
        self.status_label.config(text="🔄 Processing...", fg='#f39c12')
        self.record_button.config(text="🎤 Test Recording", bg='#e74c3c')
        
        # Update recording indicator
        if hasattr(self, 'recording_button'):
            self.recording_button.config(text="🎤", bg='#e74c3c')
        
        # Stop the audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Transcribe the audio
        if self.audio_frames:
            self.transcribe_audio()
    
    def record_audio(self):
        """Record audio from microphone"""
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.selected_microphone,
                frames_per_buffer=self.chunk_size
            )
            
            while self.is_recording:
                data = self.stream.read(self.chunk_size)
                self.audio_frames.append(data)
                
        except Exception as e:
            print(f"Error recording audio: {e}")
            self.is_recording = False
    
    def transcribe_audio(self):
        """Transcribe the recorded audio using AssemblyAI"""
        try:
            # Save audio to temporary file
            temp_filename = f"temp_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.audio_frames))
            
            # Upload to AssemblyAI
            headers = {
                'authorization': self.api_key,
                'content-type': 'application/json'
            }
            
            # Upload the file
            upload_url = "https://api.assemblyai.com/v2/upload"
            
            with open(temp_filename, "rb") as f:
                response = requests.post(upload_url, headers=headers, data=f)
                
                if response.status_code != 200:
                    raise Exception(f"Upload failed: {response.status_code}")
                
                upload_response = response.json()
                audio_url = upload_response['upload_url']
            
            # Request transcription with sentiment and context analysis
            transcript_url = "https://api.assemblyai.com/v2/transcript"
            transcript_request = {
                'audio_url': audio_url,
                'language_code': 'en',
                'sentiment_analysis': True,
                'auto_highlights': True,
                'entity_detection': True,
                'auto_chapters': True,
                'iab_categories': True
            }
            
            # Add custom vocabulary if available
            if self.custom_vocabulary:
                transcript_request['custom_vocabulary'] = self.custom_vocabulary
            
            response = requests.post(transcript_url, json=transcript_request, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"Transcription request failed: {response.status_code}")
            
            transcript_response = response.json()
            transcript_id = transcript_response['id']
            
            # Poll for completion
            polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
            
            while True:
                polling_response = requests.get(polling_url, headers=headers)
                
                if polling_response.status_code != 200:
                    raise Exception(f"Polling failed: {polling_response.status_code}")
                
                result = polling_response.json()
                
                if result['status'] == 'completed':
                    # Get the transcribed text
                    transcribed_text = result['text']
                    
                    # Process sentiment and context
                    enhanced_text = self.process_enhanced_transcription(result, transcribed_text)
                    
                    # Type the enhanced text directly into the focused application
                    self.type_text(enhanced_text)
                    
                    # Update status
                    self.status_label.config(text="✅ Ready to voice type", fg='#4CAF50')
                    break
                    
                elif result['status'] == 'error':
                    raise Exception(f"Transcription failed: {result}")
                
                time.sleep(1)
            
            # Clean up temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            messagebox.showerror("Error", f"Transcription failed: {str(e)}")
            self.status_label.config(text="❌ Ready to voice type", fg='#4CAF50')
    
    def process_enhanced_transcription(self, result, text):
        """Process transcription with sentiment and context analysis"""
        enhanced_text = text
        
        # Add punctuation based on sentiment and context
        if 'sentiment_analysis_results' in result and result['sentiment_analysis_results']:
            sentiment = result['sentiment_analysis_results']
            if sentiment and sentiment.get('overall') == 'NEGATIVE':
                # Add appropriate punctuation for negative statements
                if not enhanced_text.endswith(('.', '!', '?')):
                    enhanced_text += '.'
            elif sentiment and sentiment.get('overall') == 'POSITIVE':
                # Add exclamation for positive statements
                if not enhanced_text.endswith(('.', '!', '?')):
                    enhanced_text += '!'
        
        # Detect questions and add question marks
        question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'which', 'whose', 'whom']
        if any(word in enhanced_text.lower().split() for word in question_words):
            if not enhanced_text.endswith('?'):
                enhanced_text += '?'
        
        # Add proper capitalization
        enhanced_text = enhanced_text.capitalize()
        
        return enhanced_text
    
    def type_text(self, text):
        """Type text directly into the focused application"""
        try:
            # Split text into words and type each word with a small delay
            words = text.split()
            for i, word in enumerate(words):
                # Type the word
                keyboard.write(word)
                
                # Add space between words (except for the last word)
                if i < len(words) - 1:
                    keyboard.write(' ')
                
                # Small delay between words for natural typing
                time.sleep(0.1)
            
            messagebox.showinfo("Success", f"Voice typed: '{text}'")
            
        except Exception as e:
            print(f"Error typing text: {e}")
            messagebox.showerror("Error", "Failed to type text. Please check if you have a text field focused.")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
    
    def __del__(self):
        """Cleanup when the application is closed"""
        self.cleanup()

if __name__ == "__main__":
    app = VoiceTyping()
    app.run()
