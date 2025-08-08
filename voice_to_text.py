import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk  # Keep for some components like messagebox
import threading
import time
import keyboard
import pyaudio
import wave
import requests
import json
import os
import sys
import psutil
import tempfile
import atexit
import signal
from datetime import datetime
from cryptography.fernet import Fernet

class VoiceTyping:
    def __init__(self):
        # Check for existing instances
        if self.is_instance_running():
            messagebox.showerror("Error", "Voice Typing is already running!")
            sys.exit(1)
        
        # Create lock file
        self.lock_file = os.path.join(tempfile.gettempdir(), "voice_typing.lock")
        self.create_lock_file()
        
        # Register multiple cleanup handlers to ensure cleanup happens
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
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
        
        # Set CustomTkinter appearance - cream/black theme
        ctk.set_appearance_mode("light")
        # Create custom cream/black color theme
        ctk.set_default_color_theme("blue")  # We'll override colors manually
        
        # GUI setup
        self.root = ctk.CTk()
        self.root.title("Voice Typing")
        self.root.geometry("650x600")
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
        
        # Ensure cleanup happens on window close - X button exits completely
        self.root.protocol("WM_DELETE_WINDOW", self.safe_exit)
    
    def setup_system_tray_behavior(self):
        """Set up system tray behavior for the application"""
        # Handle minimize button - minimize to system tray (but X button exits)
        self.root.bind("<Unmap>", self.on_minimize)
        
        # Handle window state changes
        self.root.bind("<Configure>", self.on_window_configure)
        
        # Handle application destruction
        self.root.bind("<Destroy>", self.on_destroy)
    
    def on_destroy(self, event):
        """Handle application destruction"""
        if event.widget == self.root:
            self.cleanup()
    
    def is_instance_running(self):
        """Check if another instance is already running"""
        lock_file = os.path.join(tempfile.gettempdir(), "voice_typing.lock")
        
        if os.path.exists(lock_file):
            try:
                with open(lock_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process is still running
                if psutil.pid_exists(pid):
                    return True
                else:
                    # Process is dead, remove stale lock file
                    os.remove(lock_file)
            except:
                # Invalid lock file, remove it
                try:
                    os.remove(lock_file)
                except:
                    pass
        
        return False
    
    def create_lock_file(self):
        """Create lock file with current process ID"""
        try:
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            print(f"Error creating lock file: {e}")
    
    def remove_lock_file(self):
        """Remove the lock file"""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except Exception as e:
            print(f"Error removing lock file: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle system signals for cleanup"""
        print(f"Received signal {signum}, cleaning up...")
        self.cleanup()
        sys.exit(0)
    
    def safe_exit(self):
        """Safely exit the application with full cleanup"""
        try:
            self.cleanup()
            if self.root:
                self.root.quit()
                self.root.destroy()
        except:
            pass
        finally:
            os._exit(0)  # Force exit if normal exit fails
    
    def cleanup(self):
        """Clean up ALL resources when application is destroyed"""
        try:
            print("Starting cleanup...")
            
            # Stop recording if active
            if hasattr(self, 'is_recording') and self.is_recording:
                self.is_recording = False
                if hasattr(self, 'stream') and self.stream:
                    try:
                        self.stream.stop_stream()
                        self.stream.close()
                    except:
                        pass
            
            # Destroy recording indicator FIRST (most important)
            if hasattr(self, 'recording_indicator') and self.recording_indicator:
                try:
                    self.recording_indicator.destroy()
                    self.recording_indicator = None
                    print("Recording indicator destroyed")
                except:
                    pass
            
            # Clean up audio resources
            if hasattr(self, 'audio') and self.audio:
                try:
                    self.audio.terminate()
                    print("Audio resources terminated")
                except:
                    pass
            
            # Remove ALL keyboard hooks
            try:
                keyboard.unhook_all()
                print("All keyboard hooks removed")
            except:
                pass
            
            # Remove lock file
            self.remove_lock_file()
            print("Lock file removed")
            
            print("Cleanup completed successfully")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            # Force cleanup of any remaining references
            try:
                if hasattr(self, 'recording_indicator'):
                    self.recording_indicator = None
                if hasattr(self, 'audio'):
                    self.audio = None
                if hasattr(self, 'stream'):
                    self.stream = None
            except:
                pass
    
    def minimize_to_tray(self):
        """Minimize the application to system tray"""
        self.root.withdraw()  # Hide the main window
        
        # Change recording indicator appearance to show it's in background
        if hasattr(self, 'recording_button'):
            self.recording_button.config(bg='#CCCCCC', text="●")
        
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
        try:
            print("Creating recording indicator...")
            self.recording_indicator = tk.Toplevel(self.root)
            self.recording_indicator.title("Recording Indicator")
            self.recording_indicator.geometry("120x50")  # Rectangle: wider than tall
            self.recording_indicator.configure(bg='#F7F5F3')
            self.recording_indicator.overrideredirect(True)  # Remove window decorations
            self.recording_indicator.attributes('-topmost', True)  # Always on top
            self.recording_indicator.attributes('-alpha', 0.9)  # Semi-transparent
            print("Recording indicator window created successfully")
        except Exception as e:
            print(f"Error creating recording indicator: {e}")
            return
        
        # Position in top-right corner initially
        screen_width = self.recording_indicator.winfo_screenwidth()
        screen_height = self.recording_indicator.winfo_screenheight()
        x = screen_width - 140  # Account for wider rectangle
        y = 20
        self.recording_indicator.geometry(f"120x50+{x}+{y}")
        
        # Create a larger padding frame for easier dragging
        padding_frame = tk.Frame(
            self.recording_indicator, 
            bg='#F7F5F3',
            relief=tk.RAISED,
            bd=1
        )
        padding_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Add subtle drag indicator dots in corners
        for corner in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            dot = tk.Label(
                padding_frame,
                text="•",
                font=("Roboto", 6),
                bg='#F7F5F3',
                fg='#CCCCCC'
            )
            dot.place(relx=corner[0], rely=corner[1], anchor="nw" if corner == (0, 0) else "ne" if corner == (1, 0) else "sw" if corner == (0, 1) else "se")
        
        # Create a smaller recording button centered in the padding frame
        button_frame = tk.Frame(padding_frame, bg='#F7F5F3')
        button_frame.pack(expand=True, fill=tk.NONE, padx=15, pady=8)
        
        self.recording_button = tk.Button(
            button_frame,
            text="●",  # Simple dot instead of emoji
            font=("Roboto", 14, "bold"),
            bg='#F7F5F3',
            fg='#2C2C2C',
            relief=tk.FLAT,
            bd=1,
            cursor='hand2',
            command=self.toggle_recording,
            activebackground='#E8E6E4',
            highlightthickness=1,
            highlightbackground='#2C2C2C',
            width=6,  # Fixed width for consistent size
            height=1
        )
        self.recording_button.pack()
        
        # Bind mouse events for dragging to the padding frame AND the window (not the button)
        # This gives maximum drag area
        for widget in [padding_frame, self.recording_indicator]:
            widget.bind("<Button-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.on_drag)
            widget.bind("<ButtonRelease-1>", self.stop_drag)
            widget.bind("<Enter>", lambda e: e.widget.config(cursor="fleur"))  # Show move cursor
            widget.bind("<Leave>", lambda e: e.widget.config(cursor=""))  # Reset cursor
        
        # Bind right-click for context menu to frame and window (not button)
        padding_frame.bind("<Button-3>", self.show_context_menu)
        self.recording_indicator.bind("<Button-3>", self.show_context_menu)
        
        # Make the indicator always visible
        self.recording_indicator.lift()
        self.recording_indicator.attributes('-topmost', True)
        print(f"Recording indicator created and positioned at {x}, {y}")
        print("Recording indicator should now be visible")
    
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
            
            # Keep within screen bounds (account for rectangle size)
            screen_width = self.recording_indicator.winfo_screenwidth()
            screen_height = self.recording_indicator.winfo_screenheight()
            x = max(0, min(x, screen_width - 120))  # 120 is the width
            y = max(0, min(y, screen_height - 50))   # 50 is the height
            
            self.recording_indicator.geometry(f"120x50+{x}+{y}")
    
    def stop_drag(self, event):
        """Stop dragging the recording indicator"""
        self.drag_data["dragging"] = False
    
    def show_context_menu(self, event):
        """Show context menu for the recording indicator"""
        context_menu = tk.Menu(self.recording_indicator, tearoff=0, 
                              bg='#FFFFFF', fg='#2C2C2C', 
                              activebackground='#E8E6E4', activeforeground='#2C2C2C',
                              font=("Roboto", 10))
        context_menu.add_command(label="Start/Stop Recording", command=self.toggle_recording)
        context_menu.add_separator()
        context_menu.add_command(label="Show Main Window", command=self.show_main_window)
        context_menu.add_command(label="Settings", command=self.show_settings)
        context_menu.add_command(label="Vocabulary Library", command=self.show_vocabulary_library)
        context_menu.add_separator()
        context_menu.add_command(label="Exit Voice Typing", command=self.quit_application, 
                                font=("Roboto", 10, "bold"))
        
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
                self.recording_button.config(bg='#E8E6E4', text="■")  # Square for stop
            else:
                self.recording_button.config(bg='#F7F5F3', text="●")  # Dot for record
    
    def quit_application(self):
        """Quit the application completely"""
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit Voice Typing?"):
            self.safe_exit()
    
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
        """Create the modern flat graphical user interface with CustomTkinter"""
        # Set window background to cream color
        self.root.configure(fg_color="#F7F5F3")
        
        # Create main container without frame (flat design)
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Modern hero section
        hero_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        hero_frame.pack(pady=(0, 30))
        
        # Large modern title with Montserrat
        title_label = ctk.CTkLabel(
            hero_frame,
            text="Voice Typing",
            font=ctk.CTkFont(family="Montserrat", size=42, weight="bold"),
            text_color="#2C2C2C"
        )
        title_label.pack(pady=(0, 8))
        
        # Elegant subtitle with Roboto
        subtitle_label = ctk.CTkLabel(
            hero_frame,
            text="Transform speech into text instantly",
            font=ctk.CTkFont(family="Roboto", size=16),
            text_color="#666666"
        )
        subtitle_label.pack(pady=(0, 25))
        
        # Status indicator with modern styling
        status_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        status_frame.pack(pady=(0, 25))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready to voice type",
            font=ctk.CTkFont(family="Montserrat", size=18, weight="bold"),
            text_color="#2C2C2C"
        )
        self.status_label.pack()
        
        # Clean hotkey instruction (no frame)
        self.hotkey_label = ctk.CTkLabel(
            main_container,
            text=f"Hold {self.record_hotkey.upper()} to start recording",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color="#2C2C2C"
        )
        self.hotkey_label.pack(pady=(0, 30))
        
        # Simplified instructions
        workflow_text = "Click in any text field • Hold your hotkey and speak • Release to stop and see your text appear"
        
        workflow_label = ctk.CTkLabel(
            main_container,
            text=workflow_text,
            font=ctk.CTkFont(family="Roboto", size=13),
            text_color="#666666",
            justify="center"
        )
        workflow_label.pack(pady=(0, 35))
        
        # Modern button layout
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(pady=20)
        
        # Primary action button (clean, elegant)
        self.record_button = ctk.CTkButton(
            button_frame,
            text="Test",
            command=self.toggle_recording,
            font=ctk.CTkFont(family="Montserrat", size=16, weight="bold"),
            corner_radius=8,
            height=50,
            width=120,
            fg_color="#2C2C2C",
            text_color="#F7F5F3",
            hover_color="#1A1A1A"
        )
        self.record_button.pack(pady=(0, 15))
        
        # Test text box
        self.test_textbox = ctk.CTkTextbox(
            button_frame,
            width=400,
            height=80,
            font=ctk.CTkFont(family="Roboto", size=12),
            wrap="word"
        )
        self.test_textbox.pack(pady=(0, 20))
        self.test_textbox.insert("1.0", "Click Test and speak to see your transcribed text appear here...")
        
        # Secondary buttons (horizontal layout)
        secondary_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        secondary_frame.pack()
        
        # Settings button - minimal design
        settings_button = ctk.CTkButton(
            secondary_frame,
            text="Settings",
            command=self.show_settings,
            font=ctk.CTkFont(family="Roboto", size=13, weight="normal"),
            corner_radius=6,
            height=36,
            width=120,
            fg_color="transparent",
            text_color="#2C2C2C",
            hover_color="#E8E6E4",
            border_color="#DDDDDD",
            border_width=1
        )
        settings_button.pack(side="left", padx=12)
        
        # Vocabulary button - minimal design
        vocab_button = ctk.CTkButton(
            secondary_frame,
            text="Vocabulary",
            command=self.show_vocabulary_library,
            font=ctk.CTkFont(family="Roboto", size=13, weight="normal"),
            corner_radius=6,
            height=36,
            width=120,
            fg_color="transparent",
            text_color="#2C2C2C",
            hover_color="#E8E6E4",
            border_color="#DDDDDD",
            border_width=1
        )
        vocab_button.pack(side="left", padx=12)
    
    def show_settings(self):
        """Show modern settings dialog with CustomTkinter"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Voice Typing Settings")
        settings_window.geometry("700x600")
        settings_window.resizable(False, False)
        
        # Center the settings window
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Create main frame (no scrolling needed)
        main_frame = ctk.CTkFrame(settings_window, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Settings",
            font=ctk.CTkFont(family="Montserrat", size=28, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # API Key section
        api_title = ctk.CTkLabel(
            main_frame,
            text="AssemblyAI API Key",
            font=ctk.CTkFont(family="Montserrat", size=16, weight="bold")
        )
        api_title.pack(pady=(0, 10))
        
        api_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Enter your API key here",
            font=ctk.CTkFont(family="Roboto", size=12),
            width=400,
            height=35,
            show="*"
        )
        api_entry.pack(pady=(0, 10))
        
        if self.api_key:
            api_entry.delete(0, "end")
            api_entry.insert(0, self.api_key)
        
        # Button frame for API key buttons
        api_button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        api_button_frame.pack(pady=(0, 25))
        
        show_button = ctk.CTkButton(
            api_button_frame,
            text="Show/Hide",
            command=lambda: self.toggle_api_visibility(api_entry),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=100,
            height=30,
            fg_color="#F7F5F3",
            text_color="#2C2C2C",
            hover_color="#E8E6E4",
            border_color="#2C2C2C",
            border_width=1
        )
        show_button.pack(side="left", padx=5)
        
        # SEPARATE SAVE API KEY BUTTON
        save_api_button = ctk.CTkButton(
            api_button_frame,
            text="SAVE API KEY",
            command=lambda: self.save_api_key_only(api_entry),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=150,
            height=30,
            fg_color="#2C2C2C",
            text_color="#F7F5F3",
            hover_color="#1A1A1A",
            border_color="#2C2C2C",
            border_width=1
        )
        save_api_button.pack(side="left", padx=5)
        
        # Hotkey section
        hotkey_title = ctk.CTkLabel(
            main_frame,
            text="Recording Hotkey",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
        )
        hotkey_title.pack(pady=(20, 10))
        
        hotkey_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="e.g., ctrl+shift+r",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=400,
            height=35
        )
        hotkey_entry.pack(pady=(0, 25))
        hotkey_entry.insert(0, self.record_hotkey)
        
        # Microphone section
        mic_title = ctk.CTkLabel(
            main_frame,
            text="Microphone Selection",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
        )
        mic_title.pack(pady=(20, 10))
        
        # Get available microphones
        microphones = self.get_available_microphones()
        mic_names = []
        if microphones:
            mic_names = [f"{mic['index']}: {mic['name']}" for mic in microphones]
        else:
            mic_names = ["No microphones detected"]
        
        mic_dropdown = ctk.CTkOptionMenu(
            main_frame,
            values=mic_names,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=400,
            height=35,
            fg_color="#F7F5F3",
            text_color="#2C2C2C",
            button_color="#E8E6E4",
            button_hover_color="#CCCCCC"
        )
        mic_dropdown.pack(pady=(0, 25))
        
        # Set current selection
        if microphones and self.selected_microphone is not None:
            current_mic_name = f"{self.selected_microphone}: {next((mic['name'] for mic in microphones if mic['index'] == self.selected_microphone), 'Unknown')}"
            if current_mic_name in mic_names:
                mic_dropdown.set(current_mic_name)
            else:
                mic_dropdown.set(mic_names[0])
        elif mic_names:
            mic_dropdown.set(mic_names[0])
        
        # Save button
        save_button = ctk.CTkButton(
            main_frame,
            text="Save Settings",
            command=lambda: self.save_settings_from_dialog(
                settings_window, api_entry, hotkey_entry, mic_dropdown, microphones
            ),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            corner_radius=25,
            height=45,
            width=200,
            fg_color="#2C2C2C",
            text_color="#F7F5F3",
            hover_color="#1A1A1A",
            border_color="#2C2C2C",
            border_width=1
        )
        save_button.pack(pady=30)
    
    def save_api_key_only(self, api_entry):
        """Save only the API key immediately"""
        new_api_key = api_entry.get().strip()
        
        if not new_api_key:
            messagebox.showerror("Error", "Please enter your API key")
            return
        
        # Update and save API key
        self.api_key = new_api_key
        self.save_settings()
        
        print(f"API key saved successfully!")
        messagebox.showinfo("Success", "API key saved! You won't need to enter it again.")
    
    def show_vocabulary_library(self):
        """Show vocabulary library dialog with CustomTkinter"""
        vocab_window = ctk.CTkToplevel(self.root)
        vocab_window.title("Custom Vocabulary Library")
        vocab_window.geometry("700x650")
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
        main_frame = ctk.CTkFrame(vocab_window, corner_radius=15)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Custom Vocabulary Library",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Description
        desc_label = ctk.CTkLabel(
            main_frame,
            text="Add specialized words to improve transcription accuracy.\nAssemblyAI will learn to recognize these words better.",
            font=ctk.CTkFont(family="Segoe UI", size=14)
        )
        desc_label.pack(pady=(0, 25))
        
        # Add word section
        add_title = ctk.CTkLabel(
            main_frame,
            text="Add New Word",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
        )
        add_title.pack(pady=(0, 10))
        
        # Word entry
        word_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Enter specialized word or phrase",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=400,
            height=35
        )
        word_entry.pack(pady=(0, 15))
        
        # Add button
        add_button = ctk.CTkButton(
            main_frame,
            text="Add Word",
            command=lambda: self.add_word_from_dialog(word_entry, word_textbox),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=120,
            height=32,
            fg_color="#F7F5F3",
            text_color="#2C2C2C",
            hover_color="#E8E6E4",
            border_color="#2C2C2C",
            border_width=1
        )
        add_button.pack(pady=(0, 25))
        
        # Current vocabulary section
        vocab_title = ctk.CTkLabel(
            main_frame,
            text=f"Current Vocabulary ({len(self.custom_vocabulary)} words)",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
        )
        vocab_title.pack(pady=(20, 10))
        
        # Word textbox with scrollbar (CustomTkinter doesn't have Listbox, use Textbox)
        word_textbox = ctk.CTkTextbox(
            main_frame,
            width=600,
            height=250,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        word_textbox.pack(pady=(0, 15), padx=20)
        
        # Populate textbox
        if self.custom_vocabulary:
            word_textbox.insert("1.0", "\n".join(self.custom_vocabulary))
        
        # Button frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 15))
        
        # Remove button
        remove_button = ctk.CTkButton(
            button_frame,
            text="Remove Selected",
            command=lambda: self.remove_word_from_dialog_ctk(word_textbox),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=140,
            height=32,
            fg_color="#F7F5F3",
            text_color="#2C2C2C",
            hover_color="#E8E6E4",
            border_color="#2C2C2C",
            border_width=1
        )
        remove_button.pack(side="left", padx=5)
        
        # Close button
        close_button = ctk.CTkButton(
            button_frame,
            text="Done",
            command=vocab_window.destroy,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=100,
            height=32,
            fg_color="#2C2C2C",
            text_color="#F7F5F3",
            hover_color="#1A1A1A"
        )
        close_button.pack(side="left", padx=5)
    
    def add_word_from_dialog(self, entry, textbox):
        """Add word from vocabulary dialog"""
        word = entry.get().strip()
        if not word:
            messagebox.showerror("Error", "Please enter a word")
            return
        
        if self.add_custom_word(word):
            # Update the textbox display
            textbox.delete("1.0", "end")
            if self.custom_vocabulary:
                textbox.insert("1.0", "\n".join(self.custom_vocabulary))
            entry.delete(0, "end")
            pass  # Silent success
        else:
            messagebox.showerror("Error", f"'{word}' is already in vocabulary")
    
    def remove_word_from_dialog_ctk(self, textbox):
        """Remove word from vocabulary dialog (CustomTkinter version)"""
        try:
            # Get selected text
            selected_text = textbox.get("sel.first", "sel.last").strip()
            if not selected_text:
                messagebox.showerror("Error", "Please select a word to remove")
                return
            
            # Remove only the first line if multiple lines selected
            word_to_remove = selected_text.split('\n')[0].strip()
            
            if self.remove_custom_word(word_to_remove):
                # Update the textbox display
                textbox.delete("1.0", "end")
                if self.custom_vocabulary:
                    textbox.insert("1.0", "\n".join(self.custom_vocabulary))
                pass  # Silent success
            else:
                messagebox.showerror("Error", f"Could not remove '{word_to_remove}'")
        except:
            messagebox.showerror("Error", "Please select a word to remove")
    
    def remove_word_from_dialog(self, listbox):
        """Remove word from vocabulary dialog (legacy method - kept for compatibility)"""
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a word to remove")
            return
        
        word = listbox.get(selection[0])
        if self.remove_custom_word(word):
            listbox.delete(selection[0])
            pass  # Silent success
        else:
            messagebox.showerror("Error", f"Could not remove '{word}'")
    
    def toggle_api_visibility(self, entry):
        """Toggle API key visibility for CustomTkinter entry"""
        try:
            # For CustomTkinter CTkEntry, use different method
            if hasattr(entry, 'cget'):
                if entry.cget('show') == '*':
                    entry.configure(show='')
                else:
                    entry.configure(show='*')
        except:
            # Fallback for regular tkinter entries
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
    
    def save_settings_from_dialog(self, window, api_entry, hotkey_entry, mic_dropdown, microphones):
        """Save settings from dialog"""
        # Get values from CustomTkinter widgets
        new_api_key = api_entry.get().strip()
        new_record_hotkey = hotkey_entry.get().strip().lower()
        new_microphone_selection = mic_dropdown.get()
        
        if not new_api_key:
            messagebox.showerror("Error", "Please enter your API key")
            return
        
        if not new_record_hotkey:
            messagebox.showerror("Error", "Please enter the hotkey")
            return
        
        # Parse microphone selection to get index
        new_microphone_index = 0
        if new_microphone_selection and new_microphone_selection != "No microphones detected":
            try:
                new_microphone_index = int(new_microphone_selection.split(':')[0])
            except:
                new_microphone_index = 0
        
        # Update settings
        self.api_key = new_api_key
        self.record_hotkey = new_record_hotkey
        self.selected_microphone = new_microphone_index
        
        # Save to file
        self.save_settings()
        
        # Update hotkeys
        self.setup_hotkeys()
        
        # Update instructions
        self.update_instructions()
        
        print(f"Settings saved: API key updated, hotkey: {new_record_hotkey}, microphone index: {new_microphone_index}")
        messagebox.showinfo("Success", "Settings saved successfully!")
        window.destroy()
    
    def update_instructions(self):
        """Update the instructions with current hotkeys"""
        if hasattr(self, 'hotkey_label'):
            self.hotkey_label.configure(text=f"Hold {self.record_hotkey.upper()} to record voice")
    
    def setup_hotkeys(self):
        """Setup keyboard hotkeys for hold-to-record functionality"""
        # Remove existing hotkeys
        try:
            keyboard.remove_hotkey(self.record_hotkey)
        except:
            pass
        
        # Use the built-in keyboard.add_hotkey for proper suppression
        try:
            # This will only suppress the key combination, not individual keys
            keyboard.add_hotkey(self.record_hotkey, self.start_recording, suppress=True)
            
            # Set up a separate listener for release detection
            keys = self.record_hotkey.split('+')
            if len(keys) >= 2:
                # Track when the combination is released
                self.hotkey_keys = keys
                self.hotkey_active = False
                
                # Monitor key releases to stop recording
                for key in keys:
                    keyboard.on_release_key(key, self.check_hotkey_release, suppress=False)
            
            print(f"Hotkey {self.record_hotkey} registered successfully")
            
        except Exception as e:
            print(f"Error setting up hotkey {self.record_hotkey}: {e}")
            # Fallback to simple toggle method
            try:
                keyboard.add_hotkey(self.record_hotkey, self.toggle_recording, suppress=True)
                print(f"Fallback hotkey registered for toggle mode")
            except Exception as e2:
                print(f"Failed to register any hotkey: {e2}")
    
    def toggle_recording(self):
        """Toggle recording - start if not recording, stop if recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def check_hotkey_release(self, e):
        """Check if hotkey combination is released to stop recording"""
        if hasattr(self, 'hotkey_keys') and self.is_recording:
            current_key = e.name.lower()
            if current_key in self.hotkey_keys:
                # Check if any of the hotkey keys are no longer pressed
                if not all(keyboard.is_pressed(key) for key in self.hotkey_keys):
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
        if hasattr(self, 'hotkey_active'):
            self.hotkey_active = True
        
        # Update GUI
        self.status_label.configure(text="Recording... Speak now!")
        self.record_button.configure(text="Stop")
        
        # Update recording indicator
        if hasattr(self, 'recording_button'):
            self.recording_button.config(text="■", bg='#E8E6E4')
        
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
        self.status_label.configure(text="Processing...")
        self.record_button.configure(text="Test")
        
        # Update recording indicator
        if hasattr(self, 'recording_button'):
            self.recording_button.config(text="●", bg='#F7F5F3')
        
        # Stop the audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Transcribe the audio
        if self.audio_frames:
            print(f"Audio recorded: {len(self.audio_frames)} frames")
            self.transcribe_audio()
        else:
            print("No audio frames recorded!")
            self.status_label.configure(text="No audio recorded - check microphone")
    
    def record_audio(self):
        """Record audio from microphone"""
        try:
            print(f"Opening audio stream with microphone {self.selected_microphone}")
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.selected_microphone,
                frames_per_buffer=self.chunk_size
            )
            print("Audio stream opened successfully")
            
            while self.is_recording:
                data = self.stream.read(self.chunk_size)
                self.audio_frames.append(data)
                
        except Exception as e:
            print(f"Error recording audio: {e}")
            self.is_recording = False
            messagebox.showerror("Recording Error", f"Could not record audio: {str(e)}\n\nCheck your microphone selection in Settings.")
    
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
            upload_headers = {
                'authorization': self.api_key
                # Don't set content-type - let requests auto-detect for binary data
            }
            
            # Upload the file
            upload_url = "https://api.assemblyai.com/v2/upload"
            
            with open(temp_filename, "rb") as f:
                response = requests.post(upload_url, headers=upload_headers, data=f)
                
                if response.status_code != 200:
                    error_details = ""
                    try:
                        error_response = response.json()
                        error_details = f" - {error_response.get('error', 'Unknown error')}"
                    except:
                        error_details = f" - Response: {response.text[:200]}"
                    raise Exception(f"Upload failed: {response.status_code}{error_details}")
                
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
            
            # Headers for JSON transcription request
            transcript_headers = {
                'authorization': self.api_key,
                'content-type': 'application/json'
            }
            
            response = requests.post(transcript_url, json=transcript_request, headers=transcript_headers)
            
            if response.status_code != 200:
                error_details = ""
                try:
                    error_response = response.json()
                    error_details = f" - {error_response.get('error', 'Unknown error')}"
                except:
                    error_details = f" - Response: {response.text[:200]}"
                raise Exception(f"Transcription request failed: {response.status_code}{error_details}")
            
            transcript_response = response.json()
            transcript_id = transcript_response['id']
            
            # Poll for completion
            polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
            
            while True:
                polling_response = requests.get(polling_url, headers=transcript_headers)
                
                if polling_response.status_code != 200:
                    raise Exception(f"Polling failed: {polling_response.status_code}")
                
                result = polling_response.json()
                
                if result['status'] == 'completed':
                    # Get the transcribed text
                    transcribed_text = result['text']
                    
                    # Process sentiment and context
                    enhanced_text = self.process_enhanced_transcription(result, transcribed_text)
                    
                    # Display in test textbox if testing, otherwise type into focused application
                    if hasattr(self, 'test_textbox'):
                        self.test_textbox.delete("1.0", "end")
                        self.test_textbox.insert("1.0", enhanced_text)
                    else:
                        self.type_text(enhanced_text)
                    
                    # Update status
                    self.status_label.configure(text="Ready to voice type")
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
            self.status_label.configure(text="Ready to voice type")
    
    def process_enhanced_transcription(self, result, text):
        """Process transcription with sentiment and context analysis"""
        enhanced_text = text
        
        # Add punctuation based on sentiment and context
        if 'sentiment_analysis_results' in result and result['sentiment_analysis_results']:
            sentiment_results = result['sentiment_analysis_results']
            # Handle different possible formats of sentiment analysis results
            try:
                if isinstance(sentiment_results, list) and len(sentiment_results) > 0:
                    # If it's a list, get the first item
                    sentiment = sentiment_results[0]
                elif isinstance(sentiment_results, dict):
                    # If it's already a dict, use it directly
                    sentiment = sentiment_results
                else:
                    sentiment = None
                
                if sentiment and isinstance(sentiment, dict):
                    overall_sentiment = sentiment.get('overall') or sentiment.get('sentiment')
                    if overall_sentiment == 'NEGATIVE':
                        # Add appropriate punctuation for negative statements
                        if not enhanced_text.endswith(('.', '!', '?')):
                            enhanced_text += '.'
                    elif overall_sentiment == 'POSITIVE':
                        # Add exclamation for positive statements
                        if not enhanced_text.endswith(('.', '!', '?')):
                            enhanced_text += '!'
            except Exception as e:
                print(f"Error processing sentiment analysis: {e}")
                # Continue without sentiment-based punctuation
        
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
            
            # Silent success - text was typed, user will see it appear
            
        except Exception as e:
            print(f"Error typing text: {e}")
            messagebox.showerror("Error", "Failed to type text. Please check if you have a text field focused.")
    
    def run(self):
        """Start the application"""
        try:
            print("Starting Voice Typing application...")
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Application interrupted by user")
        except Exception as e:
            print(f"Error in mainloop: {e}")
        finally:
            print("Application shutting down...")
            self.cleanup()

if __name__ == "__main__":
    app = None
    try:
        app = VoiceTyping()
        app.run()
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        if app:
            app.cleanup()
        print("Application terminated")
        sys.exit(0)
