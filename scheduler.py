"""
scheduler.py — JARVIS Timer, Reminder & Alarm System
======================================================
Handles:
  - One-shot timers: "Set a timer for 10 minutes"
  - Named reminders: "Remind me in 30 minutes to call mom"
  - Repeating alarms (future)
  - Proactive battery alerts
"""

import re
import threading
import time
from datetime import datetime
from typing import Callable


# ── Active timers store ───────────────────────────────────────────────────────
_timers: list[dict] = []
_timers_lock = threading.Lock()
_notify_callback: Callable[[str], None] | None = None   # Set by UI to show notifications


def set_notification_callback(cb: Callable[[str], None]):
    """Register a function to call when a reminder fires (e.g. UI popup + TTS)."""
    global _notify_callback
    _notify_callback = cb


def _fire(message: str, speak: bool = True):
    """Deliver a notification via the registered callback."""
    print(f"[JARVIS Timer] FIRE: {message}")
    if _notify_callback:
        _notify_callback(message)


# ── Timer creation ─────────────────────────────────────────────────────────────

def set_timer(seconds: int, label: str = "Timer") -> str:
    """
    Set a countdown timer.

    Args:
        seconds: How many seconds to wait
        label:   Name of the timer

    Returns:
        Confirmation string
    """
    if seconds <= 0:
        return "That's not a valid duration, sir."

    timer_id = time.time()

    def _run():
        time.sleep(seconds)
        msg = f"⏰ **{label}** — Time's up, sir!"
        _fire(msg)
        with _timers_lock:
            _timers[:] = [t for t in _timers if t["id"] != timer_id]

    t = threading.Thread(target=_run, daemon=True, name=f"Timer-{label}")
    t.start()

    with _timers_lock:
        _timers.append({"id": timer_id, "label": label, "fires_at": time.time() + seconds})

    # Human-readable duration
    if seconds >= 3600:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        dur = f"{h}h {m}m" if m else f"{h} hour{'s' if h > 1 else ''}"
    elif seconds >= 60:
        m = seconds // 60
        s = seconds % 60
        dur = f"{m}m {s}s" if s else f"{m} minute{'s' if m > 1 else ''}"
    else:
        dur = f"{seconds} second{'s' if seconds > 1 else ''}"

    return f"⏱️ Timer set for **{dur}**. I'll notify you when it's done, sir."


def set_reminder(message: str, seconds: int) -> str:
    """
    Set a named reminder.

    Args:
        message: What to remind the user about
        seconds: When to fire

    Returns:
        Confirmation string
    """
    return set_timer(seconds, label=f"Reminder: {message}")


def list_timers() -> str:
    """Return list of active timers."""
    with _timers_lock:
        active = list(_timers)

    if not active:
        return "No active timers or reminders, sir."

    now = time.time()
    lines = ["⏱️ **Active Timers:**"]
    for t in active:
        remaining = max(0, int(t["fires_at"] - now))
        m, s = divmod(remaining, 60)
        lines.append(f"  • **{t['label']}** — {m}m {s}s remaining")
    return "\n".join(lines)


def cancel_all_timers() -> str:
    """Cancel all active timers."""
    with _timers_lock:
        count = len(_timers)
        _timers.clear()
    return f"Cancelled {count} timer{'s' if count != 1 else ''}, sir." if count else "No timers to cancel, sir."


# ── Natural language parser ────────────────────────────────────────────────────

def parse_duration(text: str) -> int | None:
    """
    Extract a duration in seconds from natural language.

    Examples:
        "10 minutes"         → 600
        "2 hours 30 minutes" → 9000
        "45 seconds"         → 45
        "1.5 hours"          → 5400

    Returns:
        Total seconds or None if not found
    """
    text = text.lower()
    total = 0
    found = False

    patterns = [
        (r'(\d+(?:\.\d+)?)\s*hour', 3600),
        (r'(\d+(?:\.\d+)?)\s*hr',   3600),
        (r'(\d+(?:\.\d+)?)\s*h\b',  3600),
        (r'(\d+(?:\.\d+)?)\s*min',  60),
        (r'(\d+(?:\.\d+)?)\s*m\b',  60),
        (r'(\d+(?:\.\d+)?)\s*sec',  1),
        (r'(\d+(?:\.\d+)?)\s*s\b',  1),
    ]

    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            total += float(match.group(1)) * multiplier
            found = True

    return int(total) if found and total > 0 else None


def handle_timer_command(text: str) -> str:
    """
    Parse and handle a full timer/reminder command from natural language.

    Examples:
        "set a timer for 5 minutes"
        "remind me in 1 hour to take my medicine"
        "timer 30 seconds"

    Returns:
        JARVIS response
    """
    text_lower = text.lower()

    # Check for list/show timers
    if any(p in text_lower for p in ["list timer", "show timer", "active timer", "what timers"]):
        return list_timers()

    # Check for cancel
    if any(p in text_lower for p in ["cancel timer", "stop timer", "cancel all"]):
        return cancel_all_timers()

    # Extract reminder message (after "to" keyword)
    reminder_match = re.search(
        r'remind(?:er)?\s+(?:me\s+)?(?:in\s+)?(.+?)\s+to\s+(.+)',
        text_lower, re.IGNORECASE
    )
    if reminder_match:
        duration_str = reminder_match.group(1)
        reminder_msg = reminder_match.group(2).strip()
        seconds = parse_duration(duration_str)
        if seconds:
            return set_reminder(reminder_msg, seconds)

    # Plain timer command
    seconds = parse_duration(text)
    if seconds:
        return set_timer(seconds)

    return "Please specify a duration, sir. For example: 'set a timer for 10 minutes'."
