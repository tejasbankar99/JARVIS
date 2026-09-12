"""
main.py — JARVIS Entry Point
==============================
Bootstraps all JARVIS modules and launches the HUD interface.
This is the only file you need to run: python main.py

Usage:
  python main.py          → Full GUI + voice mode
  python main.py --cli    → Text-only CLI mode (no GUI)
  python main.py --voice  → GUI + voice enabled on startup
"""

import sys
import threading
import datetime

# Ensure clean UTF-8 console output across Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── JARVIS Core Class ──────────────────────────────────────────────────────────

class JARVIS:
    """
    Central JARVIS orchestrator.
    Routes commands to the appropriate module and manages state.
    """

    def __init__(self):
        self.voice_enabled = True   # Voice ON by default — JARVIS always speaks
        self._last_code_response = ""

    def process_command(self, user_input: str) -> str:
        """
        Main command dispatcher.
        Classifies input and routes to the correct module.

        Args:
            user_input: Raw text from user (typed or transcribed)

        Returns:
            JARVIS response string
        """
        if not user_input or not user_input.strip():
            return "I didn't catch that, sir."

        text = user_input.lower().strip()

        # ── Privacy: log activity + update inactivity timer ────────────────
        try:
            from privacy import log_activity, update_activity, is_locked
            update_activity()
            if is_locked():
                return "🔒 JARVIS is locked, sir. Say 'unlock JARVIS' followed by your PIN."
            log_activity("COMMAND", user_input[:80])
        except Exception:
            pass

        # ── Memory commands ────────────────────────────────────────────────
        if any(p in text for p in ["remember that", "remember:", "note that", "store this"]):
            return self._handle_remember(user_input)

        if any(p in text for p in ["what did i tell you", "recall", "do you remember",
                                    "what do you know about", "look up my note"]):
            return self._handle_recall(user_input)

        if "show memory" in text or "show all memory" in text or "what's in memory" in text:
            from memory import get_all_memory
            return get_all_memory()

        if "clear memory" in text or "wipe memory" in text:
            from memory import clear_memory
            return clear_memory()

        # ── Security & Privacy commands ──────────────────────────────
        if any(p in text for p in ["unlock jarvis", "unlock with pin", "enter pin"]):
            import re
            pin_match = re.search(r'\b(\d{4,8})\b', text)
            if pin_match:
                from privacy import unlock_jarvis
                return unlock_jarvis(pin_match.group(1))
            return "Please say your PIN number after 'unlock JARVIS', sir."

        if any(p in text for p in ["lock jarvis", "lock yourself", "secure jarvis"]):
            from privacy import lock_jarvis
            return lock_jarvis()

        if any(p in text for p in ["set pin", "set master pin", "change pin", "create pin"]):
            import re
            pin_match = re.search(r'\b(\d{4,8})\b', text)
            if pin_match:
                from privacy import set_master_pin
                return set_master_pin(pin_match.group(1))
            return "Please include your 4-8 digit PIN in the command, sir."

        if any(p in text for p in ["private mode", "go private", "incognito mode",
                                    "enable privacy"]):
            from privacy import enable_private_mode
            return enable_private_mode()

        if any(p in text for p in ["disable private", "exit private", "stop private mode"]):
            from privacy import disable_private_mode
            return disable_private_mode()

        if any(p in text for p in ["security status", "privacy status", "show security",
                                    "am i locked"]):
            from privacy import get_security_status
            return get_security_status()

        if any(p in text for p in ["activity log", "show activity", "what have you done",
                                    "recent activity", "command history"]):
            from privacy import get_activity_log
            return get_activity_log()

        if "clear activity log" in text or "clear log" in text:
            from privacy import clear_activity_log
            return clear_activity_log()

        if any(p in text for p in ["auto lock", "lock after", "auto-lock"]):
            import re
            mins_match = re.search(r'(\d+)\s*min', text)
            if mins_match:
                from privacy import start_inactivity_monitor
                return start_inactivity_monitor(int(mins_match.group(1)))
            return "Please specify minutes, sir. E.g. 'auto lock after 10 minutes'."

        # ── Browser & Web Automation ──────────────────────────────────
        if any(p in text for p in ["youtube", "play ", "watch ", "netflix", "spotify",
                                    "gmail", "google maps", "whatsapp web", "chatgpt",
                                    "search on", "google search", "close tab",
                                    "new tab", "scroll down", "scroll up"]):
            from browser_control import handle_browser_command
            result = handle_browser_command(user_input, text)
            if result:
                return result

        # ── PC Control commands ────────────────────────────────────────────
        if any(p in text for p in ["open ", "launch ", "start "]):
            return self._handle_open(user_input, text)

        if "take a screenshot" in text or "screenshot" in text:
            if "describe" in text or "what's on" in text or "what is on" in text:
                from pc_control import screenshot_and_describe
                return screenshot_and_describe()
            else:
                from pc_control import take_screenshot
                path = take_screenshot()
                return f"Screenshot saved to: `{path}`, sir."

        if "volume up" in text or "turn up volume" in text or "increase volume" in text:
            from pc_control import control_volume
            return control_volume("up")

        if "volume down" in text or "turn down volume" in text or "decrease volume" in text:
            from pc_control import control_volume
            return control_volume("down")

        if "unmute" in text:
            from pc_control import control_volume
            return control_volume("unmute")

        if "mute" in text:
            from pc_control import control_volume
            return control_volume("mute")

        if "brightness" in text:
            return self._handle_brightness(user_input, text)

        if "type " in text:
            from pc_control import type_text
            typed = user_input.split("type ", 1)[-1].strip()
            return type_text(typed)

        if any(p in text for p in ["running apps", "what apps are running", "show processes"]):
            from pc_control import get_running_apps
            apps = get_running_apps()[:20]
            return "Running processes, sir:\n• " + "\n• ".join(apps)

        if any(p in text for p in ["kill ", "close ", "terminate "]):
            return self._handle_kill(user_input, text)

        # ── Power management ───────────────────────────────────────────────
        if any(p in text for p in ["put to sleep", "sleep mode", "go to sleep", "standby"]):
            import subprocess
            subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return "Putting the system to sleep, sir."

        if "hibernate" in text:
            import subprocess
            subprocess.run(["shutdown", "/h"], shell=True)
            return "Hibernating now, sir."

        if any(p in text for p in ["restart the computer", "reboot", "restart system"]):
            import subprocess
            subprocess.run(["shutdown", "/r", "/t", "10"], shell=True)
            return "Restarting in 10 seconds, sir. Save your work."

        if any(p in text for p in ["shut down the computer", "shutdown the pc", "power off",
                                    "turn off the computer"]):
            import subprocess
            subprocess.run(["shutdown", "/s", "/t", "10"], shell=True)
            return "Shutting down in 10 seconds, sir."

        if any(p in text for p in ["lock the screen", "lock screen", "lock computer", "lock pc"]):
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "Screen locked, sir."

        # ── System monitoring ──────────────────────────────────────────────
        if any(p in text for p in ["system status", "system report", "how is the system",
                                    "pc status", "computer status", "diagnostics",
                                    "system health"]):
            from system_monitor import get_full_status
            return get_full_status()

        if any(p in text for p in ["cpu usage", "processor usage", "how is the cpu",
                                    "cpu load", "cpu percent"]):
            from system_monitor import get_cpu
            return get_cpu()

        if any(p in text for p in ["ram usage", "memory usage", "how much memory",
                                    "how much ram", "ram status"]):
            from system_monitor import get_ram
            return get_ram()

        if any(p in text for p in ["battery", "power level", "battery charge",
                                    "how much battery"]):
            from system_monitor import get_battery
            return get_battery()

        if any(p in text for p in ["network speed", "internet speed", "bandwidth",
                                    "download speed", "upload speed"]):
            from system_monitor import get_network
            return get_network()

        if any(p in text for p in ["disk space", "storage space", "drive space",
                                    "how much space", "free space"]):
            from system_monitor import get_disk
            return get_disk()

        if any(p in text for p in ["how long running", "uptime", "how long has the computer",
                                    "when did i boot", "system uptime"]):
            from system_monitor import get_uptime
            return get_uptime()

        # ── Weather ────────────────────────────────────────────────────────
        if any(p in text for p in ["weather", "temperature outside", "what's the temp",
                                    "is it raining", "will it rain", "forecast",
                                    "how hot", "how cold"]):
            from weather import get_weather
            import re
            loc_match = re.search(
                r'(?:weather\s+in|weather\s+for|in\s+city|in)\s+([a-zA-Z\s]+?)(?:\?|$|\s+today)',
                text
            )
            location = loc_match.group(1).strip() if loc_match else ""
            return get_weather(location)

        # ── Timers & Reminders ─────────────────────────────────────────────
        if any(p in text for p in ["set a timer", "set timer", "timer for", "remind me",
                                    "set a reminder", "alarm for", "wake me in",
                                    "alert me in", "notify me in"]):
            from scheduler import handle_timer_command
            return handle_timer_command(user_input)

        if any(p in text for p in ["list timers", "show timers", "active timers",
                                    "what timers do i have"]):
            from scheduler import list_timers
            return list_timers()

        if any(p in text for p in ["cancel timer", "stop timer", "cancel all timers",
                                    "delete timer"]):
            from scheduler import cancel_all_timers
            return cancel_all_timers()

        # ── Date & Time ────────────────────────────────────────────────────
        if any(p in text for p in ["what time is it", "current time", "what's the time",
                                    "tell me the time"]):
            return f"It's {datetime.datetime.now().strftime('%H:%M:%S')}, sir."

        if any(p in text for p in ["what's today", "what date is it", "today's date",
                                    "what day is it", "current date"]):
            return f"Today is {datetime.datetime.now().strftime('%A, %d %B %Y')}, sir."

        # ── Clipboard ─────────────────────────────────────────────────────
        if any(p in text for p in ["what's in my clipboard", "read my clipboard",
                                    "what did i copy", "show clipboard"]):
            try:
                import subprocess
                result = subprocess.run(["powershell", "-c", "Get-Clipboard"],
                                        capture_output=True, text=True)
                content = result.stdout.strip()
                return (f"Your clipboard contains:\n\n{content[:2000]}"
                        if content else "Your clipboard is empty, sir.")
            except Exception as e:
                return f"Couldn't access clipboard: {e}"

        # ── Music & Media controls ─────────────────────────────────────────
        if any(p in text for p in ["play music", "next song", "previous song", "next track",
                                    "pause music", "stop music", "prev track",
                                    "skip song", "play pause"]):
            return self._handle_media(text)

        # ── News ───────────────────────────────────────────────────────────
        if any(p in text for p in ["latest news", "what's in the news", "top news",
                                    "news headlines", "today's news", "current events"]):
            from research import search_web
            return search_web("today's top news headlines")

        # ── Research commands ──────────────────────────────────────────────
        if any(p in text for p in ["search for", "search the web", "google ", "look up",
                                    "find information", "what is ", "who is ", "when did"]):
            return self._handle_search(user_input, text)

        if any(p in text for p in ["read this url", "summarize this url", "open url",
                                    "read the page", "summarize the page"]):
            return self._handle_read_url(user_input)

        if any(p in text for p in ["read this file", "summarize this pdf", "summarize the file",
                                    "read the pdf"]):
            return self._handle_read_file(user_input)

        # ── Code commands ──────────────────────────────────────────────────
        if any(p in text for p in ["write code", "write a ", "generate code",
                                    "create a script", "build a function", "code that"]):
            return self._handle_write_code(user_input, text)

        if any(p in text for p in ["debug this", "fix this code", "there's an error",
                                    "debug the", "what's wrong with this code"]):
            return self._handle_debug(user_input)

        if any(p in text for p in ["explain this code", "explain the code",
                                    "what does this code do"]):
            return self._handle_explain(user_input)

        if any(p in text for p in ["optimize this", "optimize the code",
                                    "improve this code", "make this faster"]):
            from code_assistant import optimize_code
            import re
            code_match = re.search(r'```[\w]*\n(.*?)```', user_input, re.DOTALL)
            code = code_match.group(1) if code_match else user_input
            return optimize_code(code)

        if any(p in text for p in ["write tests for", "generate tests", "unit tests for",
                                    "test this code"]):
            from code_assistant import generate_tests
            import re
            code_match = re.search(r'```[\w]*\n(.*?)```', user_input, re.DOTALL)
            code = code_match.group(1) if code_match else user_input
            return generate_tests(code)

        if any(p in text for p in ["save that to", "save the code to", "save it to"]):
            return self._handle_save_code(user_input, text)

        # ── Help & capabilities ────────────────────────────────────────────
        if any(p in text for p in ["what can you do", "help me", "capabilities",
                                    "list commands", "what do you know", "list your abilities",
                                    "show commands"]):
            return self._handle_help()

        # ── Fallback: AI general chat ─────────────────────────────────────
        from brain import ask
        response = ask(user_input)
        self._last_code_response = response
        return response

    # ── Command Handlers ───────────────────────────────────────────────────────

    def _handle_open(self, original: str, text: str) -> str:
        from pc_control import open_app, open_url, search_and_open_file

        # Check if it's a URL
        import re
        url_match = re.search(r'(https?://\S+|www\.\S+)', original)
        if url_match:
            return open_url(url_match.group(1))

        # Extract app name after "open/launch/start"
        for prefix in ["open ", "launch ", "start "]:
            if prefix in text:
                app = text.split(prefix, 1)[1].strip()
                # Could be a file
                if "." in app and "/" not in app and "\\" not in app:
                    return search_and_open_file(app)
                return open_app(app)

        return "What would you like me to open, sir?"

    def _handle_remember(self, text: str) -> str:
        from memory import remember, remember_note
        import re

        # Pattern: "remember that X is Y" or "remember: key = value"
        match = re.search(r'remember\s+that\s+(.+?)\s+is\s+(.+)', text, re.IGNORECASE)
        if match:
            return remember(match.group(1).strip(), match.group(2).strip())

        match = re.search(r'remember[:\s]+(.+)', text, re.IGNORECASE)
        if match:
            return remember_note(match.group(1).strip())

        return remember_note(text)

    def _handle_recall(self, text: str) -> str:
        from memory import recall
        import re

        # Extract the query topic
        for pattern in [
            r'recall\s+(.+)',
            r'what did i tell you about\s+(.+)',
            r'do you remember\s+(.+)',
            r'what do you know about\s+(.+)',
        ]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return recall(match.group(1).strip())

        return recall(text)

    def _handle_search(self, original: str, text: str) -> str:
        from research import search_web, quick_search

        # Extract query
        for prefix in ["search for ", "search the web for ", "google ", "look up "]:
            if prefix in text:
                query = original.split(prefix, 1)[-1].strip()
                return search_web(query)

        # Clean question-style queries
        query = original.strip().rstrip("?")
        return quick_search(query)

    def _handle_read_url(self, text: str) -> str:
        from research import read_and_summarize_url
        import re
        url_match = re.search(r'(https?://\S+)', text)
        if url_match:
            return read_and_summarize_url(url_match.group(1))
        return "Please provide a URL, sir."

    def _handle_read_file(self, text: str) -> str:
        from research import read_and_summarize_file
        import re
        # Look for a file path pattern
        path_match = re.search(r'([A-Za-z]:\\[\w\\/.\ \-]+|/[\w/.\ \-]+)', text)
        if path_match:
            return read_and_summarize_file(path_match.group(1))
        return "Please provide a file path, sir."

    def _handle_write_code(self, original: str, text: str) -> str:
        from code_assistant import write_code
        import re

        # Detect language
        languages = ["python", "javascript", "typescript", "java", "cpp", "c++",
                     "rust", "go", "html", "css", "sql", "bash", "powershell",
                     "kotlin", "swift", "r", "matlab"]
        detected_lang = "python"
        for lang in languages:
            if lang in text:
                detected_lang = lang
                break

        # Check if save path specified
        save_match = re.search(r'(?:save|write)\s+(?:it\s+)?to\s+([\w./\\:]+)', text)
        save_path = save_match.group(1) if save_match else None

        response = write_code(original, language=detected_lang, save_to=save_path)
        self._last_code_response = response
        return response

    def _handle_debug(self, text: str) -> str:
        from code_assistant import debug_code
        import re

        # Extract code block from input
        code_match = re.search(r'```[\w]*\n(.*?)```', text, re.DOTALL)
        if code_match:
            code = code_match.group(1)
        else:
            # Remove the debug instruction part
            for prefix in ["debug this:", "debug this code:", "fix this code:"]:
                if prefix in text.lower():
                    code = text[text.lower().find(prefix) + len(prefix):].strip()
                    break
            else:
                code = text

        return debug_code(code)

    def _handle_explain(self, text: str) -> str:
        from code_assistant import explain_code
        import re

        code_match = re.search(r'```[\w]*\n(.*?)```', text, re.DOTALL)
        code = code_match.group(1) if code_match else text
        detail = "detailed" if "in detail" in text else "concise"
        return explain_code(code, detail_level=detail)

    def _handle_save_code(self, original: str, text: str) -> str:
        from code_assistant import save_last_code
        import re

        path_match = re.search(r'save\s+(?:that|it|the\s+code)\s+to\s+([\w./\\:]+)', text)
        if path_match:
            path = path_match.group(1)
            if self._last_code_response:
                return save_last_code(self._last_code_response, path)
            return "I don't have any recent code to save, sir."
        return "Where would you like me to save the code, sir?"

    def _handle_brightness(self, original: str, text: str) -> str:
        from pc_control import set_brightness
        import re
        level_match = re.search(r'(\d+)', text)
        if level_match:
            return set_brightness(int(level_match.group(1)))
        if "up" in text or "increase" in text:
            return set_brightness(80)
        if "down" in text or "decrease" in text:
            return set_brightness(40)
        return "Please specify a brightness level (0-100), sir."

    def _handle_kill(self, original: str, text: str) -> str:
        from pc_control import kill_app
        for prefix in ["kill ", "close ", "terminate "]:
            if prefix in text:
                app = text.split(prefix, 1)[1].strip()
                return kill_app(app)
        return "Which application should I terminate, sir?"

    def _handle_media(self, text: str) -> str:
        """Control music/media via keyboard media keys."""
        import pyautogui
        if any(p in text for p in ["next song", "next track", "skip song"]):
            pyautogui.press("nexttrack")
            return "Skipping to the next track, sir."
        if any(p in text for p in ["previous song", "prev track", "previous track"]):
            pyautogui.press("prevtrack")
            return "Going back to the previous track, sir."
        if any(p in text for p in ["pause music", "stop music", "play pause", "pause"]):
            pyautogui.press("playpause")
            return "Toggling play/pause, sir."
        if "play music" in text:
            pyautogui.press("playpause")
            return "Playing music, sir."
        return "Media command received, sir."

    def _handle_help(self) -> str:
        """Return a formatted list of JARVIS capabilities."""
        return """🤖 **JARVIS Capabilities — Command Reference**

**🖥️ PC Control**
• "Open Chrome / Spotify / VS Code"
• "Take a screenshot" / "Describe what's on screen"
• "Volume up/down/mute" / "Brightness 80"
• "Kill Chrome" / "Show running apps"
• "Lock screen" / "Sleep" / "Restart" / "Shut down"
• "Type [text]"

**📊 System Monitoring**
• "System status" / "CPU usage" / "RAM usage"
• "Battery level" / "Disk space" / "Network speed"
• "How long has the system been running?"

**🌤️ Weather**
• "What's the weather?" / "Weather in Mumbai"
• "Will it rain today?" / "3-day forecast"

**⏱️ Timers & Reminders**
• "Set a timer for 10 minutes"
• "Remind me in 30 minutes to call mom"
• "List timers" / "Cancel all timers"

**🔍 Research & Web**
• "Search for quantum computing"
• "What is the speed of light?"
• "Latest news headlines"
• "Summarize this URL: [url]"
• "Read the PDF at C:\\docs\\file.pdf"

**💻 Code Assistant**
• "Write a Python web scraper"
• "Debug this code: [paste code]"
• "Explain this code: [paste code]"
• "Optimize this code"
• "Generate tests for: [paste code]"
• "Save that to filename.py"

**🧠 Memory**
• "Remember that my API key is xyz"
• "What did I tell you about my project?"
• "Show all memory" / "Clear memory"

**📋 Clipboard**
• "What's in my clipboard?"

**🎵 Media**
• "Next song" / "Previous song" / "Pause music"

**💬 General AI Chat**
• Ask me anything — I'll reason through it."""

    def speak(self, text: str):
        """Speak a response if voice is enabled."""
        if not self.voice_enabled:
            return
        try:
            from voice import speak
            speak(text)
        except Exception as e:
            print(f"[Voice Error] {e}")


# ── CLI Mode ───────────────────────────────────────────────────────────────────

def run_cli(jarvis: JARVIS):
    """Simple text-based CLI loop for testing without GUI."""
    hour = datetime.datetime.now().hour
    greeting = "morning" if hour < 12 else ("afternoon" if hour < 17 else "evening")
    print(f"\n  JARVIS: Good {greeting}, sir. All systems online.")
    print("  (Type 'exit' to shut down)\n")

    while True:
        try:
            user_input = input("  You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "shutdown", "bye"}:
                print("  JARVIS: Shutting down. Good day, sir.")
                break
            response = jarvis.process_command(user_input)
            print(f"\n  JARVIS: {response}\n")
        except KeyboardInterrupt:
            print("\n  JARVIS: Emergency shutdown initiated. Goodbye, sir.")
            break


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    # Validate environment according to selected AI provider
    from config import AI_PROVIDER, GROQ_API_KEY, GEMINI_API_KEY, CLAUDE_API_KEY
    from brain import get_active_provider

    print(f"[JARVIS] Active AI Brain: {get_active_provider()}")

    if AI_PROVIDER == "groq" and not GROQ_API_KEY:
        print("[WARNING] GROQ_API_KEY not set in .env. Get a free key at https://console.groq.com/")
    elif AI_PROVIDER == "gemini" and not GEMINI_API_KEY:
        print("[WARNING] GEMINI_API_KEY not set in .env. Get a free key at https://aistudio.google.com/app/apikey")
    elif AI_PROVIDER == "claude" and not CLAUDE_API_KEY:
        print("[WARNING] CLAUDE_API_KEY not set in .env.")

    jarvis = JARVIS()

    # Parse args
    if "--cli" in sys.argv:
        jarvis.voice_enabled = False   # CLI mode: text only, no TTS
        run_cli(jarvis)
    else:
        # GUI mode — voice always ON
        jarvis.voice_enabled = True
        print("[JARVIS] Launching HUD interface with voice enabled...")
        from ui import launch_ui
        launch_ui(jarvis)


if __name__ == "__main__":
    main()
