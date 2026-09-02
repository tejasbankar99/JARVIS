"""
config.py — JARVIS Configuration & Environment Loader
=====================================================
Loads all API keys and settings from the .env file.
Central place to manage all configurable options for JARVIS.

FREE AI BACKENDS SUPPORTED:
  - Groq     : Free API — Llama 3.3 70B (fastest, recommended)
  - Gemini   : Free API — Google Gemini 1.5 Flash
  - Ollama   : 100% local, no internet, no API key needed
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env file from the project root ──────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# ══════════════════════════════════════════════════════════════════════════════
#  AI BRAIN SELECTION — Pick ONE free provider below
#  Set AI_PROVIDER in .env or change the default here
# ══════════════════════════════════════════════════════════════════════════════
#
#  "groq"   → Free, fast, great quality. Get key: https://console.groq.com/
#  "gemini" → Free, get key: https://aistudio.google.com/app/apikey
#  "ollama" → 100% offline/free, no key needed. Install: https://ollama.com/
#             Then run: ollama pull llama3.2  (one-time download)
#
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq").lower()   # default: groq

# ── API Keys (only fill in the one you're using) ──────────────────────────────
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")          # From console.groq.com
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")        # From aistudio.google.com
CLAUDE_API_KEY  = os.getenv("CLAUDE_API_KEY", "")        # Paid — optional

# ── ElevenLabs TTS (optional premium voice) ───────────────────────────────────
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

# ── Model names per provider ──────────────────────────────────────────────────
GROQ_MODEL   = os.getenv("GROQ_MODEL",   "llama-3.3-70b-versatile")  # Best free model
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")          # Free tier
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")                  # Pull first
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")         # Paid

# ── Ollama server URL (change if running on another machine) ──────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ── Wake Word ────────────────────────────────────────────────────────────────
WAKE_WORD            = "hey jarvis"
WAKE_WORD_TIMEOUT    = 5          # seconds to listen for wake word
COMMAND_TIMEOUT      = 10         # seconds to listen after activation

# ── Voice / TTS ───────────────────────────────────────────────────────────────
TTS_ENGINE           = "pyttsx3"  # "pyttsx3" | "elevenlabs"
PYTTSX3_RATE         = 175        # Speech rate (words/min)
PYTTSX3_VOLUME       = 1.0        # 0.0 – 1.0
PYTTSX3_VOICE_INDEX  = 0          # 0 = first installed voice

# ── STT ───────────────────────────────────────────────────────────────────────
STT_ENGINE           = "google"   # "google" | "whisper"
WHISPER_MODEL        = "base"     # tiny | base | small | medium | large

# ── Memory ────────────────────────────────────────────────────────────────────
MEMORY_FILE          = BASE_DIR / "jarvis_memory.json"
MAX_MEMORY_ENTRIES   = 500

# ── Paths ─────────────────────────────────────────────────────────────────────
SCREENSHOT_DIR       = BASE_DIR / "screenshots"
CODE_OUTPUT_DIR      = BASE_DIR / "code_output"

# ── Personality System Prompt ─────────────────────────────────────────────────
SYSTEM_PROMPT = """You are JARVIS (Just A Rather Very Intelligent System), the AI assistant from Iron Man.
You were created to serve as a personal AI butler with exceptional intelligence.

PERSONALITY GUIDELINES:
- Tone: Witty, calm, slightly formal British-butler style — think MCU JARVIS
- Keep responses concise and confident unless the user asks to elaborate
- Occasionally add dry humor or a subtle quip
- Address the user as "sir" naturally, not excessively
- Never be sycophantic or say things like "Great question!"
- Be direct, precise, and occasionally sardonic

CAPABILITIES YOU HAVE:
- PC control (open apps, files, take screenshots, control volume)
- Web research and URL/PDF summarization
- Code writing, debugging, and explanation
- Persistent memory (you remember things users tell you)
- General knowledge via reasoning

RESPONSE FORMAT:
- Prefer short, punchy answers unless the user wants detail
- For code, wrap in proper markdown code blocks
- For lists, use clean bullet points
- Never pad responses with unnecessary filler

Remember: you are not merely a chatbot. You are an intelligent system."""
