# test_mic.py
import sounddevice as sd
import numpy as np

def test():
    print("Testing microphone...")
    try:
        # Query default input device
        device_info = sd.query_devices(kind='input')
        print(f"Default input device: {device_info['name']}")
        
        # Try to open stream
        with sd.InputStream(channels=1, callback=lambda *args: None):
            print("Successfully opened InputStream!")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nAll devices:")
        print(sd.query_devices())

if __name__ == "__main__":
    test()
