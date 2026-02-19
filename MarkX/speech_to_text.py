# speech_to_text.py
"""
Dmitry Voice Input - Improved STT with Vosk

Features:
- Local queue per listen call (no stale audio)
- Automatic stop flag reset
- Timeout to prevent hanging
- Optional partial transcript streaming for UI
- Thread-safe operation
"""

import sounddevice as sd
import vosk
import queue
import sys
import json
import threading
import time
import os
from typing import Callable, Optional

# Model path - supports environment variable override
MODEL_PATH = os.environ.get(
    "VOSK_MODEL_PATH",
    r"C:\Users\bathini bona\Downloads\vosk-model-small-en-us-0.15\vosk-model-small-en-us-0.15"
)

# Lazy load model (so import doesn't fail if model missing)
_model = None

def get_model():
    """Lazy load the Vosk model."""
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Vosk model not found at: {MODEL_PATH}")
        _model = vosk.Model(MODEL_PATH)
    return _model


# Global stop flag
stop_listening_flag = threading.Event()


def stop_listening():
    """Signal the current recording to stop."""
    stop_listening_flag.set()


def record_voice(
    prompt: str = "I'm listening, sir...",
    timeout_seconds: float = 15.0,
    on_partial: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Blocking call. Returns the first recognized sentence.
    
    Args:
        prompt: Message to display when starting
        timeout_seconds: Maximum time to wait for speech (prevents hanging)
        on_partial: Optional callback for streaming partial results to UI
        
    Returns:
        Recognized text, or empty string if stopped/timed out
    """
    print(prompt)

    # Reset stop flag for this run
    stop_listening_flag.clear()

    # Local queue for this call (no stale audio from previous runs)
    audio_q: "queue.Queue[bytes]" = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print(status, file=sys.stderr)
        audio_q.put(bytes(indata))

    model = get_model()
    rec = vosk.KaldiRecognizer(model, 16000)
    start_time = time.time()

    # Device selection strategy
    # 1. Try default
    # 2. Try specific likely working hosts (MME, DirectSound, WASAPI)
    # 3. Fail gracefully
    
    device_config = None
    
    try:
        # Try finding a valid input device if default fails
        try:
            with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=lambda *a: None):
                pass # Default works
        except Exception:
            print("Warning: Default mic failed. Searching for working input device...")
            # Search for a working device
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    try:
                        # Test device
                        with sd.RawInputStream(device=i, samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=lambda *a: None):
                            print(f"Found working mic: {dev['name']} (Index {i})")
                            device_config = i
                            break
                    except:
                        continue
    except Exception as e:
        print(f"Warning: Mic detection error: {e}")

    try:
        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=callback,
            device=device_config
        ):
            while True:
                # Check stop flag
                if stop_listening_flag.is_set():
                    return ""

                # Check timeout
                if (time.time() - start_time) > timeout_seconds:
                    print("Voice input timed out")
                    return ""

                # Get audio data
                try:
                    data = audio_q.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Stream partial results to UI if callback provided
                if on_partial:
                    try:
                        partial_result = json.loads(rec.PartialResult())
                        partial_text = partial_result.get("partial", "")
                        if partial_text:
                            on_partial(partial_text)
                    except:
                        pass

                # Check for final result
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").strip()
                    if text:
                        print("You:", text)
                        return text

    except Exception as e:
        print(f"Warning: STT Error: {e}")
        return ""

    return ""


def record_voice_async(
    callback_done: Callable[[str], None],
    prompt: str = "I'm listening, sir...",
    timeout_seconds: float = 15.0,
    on_partial: Optional[Callable[[str], None]] = None,
) -> threading.Thread:
    """
    Non-blocking version. Runs in a thread and calls callback_done with result.
    
    Args:
        callback_done: Called with the final text when done
        prompt: Message to display when starting
        timeout_seconds: Maximum time to wait
        on_partial: Optional callback for partial results
        
    Returns:
        The thread object (for joining if needed)
    """
    def run():
        result = record_voice(prompt, timeout_seconds, on_partial)
        callback_done(result)
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
