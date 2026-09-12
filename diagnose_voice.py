import sys
sys.path.insert(0, r'd:\JARVIS')
import pyaudio_shim  # noqa
import speech_recognition as sr

print("=== JARVIS Voice Diagnostic ===\n")

# 1. List microphones
print("1. Available microphones:")
try:
    mics = sr.Microphone.list_microphone_names()
    if not mics:
        print("   No microphones found!")
    for i, m in enumerate(mics):
        print(f"   [{i}] {m}")
except Exception as e:
    print(f"   ERROR listing mics: {e}")

print()

# 2. Capture test
print("2. Microphone capture test — speak anything in the next 5 seconds...")
r = sr.Recognizer()
r.energy_threshold = 200
r.dynamic_energy_threshold = True

try:
    with sr.Microphone() as source:
        print("   Adjusting for ambient noise (1 sec)...")
        r.adjust_for_ambient_noise(source, duration=1)
        print(f"   Energy threshold: {r.energy_threshold:.0f}")
        print("   >>> SPEAK NOW — you have 5 seconds <<<")
        audio = r.listen(source, timeout=5, phrase_time_limit=5)
    print("   Audio captured! Sending to Google STT...")
    try:
        text = r.recognize_google(audio)
        print(f"   SUCCESS - Heard: \"{text}\"")
    except sr.UnknownValueError:
        print("   FAIL - Could not understand (too quiet or unclear?)")
    except sr.RequestError as e:
        print(f"   FAIL - Google STT error: {e}")
        print("   Check internet connection.")
except sr.WaitTimeoutError:
    print("   TIMEOUT - No speech detected in 5 seconds.")
    print("   FIX: Check mic in Windows Sound Settings > Recording")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n=== Diagnostic complete ===")
