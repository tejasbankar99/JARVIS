"""
listener.py — JARVIS Always-On Voice Startup Listener
======================================================
Runs silently in the Windows system tray.
Listens for the phrase "wakeup jarvis" (or custom STARTUP_WAKE_WORD).
When heard → launches the full JARVIS GUI automatically.

How to use:
  python listener.py          ← runs in background with tray icon
  python listener.py --startup ← also adds itself to Windows startup

Tray icon menu:
  - Status indicator
  - Launch JARVIS manually
  - Enable / Disable listening
  - Exit
"""

import sys
import os
import time
import threading
import subprocess
import winreg
from pathlib import Path

# Ensure clean UTF-8 console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── PyAudio shim must come first ─────────────────────────────────────────────
import pyaudio_shim  # noqa

import speech_recognition as sr
import pystray
from PIL import Image, ImageDraw, ImageFont

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
PYTHON_EXE  = BASE_DIR / ".venv" / "Scripts" / "python.exe"
MAIN_SCRIPT = BASE_DIR / "main.py"

# ── Wake phrase (what you say to start JARVIS) ────────────────────────────────
STARTUP_WAKE_WORD = "wakeup jarvis"          # Say this to launch JARVIS
ALT_WAKE_WORDS    = ["wake up jarvis", "start jarvis", "launch jarvis", "jarvis wake up"]

# ── State ─────────────────────────────────────────────────────────────────────
_listening   = True      # Can be toggled from tray menu
_jarvis_open = False     # Track if JARVIS is already running
_tray_icon   = None


# ── Tray Icon Drawing ─────────────────────────────────────────────────────────

def _make_tray_image(active: bool = True) -> Image.Image:
    """
    Draw the system tray icon.
    Glowing cyan arc reactor when active, grey when paused.
    """
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer circle
    outer_color = (0, 200, 255, 255) if active else (80, 80, 80, 200)
    draw.ellipse([2, 2, size - 2, size - 2], outline=outer_color, width=3)

    # Inner ring
    inner_color = (0, 150, 220, 200) if active else (60, 60, 60, 150)
    draw.ellipse([10, 10, size - 10, size - 10], outline=inner_color, width=2)

    # Core glow
    core_color = (0, 220, 255, 230) if active else (50, 50, 50, 180)
    draw.ellipse([20, 20, size - 20, size - 20], fill=core_color)

    # Letter J in center
    j_color = (0, 0, 30, 255) if active else (20, 20, 20, 255)
    draw.text((26, 19), "J", fill=j_color)

    return img


# ── JARVIS Launcher ───────────────────────────────────────────────────────────

def _is_jarvis_running() -> bool:
    """Check if a JARVIS main.py process is already running."""
    import psutil
    for proc in psutil.process_iter(["cmdline"]):
        try:
            cmdline = " ".join(proc.info["cmdline"] or []).lower()
            if "main.py" in cmdline and "jarvis" in cmdline:
                return True
        except Exception:
            pass
    return False


def launch_jarvis():
    """Spawn the JARVIS GUI as an independent process."""
    global _jarvis_open

    if _is_jarvis_running():
        print("[Listener] JARVIS is already running, sir.")
        _play_beep()
        return

    print("[Listener] Wake word detected — launching JARVIS!")
    _play_beep()

    # Update tray tooltip
    if _tray_icon:
        _tray_icon.title = "JARVIS — Launching..."

    # Launch JARVIS as a separate process (detached)
    subprocess.Popen(
        [str(PYTHON_EXE), str(MAIN_SCRIPT)],
        cwd=str(BASE_DIR),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    _jarvis_open = True

    # Reset tray after a moment
    time.sleep(2)
    if _tray_icon:
        _tray_icon.title = "JARVIS Listener — Active"


def _play_beep():
    """Play a short confirmation beep using Windows API."""
    try:
        import winsound
        winsound.Beep(880, 150)
        time.sleep(0.05)
        winsound.Beep(1100, 200)
    except Exception:
        pass


# ── Voice Listener Loop ───────────────────────────────────────────────────────

def _listen_loop():
    """
    Background thread: continuously listens for the startup wake word.
    Uses ambient noise adjustment for accuracy in noisy environments.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold        = 300   # Start higher — prevents early mis-calibration
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold         = 0.6

    print(f"[Listener] Listening for: \"{STARTUP_WAKE_WORD}\"")
    print(f"[Listener] Alternatives : {ALT_WAKE_WORDS}")

    # Use Realtek Microphone Array (index 1) — better for wake word detection
    # Fall back to default if not available
    try:
        mic = sr.Microphone(device_index=1)  # Realtek Array
        # Quick test open
        with mic as _:
            pass
    except Exception:
        try:
            mic = sr.Microphone()  # system default
        except Exception as e:
            print(f"[Listener] Microphone not available: {e}")
            return

    # Apply minimum floor AFTER ambient calibration — prevents threshold dropping to ~30
    # which causes real speech to be ignored.
    recognizer.energy_threshold = max(recognizer.energy_threshold, 150)
    loop_count = 0

    while True:
        if not _listening:
            time.sleep(0.5)
            continue

        loop_count += 1
        try:
            with mic as source:
                # Recalibrate every 10 loops to adapt to room noise
                if loop_count % 10 == 0:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                try:
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                except sr.WaitTimeoutError:
                    continue

            # Transcribe
            try:
                text = recognizer.recognize_google(audio).lower().strip()
                print(f"[Listener] Heard: {text}")

                # Check for any wake phrase
                all_phrases = [STARTUP_WAKE_WORD] + ALT_WAKE_WORDS
                if any(phrase in text for phrase in all_phrases):
                    threading.Thread(target=launch_jarvis, daemon=True).start()

            except sr.UnknownValueError:
                pass  # Silence or unintelligible — keep going
            except sr.RequestError as e:
                print(f"[Listener] STT error: {e}")
                time.sleep(2)

        except Exception as e:
            print(f"[Listener] Loop error: {e}")
            time.sleep(1)


# ── System Tray Setup ─────────────────────────────────────────────────────────

def _build_tray_menu():
    """Build the right-click tray menu."""
    return pystray.Menu(
        pystray.MenuItem(
            "◉  JARVIS Listener — Active",
            lambda: None,
            enabled=False
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "▶  Launch JARVIS Now",
            lambda icon, item: threading.Thread(target=launch_jarvis, daemon=True).start()
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "🎤  Toggle Listening",
            _toggle_listening,
            checked=lambda item: _listening
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "⚙  Add to Windows Startup",
            _add_to_startup
        ),
        pystray.MenuItem(
            "✕  Exit Listener",
            _exit_listener
        ),
    )


def _toggle_listening(icon, item):
    """Pause or resume voice listening."""
    global _listening
    _listening = not _listening
    status = "Active" if _listening else "Paused"
    icon.icon = _make_tray_image(active=_listening)
    icon.title = f"JARVIS Listener — {status}"
    print(f"[Listener] Listening {'enabled' if _listening else 'paused'}.")


def _exit_listener(icon, item):
    """Shut down the tray listener."""
    print("[Listener] Shutting down.")
    icon.stop()
    os._exit(0)


# ── Windows Startup Registration ──────────────────────────────────────────────

def _add_to_startup(icon=None, item=None):
    """
    Add JARVIS listener to Windows startup via Registry.
    It will auto-start next time Windows boots.
    """
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "JARVIS_Listener"
    # Build the command: pythonw (no console window) listener.py
    pythonw = str(PYTHON_EXE).replace("python.exe", "pythonw.exe")
    command  = f'"{pythonw}" "{MAIN_SCRIPT.parent / "listener.py"}"'

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        print(f"[Listener] Added to Windows startup: {command}")
        # Confirmation beep
        try:
            import winsound
            winsound.Beep(660, 100)
            winsound.Beep(880, 100)
            winsound.Beep(1100, 200)
        except Exception:
            pass
    except Exception as e:
        print(f"[Listener] Could not add to startup: {e}")


def _remove_from_startup():
    """Remove JARVIS listener from Windows startup."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "JARVIS_Listener")
        winreg.CloseKey(key)
        print("[Listener] Removed from Windows startup.")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[Listener] Startup removal error: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    global _tray_icon

    print("=" * 50)
    print("  J.A.R.V.I.S — Voice Startup Listener")
    print(f"  Say: \"{STARTUP_WAKE_WORD}\" to launch JARVIS")
    print("  Tray icon in system taskbar → right-click for menu")
    print("=" * 50)

    # Handle --startup flag (add to registry and exit)
    if "--startup" in sys.argv:
        _add_to_startup()
        print("[Listener] Registered in Windows startup. Done.")

    # Start the voice listening thread
    listener_thread = threading.Thread(target=_listen_loop, daemon=True)
    listener_thread.start()

    # Build and run the system tray icon (blocks main thread)
    icon_image = _make_tray_image(active=True)
    _tray_icon = pystray.Icon(
        name="jarvis_listener",
        icon=icon_image,
        title="JARVIS Listener — Active",
        menu=_build_tray_menu()
    )
    _tray_icon.run()


if __name__ == "__main__":
    main()
