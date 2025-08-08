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

class CleanVoiceToText:
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
        self.paste_hotkey = 'ctrl+shift+v'
        
        # Security setup
        self.encryption_key = self.get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("Voice to Text")
        self.root.geometry("600x400")
        self.root.configure(bg='#f8f9fa')
        
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
                    self.paste_hotkey = settings.get('paste_hotkey', 'ctrl+shift+v')
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to file with encrypted API key"""
        try:
            settings = {
                'encrypted_api_key': self.encrypt_data(self.api_key) if self.api_key else None,
                'record_hotkey': self.record_hotkey,
                'paste_hotkey': self.paste_hotkey
            }
            with open('settings.json', 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def setup_gui(self):
        """Create the clean graphical user interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#f8f9fa')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="Voice to Text", 
            font=("Segoe UI", 24, "bold"),
            bg='#f8f9fa',
            fg='#212529'
        )
        title_label.pack(pady=(0, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_frame,
            text="Speak into any text field on your computer",
            font=("Segoe UI", 12),
            bg='#f8f9fa',
            fg='#6c757d'
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg='#f8f9fa')
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready to record",
            font=("Segoe UI", 14),
            bg='#f8f9fa',
            fg='#28a745'
        )
        self.status_label.pack()
        
        # Instructions
        instructions_label = tk.Label(
            status_frame,
            text=f"Press {self.record_hotkey.upper()} to record • Press {self.paste_hotkey.upper()} to paste",
            font=("Segoe UI", 11),
            bg='#f8f9fa',
            fg='#6c757d'
        )
        instructions_label.pack(pady=(5, 0))
        
        # Text area
        text_frame = tk.Frame(main_frame, bg='white', relief=tk.FLAT, bd=1)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.text_area = tk.Text(
            text_frame,
            font=("Segoe UI", 12),
            bg='white',
            fg='#212529',
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=15,
            pady=15,
            selectbackground='#007bff',
            selectforeground='white'
        )
        
        scrollbar = tk.Scrollbar(text_frame, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg='#f8f9fa')
        button_frame.pack()
        
        # Record button
        self.record_button = tk.Button(
            button_frame,
            text="🎤 Record",
            command=self.toggle_recording,
            font=("Segoe UI", 12, "bold"),
            bg='#dc3545',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            activebackground='#c82333',
            activeforeground='white'
        )
        self.record_button.pack(side=tk.LEFT, padx=5)
        
        # Paste button
        paste_button = tk.Button(
            button_frame,
            text="📋 Paste to App",
            command=self.paste_to_app,
            font=("Segoe UI", 12, "bold"),
            bg='#007bff',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            activebackground='#0056b3',
            activeforeground='white'
        )
        paste_button.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        clear_button = tk.Button(
            button_frame,
            text="🗑️ Clear",
            command=self.clear_text,
            font=("Segoe UI", 12, "bold"),
            bg='#6c757d',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            activebackground='#545b62',
            activeforeground='white'
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # Settings button
        settings_button = tk.Button(
            button_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            font=("Segoe UI", 12, "bold"),
            bg='#28a745',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            activebackground='#1e7e34',
            activeforeground='white'
        )
        settings_button.pack(side=tk.LEFT, padx=5)
    
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.configure(bg='#f8f9fa')
        settings_window.resizable(False, False)
        
        # Center the window
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # API Key section
        api_frame = tk.LabelFrame(
            settings_window,
            text="AssemblyAI API Key",
            font=("Segoe UI", 12, "bold"),
            bg='#f8f9fa',
            fg='#212529'
        )
        api_frame.pack(fill=tk.X, padx=20, pady=20)
        
        api_label = tk.Label(
            api_frame,
            text="Enter your API key:",
            font=("Segoe UI", 11),
            bg='#f8f9fa',
            fg='#212529'
        )
        api_label.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        api_entry = tk.Entry(
            api_frame,
            font=("Segoe UI", 12),
            width=50,
            show="*",
            relief=tk.FLAT,
            bd=1
        )
        api_entry.pack(padx=15, pady=(0, 15))
        
        if self.api_key:
            api_entry.insert(0, self.api_key)
        
        # Show/Hide button
        show_button = tk.Button(
            api_frame,
            text="Show/Hide",
            command=lambda: self.toggle_api_visibility(api_entry),
            font=("Segoe UI", 10),
            bg='#6c757d',
            fg='white',
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        show_button.pack(pady=(0, 15))
        
        # Hotkeys section
        hotkey_frame = tk.LabelFrame(
            settings_window,
            text="Keyboard Shortcuts",
            font=("Segoe UI", 12, "bold"),
            bg='#f8f9fa',
            fg='#212529'
        )
        hotkey_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Record hotkey
        record_label = tk.Label(
            hotkey_frame,
            text="Recording hotkey:",
            font=("Segoe UI", 11),
            bg='#f8f9fa',
            fg='#212529'
        )
        record_label.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        record_entry = tk.Entry(
            hotkey_frame,
            font=("Segoe UI", 12),
            width=30,
            relief=tk.FLAT,
            bd=1
        )
        record_entry.pack(padx=15, pady=(0, 15))
        record_entry.insert(0, self.record_hotkey)
        
        # Paste hotkey
        paste_label = tk.Label(
            hotkey_frame,
            text="Paste hotkey:",
            font=("Segoe UI", 11),
            bg='#f8f9fa',
            fg='#212529'
        )
        paste_label.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        paste_entry = tk.Entry(
            hotkey_frame,
            font=("Segoe UI", 12),
            width=30,
            relief=tk.FLAT,
            bd=1
        )
        paste_entry.pack(padx=15, pady=(0, 15))
        paste_entry.insert(0, self.paste_hotkey)
        
        # Save button
        save_button = tk.Button(
            settings_window,
            text="Save Settings",
            command=lambda: self.save_settings_from_dialog(
                settings_window, api_entry, record_entry, paste_entry
            ),
            font=("Segoe UI", 12, "bold"),
            bg='#28a745',
            fg='white',
            relief=tk.FLAT,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        save_button.pack(pady=20)
    
    def toggle_api_visibility(self, entry):
        """Toggle API key visibility"""
        if entry.cget('show') == '*':
            entry.config(show='')
        else:
            entry.config(show='*')
    
    def save_settings_from_dialog(self, window, api_entry, record_entry, paste_entry):
        """Save settings from dialog"""
        # Get values
        new_api_key = api_entry.get().strip()
        new_record_hotkey = record_entry.get().strip().lower()
        new_paste_hotkey = paste_entry.get().strip().lower()
        
        if not new_api_key:
            messagebox.showerror("Error", "Please enter your API key")
            return
        
        if not new_record_hotkey or not new_paste_hotkey:
            messagebox.showerror("Error", "Please enter both hotkeys")
            return
        
        # Update settings
        self.api_key = new_api_key
        self.record_hotkey = new_record_hotkey
        self.paste_hotkey = new_paste_hotkey
        
        # Save to file
        self.save_settings()
        
        # Update hotkeys
        self.setup_hotkeys()
        
        # Update instructions
        self.update_instructions()
        
        messagebox.showinfo("Success", "Settings saved!")
        window.destroy()
    
    def update_instructions(self):
        """Update the instructions with current hotkeys"""
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and "Press" in child.cget('text'):
                        child.config(text=f"Press {self.record_hotkey.upper()} to record • Press {self.paste_hotkey.upper()} to paste")
                        break
    
    def setup_hotkeys(self):
        """Setup keyboard hotkeys"""
        # Remove existing hotkeys
        try:
            keyboard.remove_hotkey(self.record_hotkey)
            keyboard.remove_hotkey(self.paste_hotkey)
        except:
            pass
        
        # Add new hotkeys
        keyboard.add_hotkey(self.record_hotkey, self.toggle_recording)
        keyboard.add_hotkey(self.paste_hotkey, self.paste_to_app)
    
    def check_api_key(self):
        """Check if API key is set"""
        if not self.api_key:
            messagebox.showinfo("Welcome!", "Please click Settings to enter your AssemblyAI API key")
    
    def toggle_recording(self):
        """Start or stop recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording audio"""
        if not self.api_key:
            messagebox.showerror("Error", "Please set your API key in Settings first")
            return
        
        self.is_recording = True
        self.audio_frames = []
        
        # Update GUI
        self.status_label.config(text="🔴 Recording...", fg='#dc3545')
        self.record_button.config(text="⏹️ Stop", bg='#ffc107')
        
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
        self.status_label.config(text="🔄 Processing...", fg='#ffc107')
        self.record_button.config(text="🎤 Record", bg='#dc3545')
        
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
                
                if response.status_code != 200:
                    raise Exception(f"Upload failed: {response.status_code}")
                
                upload_response = response.json()
                audio_url = upload_response['upload_url']
            
            # Request transcription
            transcript_url = "https://api.assemblyai.com/v2/transcript"
            transcript_request = {
                'audio_url': audio_url,
                'language_code': 'en'
            }
            
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
                    
                    # Add to text area
                    self.text_area.insert(tk.END, transcribed_text + "\n\n")
                    self.text_area.see(tk.END)
                    
                    # Update status
                    self.status_label.config(text="✅ Ready to record", fg='#28a745')
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
            self.status_label.config(text="❌ Ready to record", fg='#28a745')
    
    def paste_to_app(self):
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
    app = CleanVoiceToText()
    app.run()
