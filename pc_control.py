"""
pc_control.py — JARVIS PC Control Module
==========================================
Provides full Windows desktop control:
  - Launch applications by name
  - File search and opening
  - Screenshots with optional AI description
  - Volume and brightness control
  - Text typing via keyboard automation
  - Opening URLs in the browser
"""

import os
import subprocess
import webbrowser
import time
import glob
from pathlib import Path

import pyautogui
import psutil

# ── App name → executable mapping ─────────────────────────────────────────────
APP_MAP = {
    "chrome": "chrome.exe", "google chrome": "chrome.exe",
    "firefox": "firefox.exe", "edge": "msedge.exe",
    "microsoft edge": "msedge.exe", "notepad": "notepad.exe",
    "calculator": "calc.exe", "paint": "mspaint.exe",
    "word": "WINWORD.EXE", "excel": "EXCEL.EXE",
    "powerpoint": "POWERPNT.EXE", "vscode": "code.exe",
    "vs code": "code.exe", "visual studio code": "code.exe",
    "spotify": "Spotify.exe", "discord": "Discord.exe",
    "whatsapp": "WhatsApp.exe", "steam": "Steam.exe",
    "explorer": "explorer.exe", "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe", "cmd": "cmd.exe",
    "command prompt": "cmd.exe", "powershell": "powershell.exe",
    "terminal": "wt.exe", "windows terminal": "wt.exe",
    "vlc": "vlc.exe", "obs": "obs64.exe", "telegram": "Telegram.exe",
}


def open_app(app_name: str) -> str:
    """Open an application by its common name."""
    name_lower = app_name.lower().strip()
    exe = APP_MAP.get(name_lower)
    if exe:
        try:
            subprocess.Popen(exe, shell=True)
            return f"Opening {app_name}, sir."
        except Exception:
            pass
    # Try directly
    try:
        subprocess.Popen(app_name, shell=True)
        return f"Launching {app_name}, sir."
    except Exception:
        pass
    # Search common install paths
    for base in [r"C:\Program Files", r"C:\Program Files (x86)",
                 os.path.expandvars(r"%LOCALAPPDATA%")]:
        matches = glob.glob(os.path.join(base, "**", f"*{app_name}*.exe"), recursive=True)
        if matches:
            subprocess.Popen(matches[0])
            return f"Found and launching {matches[0]}, sir."
    return f"I couldn't locate '{app_name}' on your system, sir."


def open_url(url: str) -> str:
    """Open a URL in the default browser."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url} in your browser, sir."


def search_and_open_file(filename: str, search_root: str = None) -> str:
    """Search for a file by name pattern on the filesystem and open it."""
    print(f"[PC] Searching for '{filename}'...")
    # Quick search in user directories first
    for d in [Path.home() / "Desktop", Path.home() / "Documents",
              Path.home() / "Downloads", Path.home()]:
        try:
            matches = list(d.rglob(filename))
            if matches:
                os.startfile(str(matches[0]))
                return f"Found and opening: {matches[0]}, sir."
        except Exception:
            pass
    # Broader search
    root = search_root or str(Path.home())
    try:
        for root_dir, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in {"Windows", "$Recycle.Bin"}]
            for f in files:
                if filename.lower() in f.lower():
                    full_path = os.path.join(root_dir, f)
                    os.startfile(full_path)
                    return f"Found and opening: {full_path}, sir."
    except PermissionError:
        pass
    return f"I couldn't find '{filename}' on your system, sir."


def take_screenshot(save_path: str = None) -> str:
    """Capture the current screen and save it as PNG."""
    from config import SCREENSHOT_DIR
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    if save_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_path = str(SCREENSHOT_DIR / f"screenshot_{timestamp}.png")
    screenshot = pyautogui.screenshot()
    screenshot.save(save_path)
    return save_path


def screenshot_and_describe() -> str:
    """Take a screenshot and use AI vision (Gemini or Claude) to describe what's on screen."""
    path = take_screenshot()
    
    # 1. Try Google Gemini Vision if key available
    from config import GEMINI_API_KEY, GEMINI_MODEL, CLAUDE_API_KEY, CLAUDE_MODEL
    import base64
    import requests

    if GEMINI_API_KEY:
        try:
            with open(path, "rb") as f:
                img_data = base64.standard_b64encode(f.read()).decode("utf-8")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{
                    "parts": [
                        {"text": "Describe what is visible on this computer screen concisely. Mention open applications, active windows, and any notable content."},
                        {"inline_data": {"mime_type": "image/png", "data": img_data}}
                    ]
                }]
            }
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                desc = data["candidates"][0]["content"]["parts"][0]["text"]
                return f"Screenshot saved to `{path}`\n\n🖥️ **Screen Analysis:**\n{desc}"
        except Exception as e:
            print(f"[Vision Gemini Error] {e}")

    # 2. Try Anthropic Claude Vision if key available
    if CLAUDE_API_KEY:
        try:
            import anthropic
            with open(path, "rb") as f:
                img_data = base64.standard_b64encode(f.read()).decode("utf-8")
            client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_data}},
                    {"type": "text", "text": "Describe what's on this screen concisely. Mention open apps, windows, and notable content."}
                ]}]
            )
            return f"Screenshot saved to `{path}`\n\n🖥️ **Screen Analysis:**\n{response.content[0].text}"
        except Exception as e:
            print(f"[Vision Claude Error] {e}")

    return f"Screenshot saved to `{path}`, sir. (To enable AI screen analysis, add GEMINI_API_KEY or CLAUDE_API_KEY in .env)"


def control_volume(action: str, level: int = None) -> str:
    """Control system volume. action: up/down/mute/unmute/set. level: 0-100."""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        vol = cast(interface, POINTER(IAudioEndpointVolume))
        if action == "mute":
            vol.SetMute(1, None); return "Muted, sir."
        elif action == "unmute":
            vol.SetMute(0, None); return "Unmuted, sir."
        elif action == "up":
            cur = vol.GetMasterVolumeLevelScalar()
            vol.SetMasterVolumeLevelScalar(min(1.0, cur + 0.1), None)
            return f"Volume up to {int(min(1.0, cur+0.1)*100)}%, sir."
        elif action == "down":
            cur = vol.GetMasterVolumeLevelScalar()
            vol.SetMasterVolumeLevelScalar(max(0.0, cur - 0.1), None)
            return f"Volume down to {int(max(0.0, cur-0.1)*100)}%, sir."
        elif action == "set" and level is not None:
            vol.SetMasterVolumeLevelScalar(level / 100.0, None)
            return f"Volume set to {level}%, sir."
    except Exception as e:
        # PowerShell fallback
        key_map = {"mute": 173, "up": 175, "down": 174}
        key = key_map.get(action)
        if key:
            subprocess.run(["powershell", "-c",
                f"$o=New-Object -ComObject WScript.Shell; $o.SendKeys([char]{key})"],
                capture_output=True)
            return f"Volume {action} executed, sir."
    return "Volume command processed, sir."


def set_brightness(level: int) -> str:
    """Set screen brightness 0-100 via WMI."""
    level = max(0, min(100, level))
    try:
        script = (f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                  f".WmiSetBrightness(1, {level})")
        subprocess.run(["powershell", "-Command", script], capture_output=True)
        return f"Brightness set to {level}%, sir."
    except Exception as e:
        return f"Could not adjust brightness: {e}"


def type_text(text: str, interval: float = 0.03) -> str:
    """Type text at the current cursor position using keyboard automation."""
    time.sleep(0.5)
    pyautogui.typewrite(text, interval=interval)
    return "Typed the requested text, sir."


def get_running_apps() -> list:
    """Return list of currently running application process names."""
    return list({p.name() for p in psutil.process_iter(["name"]) if p.info["name"]})


def kill_app(app_name: str) -> str:
    """Terminate a running application by name."""
    killed = []
    for proc in psutil.process_iter(["name", "pid"]):
        if app_name.lower() in proc.info["name"].lower():
            try:
                proc.kill(); killed.append(proc.info["name"])
            except Exception:
                pass
    if killed:
        return f"Terminated: {', '.join(killed)}, sir."
    return f"No process matching '{app_name}' was found, sir."
