# Voice Typing App - Troubleshooting Guide (Legacy UI)

## Issue: Microphone Dropdown Not Rendering

### Root Cause Analysis

The settings dialog in `voice_to_text.py` had a critical implementation problem that prevented the microphone dropdown from rendering properly.

Status: Legacy reference — as of v2.2.0 the app is headless and no longer uses the settings dialog. This document is kept for historical context only.

### Problem Details

#### 1. Dual Implementation Conflict
- **Lines 669-800**: Incomplete CustomTkinter implementation
- **Lines 820-1034**: Complete traditional Tkinter implementation
- Both implementations existed simultaneously, causing conflicts

#### 2. Incomplete CustomTkinter Implementation
The CustomTkinter section created UI elements but:
- Ended abruptly at line 800 with no completion logic
- Had no save button or settings persistence
- Left the dialog in an incomplete state

#### 3. Data Type Mismatch
```python
# WRONG - get_available_microphones() returns list of dictionaries
microphones = self.get_available_microphones()
mic_dropdown = ctk.CTkOptionMenu(
    mic_frame,
    values=microphones,  # CustomTkinter expects list of strings, not objects
)

# CORRECT - Extract names from microphone objects
mic_names = [f"{mic['index']}: {mic['name']}" for mic in microphones]
mic_dropdown = ctk.CTkOptionMenu(
    mic_frame,
    values=mic_names,  # Now it's a list of strings
)
```

#### 4. Missing Save Functionality
The CustomTkinter implementation lacked:
- Save button to persist settings
- Proper dialog completion
- Settings validation
- Window cleanup

### Solution Implemented

1. **Removed incomplete CustomTkinter code** (lines 669-800)
2. **Completed proper CustomTkinter implementation** with modern styling
3. **Fixed microphone data formatting** for dropdown compatibility
4. **Added comprehensive save functionality** for all settings
5. **Implemented proper dialog management** with validation and cleanup

### Prevention Strategies

#### For Future Development:
1. **Complete implementations before merging** - Don't leave partial code
2. **Verify data types** match UI component expectations
3. **Test all dialog functionality** before considering complete
4. **Document UI component requirements** (strings vs objects)
5. **Use consistent UI frameworks** - don't mix Tkinter and CustomTkinter

#### Code Review Checklist:
- [ ] All UI dialogs have save/cancel buttons
- [ ] Data types match component requirements
- [ ] Settings persistence works correctly
- [ ] Dialog cleanup and window management implemented
- [ ] No duplicate/conflicting implementations

### Technical Notes

#### CustomTkinter Requirements:
- `CTkOptionMenu` requires `values` parameter as list of strings
- Use `CTkButton` with `command` parameter for actions
- Set `fg_color`, `text_color`, `hover_color` for consistent theming
- Use `CTkFrame` with `corner_radius` for modern appearance

#### Settings Dialog Best Practices:
- Always include validation before saving
- Provide user feedback for save operations
- Handle dialog cancellation properly
- Center dialog on parent window
- Use `transient()` and `grab_set()` for modal behavior

This issue demonstrates the importance of completing UI implementations fully and testing all functionality before considering a feature complete.

---

## Issue: Transcription Failing with 400 Error

### Root Cause Analysis

The transcription system was failing with HTTP 400 errors due to incorrect content-type headers in API requests.

**Status: ✅ RESOLVED in v2.1.0**

### Problem Details

#### Content-Type Header Mismatch
The AssemblyAI file upload was using incorrect headers:

```python
# WRONG - Sending binary data with JSON headers
headers = {
    'authorization': self.api_key,
    'content-type': 'application/json'  # ❌ Told API to expect JSON
}
# But sending binary WAV file data
response = requests.post(upload_url, headers=headers, data=binary_audio_file)
```

#### Why This Failed
1. **Server expectation mismatch**: API expected JSON but received binary audio
2. **400 Bad Request**: Server correctly rejected malformed request
3. **Silent failure**: Error wasn't descriptive enough for debugging

### Solution Implemented

#### Separate Headers for Different Request Types
```python
# File upload headers (binary data)
upload_headers = {
    'authorization': self.api_key
    # No content-type - let requests auto-detect
}

# Transcription request headers (JSON data)
transcript_headers = {
    'authorization': self.api_key,
    'content-type': 'application/json'
}
```

#### Enhanced Error Reporting
Added detailed error messages showing actual API responses:
```python
if response.status_code != 200:
    error_details = ""
    try:
        error_response = response.json()
        error_details = f" - {error_response.get('error', 'Unknown error')}"
    except:
        error_details = f" - Response: {response.text[:200]}"
    raise Exception(f"Upload failed: {response.status_code}{error_details}")
```

### Prevention Strategies
1. **Match content-type to actual data**: Binary for files, JSON for structured data
2. **Use different headers for different endpoints**: Don't reuse headers inappropriately
3. **Add comprehensive error logging**: Include API response details in error messages
4. **Test with real API calls**: Verify actual network requests work as expected

---

## Issue: Hotkeys Preventing Normal Typing

### Root Cause Analysis

The keyboard hook system was suppressing individual keys instead of just the hotkey combination, preventing normal typing.

**Status: ✅ RESOLVED in v2.1.0**

### Problem Details

#### Over-Suppression of Keys
The original implementation suppressed ALL instances of hotkey component keys:

```python
# WRONG - Suppressed individual keys everywhere
for key in keys:
    keyboard.on_press_key(key, self.on_key_press, suppress=True)  # ❌
    keyboard.on_release_key(key, self.on_key_release, suppress=True)  # ❌
```

#### Impact on User Experience
1. **"r" key blocked**: Couldn't type "r" anywhere because it was part of Ctrl+Shift+R
2. **Ctrl combinations broken**: Ctrl+C, Ctrl+V stopped working
3. **Normal typing disrupted**: Basic text input was compromised

### Solution Implemented

#### Smart Combination-Only Suppression
```python
# CORRECT - Only suppress the exact combination
keyboard.add_hotkey(self.record_hotkey, self.start_recording, suppress=True)

# Separate release detection without suppression
for key in keys:
    keyboard.on_release_key(key, self.check_hotkey_release, suppress=False)
```

#### How It Works Now
1. **Normal keys work**: "r", "ctrl+c", etc. function normally
2. **Combination suppressed**: Only "ctrl+shift+r" is blocked from typing
3. **Hold-to-record preserved**: Still works as intended
4. **Release detection**: Monitors when combination is released

### Prevention Strategies
1. **Use keyboard.add_hotkey()**: Built-in method handles suppression correctly
2. **Test individual keys**: Ensure normal typing isn't affected
3. **Separate concerns**: Different handlers for press vs release detection
4. **Minimal suppression**: Only block what's absolutely necessary

This demonstrates the importance of understanding how keyboard hooks affect the entire system, not just the target application.
