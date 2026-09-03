"""
memory.py — JARVIS Persistent Memory System
============================================
Stores and retrieves facts, notes, and contextual info the user tells JARVIS.
All data is saved to a local JSON file so memory persists across sessions.
"""

import json
import datetime
from pathlib import Path
from config import MEMORY_FILE, MAX_MEMORY_ENTRIES


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load() -> dict:
    """Load the full memory store from disk. Returns empty structure if missing."""
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"entries": [], "facts": {}}
    return {"entries": [], "facts": {}}


def _save(data: dict) -> None:
    """Persist the memory store to disk."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Public API ────────────────────────────────────────────────────────────────

def remember(key: str, value: str) -> str:
    """
    Store a named fact.
    Example: remember("project", "Building JARVIS with Python")
    Returns confirmation string.
    """
    data = _load()
    data["facts"][key.lower().strip()] = {
        "value": value,
        "timestamp": datetime.datetime.now().isoformat()
    }

    # Also add to chronological log
    data["entries"].append({
        "type": "fact",
        "key": key.lower().strip(),
        "value": value,
        "timestamp": datetime.datetime.now().isoformat()
    })

    # Trim old entries if over limit
    if len(data["entries"]) > MAX_MEMORY_ENTRIES:
        data["entries"] = data["entries"][-MAX_MEMORY_ENTRIES:]

    _save(data)
    return f"Noted, sir. I'll remember that {key} is: {value}"


def recall(query: str) -> str:
    """
    Retrieve a stored fact by keyword search.
    Searches both keys and values for the query term.
    Returns the result or a polite "nothing found" message.
    """
    data = _load()
    query_lower = query.lower().strip()

    # Direct key match first
    if query_lower in data["facts"]:
        entry = data["facts"][query_lower]
        return f"You told me that {query_lower} is: {entry['value']} (stored on {entry['timestamp'][:10]})"

    # Fuzzy search through keys and values
    matches = []
    for key, entry in data["facts"].items():
        if query_lower in key or query_lower in entry["value"].lower():
            matches.append(f"• {key}: {entry['value']}")

    if matches:
        return "Here's what I found in memory, sir:\n" + "\n".join(matches)

    return f"I'm afraid I don't have anything stored about '{query}', sir."


def remember_note(note: str) -> str:
    """
    Store a free-form note without a specific key.
    Auto-generates a timestamp-based key.
    """
    data = _load()
    key = f"note_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    data["entries"].append({
        "type": "note",
        "key": key,
        "value": note,
        "timestamp": datetime.datetime.now().isoformat()
    })

    if len(data["entries"]) > MAX_MEMORY_ENTRIES:
        data["entries"] = data["entries"][-MAX_MEMORY_ENTRIES:]

    _save(data)
    return "Noted, sir. I've logged that for you."


def get_all_memory() -> str:
    """Return a formatted summary of everything in memory."""
    data = _load()

    if not data["facts"] and not data["entries"]:
        return "Memory banks are empty, sir. A blank slate."

    output = ["=== JARVIS Memory Store ===\n"]

    if data["facts"]:
        output.append("📌 Named Facts:")
        for key, entry in data["facts"].items():
            output.append(f"  • {key}: {entry['value']}")
        output.append("")

    notes = [e for e in data["entries"] if e["type"] == "note"]
    if notes:
        output.append("📝 Notes:")
        for note in notes[-10:]:  # Show last 10 notes
            output.append(f"  • [{note['timestamp'][:10]}] {note['value']}")

    return "\n".join(output)


def clear_memory() -> str:
    """Wipe all stored memory. Use with caution."""
    _save({"entries": [], "facts": {}})
    return "Memory cleared, sir. Starting fresh."


def add_to_conversation_log(role: str, content: str) -> None:
    """
    Append a conversation turn to the memory log.
    Used by brain.py to maintain context across turns.
    """
    data = _load()
    data["entries"].append({
        "type": "conversation",
        "role": role,
        "value": content[:500],  # Truncate long entries
        "timestamp": datetime.datetime.now().isoformat()
    })
    if len(data["entries"]) > MAX_MEMORY_ENTRIES:
        data["entries"] = data["entries"][-MAX_MEMORY_ENTRIES:]
    _save(data)


def get_recent_conversation(n: int = 10) -> list:
    """
    Return the last n conversation turns for context injection.
    Returns list of {"role": ..., "content": ...} dicts.
    """
    data = _load()
    conv_entries = [e for e in data["entries"] if e.get("type") == "conversation"]
    recent = conv_entries[-n:]
    return [{"role": e["role"], "content": e["value"]} for e in recent]


if __name__ == "__main__":
    # Quick test
    print(remember("project", "Building JARVIS with Python"))
    print(recall("project"))
    print(get_all_memory())
