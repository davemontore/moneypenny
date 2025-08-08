import pyaudio

def test_microphones():
    """Test microphone detection"""
    print("🔍 Testing Microphone Detection...")
    print("=" * 50)
    
    audio = pyaudio.PyAudio()
    
    try:
        device_count = audio.get_device_count()
        print(f"Total audio devices found: {device_count}")
        print()
        
        microphones = []
        
        for i in range(device_count):
            device_info = audio.get_device_info_by_index(i)
            name = device_info['name']
            input_channels = device_info['maxInputChannels']
            output_channels = device_info['maxOutputChannels']
            sample_rate = int(device_info['defaultSampleRate'])
            
            print(f"Device {i}:")
            print(f"  Name: {name}")
            print(f"  Input channels: {input_channels}")
            print(f"  Output channels: {output_channels}")
            print(f"  Sample rate: {sample_rate} Hz")
            
            if input_channels > 0:
                microphones.append({
                    'index': i,
                    'name': name,
                    'channels': input_channels,
                    'sample_rate': sample_rate
                })
                print(f"  ✅ This is a microphone!")
            else:
                print(f"  ❌ Not a microphone (no input channels)")
            print()
        
        print("=" * 50)
        print(f"🎤 Microphones found: {len(microphones)}")
        
        if microphones:
            print("\nAvailable microphones:")
            for i, mic in enumerate(microphones):
                print(f"  {i+1}. Device {mic['index']}: {mic['name']}")
                print(f"     Channels: {mic['channels']}, Sample Rate: {mic['sample_rate']} Hz")
        else:
            print("❌ No microphones found!")
            print("Please check:")
            print("  1. Your microphone is connected")
            print("  2. Microphone permissions are enabled")
            print("  3. No other app is using the microphone")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        audio.terminate()

if __name__ == "__main__":
    test_microphones()
    input("\nPress Enter to exit...")
