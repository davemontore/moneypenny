import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import keyboard
import pyaudio
import wave
import requests
import json
import os
from datetime import datetime
from cryptography.fernet import Fernet

class ModernVoiceToText:
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
        self.copy_hotkey = 'ctrl+shift+c'
        
        # Security setup
        self.encryption_key = self.get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("Voice to Text - Modern Edition")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a1a')
        
        # Make window resizable
        self.root.resizable(True, True)
        
        # Load saved settings
        self.load_settings()
        
        # Create GUI elements
        self.setup_gui()
        
        # Setup hotkeys
        self.setup_hotkeys()
        
        # Check for API key
        self.check_api_key()
    
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
                    self.copy_hotkey = settings.get('copy_hotkey', 'ctrl+shift+c')
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to file with encrypted API key"""
        try:
            settings = {
                'encrypted_api_key': self.encrypt_data(self.api_key) if self.api_key else None,
                'record_hotkey': self.record_hotkey,
                'copy_hotkey': self.copy_hotkey
            }
            with open('settings.json', 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def setup_gui(self):
        """Create the modern graphical user interface"""
        # Configure style for modern look
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure notebook style
        style.configure('TNotebook', background='#1a1a1a', borderwidth=0)
        style.configure('TNotebook.Tab', background='#2d2d2d', foreground='white', 
                       padding=[20, 10], font=('Segoe UI', 10))
        style.map('TNotebook.Tab', background=[('selected', '#007acc'), ('active', '#404040')])
        
        # Main container with padding
        main_container = tk.Frame(self.root, bg='#1a1a1a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Modern title
        title_frame = tk.Frame(main_container, bg='#1a1a1a')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            title_frame, 
            text="🎤 Voice to Text Anywhere", 
            font=("Segoe UI", 28, "bold"),
            bg='#1a1a1a',
            fg='white'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Speak into any text field on your computer",
            font=("Segoe UI", 12),
            bg='#1a1a1a',
            fg='#888888'
        )
        subtitle_label.pack()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Main tab
        self.setup_main_tab()
        
        # Settings tab
        self.setup_settings_tab()
    
    def setup_main_tab(self):
        """Setup the main recording tab"""
        main_tab = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(main_tab, text="🎤 Record")
        
        # Instructions with modern styling
        instructions_frame = tk.Frame(main_tab, bg='#1a1a1a')
        instructions_frame.pack(fill=tk.X, pady=20)
        
        instructions = tk.Label(
            instructions_frame,
            text=f"Press {self.record_hotkey.upper()} to start/stop recording",
            font=("Segoe UI", 12),
            bg='#1a1a1a',
            fg='#ffffff'
        )
        instructions.pack()
        
        instructions2 = tk.Label(
            instructions_frame,
            text=f"Press {self.copy_hotkey.upper()} to paste text into your active application",
            font=("Segoe UI", 12),
            bg='#1a1a1a',
            fg='#ffffff'
        )
        instructions2.pack()
        
        # Workflow instructions
        workflow_label = tk.Label(
            instructions_frame,
            text="💡 Workflow: 1) Click in any text field → 2) Press hotkey to record → 3) Speak → 4) Press hotkey to paste",
            font=("Segoe UI", 10),
            bg='#1a1a1a',
            fg='#00ff88',
            wraplength=600
        )
        workflow_label.pack(pady=(10, 0))
        
        # Status label with modern styling
        self.status_label = tk.Label(
            main_tab,
            text="Ready to record",
            font=("Segoe UI", 14, "bold"),
            bg='#1a1a1a',
            fg='#00ff88'
        )
        self.status_label.pack(pady=10)
        
        # Text area with modern styling
        text_container = tk.Frame(main_tab, bg='#2d2d2d', relief=tk.FLAT, bd=0)
        text_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.text_area = tk.Text(
            text_container,
            font=("Segoe UI", 12),
            bg='#2d2d2d',
            fg='white',
            insertbackground='white',
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=15,
            pady=15,
            selectbackground='#007acc',
            selectforeground='white'
        )
        
        # Modern scrollbar
        scrollbar = tk.Scrollbar(text_container, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Modern buttons frame
        button_container = tk.Frame(main_tab, bg='#1a1a1a')
        button_container.pack(pady=20)
        
        # Record button with modern styling
        self.record_button = tk.Button(
            button_container,
            text="🎤 Start Recording",
            command=self.toggle_recording,
            font=("Segoe UI", 12, "bold"),
            bg='#ff4757',
            fg='white',
            relief=tk.FLAT,
            padx=25,
            pady=12,
            cursor='hand2',
            activebackground='#ff3742',
            activeforeground='white'
        )
        self.record_button.pack(side=tk.LEFT, padx=10)
        
        # Copy button with modern styling
        copy_button = tk.Button(
            button_container,
            text="📋 Paste to App",
            command=self.copy_to_clipboard,
            font=("Segoe UI", 12, "bold"),
            bg='#3742fa',
            fg='white',
            relief=tk.FLAT,
            padx=25,
            pady=12,
            cursor='hand2',
            activebackground='#2f3542',
            activeforeground='white'
        )
        copy_button.pack(side=tk.LEFT, padx=10)
        
        # Clear button with modern styling
        clear_button = tk.Button(
            button_container,
            text="🗑️ Clear Text",
            command=self.clear_text,
            font=("Segoe UI", 12, "bold"),
            bg='#747d8c',
            fg='white',
            relief=tk.FLAT,
            padx=25,
            pady=12,
            cursor='hand2',
            activebackground='#57606f',
            activeforeground='white'
        )
        clear_button.pack(side=tk.LEFT, padx=10)
    
    def setup_settings_tab(self):
        """Setup the modern settings tab"""
        settings_tab = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(settings_tab, text="⚙️ Settings")
        
        # Create scrollable frame for settings
        canvas = tk.Canvas(settings_tab, bg='#1a1a1a', highlightthickness=0)
        scrollbar = tk.Scrollbar(settings_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1a1a1a')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # API Key Section with modern styling
        api_frame = tk.LabelFrame(
            scrollable_frame,
            text="🔑 AssemblyAI API Key",
            font=("Segoe UI", 14, "bold"),
            bg='#1a1a1a',
            fg='white',
            relief=tk.FLAT,
            bd=2
        )
        api_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Security info with modern styling
        security_info = tk.Label(
            api_frame,
            text="🔒 Your API key is encrypted and stored locally. It's only sent to AssemblyAI over secure HTTPS.",
            font=("Segoe UI", 10),
            bg='#1a1a1a',
            fg='#00ff88',
            wraplength=600
        )
        security_info.pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        # API Key entry with modern styling
        api_label = tk.Label(
            api_frame,
            text="Enter your AssemblyAI API key:",
            font=("Segoe UI", 11),
            bg='#1a1a1a',
            fg='#ffffff'
        )
        api_label.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        self.api_entry = tk.Entry(
            api_frame,
            font=("Segoe UI", 12),
            width=60,
            show="*",
            bg='#2d2d2d',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT,
            bd=0
        )
        self.api_entry.pack(padx=15, pady=(0, 15))
        
        if self.api_key:
            self.api_entry.insert(0, self.api_key)
        
        # API Key buttons frame
        api_button_frame = tk.Frame(api_frame, bg='#1a1a1a')
        api_button_frame.pack(padx=15, pady=(0, 15))
        
        # Show/Hide API key button
        show_api_button = tk.Button(
            api_button_frame,
            text="👁️ Show/Hide",
            command=self.toggle_api_visibility,
            font=("Segoe UI", 10),
            bg='#747d8c',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2',
            activebackground='#57606f',
            activeforeground='white'
        )
        show_api_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear API key button
        clear_api_button = tk.Button(
            api_button_frame,
            text="🗑️ Clear API Key",
            command=self.clear_api_key,
            font=("Segoe UI", 10),
            bg='#ff4757',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2',
            activebackground='#ff3742',
            activeforeground='white'
        )
        clear_api_button.pack(side=tk.LEFT)
        
        # Hotkeys Section with modern styling
        hotkey_frame = tk.LabelFrame(
            scrollable_frame,
            text="⌨️ Keyboard Shortcuts",
            font=("Segoe UI", 14, "bold"),
            bg='#1a1a1a',
            fg='white',
            relief=tk.FLAT,
            bd=2
        )
        hotkey_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Record hotkey
        record_hotkey_label = tk.Label(
            hotkey_frame,
            text="Recording hotkey:",
            font=("Segoe UI", 11),
            bg='#1a1a1a',
            fg='#ffffff'
        )
        record_hotkey_label.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        self.record_hotkey_entry = tk.Entry(
            hotkey_frame,
            font=("Segoe UI", 12),
            width=40,
            bg='#2d2d2d',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT,
            bd=0
        )
        self.record_hotkey_entry.pack(padx=15, pady=(0, 15))
        self.record_hotkey_entry.insert(0, self.record_hotkey)
        
        # Copy hotkey
        copy_hotkey_label = tk.Label(
            hotkey_frame,
            text="Paste to app hotkey:",
            font=("Segoe UI", 11),
            bg='#1a1a1a',
            fg='#ffffff'
        )
        copy_hotkey_label.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        self.copy_hotkey_entry = tk.Entry(
            hotkey_frame,
            font=("Segoe UI", 12),
            width=40,
            bg='#2d2d2d',
            fg='white',
            insertbackground='white',
            relief=tk.FLAT,
            bd=0
        )
        self.copy_hotkey_entry.pack(padx=15, pady=(0, 15))
        self.copy_hotkey_entry.insert(0, self.copy_hotkey)
        
        # Hotkey help
        hotkey_help = tk.Label(
            hotkey_frame,
            text="💡 Tip: Use combinations like 'ctrl+shift+r', 'f2', 'alt+r', etc.",
            font=("Segoe UI", 9),
            bg='#1a1a1a',
            fg='#888888',
            wraplength=500
        )
        hotkey_help.pack(padx=15, pady=(0, 15))
        
        # Action buttons frame
        action_frame = tk.Frame(scrollable_frame, bg='#1a1a1a')
        action_frame.pack(pady=30)
        
        # Save button with modern styling
        save_button = tk.Button(
            action_frame,
            text="💾 Save Settings",
            command=self.save_settings_from_gui,
            font=("Segoe UI", 14, "bold"),
            bg='#00ff88',
            fg='#1a1a1a',
            relief=tk.FLAT,
            padx=40,
            pady=15,
            cursor='hand2',
            activebackground='#00cc6a',
            activeforeground='#1a1a1a'
        )
        save_button.pack(side=tk.LEFT, padx=10)
        
        # Test API button with modern styling
        test_api_button = tk.Button(
            action_frame,
            text="🧪 Test API Key",
            command=self.test_api_key,
            font=("Segoe UI", 14, "bold"),
            bg='#ffa502',
            fg='#1a1a1a',
            relief=tk.FLAT,
            padx=40,
            pady=15,
            cursor='hand2',
            activebackground='#ff9500',
            activeforeground='#1a1a1a'
        )
        test_api_button.pack(side=tk.LEFT, padx=10)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def clear_api_key(self):
        """Clear the stored API key"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear your API key? You'll need to enter it again."):
            self.api_key = None
            self.api_entry.delete(0, tk.END)
            self.save_settings()
            messagebox.showinfo("Success", "API key cleared successfully!")
    
    def toggle_api_visibility(self):
        """Toggle API key visibility"""
        if self.api_entry.cget('show') == '*':
            self.api_entry.config(show='')
        else:
            self.api_entry.config(show='*')
    
    def save_settings_from_gui(self):
        """Save settings from the GUI"""
        # Get API key
        new_api_key = self.api_entry.get().strip()
        if new_api_key:
            self.api_key = new_api_key
        else:
            messagebox.showerror("Error", "Please enter your AssemblyAI API key")
            return
        
        # Get hotkeys
        new_record_hotkey = self.record_hotkey_entry.get().strip().lower()
        new_copy_hotkey = self.copy_hotkey_entry.get().strip().lower()
        
        if not new_record_hotkey or not new_copy_hotkey:
            messagebox.showerror("Error", "Please enter both hotkeys")
            return
        
        # Update hotkeys
        self.record_hotkey = new_record_hotkey
        self.copy_hotkey = new_copy_hotkey
        
        # Save to file
        self.save_settings()
        
        # Update hotkeys
        self.setup_hotkeys()
        
        # Update instructions
        self.update_instructions()
        
        messagebox.showinfo("Success", "Settings saved successfully!")
    
    def test_api_key(self):
        """Test the API key"""
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your API key first")
            return
        
        # Test with a simple API call
        headers = {
            'authorization': api_key,
            'content-type': 'application/json'
        }
        
        try:
            response = requests.get("https://api.assemblyai.com/v2/transcript", headers=headers)
            if response.status_code == 200:
                messagebox.showinfo("Success", "✅ API key is valid!")
            else:
                messagebox.showerror("Error", f"❌ API key test failed: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Connection error: {str(e)}")
    
    def update_instructions(self):
        """Update the instructions with current hotkeys"""
        # Find the instructions labels in the main tab
        for widget in self.notebook.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and "Press" in child.cget('text'):
                        child.config(text=f"Press {self.record_hotkey.upper()} to start/stop recording")
                        break
                    elif isinstance(child, tk.Label) and "copy" in child.cget('text').lower():
                        child.config(text=f"Press {self.copy_hotkey.upper()} to paste text into your active application")
                        break
    
    def setup_hotkeys(self):
        """Setup keyboard hotkeys"""
        # Remove existing hotkeys
        try:
            keyboard.remove_hotkey(self.record_hotkey)
            keyboard.remove_hotkey(self.copy_hotkey)
        except:
            pass
        
        # Add new hotkeys
        keyboard.add_hotkey(self.record_hotkey, self.toggle_recording)
        keyboard.add_hotkey(self.copy_hotkey, self.copy_to_clipboard)
    
    def check_api_key(self):
        """Check if API key is set"""
        if not self.api_key:
            # Switch to settings tab and show message
            self.notebook.select(1)  # Switch to settings tab
            messagebox.showinfo("Welcome!", "Please enter your AssemblyAI API key in the Settings tab to get started!")
    
    def toggle_recording(self):
        """Start or stop recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording audio"""
        if not self.api_key:
            messagebox.showerror("Error", "Please set your AssemblyAI API key first in the Settings tab")
            self.notebook.select(1)  # Switch to settings tab
            return
        
        self.is_recording = True
        self.audio_frames = []
        
        # Update GUI
        self.status_label.config(text="🔴 Recording...", fg='#ff4757')
        self.record_button.config(text="⏹️ Stop Recording", bg='#ffa502')
        
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
        self.status_label.config(text="🔄 Processing...", fg='#ffa502')
        self.record_button.config(text="🎤 Start Recording", bg='#ff4757')
        
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
                upload_url_response = response.json()
            
            if response.status_code != 200:
                raise Exception(f"Upload failed: {upload_url_response}")
            
            audio_url = upload_url_response['upload_url']
            
            # Request transcription
            transcript_url = "https://api.assemblyai.com/v2/transcript"
            transcript_request = {
                'audio_url': audio_url,
                'language_code': 'en'
            }
            
            response = requests.post(transcript_url, json=transcript_request, headers=headers)
            transcript_response = response.json()
            
            if response.status_code != 200:
                raise Exception(f"Transcription request failed: {transcript_response}")
            
            transcript_id = transcript_response['id']
            
            # Poll for completion
            polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
            
            while True:
                polling_response = requests.get(polling_url, headers=headers)
                polling_response = polling_response.json()
                
                if polling_response['status'] == 'completed':
                    # Get the transcribed text
                    transcribed_text = polling_response['text']
                    
                    # Add to text area
                    self.text_area.insert(tk.END, transcribed_text + "\n\n")
                    self.text_area.see(tk.END)
                    
                    # Update status
                    self.status_label.config(text="✅ Transcription complete", fg='#00ff88')
                    break
                    
                elif polling_response['status'] == 'error':
                    raise Exception(f"Transcription failed: {polling_response}")
                
                time.sleep(1)
            
            # Clean up temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            messagebox.showerror("Error", f"Transcription failed: {str(e)}")
            self.status_label.config(text="❌ Transcription failed", fg='#ff4757')
    
    def copy_to_clipboard(self):
        """Copy text to clipboard and paste it into the currently focused application"""
        text = self.text_area.get(1.0, tk.END).strip()
        if text:
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            
            # Wait a moment for clipboard to update
            self.root.after(100, self.paste_to_focused_app)
        else:
            messagebox.showwarning("Warning", "No text to paste")
    
    def paste_to_focused_app(self):
        """Paste the clipboard content into the currently focused application"""
        try:
            # Simulate Ctrl+V to paste into the focused application
            keyboard.press_and_release('ctrl+v')
            messagebox.showinfo("Success", "Text pasted into your active application!")
        except Exception as e:
            print(f"Error pasting text: {e}")
            messagebox.showerror("Error", "Failed to paste text. Please manually paste with Ctrl+V.")
    
    def clear_text(self):
        """Clear the text area"""
        self.text_area.delete(1.0, tk.END)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
    
    def __del__(self):
        """Cleanup when the application is closed"""
        if self.audio:
            self.audio.terminate()

if __name__ == "__main__":
    app = ModernVoiceToText()
    app.run()
