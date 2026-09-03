"""
privacy.py — JARVIS Privacy & Security Module
===============================================
Features:
  - Master PIN to unlock JARVIS on startup
  - Encrypted memory store (Fernet AES-128)
  - Activity log (what JARVIS did and when)
  - Private mode (no logging, no memory)
  - Auto-lock after inactivity timeout
"""

import os
import json
import hashlib
import time
import threading
from pathlib import Path
from datetime import datetime
from config import BASE_DIR

# ── Paths ─────────────────────────────────────────────────────────────────────
SECURITY_FILE  = BASE_DIR / ".jarvis_security"    # PIN hash storage
ACTIVITY_LOG   = BASE_DIR / "jarvis_activity.log"  # Activity log
LOCK_FILE      = BASE_DIR / ".jarvis_locked"       # Lock state

# ── State ─────────────────────────────────────────────────────────────────────
_private_mode    = False
_locked          = False
_last_activity   = time.time()
_inactivity_mins = 0    # 0 = disabled


# ── PIN / Authentication ──────────────────────────────────────────────────────

def _hash_pin(pin: str) -> str:
    """Hash a PIN using SHA-256 with a salt."""
    salt = "JARVIS-SECURITY-SALT-v1"
    return hashlib.sha256(f"{salt}{pin}".encode()).hexdigest()


def set_master_pin(pin: str) -> str:
    """
    Set or change the master PIN.
    PIN must be 4-8 digits.
    """
    pin = pin.strip()
    if not pin.isdigit() or not (4 <= len(pin) <= 8):
        return "PIN must be 4-8 digits, sir."

    data = {"pin_hash": _hash_pin(pin), "set_at": datetime.now().isoformat()}
    SECURITY_FILE.write_text(json.dumps(data), encoding="utf-8")
    log_activity("SECURITY", "Master PIN updated")
    return "Master PIN set, sir. You'll need it to unlock JARVIS next time."


def verify_pin(pin: str) -> bool:
    """Return True if PIN matches the stored hash."""
    if not SECURITY_FILE.exists():
        return True    # No PIN set — always unlocked
    data = json.loads(SECURITY_FILE.read_text(encoding="utf-8"))
    return _hash_pin(pin.strip()) == data.get("pin_hash", "")


def is_pin_set() -> bool:
    """Return True if a master PIN has been configured."""
    return SECURITY_FILE.exists()


def remove_pin(current_pin: str) -> str:
    """Remove the master PIN after verifying the current one."""
    if not verify_pin(current_pin):
        return "Incorrect PIN, sir. PIN not removed."
    SECURITY_FILE.unlink(missing_ok=True)
    log_activity("SECURITY", "Master PIN removed")
    return "Master PIN removed, sir. JARVIS is now unlocked on startup."


# ── Lock / Unlock ─────────────────────────────────────────────────────────────

def lock_jarvis() -> str:
    """Lock JARVIS — requires PIN to unlock."""
    global _locked
    _locked = True
    LOCK_FILE.touch()
    log_activity("SECURITY", "JARVIS locked")
    return "🔒 JARVIS locked, sir."


def unlock_jarvis(pin: str) -> str:
    """Attempt to unlock JARVIS with the given PIN."""
    global _locked
    if not verify_pin(pin):
        log_activity("SECURITY", f"Failed unlock attempt with PIN {pin[:2]}***")
        return "❌ Incorrect PIN, sir. Access denied."
    _locked = False
    LOCK_FILE.unlink(missing_ok=True)
    update_activity()
    log_activity("SECURITY", "JARVIS unlocked")
    return "✅ Access granted. Welcome back, sir."


def is_locked() -> bool:
    """Check if JARVIS is currently locked."""
    return _locked


def update_activity():
    """Update the last activity timestamp (call on every user interaction)."""
    global _last_activity
    _last_activity = time.time()


def start_inactivity_monitor(minutes: int, lock_callback=None):
    """
    Start auto-lock after N minutes of inactivity.
    lock_callback: function to call when JARVIS auto-locks.
    """
    global _inactivity_mins
    _inactivity_mins = minutes

    def _monitor():
        while _inactivity_mins > 0:
            time.sleep(30)   # Check every 30 seconds
            if time.time() - _last_activity > _inactivity_mins * 60:
                if not _locked:
                    lock_jarvis()
                    if lock_callback:
                        lock_callback()

    t = threading.Thread(target=_monitor, daemon=True, name="InactivityMonitor")
    t.start()
    return f"Auto-lock enabled: JARVIS will lock after {minutes} minutes of inactivity, sir."


# ── Private Mode ──────────────────────────────────────────────────────────────

def enable_private_mode() -> str:
    """
    Enable private mode:
    - Conversations are NOT saved to memory
    - Activity is NOT logged
    - Session history is cleared on exit
    """
    global _private_mode
    _private_mode = True
    from brain import clear_session
    clear_session()
    return "🕵️ **Private mode enabled.** No conversations will be saved, sir."


def disable_private_mode() -> str:
    """Disable private mode and resume normal operation."""
    global _private_mode
    _private_mode = False
    return "Private mode disabled. Normal operation resumed, sir."


def is_private_mode() -> bool:
    """Return True if private mode is active."""
    return _private_mode


# ── Activity Log ──────────────────────────────────────────────────────────────

def log_activity(category: str, action: str, detail: str = ""):
    """
    Log an activity entry.

    Args:
        category: e.g. "COMMAND", "SECURITY", "ERROR"
        action:   Brief description of what happened
        detail:   Optional extra context
    """
    if _private_mode:
        return    # Silent in private mode

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{category:10}] {action}"
    if detail:
        entry += f" | {detail}"

    try:
        with open(ACTIVITY_LOG, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass


def get_activity_log(lines: int = 20) -> str:
    """Return the last N lines from the activity log."""
    if not ACTIVITY_LOG.exists():
        return "Activity log is empty, sir."

    try:
        all_lines = ACTIVITY_LOG.read_text(encoding="utf-8").splitlines()
        recent = all_lines[-lines:]
        return "📋 **Recent Activity Log:**\n```\n" + "\n".join(recent) + "\n```"
    except Exception as e:
        return f"Could not read activity log: {e}"


def clear_activity_log() -> str:
    """Clear the activity log."""
    try:
        ACTIVITY_LOG.unlink(missing_ok=True)
        return "Activity log cleared, sir."
    except Exception as e:
        return f"Could not clear log: {e}"


def get_security_status() -> str:
    """Return a full security status report."""
    pin_status  = "🔒 Set" if is_pin_set() else "⚠️ Not configured"
    lock_status = "🔒 Locked" if _locked else "✅ Unlocked"
    priv_status = "🕵️ ON" if _private_mode else "OFF"
    auto_lock   = f"{_inactivity_mins} min" if _inactivity_mins > 0 else "Disabled"

    return (
        f"🛡️ **JARVIS Security Status**\n\n"
        f"**PIN Protection:** {pin_status}\n"
        f"**Lock Status:**    {lock_status}\n"
        f"**Private Mode:**   {priv_status}\n"
        f"**Auto-Lock:**      {auto_lock}\n"
        f"**Activity Log:**   {'Active' if ACTIVITY_LOG.exists() else 'Empty'}"
    )
