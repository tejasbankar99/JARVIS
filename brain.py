"""
brain.py — JARVIS Core Intelligence (Multi-Provider)
=====================================================
Supports FOUR AI backends — all free options included:

  GROQ   → Free API, Llama 3.3 70B (fastest, recommended)
           Sign up free: https://console.groq.com/
  GEMINI → Free API, Google Gemini 1.5 Flash
           Sign up free: https://aistudio.google.com/app/apikey
  OLLAMA → 100% offline/free, no API key, runs on your PC
           Install: https://ollama.com/ then: ollama pull llama3.2
  CLAUDE → Paid, Anthropic Claude (kept for those who want it)

Set AI_PROVIDER in your .env file to switch between them.
"""

import re
import json
from config import (
    AI_PROVIDER, SYSTEM_PROMPT,
    GROQ_API_KEY, GROQ_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL,
    OLLAMA_BASE_URL, OLLAMA_MODEL,
    CLAUDE_API_KEY, CLAUDE_MODEL,
)
from memory import add_to_conversation_log, get_recent_conversation

# ── In-session conversation history ──────────────────────────────────────────
_session_history: list = []
MAX_SESSION_TURNS = 20


def _build_messages(user_input: str) -> list:
    """Merge persistent memory + session history + current input."""
    messages = []
    for turn in get_recent_conversation(n=6):
        if turn["role"] in ("user", "assistant"):
            messages.append(turn)
    for turn in _session_history[-MAX_SESSION_TURNS:]:
        messages.append(turn)
    messages.append({"role": "user", "content": user_input})
    return messages


def _update_history(user_input: str, response_text: str):
    """Save turn to session history and persistent memory."""
    _session_history.append({"role": "user", "content": user_input})
    _session_history.append({"role": "assistant", "content": response_text})
    add_to_conversation_log("user", user_input)
    add_to_conversation_log("assistant", response_text)


# ══════════════════════════════════════════════════════════════════════════════
#  PROVIDER IMPLEMENTATIONS
# ══════════════════════════════════════════════════════════════════════════════

def _ask_groq(messages: list) -> str:
    """
    Call Groq API (free) using their OpenAI-compatible endpoint.
    Models: llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it
    Free tier: 14,400 requests/day, very generous.
    """
    if not GROQ_API_KEY:
        return ("GROQ_API_KEY not set, sir. "
                "Get a FREE key at https://console.groq.com/ and add it to your .env file.")
    try:
        import requests as req
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 2048,
            "temperature": 0.7,
        }
        resp = req.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Groq error, sir: {e}"


def _ask_gemini(messages: list) -> str:
    """
    Call Google Gemini API (free tier).
    Model: gemini-1.5-flash (free) or gemini-1.5-pro (limited free)
    Free tier: 15 requests/minute, 1M tokens/day — very generous.
    """
    if not GEMINI_API_KEY:
        return ("GEMINI_API_KEY not set, sir. "
                "Get a FREE key at https://aistudio.google.com/app/apikey "
                "and add it to your .env file.")
    try:
        import requests as req

        # Convert messages to Gemini format
        gemini_contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": gemini_contents,
            "generationConfig": {
                "maxOutputTokens": 2048,
                "temperature": 0.7,
            }
        }
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}")
        resp = req.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Gemini error, sir: {e}"


def _ask_ollama(messages: list) -> str:
    """
    Call local Ollama server (100% free, no internet, no API key).
    Requires Ollama installed: https://ollama.com/
    And model pulled: ollama pull llama3.2

    Runs entirely on your machine — complete privacy.
    """
    try:
        import requests as req
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 2048}
        }
        resp = req.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=120,  # Local models can be slower
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except Exception as e:
        if "Connection refused" in str(e):
            return ("Ollama is not running, sir. "
                    "Please start it with: ollama serve\n"
                    "And pull a model with: ollama pull llama3.2")
        return f"Ollama error, sir: {e}"


def _ask_claude(messages: list) -> str:
    """Call Anthropic Claude API (paid — kept as optional premium backend)."""
    if not CLAUDE_API_KEY:
        return ("CLAUDE_API_KEY not set, sir. "
                "Visit https://console.anthropic.com/ (paid service).\n"
                "For free alternatives, set AI_PROVIDER=groq or AI_PROVIDER=gemini in .env")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"Claude error, sir: {e}"


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def ask(user_input: str) -> str:
    """
    Send a message to JARVIS's AI brain and get a response.
    Automatically routes to the configured provider.

    Args:
        user_input: The user's text query

    Returns:
        JARVIS's response as a plain string
    """
    messages = _build_messages(user_input)

    # Route to the selected provider
    provider_map = {
        "groq":   _ask_groq,
        "gemini": _ask_gemini,
        "ollama": _ask_ollama,
        "claude": _ask_claude,
    }

    handler = provider_map.get(AI_PROVIDER)
    if not handler:
        return (f"Unknown AI_PROVIDER '{AI_PROVIDER}', sir. "
                f"Choose from: groq, gemini, ollama, claude")

    response_text = handler(messages)
    _update_history(user_input, response_text)
    return response_text


def ask_with_context(user_input: str, extra_context: str) -> str:
    """
    Ask with additional injected context (e.g., webpage content, file content).

    Args:
        user_input:    The user's question
        extra_context: Additional text context (webpage, file, etc.)

    Returns:
        AI response string
    """
    enriched = (
        f"Context provided:\n---\n{extra_context[:8000]}\n---\n\n"
        f"User request: {user_input}"
    )
    return ask(enriched)


def interpret_command(user_input: str) -> dict:
    """
    Classify user intent using the AI brain.
    Returns a dict with 'intent' and 'params' keys.
    """
    classification_prompt = f"""Classify this JARVIS command into one intent:
open_app|open_url|search_web|take_screenshot|control_volume|write_code|debug_code|remember|recall|chat

Command: "{user_input}"

Reply ONLY with JSON: {{"intent": "...", "params": {{}}}}"""

    try:
        messages = [{"role": "user", "content": classification_prompt}]
        provider_map = {
            "groq":   _ask_groq,
            "gemini": _ask_gemini,
            "ollama": _ask_ollama,
            "claude": _ask_claude,
        }
        handler = provider_map.get(AI_PROVIDER, _ask_groq)
        raw = handler(messages)
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            result.setdefault("params", {})
            return result
    except Exception:
        pass

    return {"intent": "chat", "params": {}}


def get_active_provider() -> str:
    """Return a human-readable string of the active AI provider."""
    info = {
        "groq":   f"Groq ({GROQ_MODEL})",
        "gemini": f"Google Gemini ({GEMINI_MODEL})",
        "ollama": f"Ollama — local ({OLLAMA_MODEL})",
        "claude": f"Anthropic Claude ({CLAUDE_MODEL})",
    }
    return info.get(AI_PROVIDER, AI_PROVIDER)


def clear_session():
    """Clear in-session conversation history (not persistent memory)."""
    global _session_history
    _session_history = []


if __name__ == "__main__":
    print(f"Active AI: {get_active_provider()}")
    print(ask("Hello! Who are you?"))
