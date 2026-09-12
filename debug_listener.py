"""
debug_listener.py — JARVIS Voice Debug Mode
============================================
Run this to see EXACTLY what JARVIS is hearing in real time.
Prints every word it detects, with energy levels.
Say "wakeup jarvis" to test the wake word.
Press Ctrl+C to stop.
"""

import sys
sys.path.insert(0, r'd:\JARVIS')

import pyaudio_shim  # noqa
import speech_recognition as sr
import time

WAKE_PHRASES = ["wakeup jarvis", "wake up jarvis", "start jarvis",
                "launch jarvis", "jarvis wake up"]

print("=" * 55)
print("  JARVIS — Voice Debug Mode")
print("  Mic: Microphone Array (Realtek) — index 1")
print("  Say 'wakeup jarvis' to test")
print("  Press Ctrl+C to stop")
print("=" * 55)
print()

r = sr.Recognizer()
r.energy_threshold = 200            # Low = sensitive, High = needs louder voice
r.dynamic_energy_threshold = True   # Auto-adjusts based on room noise
r.pause_threshold = 0.6

# Use mic index 1 (Realtek Array — best for wake word)
mic = sr.Microphone(device_index=1)

loop = 0
with mic as source:
    print("Calibrating for room noise (2 seconds)...")
    r.adjust_for_ambient_noise(source, duration=2)
    print(f"Energy threshold set to: {r.energy_threshold:.0f}")
    print(f"(If too many false triggers, raise it. If missing speech, lower it.)\n")
    print("Listening... speak naturally.\n")

    while True:
        try:
            loop += 1
            print(f"[Loop {loop}] Waiting for speech...", end="\r")
            audio = r.listen(source, timeout=3, phrase_time_limit=5)
            print(f"[Loop {loop}] Audio captured! Transcribing...    ")

            try:
                text = r.recognize_google(audio).lower().strip()
                print(f"  >>> HEARD: \"{text}\"")

                if any(p in text for p in WAKE_PHRASES):
                    print()
                    print("  ✅ WAKE WORD DETECTED! JARVIS would launch now.")
                    print()
                else:
                    print(f"  (not a wake phrase — keep saying 'wakeup jarvis')")

            except sr.UnknownValueError:
                print(f"  [Could not understand — too quiet or unclear]")
            except sr.RequestError as e:
                print(f"  [Google STT error: {e}]")

        except sr.WaitTimeoutError:
            pass  # Normal — just no speech in 3 sec window
        except KeyboardInterrupt:
            print("\n\nStopped. Goodbye, sir.")
            break
        except Exception as e:
            print(f"  [Error: {e}]")
            time.sleep(1)
