"""
voice.py — JARVIS Voice Input (STT) & Output (TTS)
====================================================
TTS: Uses Windows SAPI COM object (win32com) — most reliable on Windows.
     Falls back to pyttsx3 if win32com unavailable.
STT: speech_recognition with PyAudioWPatch (Python 3.14 compatible).
"""

# ── PyAudio compatibility shim (must be first) ────────────────────────────────
import pyaudio_shim  # noqa — registers PyAudioWPatch as 'pyaudio' for SpeechRecognition

import re
import io
import queue
import threading
import speech_recognition as sr

from config import (
    TTS_ENGINE, PYTTSX3_RATE, PYTTSX3_VOLUME, PYTTSX3_VOICE_INDEX,
    STT_ENGINE, WHISPER_MODEL, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
    COMMAND_TIMEOUT, WAKE_WORD_TIMEOUT
)

# ══════════════════════════════════════════════════════════════════════════════
#  TTS — Windows SAPI COM (most reliable on Windows)
# ══════════════════════════════════════════════════════════════════════════════

_tts_queue  = queue.Queue()
_tts_thread = None
_tts_ready  = threading.Event()


def _tts_worker():
    """
    Dedicated TTS thread using Windows SAPI COM.
    COM objects must be created and used in the same thread (CoInitialize).
    """
    # Initialize COM for this thread
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except ImportError:
        pass

    # Try SAPI COM first (proven working on this machine)
    speaker = None
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Volume = 100
        speaker.Rate   = 1    # Slightly faster than default (0)
        print("[TTS] Using Windows SAPI COM engine")
    except Exception as e:
        print(f"[TTS] SAPI COM unavailable ({e}), falling back to pyttsx3")

    # Fallback: pyttsx3
    pyttsx3_engine = None
    if speaker is None:
        try:
            import pyttsx3
            pyttsx3_engine = pyttsx3.init()
            pyttsx3_engine.setProperty("rate",   PYTTSX3_RATE)
            pyttsx3_engine.setProperty("volume", PYTTSX3_VOLUME)
            voices = pyttsx3_engine.getProperty("voices")
            if voices and PYTTSX3_VOICE_INDEX < len(voices):
                pyttsx3_engine.setProperty("voice", voices[PYTTSX3_VOICE_INDEX].id)
            print("[TTS] Using pyttsx3 fallback engine")
        except Exception as e:
            print(f"[TTS] pyttsx3 also unavailable: {e}")

    _tts_ready.set()

    while True:
        text = _tts_queue.get()
        if text is None:   # Poison pill
            break
        try:
            if speaker is not None:
                speaker.Speak(text)
            elif pyttsx3_engine is not None:
                pyttsx3_engine.say(text)
                pyttsx3_engine.runAndWait()
            else:
                print(f"[TTS] No engine available. Would say: {text[:60]}")
        except Exception as e:
            print(f"[TTS] Speak error: {e}")
        finally:
            _tts_queue.task_done()


def _ensure_tts_running():
    """Start the TTS worker thread if not already running."""
    global _tts_thread
    if _tts_thread is None or not _tts_thread.is_alive():
        _tts_thread = threading.Thread(target=_tts_worker, daemon=True, name="TTS-Worker")
        _tts_thread.start()
        _tts_ready.wait(timeout=5)


# ── Public TTS API ─────────────────────────────────────────────────────────────

def speak(text: str) -> None:
    """
    Speak the given text aloud.
    Safe to call from ANY thread — queues text for the dedicated TTS worker.

    Args:
        text: The string to speak (markdown stripped automatically)
    """
    if not text or not text.strip():
        return

    clean = _strip_markdown(text)
    if not clean:
        return

    if TTS_ENGINE == "elevenlabs" and ELEVENLABS_API_KEY:
        threading.Thread(target=_speak_elevenlabs, args=(clean,), daemon=True).start()
    else:
        _ensure_tts_running()
        _tts_queue.put(clean)



def stop_speaking() -> None:
    """Clear the TTS queue (interrupt current/pending speech)."""
    try:
        while not _tts_queue.empty():
            _tts_queue.get_nowait()
            _tts_queue.task_done()
    except queue.Empty:
        pass


def _strip_markdown(text: str) -> str:
    """Remove markdown symbols so TTS reads naturally."""
    text = re.sub(r'\*\*?(.*?)\*\*?', r'\1', text)          # bold/italic
    text = re.sub(r'`{1,3}.*?`{1,3}', '', text, flags=re.DOTALL)  # code
    text = re.sub(r'#+\s', '', text)                          # headings
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)           # links
    text = re.sub(r'[-*•]\s', '', text)                       # list markers
    text = re.sub(r'\n{2,}', '. ', text)                      # paragraph breaks
    return text.strip()


def _speak_elevenlabs(text: str) -> None:
    """Speak using ElevenLabs cloud TTS."""
    try:
        import requests
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code == 200:
            _play_audio_bytes(resp.content)
            _ensure_tts_running()
            _tts_queue.put(text)
    except Exception as e:
        print(f"[ElevenLabs] {e} — using pyttsx3")
        _ensure_tts_running()
        _tts_queue.put(text)


def _play_audio_bytes(audio_bytes: bytes) -> None:
    """Play MP3 audio bytes."""
    try:
        import pygame
        pygame.mixer.init()
        audio_io = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(audio_io)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except ImportError:
        import tempfile, subprocess
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
        subprocess.run(["start", f.name], shell=True)


# ══════════════════════════════════════════════════════════════════════════════
#  STT — Speech Recognition
# ══════════════════════════════════════════════════════════════════════════════

# Check mic availability at import time
try:
    with sr.Microphone(device_index=1) as _tm:
        pass
    VOICE_AVAILABLE = True
    MIC_INDEX = 1    # Realtek Array
except Exception:
    try:
        with sr.Microphone() as _tm:
            pass
        VOICE_AVAILABLE = True
        MIC_INDEX = None   # System default
    except Exception:
        VOICE_AVAILABLE = False
        MIC_INDEX = None
        print("[Voice] No microphone found — voice mode disabled.")

_recognizer = sr.Recognizer()
_recognizer.energy_threshold        = 300   # Start high — will be lowered by calibration
_recognizer.dynamic_energy_threshold = True
_recognizer.pause_threshold         = 0.8


def _get_mic() -> sr.Microphone:
    """Return the best available microphone."""
    if MIC_INDEX is not None:
        return sr.Microphone(device_index=MIC_INDEX)
    return sr.Microphone()


def listen(timeout: int = COMMAND_TIMEOUT, phrase_limit: int = 15):
    """
    Listen for a voice command and return transcribed text.
    Returns None if microphone unavailable or no speech detected.
    """
    if not VOICE_AVAILABLE:
        return None
    try:
        with _get_mic() as source:
            _recognizer.adjust_for_ambient_noise(source, duration=0.4)
            # Prevent over-calibration to near-zero in a quiet room
            if _recognizer.energy_threshold < 150:
                _recognizer.energy_threshold = 150
            print("[JARVIS] Listening…")
            try:
                audio = _recognizer.listen(source, timeout=timeout,
                                           phrase_time_limit=phrase_limit)
            except sr.WaitTimeoutError:
                return None
        return _transcribe(audio)
    except Exception as e:
        print(f"[Voice] Listen error: {e}")
        return None


def listen_for_wake_word() -> bool:
    """
    Listen for "hey jarvis" (in-app activation).
    Returns True when detected, False on timeout/error.
    """
    if not VOICE_AVAILABLE:
        return False
    from config import WAKE_WORD
    try:
        with _get_mic() as source:
            _recognizer.adjust_for_ambient_noise(source, duration=0.3)
            try:
                audio = _recognizer.listen(source, timeout=WAKE_WORD_TIMEOUT,
                                           phrase_time_limit=4)
            except sr.WaitTimeoutError:
                return False
        text = _transcribe(audio)
        if text and WAKE_WORD in text:
            print("[JARVIS] Wake word detected!")
            return True
    except Exception as e:
        print(f"[Voice] Wake word error: {e}")
    return False


def _transcribe(audio: sr.AudioData):
    """Transcribe audio using the configured STT engine."""
    if STT_ENGINE == "whisper":
        return _transcribe_whisper(audio)
    return _transcribe_google(audio)


def _transcribe_google(audio: sr.AudioData):
    """Transcribe using Google Web Speech API (free, needs internet)."""
    try:
        text = _recognizer.recognize_google(audio)
        print(f"[STT] You said: {text}")
        return text.lower()
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"[STT] Google error: {e}")
        return None


def _transcribe_whisper(audio: sr.AudioData):
    """Transcribe using local OpenAI Whisper model (offline)."""
    try:
        import whisper, numpy as np
        model = whisper.load_model(WHISPER_MODEL)
        wav   = audio.get_wav_data()
        arr   = np.frombuffer(wav, dtype=np.int16).astype(np.float32) / 32768.0
        result = model.transcribe(arr)
        text   = result["text"].strip().lower()
        print(f"[Whisper] You said: {text}")
        return text
    except Exception as e:
        print(f"[Whisper] Error: {e}")
        return None


def get_microphone_list() -> list:
    """Return list of available microphone names."""
    return sr.Microphone.list_microphone_names()


# ── Auto-start TTS worker on module load ─────────────────────────────────────
_ensure_tts_running()


if __name__ == "__main__":
    print("Testing TTS...")
    speak("Good evening, sir. All voice systems are operational.")
    import time; time.sleep(4)
    print("Testing STT...")
    result = listen()
    print(f"Heard: {result}" if result else "No speech detected.")
